#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from nrhgen.hasher import hash_text, hash_file, SUPPORTED_ALGOS
from rich.console import Console
from rich.text import Text

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description="nrhgen - Generate/Verify cryptographic hashes\nby noraraven"
    )
    parser.add_argument("-t", "--text", type=str, help="Text to hash")
    parser.add_argument("-f", "--file", type=str, nargs="+", help="One or more files to hash")
    parser.add_argument(
        "-a", "--algo", type=str, required=True, choices=SUPPORTED_ALGOS,
        help="Hashing algorithm (must be specified)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show filename, size, and hash for files")
    parser.add_argument("--verify", "-c", type=str, nargs="+",
                        help="Verify file(s) against given hash(es). Format: filename:hash")

    args = parser.parse_args()

    # Validate argument conflicts
    if args.text and args.file:
        console.print("[bold red]Error:[/] Cannot use --text and --file together")
        sys.exit(1)
    if args.verify and (args.text or args.file):
        console.print("[bold red]Error:[/] Cannot use --verify with --text or --file")
        sys.exit(1)
    if not (args.text or args.file or args.verify):
        console.print("[bold red]Error:[/] Please provide --text, --file, or --verify")
        sys.exit(1)

    try:
        # Text hashing
        if args.text:
            result = hash_text(args.text, args.algo)
            print(result)

        # File hashing
        if args.file:
            multiple = len(args.file) > 1
            for idx, file_path in enumerate(args.file):
                path = Path(file_path)
                if not path.exists() or not path.is_file():
                    console.print(f"[bold red]Error:[/] File not found: {file_path}")
                    continue

                result = hash_file(path, args.algo)
                filename_text = Text(f"{path.name}:", style="bold red")

                if args.verbose:
                    console.print(filename_text)
                    console.print(f"size: {path.stat().st_size} bytes")
                    print(result)
                    if idx < len(args.file) - 1:
                        print()  # blank line between files
                else:
                    console.print(filename_text, result)

        # Verify mode
        if args.verify:
            for item in args.verify:
                try:
                    filename, expected_hash = item.split(":", 1)
                except ValueError:
                    console.print(f"[bold red]Error:[/] Invalid format: {item}. Use filename:hash")
                    continue
                path = Path(filename)
                if not path.exists() or not path.is_file():
                    console.print(f"[bold red]Error:[/] File not found: {filename}")
                    continue
                actual_hash = hash_file(path, args.algo)
                filename_text = Text(f"{filename}:", style="bold red")
                if actual_hash.lower() == expected_hash.lower():
                    console.print(filename_text, "[bold green]OK[/]")
                else:
                    console.print(filename_text, "[bold red]FAILED[/]")
                    console.print(f"Expected: {expected_hash}")
                    console.print(f"Actual:   {actual_hash}")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)

