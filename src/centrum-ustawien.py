#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GioUnix", "2.0")
from gi.repository import Gtk, Gio, GioUnix, GLib


APP_TITLE = "Centrum ustawień"
COLUMNS = 9
ICON_SIZE = 42


def application_directories():
    """Zwraca katalogi .desktop w kolejności pierwszeństwa."""
    home = os.path.expanduser("~")
    data_home = os.environ.get(
        "XDG_DATA_HOME",
        os.path.join(home, ".local", "share")
    )

    directories = [
        os.path.join(data_home, "applications"),
        os.path.join(home, ".local", "share", "applications"),
        os.path.join(home, ".local", "share", "flatpak", "exports", "share", "applications"),
        "/usr/local/share/applications",
        "/usr/share/applications",
        "/var/lib/flatpak/exports/share/applications",
    ]

    # XDG_DATA_DIRS może zawierać dodatkowe katalogi z aplikacjami.
    for base in os.environ.get(
        "XDG_DATA_DIRS",
        "/usr/local/share:/usr/share"
    ).split(":"):
        if base:
            directories.append(os.path.join(base, "applications"))

    result = []
    seen = set()

    for directory in directories:
        directory = os.path.abspath(os.path.expanduser(directory))
        if directory not in seen:
            seen.add(directory)
            result.append(directory)

    return result


def keyfile_string(keyfile, key, locale=None, default=""):
    """Bezpieczne odczytanie pola z pliku .desktop."""
    try:
        if locale:
            return keyfile.get_locale_string(
                "Desktop Entry", key, locale
            )
        return keyfile.get_string("Desktop Entry", key)
    except GLib.Error:
        return default



FUNCTION_RULES = [
    ("Wygląd i motywy", {
        "settings", "desktopsettings", "appearance", "theme", "themes",
        "icontheme", "font", "fonts", "desktopappearance"
    }),
    ("Pulpit i okna", {
        "desktop", "desktopsettings", "windowmanager", "wm", "screensaver"
    }),
    ("Sprzęt i urządzenia", {
        "hardware", "hardwaresettings", "input", "keyboard", "mouse",
        "display", "screensettings", "monitor", "printers", "printing",
        "scanners", "audio", "audiovideo", "bluetooth"
    }),
    ("Sieć i internet", {
        "network", "networksettings", "internet", "remoteaccess",
        "telephony"
    }),
    ("System i administracja", {
        "system", "systemsettings", "administration", "package", "packages",
        "security", "filesystem", "disk", "disks", "storage"
    }),
    ("Zasilanie", {
        "power", "powersettings"
    }),
    ("Język i lokalizacja", {
        "localization", "locale", "languages", "timezone", "settings"
    }),
    ("Użytkownicy i konta", {
        "account", "accounts", "users", "user", "group", "groups"
    }),
    ("Multimedia", {
        "audio", "audiovideo", "video", "player", "multimedia"
    }),
    ("Dostępność", {
        "accessibility", "access"
    }),
    ("Programowanie", {
        "development", "developertools", "programming", "debugger"
    }),
]


ENVIRONMENT_MAP = [
    ("LXDE", {"lxde", "x-lxde", "x-lxde-settings", "x-lxde-desktop"}),
    ("LXQt", {"lxqt", "x-lxqt", "x-lxqt-settings"}),
    ("XFCE", {"xfce", "xfce4", "x-xfce", "x-xfce-settings"}),
    ("KDE Plasma", {"kde", "kde4", "kde5", "kde6", "x-kde", "plasma"}),
    ("GNOME", {"gnome", "x-gnome", "gnome-settings"}),
    ("MATE", {"mate", "x-mate"}),
    ("Cinnamon", {"cinnamon", "x-cinnamon"}),
    ("Budgie", {"budgie", "x-budgie"}),
    ("Deepin", {"deepin", "x-deepin"}),
]


def classify_function(categories):
    """
    Określa funkcjonalną kategorię aktywatora.
    Najpierw sprawdzane są bardziej szczegółowe kategorie.
    """
    normalized = {
        category.strip().casefold()
        for category in categories
        if category.strip()
    }

    # Specjalne przypadki, żeby np. PowerSettings nie trafiło do ogólnego System.
    priority = [
        "Zasilanie",
        "Użytkownicy i konta",
        "Język i lokalizacja",
        "Sieć i internet",
        "Multimedia",
        "Dostępność",
        "Programowanie",
        "Sprzęt i urządzenia",
        "Pulpit i okna",
        "Wygląd i motywy",
        "System i administracja",
    ]

    for function_name in priority:
        for rule_name, rule_categories in FUNCTION_RULES:
            if rule_name != function_name:
                continue
            if normalized & rule_categories:
                return function_name

    return "Pozostałe ustawienia"


def detect_environments(categories, keyfile):
    """
    Określa środowisko graficzne na podstawie jawnych danych .desktop:
    Categories, OnlyShowIn, NotShowIn oraz rozszerzeń X-*.
    Nie zgadujemy środowiska wyłącznie na podstawie nazwy programu.
    """
    values = set(
        category.strip().casefold()
        for category in categories
        if category.strip()
    )

    for key in ("OnlyShowIn", "NotShowIn"):
        try:
            values.update(
                value.strip().casefold()
                for value in keyfile.get_string(
                    "Desktop Entry", key
                ).replace(";", " ").split()
                if value.strip()
            )
        except GLib.Error:
            pass

    environments = []

    for environment_name, signatures in ENVIRONMENT_MAP:
        if values & signatures:
            environments.append(environment_name)

    # Wpisy zawierające GNOME/KDE/LXDE itd. w rozszerzeniach
    # X-* są obsługiwane również przez prosty test prefiksu.
    for value in values:
        if value.startswith("x-lxde"):
            if "LXDE" not in environments:
                environments.append("LXDE")
        elif value.startswith("x-lxqt"):
            if "LXQt" not in environments:
                environments.append("LXQt")
        elif value.startswith("x-xfce"):
            if "XFCE" not in environments:
                environments.append("XFCE")
        elif value.startswith("x-kde"):
            if "KDE Plasma" not in environments:
                environments.append("KDE Plasma")
        elif value.startswith("x-gnome"):
            if "GNOME" not in environments:
                environments.append("GNOME")
        elif value.startswith("x-mate"):
            if "MATE" not in environments:
                environments.append("MATE")
        elif value.startswith("x-cinnamon"):
            if "Cinnamon" not in environments:
                environments.append("Cinnamon")
        elif value.startswith("x-budgie"):
            if "Budgie" not in environments:
                environments.append("Budgie")
        elif value.startswith("x-deepin"):
            if "Deepin" not in environments:
                environments.append("Deepin")

    return environments or ["Wspólne / niezależne od środowiska"]


def load_settings_desktop_files():
    """
    Wyszukuje aktywatory .desktop należące do kategorii
    Settings lub Preferences.
    """
    found = {}

    # Pierwszy znaleziony plik ma pierwszeństwo.
    for directory in application_directories():
        if not os.path.isdir(directory):
            continue

        try:
            filenames = sorted(os.listdir(directory))
        except OSError:
            continue

        for filename in filenames:
            if not filename.endswith(".desktop"):
                continue

            if filename in found:
                continue

            path = os.path.join(directory, filename)
            if not os.path.isfile(path):
                continue

            keyfile = GLib.KeyFile()

            try:
                keyfile.load_from_file(
                    path,
                    GLib.KeyFileFlags.NONE
                )
            except GLib.Error:
                continue

            if keyfile_string(
                keyfile, "Type", default=""
            ).casefold() != "application":
                continue

            # Ukryte / przeznaczone wyłącznie do użytku wewnętrznego
            # nie są aktywnymi pozycjami centrum ustawień.
            hidden = keyfile_string(
                keyfile, "Hidden", default="false"
            ).casefold() == "true"

            no_display = keyfile_string(
                keyfile, "NoDisplay", default="false"
            ).casefold() == "true"

            if hidden or no_display:
                continue

            categories_text = keyfile_string(
                keyfile, "Categories", default=""
            )

            categories = {
                category.strip().casefold()
                for category in categories_text.split(";")
                if category.strip()
            }

            if "settings" not in categories and "preferences" not in categories:
                continue

            name = keyfile_string(
                keyfile, "Name", locale="pl", default=""
            ).strip()

            if not name:
                name = keyfile_string(
                    keyfile, "Name", default=filename
                ).strip()

            comment = keyfile_string(
                keyfile, "Comment", locale="pl", default=""
            ).strip()

            if not comment:
                comment = keyfile_string(
                    keyfile, "Comment", default=""
                ).strip()

            icon_name = keyfile_string(
                keyfile, "Icon", default=""
            ).strip()

            categories_list = [
                category for category in categories_text.split(";")
                if category.strip()
            ]

            # GioUnix.DesktopAppInfo jest właściwą implementacją
            # DesktopAppInfo dla systemowych plików .desktop.
            # Niektóre pliki mogą być poprawnie odczytane przez GLib.KeyFile,
            # ale nie być prawidłowym aktywatorem dla DesktopAppInfo.
            try:
                desktop = GioUnix.DesktopAppInfo.new_from_filename(path)
            except (GLib.Error, TypeError, ValueError):
                desktop = None

            if desktop is None:
                continue

            found[filename] = {
                "filename": filename,
                "path": path,
                "name": name,
                "comment": comment,
                "icon": icon_name,
                "categories": categories_list,
                "function": classify_function(categories_list),
                "environments": detect_environments(
                    categories_list,
                    keyfile
                ),
                "desktop": desktop,
            }

    return sorted(
        found.values(),
        key=lambda item: (
            item["function"].casefold(),
            ", ".join(item["environments"]).casefold(),
            item["name"].casefold()
        )
    )


class DesktopTile(Gtk.Button):
    def __init__(self, application, window):
        super().__init__()

        self.application = application
        self.window = window

        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_can_focus(True)

        tooltip = application["comment"]

        if tooltip:
            self.set_tooltip_text(tooltip)
        else:
            self.set_tooltip_text(
                application["filename"]
            )

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5
        )

        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(10)
        box.set_margin_end(10)

        image = self.create_icon(
            application["icon"]
        )

        image.set_pixel_size(ICON_SIZE)
        box.pack_start(image, False, False, 0)

        label = Gtk.Label(
            label=application["name"]
        )

        label.set_justify(Gtk.Justification.CENTER)
        label.set_line_wrap(True)
        label.set_max_width_chars(17)

        box.pack_start(label, False, False, 0)

        self.add(box)

        self.connect(
            "clicked",
            self.launch_application
        )

    def create_icon(self, icon_name):
        if not icon_name:
            return Gtk.Image.new_from_icon_name(
                "preferences-system",
                Gtk.IconSize.DIALOG
            )

        # Ikona może być podana jako pełna ścieżka.
        if os.path.isabs(icon_name) and os.path.exists(icon_name):
            try:
                file_icon = Gio.FileIcon.new(
                    Gio.File.new_for_path(icon_name)
                )
                return Gtk.Image.new_from_gicon(
                    file_icon,
                    Gtk.IconSize.DIALOG
                )
            except GLib.Error:
                pass

        # Standardowa nazwa ikony z motywu GTK.
        return Gtk.Image.new_from_icon_name(
            icon_name,
            Gtk.IconSize.DIALOG
        )

    def launch_application(self, *_):
        desktop = self.application["desktop"]

        if desktop is None:
            self.window.show_error(
                self.application["name"],
                "Nie udało się odczytać aktywatora .desktop."
            )
            return

        try:
            # GIO interpretuje pole Exec zgodnie ze specyfikacją
            # plików .desktop, w tym %U, %F itd.
            desktop.launch([], None)
        except GLib.Error as exc:
            self.window.show_error(
                self.application["name"],
                str(exc)
            )


class LXDECenter(Gtk.Window):
    def __init__(self):
        super().__init__(title=APP_TITLE)

        self.set_default_size(1200, 760)
        self.set_size_request(800, 550)

        self.connect(
            "destroy",
            Gtk.main_quit
        )

        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL
        )

        self.add(root)

        scroll = Gtk.ScrolledWindow()

        scroll.set_policy(
            Gtk.PolicyType.AUTOMATIC,
            Gtk.PolicyType.AUTOMATIC
        )

        root.pack_start(
            scroll,
            True,
            True,
            0
        )

        self.content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8
        )

        self.content.set_margin_top(4)
        self.content.set_margin_bottom(8)
        self.content.set_margin_start(5)
        self.content.set_margin_end(5)

        scroll.add(self.content)

        self.applications = []

        self.reload_applications()

        bottom = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL
        )

        bottom.set_margin_top(5)
        bottom.set_margin_bottom(5)
        bottom.set_margin_start(5)
        bottom.set_margin_end(5)

        close_button = Gtk.Button(
            label="Zamknij"
        )

        close_button.connect(
            "clicked",
            lambda *_: self.destroy()
        )

        bottom.pack_end(
            close_button,
            False,
            False,
            0
        )

        root.pack_start(
            bottom,
            False,
            False,
            0
        )

        self.show_all()

    def reload_applications(self):
        self.applications = load_settings_desktop_files()

        for child in self.content.get_children():
            self.content.remove(child)

        if not self.applications:
            frame = Gtk.Frame(label="Ustawienia")
            frame.set_shadow_type(Gtk.ShadowType.IN)

            label = Gtk.Label(
                label=(
                    "Nie znaleziono aktywatorów .desktop "
                    "z kategorią Settings lub Preferences."
                )
            )
            label.set_margin_top(30)
            label.set_margin_bottom(30)
            label.set_margin_start(20)
            label.set_margin_end(20)

            frame.add(label)
            self.content.pack_start(frame, False, False, 0)
            self.content.show_all()
            return

        # Pierwszy poziom: za co odpowiada program.
        function_groups = {}

        for application in self.applications:
            function_groups.setdefault(
                application["function"], []
            ).append(application)

        function_order = [
            "Wygląd i motywy",
            "Pulpit i okna",
            "Sprzęt i urządzenia",
            "Sieć i internet",
            "Zasilanie",
            "Język i lokalizacja",
            "Użytkownicy i konta",
            "System i administracja",
            "Multimedia",
            "Dostępność",
            "Programowanie",
            "Pozostałe ustawienia",
        ]

        ordered_functions = [
            name for name in function_order
            if name in function_groups
        ]

        # Dodatkowe, nieprzewidziane kategorie też pokazujemy.
        ordered_functions.extend(
            name for name in sorted(function_groups)
            if name not in ordered_functions
        )

        for function_name in ordered_functions:
            function_frame = Gtk.Frame(
                label=function_name
            )
            function_frame.set_shadow_type(
                Gtk.ShadowType.IN
            )

            function_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL,
                spacing=4
            )

            function_box.set_margin_top(3)
            function_box.set_margin_bottom(5)
            function_box.set_margin_start(4)
            function_box.set_margin_end(4)

            # Drugi poziom: środowisko graficzne.
            environment_groups = {}

            for application in function_groups[function_name]:
                for environment in application["environments"]:
                    environment_groups.setdefault(
                        environment, []
                    ).append(application)

            environment_order = [
                "LXDE",
                "LXQt",
                "XFCE",
                "KDE Plasma",
                "GNOME",
                "MATE",
                "Cinnamon",
                "Budgie",
                "Deepin",
                "Wspólne / niezależne od środowiska",
            ]

            ordered_environments = [
                name for name in environment_order
                if name in environment_groups
            ]

            ordered_environments.extend(
                name for name in sorted(environment_groups)
                if name not in ordered_environments
            )

            for environment_name in ordered_environments:
                environment_frame = Gtk.Frame(
                    label=environment_name
                )

                environment_grid = Gtk.Grid()
                environment_grid.set_column_spacing(4)
                environment_grid.set_row_spacing(2)
                environment_grid.set_margin_top(2)
                environment_grid.set_margin_bottom(2)
                environment_grid.set_margin_start(6)
                environment_grid.set_margin_end(6)

                applications = sorted(
                    environment_groups[environment_name],
                    key=lambda item: item["name"].casefold()
                )

                for index, application in enumerate(applications):
                    tile = DesktopTile(
                        application,
                        self
                    )

                    environment_grid.attach(
                        tile,
                        index % COLUMNS,
                        index // COLUMNS,
                        1,
                        1
                    )

                environment_frame.add(
                    environment_grid
                )

                function_box.pack_start(
                    environment_frame,
                    False,
                    False,
                    0
                )

            function_frame.add(function_box)

            self.content.pack_start(
                function_frame,
                False,
                False,
                0
            )

        self.content.show_all()

    def show_error(self, name, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Nie można uruchomić: " + name
        )

        dialog.format_secondary_text(
            message
        )

        dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    LXDECenter()
    Gtk.main()
