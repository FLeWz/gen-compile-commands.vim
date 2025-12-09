#!/usr/bin/env python3
import json
import os
import shlex
import subprocess
import sys

def detect_compiler_names():
    """
    Determine compiler executable names the Makefile might use.
    Includes:
      - the CC env var (first token only)
      - fallback common compilers
    """
    compilers = ["gcc", "g++"]

    cc_env = os.environ.get("CC")
    if cc_env:
        tokens = shlex.split(cc_env)
        if tokens:
            compilers.append(tokens[0])  # actual compiler executable

    # Remove duplicates while keeping order
    seen = set()
    out = []
    for c in compilers:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return tuple(out)


def run_make_dry_run(make_args):
    """Run `make -n` and capture output."""
    result = subprocess.run(
        ["make", "-n"] + make_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.stdout


def extract_compile_commands(make_output, compiler_prefixes):
    """Parse compiler commands from make -n output."""
    compile_cmds = []

    for line in make_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Check whether line starts with any valid compiler executable
        if not any(stripped.startswith(c) for c in compiler_prefixes):
            continue

        # Tokenize safely
        parts = shlex.split(stripped)

        # Identify source file
        src = None
        for p in parts:
            if p.endswith((".c", ".cc", ".cpp", ".cxx")):
                src = p
                break
        if not src:
            continue

        entry = {
            "directory": os.getcwd(),
            "command": stripped,
            "file": src,
        }
        compile_cmds.append(entry)

    return compile_cmds


def write_compile_commands(entries, output_file="compile_commands.json"):
    with open(output_file, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Generated {output_file} with {len(entries)} entries.")


def main():
    make_args = sys.argv[1:]
    compiler_prefixes = detect_compiler_names()

    print("Detected compiler prefixes:", compiler_prefixes)
    print("Running make in dry-run mode...")

    out = run_make_dry_run(make_args)

    print("Extracting compile commands...")
    entries = extract_compile_commands(out, compiler_prefixes)

    if not entries:
        print("Warning: no compile commands detected. Try `make clean` then rerun.")

    write_compile_commands(entries)


if __name__ == "__main__":
    main()
