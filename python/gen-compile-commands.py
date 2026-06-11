#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys

# clang does not recognize lp64 arm flags
# and fails to start/provide hints
BAD_FLAGS = {
    "-mabi=lp64",
    "-mabi=lp64d",
}

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
    result = subprocess.run(
        ["make", "-n"] + make_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.stdout

def sanitize_command(cmd: str) -> str:
    parts = cmd.split()
    parts = [p for p in parts if p not in BAD_FLAGS]
    return " ".join(parts)

def extract_compile_commands(make_output, compiler_prefixes):
    compile_cmds = []

    for line in make_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Remove leading '@'
        stripped = stripped.lstrip("@").strip()

        # Remove surrounding parentheses: ( ... )
        if stripped.startswith("(") and stripped.endswith(")"):
            stripped = stripped[1:-1].strip()

        # Remove leading 'set ...;' chains
        stripped = re.sub(r'^\s*(set\s+[^\;]+;\s*)+', '', stripped)

        # Split chained commands on && and ;
        segments = re.split(r'\s*(?:&&|;)\s*', stripped)

        current_dir = os.getcwd()
        compiler_cmd = None

        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue

            # Ignore echo commands completely
            if seg.startswith("echo "):
                continue

            # Handle cd commands (cd dir, cd "dir", etc.)
            if seg.startswith("cd "):
                try:
                    parts = shlex.split(seg)
                    if len(parts) >= 2:
                        new_dir = parts[1]

                        if not os.path.isabs(new_dir):
                            current_dir = os.path.normpath(
                                os.path.join(current_dir, new_dir)
                            )
                        else:
                            current_dir = os.path.normpath(new_dir)
                except ValueError:
                    pass
                continue

            # Detect compiler invocation
            if any(seg.startswith(c) for c in compiler_prefixes):
                compiler_cmd = seg
                break

        if not compiler_cmd:
            continue

        # Tokenize compiler command safely
        try:
            parts = shlex.split(compiler_cmd)
        except ValueError:
            continue

        # Identify source file
        src = None
        for p in parts:
            if p.endswith((".c", ".cc", ".cpp", ".cxx")):
                src = p
                break
        if not src:
            continue

        # Normalize source path relative to final directory
        if not os.path.isabs(src):
            src = os.path.normpath(os.path.join(current_dir, src))

        clean_cmd = sanitize_command(compiler_cmd)

        entry = {
            "directory": current_dir,
            "command": clean_cmd,
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
