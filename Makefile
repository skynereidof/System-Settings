PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
APPDIR ?= $(DATADIR)/applications

PROGRAM := centrum-ustawien
SOURCE := src/centrum-ustawien.py
INSTALL_PROGRAM := $(BINDIR)/$(PROGRAM)
INSTALL_DESKTOP := $(APPDIR)/$(PROGRAM).desktop

.PHONY: all install uninstall clean run check

all: check

check:
	@command -v python3 >/dev/null || { echo "Błąd: brak python3."; exit 1; }
	@python3 -c 'import gi; gi.require_version("Gtk","3.0"); gi.require_version("GioUnix","2.0"); from gi.repository import Gtk, GioUnix, GLib' || { echo "Błąd: brak PyGObject/GTK3/GioUnix."; echo "Zainstaluj pakiety python3-gi, gir1.2-gtk-3.0 oraz pakiet zapewniający GioUnix."; exit 1; }
	@python3 -m py_compile "$(SOURCE)"
	@echo "Kontrola zakończona pomyślnie."

install: check
	@mkdir -p "$(BINDIR)" "$(APPDIR)"
	@install -m 0755 "$(SOURCE)" "$(INSTALL_PROGRAM)"
	@install -m 0644 "centrum-ustawien.desktop" "$(INSTALL_DESKTOP)"
	@echo "Zainstalowano:"
	@echo "  $(INSTALL_PROGRAM)"
	@echo "  $(INSTALL_DESKTOP)"
	@echo
	@echo "Uruchom: centrum-ustawien"

uninstall:
	@rm -f "$(INSTALL_PROGRAM)" "$(INSTALL_DESKTOP)"
	@echo "Odinstalowano Centrum ustawień."

run: check
	@python3 "$(SOURCE)"

clean:
	@rm -rf src/__pycache__
	@echo "Usunięto pliki tymczasowe."

help:
	@echo "make          - sprawdzenie programu"
	@echo "make install  - instalacja do ~/.local"
	@echo "make run      - uruchomienie bez instalacji"
	@echo "make uninstall - odinstalowanie"
	@echo "make clean    - usunięcie plików tymczasowych"
