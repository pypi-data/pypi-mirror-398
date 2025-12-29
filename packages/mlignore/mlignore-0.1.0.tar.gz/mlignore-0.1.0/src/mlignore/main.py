"""
mlignore: The Industrial-Grade Context Leakage Utility.
Optimized for feeding LLMs minified codebase contexts.
"""

import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set

import pathspec
import typer
from tree_sitter import Language, Node, Parser

# Language Bindings Initialization
try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjs
    import tree_sitter_css as tscss
except ImportError as error:
    logging.critical(f"Missing tree-sitter grammars: {error}")
    sys.exit(1)

# Configure logging to stderr to keep stdout clean for piping
logger = logging.getLogger("mlignore")
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

app = typer.Typer(
    help="Minify and pack your codebase for LLM consumption.",
    add_completion=False,
    no_args_is_help=True,
)


class ContextEngine:
    """Handles syntax-aware minification using Tree-sitter ASTs."""

    def __init__(self, smart_extensions: Set[str]):
        """
        Initializes the engine with specific language parsers.

        Args:
            smart_extensions: Extensions to be minified via Tree-sitter.
        """
        self.parsers: Dict[str, Parser] = {}
        self.smart_extensions = smart_extensions
        self._init_parsers()

    def _init_parsers(self) -> None:
        """Initializes tree-sitter parsers for supported languages."""
        try:
            self.parsers[".py"] = Parser(Language(tspython.language()))
            self.parsers[".js"] = Parser(Language(tsjs.language()))
            self.parsers[".jsx"] = Parser(Language(tsjs.language()))
            self.parsers[".css"] = Parser(Language(tscss.language()))
        except Exception as error:
            logger.error(f"Failed to initialize tree-sitter: {error}")

    def _is_python_docstring(self, node: Node) -> bool:
        """Determines if a Python AST node is a docstring."""
        if node.type != "expression_statement":
            return False
        child = node.named_children[0] if node.named_children else None
        return bool(
            child
            and child.type == "string"
            and node.parent
            and node.parent.type in ["module", "block"]
        )

    def _compress_python_indentation(self, code: str) -> str:
        """Compresses Python indentation to 1 space per level."""
        lines = code.splitlines()
        compressed = []
        for line in lines:
            if not line.strip():
                continue
            match = re.match(r"^(\s*)", line)
            whitespace = match.group(1) if match else ""
            tabs, spaces = whitespace.count("\t"), whitespace.count(" ")
            level = tabs + (spaces // 4 if spaces % 4 == 0 else spaces // 2)
            compressed.append(f"{' ' * level}{line.lstrip()}")
        return "\n".join(compressed)

    def _get_noise_ranges(self, node: Node, extension: str) -> List[tuple[int, int]]:
        """Finds byte ranges for comments and docstrings."""
        ranges = []
        comment_types = {"comment", "line_comment", "block_comment"}

        def traverse(n: Node):
            if n.type in comment_types or (
                extension == ".py" and self._is_python_docstring(n)
            ):
                ranges.append((n.start_byte, n.end_byte))
            for child in n.children:
                traverse(child)

        traverse(node)
        return sorted(ranges)

    def process_file(self, content: bytes, extension: str) -> str:
        """
        Minifies content based on file extension.

        Args:
            content: Raw file bytes.
            extension: The file extension (e.g., '.py').

        Returns:
            A cleaned and minified string.
        """
        if extension not in self.parsers:
            return content.decode("utf-8", errors="replace")

        parser = self.parsers[extension]
        tree = parser.parse(content)
        noise = self._get_noise_ranges(tree.root_node, extension)

        cleaned_parts = []
        last_index = 0
        for start, end in noise:
            cleaned_parts.append(
                content[last_index:start].decode("utf-8", errors="replace")
            )
            last_index = end
        cleaned_parts.append(content[last_index:].decode("utf-8", errors="replace"))

        output = "".join(cleaned_parts)
        if extension == ".py":
            return self._compress_python_indentation(output)

        # Standard minification for JS/CSS: remove empty lines and trim
        return "\n".join(
            [line.rstrip() for line in output.splitlines() if line.strip()]
        )


def load_ignore_spec(root: Path, filename: str) -> Optional[pathspec.PathSpec]:
    """Loads a pathspec from an ignore file."""
    path = root / filename
    if path.exists():
        try:
            return pathspec.PathSpec.from_lines(
                "gitwildmatch", path.read_text().splitlines()
            )
        except Exception as error:
            logger.warning(f"Skipping {filename} due to error: {error}")
    return None


def get_files(
    root: Path,
    exclude_dirs: Set[str],
    gitignore: Optional[pathspec.PathSpec],
    mlignore: Optional[pathspec.PathSpec],
) -> Generator[Path, None, None]:
    """Yields valid files while respecting ignore rules."""
    for path in sorted(root.rglob("*")):
        rel_path = path.relative_to(root)
        str_rel = str(rel_path)

        if any(part in exclude_dirs for part in rel_path.parts):
            continue
        if gitignore and gitignore.match_file(str_rel):
            continue
        if mlignore and mlignore.match_file(str_rel):
            continue

        if path.is_file():
            yield path


@app.command()
def main(
    root: Path = typer.Option(
        Path("."), "--root", "-r", help="The root directory of your project."
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Where to save the context. If omitted, prints to stdout.",
    ),
    exclude: str = typer.Option(
        "node_modules,dist,.venv,.git,build,__pycache__",
        help="Comma-separated list of directories to ignore.",
    ),
    smart_exts: str = typer.Option(
        ".py,.js,.jsx,.css", help="Extensions to minify using Tree-sitter."
    ),
    text_exts: str = typer.Option(
        "", help="Additional extensions to include as raw text (e.g., .md,.txt)."
    ),
    max_files: int = typer.Option(500, help="Maximum number of files to process."),
    max_size_kb: int = typer.Option(
        512, help="Skip files larger than this size in KB."
    ),
    silent: bool = typer.Option(
        False, "--silent", "-s", help="Suppress all logs in stderr."
    ),
):
    """
    Scans a codebase, minifies supported files, and packs them into a single context.

    If no output is provided, the result is printed to stdout, allowing you to use
    redirection (e.g., mlignore > context.md) or pipes.
    """
    logger.setLevel(logging.CRITICAL + 1 if silent else logging.INFO)

    s_exts = {e.strip().lower() for e in smart_exts.split(",") if e.strip()}
    t_exts = {e.strip().lower() for e in text_exts.split(",") if e.strip()}
    exclude_dirs = {d.strip() for d in exclude.split(",")}

    engine = ContextEngine(s_exts)
    root = root.resolve()

    gitignore = load_ignore_spec(root, ".gitignore")
    mlignore = load_ignore_spec(root, ".mlignore")

    out_handle = output.open("w", encoding="utf-8") if output else sys.stdout

    try:
        out_handle.write(f"# ML-Context Dump | {datetime.now().isoformat()}\n")
        out_handle.write(f"Root: `{root}`\n\n")

        file_count = 0
        for path in get_files(root, exclude_dirs, gitignore, mlignore):
            ext = path.suffix.lower()
            if ext not in s_exts and ext not in t_exts:
                continue

            # Performance: Skip large files early
            if path.stat().st_size > (max_size_kb * 1024):
                logger.warning(f"Skipping {path.name}: Exceeds {max_size_kb}KB")
                continue

            rel_path = path.relative_to(root)
            logger.info(f"Packing: {rel_path}")

            out_handle.write(f"### File: {rel_path}\n")
            out_handle.write(f"```{ext.lstrip('.') or 'text'}\n")

            try:
                content_bytes = path.read_bytes()
                out_handle.write(engine.process_file(content_bytes, ext))
            except Exception as error:
                out_handle.write(f"// Error reading file: {error}")

            out_handle.write("\n```\n")

            file_count += 1
            if file_count >= max_files:
                logger.info("Reached maximum file count limit.")
                break

        logger.info(f"Success! Processed {file_count} files.")

    except Exception as fatal:
        logger.critical(f"Fatal execution error: {fatal}")
        raise typer.Exit(code=1)
    finally:
        if output:
            out_handle.close()


if __name__ == "__main__":
    app()
