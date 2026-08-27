# Settings Center

Program installer using GNU Make.

## Requirements

- Python 3
- GTK 3
- PyGObject (`python3-gi`)
- GTK 3 introspection (`gir1.2-gtk-3.0`)
- `GioUnix` available via PyGObject

## Installation

In the project directory:

```bash
make
make install
```

By default, the program will be installed to:

- `~/.local/bin/settings-center`
- `~/.local/share/applications/settings-center.desktop`

If `~/.local/bin` is not in the `PATH`, you can run:

```bash
~/.local/bin/settings-center
```

After installation, the launcher should be available in the applications menu.

## Launching without installation

```bash
make run
```

## Uninstalling

```bash
make uninstall
```

## Other prefix

You can change the installation location:

```bash
make install PREFIX=/usr/local
```

You can also use `DESTDIR` for system packaging:

```bash
make install PREFIX=/usr DESTDIR=/tmp/package
```

## Note

The program does not include its own icon. Activator icons are taken from their `.desktop` files and the installed GTK icon theme.
