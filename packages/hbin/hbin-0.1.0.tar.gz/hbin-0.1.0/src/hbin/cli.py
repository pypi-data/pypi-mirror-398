#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import subprocess
from datetime import datetime
import shutil
import os

def main():
    pass

if __name__ == "__main__":
    main()

DEFAULT_LAST = 100
HISTORY_FILE = Path.home() / ".bash_history"
HBIN_DIR = Path.home() / ".hbin"
SAVE_DIR = Path.home() / ".hbin" / "saved"
HELP_LINE = (
    "ℹ `hbin` actions. NOTE, actions cannot be combined: \n"
    "-------------------------------------------------- \n"
    "-r (refresh history) \n"
    "-n NUM (show last NUM lines of history - goes into buffer) \n"
    "       (no flag: equivalent to -n 100) \n"
    "-c LIST (snip history; eg 1,3,5-9 - goes into buffer) \n"
    "        (COMMA-SEP, NO SPACES, ignores unmatched) \n"
    "-b (show what's in the buffer - from last -n or -c) \n"
    "-s NAME (save latest output - the buffer - as a snippet) \n"
    "        (saving overwrites on name without warning!) \n"
    "-k NUM (delete the saved snippet) \n"
    "       (deleting does so without warning!) \n"
    "-l (list saved snippets) \n"
    "-d NUM (display saved snippet) \n"
    "-e NUM (edit saved snippet) \n"
    "-x NUM (execute saved snippet) \n"
    "-p NUM (paste saved snippet to paste.rs) \n"
    "-f NUM (export saved snippet as a shell script file) \n"
    "-u [USER] (get or set username) \n"
    "-h (this help)"
)
BOLD = "\033[1m"
RESET = "\033[0m"

def get_config_value(key):
    config_file = Path.home() / ".hbin" / "config"
    if not config_file.exists():
        return None

    for line in config_file.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip() or None
    return None

def set_config_value(key, value):
    config_dir = Path.home() / ".hbin"
    config_file = config_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    if config_file.exists():
        lines = config_file.read_text().splitlines()

    updated = False
    out = []

    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            updated = True
        else:
            out.append(line)

    if not updated:
        out.append(f"{key}={value}")

    config_file.write_text("\n".join(out) + "\n")

def detect_editors():
    editors = []

    env_editor = os.environ.get("EDITOR")
    if env_editor and shutil.which(env_editor):
        editors.append(env_editor)

    for ed in ["nano", "vim", "vi", "micro", "nvim"]:
        if shutil.which(ed) and ed not in editors:
            editors.append(ed)

    return editors
    
def print_help_line():
    print(HELP_LINE)

def parse_snip(expr):
    result = set()
    for part in expr.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            if a.isdigit() and b.isdigit():
                result.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            result.add(int(part))
    return sorted(result)

def get_saved_files():
    if not SAVE_DIR.exists():
        return []
    return sorted(p for p in SAVE_DIR.iterdir() if p.is_file())

def get_saved_latest():
    if not HBIN_DIR.exists():
        return None
    for p in HBIN_DIR.iterdir():
        if p.is_file() and p.name == '.latest':
            return p
    return None

def save_latest_result(display_output):
    HBIN_DIR.mkdir(parents=True, exist_ok=True)
    save_path = HBIN_DIR / '.latest'

    with save_path.open("w") as f:
        for _, cmd in display_output:  # unpack the tuple
            f.write(cmd + "\n")

def save_to_file(lines, name):
    export_dir = HBIN_DIR / "exported"
    export_dir.mkdir(parents=True, exist_ok=True)

    file_path = export_dir / f"{name}.sh"

    with file_path.open("w") as f:
        for line in lines:
            f.write(line + "\n")

    return file_path

def get_username():
    config_file = Path.home() / ".hbin" / "config"
    if not config_file.exists():
        return "anon"

    for line in config_file.read_text().splitlines():
        if line.startswith("username="):
            value = line.split("=", 1)[1].strip()
            return value if value else "anon"

    return "anon"

# Disable default argparse help
parser = argparse.ArgumentParser(add_help=False)

parser.add_argument("-n", "--last", type=int, metavar="N")
parser.add_argument("-c", "--snip", metavar="LIST")
parser.add_argument("-s", "--save", metavar="NAME", nargs="?")
parser.add_argument(
    "-b", "--buffer",
    nargs="?",
    const=True,
    help="Show what’s in the buffer"
)
parser.add_argument("-l", "--list", action="store_true")
parser.add_argument("-d", "--display", type=int, metavar="NUM")
parser.add_argument("-k", "--delete", type=int, metavar="NUM")
parser.add_argument("-x", "--execute", type=int, metavar="NUM")
parser.add_argument("-h", "--help", action="store_true")
parser.add_argument(
    "-r", "--refresh",
    action="store_true",
    help="Refresh bash history from current shell session"
)
parser.add_argument(
    "-p", "--paste",
    type=int,
    metavar="NUM")
parser.add_argument(
    "-f", "--file",
    type=int,
    metavar="NUM")
parser.add_argument(
    "-u", "--username",
    metavar="VALUE",
    nargs="?",
    const=True)
parser.add_argument(
    "-e", "--edit",
    type=int,
    metavar="NUM")

args = parser.parse_args()

# ---- SET USERNAME ----
if args.username is True:
    # -u with NO value → show username
    print("ℹ User name:")
    print(f'"{get_username()}"')
    sys.exit(0)

elif args.username is not None:
    config_dir = Path.home() / ".hbin"
    config_file = config_dir / "config"

    config_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    if config_file.exists():
        lines = config_file.read_text().splitlines()

    updated = False
    new_lines = []

    for line in lines:
        if line.startswith("username="):
            new_lines.append(f"username={args.username}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"username={args.username}")

    config_file.write_text("\n".join(new_lines) + "\n")

    print("ℹ User name set to:")
    print(f'"{args.username}"')
    sys.exit(0)

# ---- REFRESH BASH HISTORY ----
if args.refresh:
    subprocess.run(
        ["bash", "-c", "history -a"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print('✓ BASH history refreshed..')
    sys.exit(0)
    
# ---- HANDY HELP ----
if args.help:
    print_help_line()
    sys.exit(0)

# ---- PASTE OR EXPORT SAVED FILE ----
if args.paste is not None or args.file is not None:
    files = get_saved_files()
    if not files:
        print("✗ No saved history files found!")
        sys.exit(1)

    if args.paste:
        idx = args.paste - 1
    else:
        idx = args.file - 1

    if idx < 0 or idx >= len(files):
        print(f"✗ Error: invalid file number!")
        sys.exit(1)

    snippet_file = files[idx]
    snippet_name = snippet_file.name
    raw_content = snippet_file.read_text()

    saved_ts = datetime.fromtimestamp(snippet_file.stat().st_mtime)
    saved_str = saved_ts.strftime("%Y-%m-%d %H:%M:%S")

    username = get_username()

    content = (
        f"#!/usr/bin/env bash\n\n"
        f'# Exported with hbin using saved snippet "{snippet_name}". \n'
        f'# Saved {saved_str}, by user "{username}".\n\n'
        f'{raw_content}'
    )

    if args.paste is not None:
        print("⚠ Uploading snippet to paste service..", flush=True)

        try:
            result = subprocess.run(
                ["curl", "-#S", "--data-binary", "@-", "https://paste.rs"],
                input=content,
                text=True,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            print("✗ Error: failed to upload to paste service!")
            sys.exit(1)

        print('✓ Snippet uploaded, here\'s your pasted URL:')
        print(result.stdout.strip())

    else:
        print(f"⚠ Exporting snippet '{snippet_name}' to file..", flush=True)
        exported = save_to_file(content.splitlines(), snippet_name)
        print('✓ Snippet exported, here\'s your script file:')
        print(exported)

    sys.exit(0)

# ---- EDIT SAVED SNIPPET ----
if args.edit is not None:
    files = get_saved_files()
    if not files:
        print("✗ No saved snippets found.")
        sys.exit(1)

    idx = args.edit - 1
    if idx < 0 or idx >= len(files):
        print(f"✗ Error: invalid snippet number {args.edit}")
        sys.exit(1)

    snippet = files[idx]

    editor = get_config_value("editor")

    if not editor:
        editors = detect_editors()
        if not editors:
            print("✗ No editor found. Set one with: hbin.py -u editor=<editor>")
            sys.exit(1)

        if len(editors) == 1:
            editor = editors[0]
        else:
            print("Select editor:")
            for i, ed in enumerate(editors, start=1):
                print(f" {i}) {ed}")

            choice = input("Choice: ").strip()
            if not choice.isdigit() or not (1 <= int(choice) <= len(editors)):
                sys.exit(0)

            editor = editors[int(choice) - 1]

        set_config_value("editor", editor)
        print(f'✓ Editor set to:\n "{editor}"')

    subprocess.run([editor, str(snippet)])
    
    files = get_saved_files()
    with files[idx].open() as f:
        print(f"{BOLD}{f.read()}{RESET}", end="")

    print(f"↑ Displayed snippet (after edit): {idx+1}. → {files[idx].name}.", file=sys.stderr)
    
    sys.exit(0)
    
# ---- DISPLAY SAVED FILE ----
if args.display is not None:
    files = get_saved_files()
    if not files:
        print("✗ No saved history files found.")
        sys.exit(1)

    idx = args.display - 1
    if idx < 0 or idx >= len(files):
        print(f"✗ Error: invalid file number {args.display}")
        sys.exit(1)

    with files[idx].open() as f:
        print(f"{BOLD}{f.read()}{RESET}", end="")

    print(f"↑ Displayed snippet: {idx+1}. → {files[idx].name}.", file=sys.stderr)

    sys.exit(0)

# ---- DELETE SAVED FILE ----
if args.delete is not None:
    files = get_saved_files()
    if not files:
        print("✗ No saved history files found.")
        sys.exit(1)

    idx = args.delete - 1
    if idx < 0 or idx >= len(files):
        print(f"✗ Error: invalid file number {args.delete}")
        sys.exit(1)

    deleted = files[idx].name
    files[idx].unlink()

    print(f"✓ Deleted snippet: {idx+1}. → {deleted}.", file=sys.stderr)
    
# ---- LIST SAVED FILES ----
if args.list or args.delete is not None:
    files = get_saved_files()
    if not files:
        print("✗ No saved history files found.")
    else:
        for i, f in enumerate(files, start=1):
            print(f"{BOLD}{i:3d}. → {f.name}{RESET}")
        print('↑ Listed your saved snippets.')
    sys.exit(0)

# ---- EXECUTE SAVED FILE ----
if args.execute is not None:
    files = get_saved_files()
    if not files:
        print("No saved history files found.")
        sys.exit(1)

    idx = args.execute - 1
    if idx < 0 or idx >= len(files):
        print(f"✗ Error: invalid file number {args.execute}")
        sys.exit(1)

    commands = files[idx].read_text().splitlines()
    commands = [c for c in commands if c.strip()]

    if not commands:
        print("✗ Saved file is empty.")
        sys.exit(0)

    # Display commands
    for cmd in commands:
        print(f"{BOLD}{cmd}{RESET}")

    print("↑ You are about to run *all* these commands in the order shown. Please be careful.")
    resp = input("Do you wish to proceed? y/N: ").strip()

    if resp != "y":
        print("✗ Aborted.")
        sys.exit(0)

    # Execute commands
    for cmd in commands:
        subprocess.run(
            ["bash", "-c", cmd],
            check=False
        )

    print("✓ Execution complete.")
    sys.exit(0)

# ---- VALIDATE SAVE FLAG ----
if args.save is None and "-s" in sys.argv:
    print("✗ Error: -s requires a file name (e.g. -s mycommands)")
    sys.exit(1)

# ---- SAVE LAST OUTPUT ----
if args.save:
    display_output = get_saved_latest().read_text().splitlines()

    # SAVE_DIR.mkdir(parents=True, exist_ok=True)
    save_path = SAVE_DIR / args.save

    with save_path.open("w") as f:
        for cmd in display_output:  # unpack the tuple
            f.write(cmd + "\n")

    print(f"✓ Saved last output/buffer ({len(display_output)} lines) as \'{args.save}\".")
    sys.exit(0)
    
# ---- SHOW LAST OUTPUT ----
if args.buffer is True:
    latest = get_saved_latest()
    if not latest:
        print("✗ No buffered output found.")
        sys.exit(1)

    print(f"{BOLD}{latest.read_text()}{RESET}", end="")
    print("↑ Dislpayed buffer.")
    sys.exit(0)

if not HISTORY_FILE.exists():
    print("✗ No ~/.bash_history file found.")
    sys.exit(1)

# ---- LOAD HISTORY ----
lines = HISTORY_FILE.read_text(errors="ignore").splitlines()
lines = [line for line in lines if line.strip()]
total = len(lines)

# ---- BUILD DISPLAY OUTPUT ----
if args.snip:
    # -f: show specific line numbers
    wanted_set = set(parse_snip(args.snip))
    display_output = [(i+1, line) for i, line in enumerate(lines) if (i+1) in wanted_set]

else:
    # -n or default: show last N lines
    last_n = args.last if args.last is not None else DEFAULT_LAST
    start_index = max(total - last_n, 0)
    display_output = list(enumerate(lines[start_index:], start=start_index + 1))

save_latest_result(display_output)

# ---- DISPLAY HISTORY ----
for i, cmd in display_output:
    print(f"{BOLD}{i:5d}  {cmd}{RESET}")

if args.snip:
    print(f"↑ Displayed your ({len(display_output)} lines) snipped selection entries.")
else:
    print(f"↑ Displayed last {len(display_output)} of {total} total history entries. ")
    if args.last is None:
        print('ℹ Use the -h (--help) flag for usage.')
