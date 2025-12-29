# `just_fix_windows_console`

A tiny, dependency-free Python module that does one thing and one thing only - enables ANSI / VT escape sequence processing on Windows consoles.

### Usage

```python
from just_fix_windows_console import just_fix_windows_console
just_fix_windows_console()

print("\x1b[32mHello, green world!\x1b[0m")
```
