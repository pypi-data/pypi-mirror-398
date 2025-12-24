### `cli-clip` - console clipboard utilities


```sh
pip install cclip
uv tool install cclip
```

`cclip` provides two simple commandline scripts to interact with the system clipboard:
- `cclip` - copy stdin to clipboard (e.g. `echo "hello" | cclip`).
- `cpaste` - paste clipboard contents to stdout (e.g. `cpaste > file.txt`)

`c` in commands stands for "console".

`cclip` is using `pyperclip`, so it should be cross-platform.

I really liked `clip` on Windows and was always missing corresponding `paste` command, so here there are both.

Names were chosen to avoid collisions with `clip` on Windows and `paste` on Unix.
