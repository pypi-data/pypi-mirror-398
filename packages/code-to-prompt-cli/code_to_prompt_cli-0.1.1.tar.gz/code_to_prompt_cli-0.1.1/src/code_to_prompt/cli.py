"""
Codebase to LLM Prompt Converter

Recursively reads all code files in a folder and outputs them to a single .txt file
formatted for easy copy-pasting to AI chatbots.
"""

import argparse
import os
from pathlib import Path

INCLUDE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.html', '.css', '.scss', '.sass', '.less',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.md', '.rst', '.txt',
    '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd',
    '.java', '.kt', '.scala', '.go', '.rs', '.rb', '.php',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.m',
    '.sql', '.graphql', '.proto',
    '.env', '.gitignore', '.dockerignore',
}

SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    '.venv', 'venv', 'env', '.tox', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'dist', 'build',
    '.eggs', '.idea', '.vscode', '.vs',
}

SKIP_FILES = {'.DS_Store', 'Thumbs.db', '.gitkeep'}

SKIP_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
    '.exe', '.bin', '.class', '.jar',
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    '.woff', '.woff2', '.ttf', '.eot',
    '.lock', '.log', '.db', '.sqlite', '.sqlite3',
}


def should_include_file(path: Path, skip: set[str] | None) -> bool:
    if skip and path.name in skip:
        return False
    if path.name in SKIP_FILES:
        return False
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return False
    if path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True
    return not path.suffix and path.name in {
        "Dockerfile", "Makefile", "Procfile", "Gemfile"
    }


def get_files(folder: Path, skip: set[str] | None) -> list[Path]:
    files = []
    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(filenames):
            path = Path(root) / name
            if should_include_file(path, skip):
                files.append(path)
    return files


def folder_to_txt(folder_path: str, output: str | None, skip_files: list[str] | None):
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")

    output = output or f"{folder.name}_output.txt"
    skip = set(skip_files) if skip_files else None

    files = get_files(folder, skip)
    if not files:
        raise ValueError("No files found")

    lines = []
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        lines.append(str(path.relative_to(folder)))
        lines.append("```")
        lines.append(content.rstrip())
        lines.append("```")
        lines.append("")

    Path(output).write_text("\n".join(lines), encoding="utf-8")
    print(f"Created {output} ({len(files)} files)")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a code folder into a single LLM-ready text file"
    )
    parser.add_argument("folder")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--skip", nargs="+")
    args = parser.parse_args()

    folder_to_txt(args.folder, args.output, args.skip)
