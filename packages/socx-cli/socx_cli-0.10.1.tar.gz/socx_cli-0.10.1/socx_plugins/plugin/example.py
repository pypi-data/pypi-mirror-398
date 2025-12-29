"""Static Markdown content used by the plugin quickstart command."""

from __future__ import annotations

from rich.markdown import Markdown


QUICKSTART: Markdown = Markdown("""
# Plugin Example

This is a quickstart example to show how simple it is to write and add your
own custom plugin to *socx*.

As the matter of fact, the command you just ran to start this example, as well
as any other subcommand in `socx`, are all implemented as plugins.

## Adding a custom plugin

### Step 1 - Do the thing

Whatever it is you want your plugin to do, you need to have SOMETHING to do it,
whether its a python script, bash script, another cli, you need something.

For our purpose, a simple hello world would do:
```python
# hello_world.py
import os


def main():
    user = os.environ.get("USER")
    print(f"Hello {{user}}")
```

### Step 2 - Add the thing

Plugins can be added using the `socx plugin add` command.

You can also use the -n or --name flag to specify a name for the command,
otherwise, socx will use the function name as the name for the command:

```python
socx plugin add --name say-hello /path/to/hello_world.py main
```
""")
