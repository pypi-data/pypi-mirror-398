# hbin

> Save your Bash history as snippets!

`hbin` (or history-bin) is a CLI tool that allows you to save snippets of your Bash history. You can list, view, edit, delete, export, share, or run your saved history snippets at any time, using a simple command line interface (with zero external package deps). It works by viewing and slicing your history to extract specific lines you want to save as a snippet.

## Install

```bash
pip install hbin
```

## Usage

```
ℹ `hbin` command actions. NOTE: actions cannot be combined: 
----------------------------------------------------------
-r (refresh history) 
-n NUM (show last NUM lines of history - goes into buffer) 
       (no flag: equivalent to -n 100) 
-c LIST (snip history; eg 1,3,5-9 - goes into buffer) 
        (COMMA-SEP lines or ranges, ignores unmatched) 
-b (show what's in the buffer - from last -n or -c) 
-s NAME (save latest output - the buffer - as a snippet) 
        (saving overwrites on name without warning!) 
-k NUM (delete the saved snippet) 
       (deleting does so without warning!) 
-l (list saved snippets) 
-d NUM (display saved snippet) 
-e NUM (edit saved snippet) 
-x NUM (execute saved snippet) 
-p NUM (paste saved snippet to paste.rs) 
-f NUM (export saved snippet as a shell script file) 
-u [USER] (get or set username) 
-h (this help)
```

## FAQ

### Only Bash?

Yes, for now.

### Can I get involved?

Yes, you can. Pick a fix or enhancement from Codeberg, fork the repo, and issue a pull request when ready.

## Future features

- Support for other shells / switch between shells (zsh, fish, csh, etc..)
- Back-up / restore your snippets
- Search history to find relevant lines
- Multi-lingual
