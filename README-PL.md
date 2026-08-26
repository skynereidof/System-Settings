# Centrum ustawień

Instalator programu wykorzystujący GNU Make.

## Wymagania

- Python 3
- GTK 3
- PyGObject (`python3-gi`)
- introspekcja GTK 3 (`gir1.2-gtk-3.0`)
- `GioUnix` dostępne przez PyGObject

## Instalacja

W katalogu projektu:

```bash
make
make install
```

Domyślnie program zostanie zainstalowany do:

- `~/.local/bin/centrum-ustawien`
- `~/.local/share/applications/centrum-ustawien.desktop`

Jeżeli `~/.local/bin` nie jest w `PATH`, można uruchomić:

```bash
~/.local/bin/centrum-ustawien
```

Po instalacji aktywator powinien być dostępny w menu aplikacji.

## Uruchomienie bez instalacji

```bash
make run
```

## Odinstalowanie

```bash
make uninstall
```

## Inny prefix

Można zmienić miejsce instalacji:

```bash
make install PREFIX=/usr/local
```

Do pakowania systemowego można również użyć `DESTDIR`:

```bash
make install PREFIX=/usr DESTDIR=/tmp/pakiet
```

## Uwaga

Program nie zawiera własnej ikony. Ikony aktywatorów są pobierane z ich plików `.desktop` i zainstalowanego motywu ikon GTK.
