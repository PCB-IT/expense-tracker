import json

import flet as ft
from flet.core.column import Column
from flet.core.row import Row

from pages.view_helpers import Container, Controller

ft.icons = ft.Icons
ft.colors = ft.Colors


class Settings:
    """
    A class to hold application settings and manage their persistence
    using Flet's client_storage.
    """

    def __init__(self, page: ft.Page):
        self.page = page  # Store the page instance

        # Default values for settings
        self._default_categories = ["Food", "Transportation", "Entertainment"]
        self._default_appearance_theme = "light"
        self._default_default_currency = "USD"

        # Load settings from client storage or use defaults
        self._load_settings()

    # Properties for settings to allow controlled access and potential saving on change
    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, value):
        self._categories = value
        self._save_all_settings()  # Save whenever categories are updated

    @property
    def appearance_theme(self):
        return self._appearance_theme

    @appearance_theme.setter
    def appearance_theme(self, value):
        self._appearance_theme = value
        self._save_all_settings()  # Save whenever theme is updated

    @property
    def default_currency(self):
        return self._default_currency

    @default_currency.setter
    def default_currency(self, value):
        self._default_currency = value
        self._save_all_settings()  # Save whenever currency is updated

    def _load_settings(self):
        """
        Loads all settings from client_storage.
        """
        try:
            # Categories need to be loaded as JSON
            categories_json = self.page.client_storage.get("settings_categories")
            print(f"Categories JSON: {categories_json}")
            if categories_json:
                self._categories = json.loads(categories_json)
            else:
                self._categories = self._default_categories

            self._appearance_theme = self.page.client_storage.get(
                "settings_appearance_theme") or self._default_appearance_theme
            self._default_currency = self.page.client_storage.get(
                "settings_default_currency") or self._default_default_currency

            print("Settings loaded successfully.")
        except Exception as e:
            print(f"Error loading settings: {e}. Using default settings.")
            self._categories = self._default_categories
            self._appearance_theme = self._default_appearance_theme
            self._default_currency = self._default_default_currency

    def _save_all_settings(self):
        """
        Saves all current settings to client_storage.
        """
        try:
            # Categories need to be saved as JSON
            self.page.client_storage.set("settings_categories", json.dumps(self._categories))
            self.page.client_storage.set("settings_appearance_theme", self._appearance_theme)
            self.page.client_storage.set("settings_default_currency", self._default_currency)
            print("Settings saved successfully.")
        except Exception as e:
            print(f"Error saving settings: {e}")


# --- New Controller Classes for each setting page ---

class ManageCategoriesController(Controller):
    def __init__(self, page, settings_instance):
        super().__init__(page, settings_instance, "/settings/manage_categories")
        self.settings = settings_instance

    def build(self, page_route, **kwargs):
        if page_route != self.route:
            return

        # Dynamically create categories list to reflect changes
        categories_list_controls = [
            ft.Row([
                ft.Text(f"- {cat}", font_family="Inter", expand=True),
                ft.IconButton(
                    icon=ft.icons.DELETE,
                    icon_color=ft.colors.RED_500,
                    on_click=lambda e, category=cat: self._remove_category(category),
                    tooltip=f"Remove {cat}"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            for cat in self.settings.categories
        ]

        self.new_category_input = ft.TextField(label="Add New Category", on_submit=self._add_category, expand=True)

        content = [
            ft.Text("Current Categories:", size=16, weight=ft.FontWeight.BOLD, font_family="Inter"),
            ft.Column(categories_list_controls, spacing=8),
            ft.Row([
                self.new_category_input,
                ft.ElevatedButton("Add", on_click=self._add_category_button_click)
            ], alignment=ft.MainAxisAlignment.START),
            ft.ElevatedButton("Save Changes", on_click=lambda e: print("Categories Saved")),
            ft.TextButton("Back to Settings", on_click=lambda e: self.page.go("/settings"))
        ]
        return super().build("Manage Categories", content)

    def _add_category(self, e):
        # This is called on TextField submit (Enter key)
        self._add_category_logic(e.control.value)

    def _add_category_button_click(self, e):
        # This is called when the "Add" button is clicked
        self._add_category_logic(self.new_category_input.value)

    def _add_category_logic(self, new_category):
        new_category = new_category.strip()
        if new_category and new_category not in self.settings.categories:
            self.settings.categories.append(new_category)
            self.new_category_input.value = ""  # Clear the input
            self.page.update()  # Update UI to show new category
            print(f"Added category: {new_category}")

    def _remove_category(self, category_to_remove):
        if category_to_remove in self.settings.categories:
            self.settings.categories.remove(category_to_remove)
            self.page.update()
            print(f"Removed category: {category_to_remove}")


class ImportDataController(Controller):
    def __init__(self, page, settings_instance):
        super().__init__(page, settings_instance, "/settings/import_data")
        self.settings = settings_instance

    def build(self, page_route, **kwargs):
        if page_route != self.route:
            return
        content = [
            ft.Text("Import your financial data from a file.", size=16, font_family="Inter"),
            ft.ElevatedButton("Choose File to Import", on_click=lambda e: print("Import file dialog")),
            ft.TextButton("Back to Settings", on_click=lambda e: self.page.go("/settings"))
        ]
        return super().build("Import Data", content)


class ExportDataController(Controller):
    def __init__(self, page, settings_instance):
        super().__init__(page, settings_instance, "/settings/export_data")
        self.settings = settings_instance

    def build(self, page_route, **kwargs):
        if page_route != self.route:
            return
        content = [
            ft.Text("Export your financial data to a file.", size=16, font_family="Inter"),
            ft.ElevatedButton("Export Data Now", on_click=lambda e: print("Export data triggered")),
            ft.TextButton("Back to Settings", on_click=lambda e: self.page.go("/settings"))
        ]
        return super().build("Export Data", content)


class AppearanceController(Controller):
    def __init__(self, page, settings_instance):
        super().__init__(page, settings_instance, "/settings/appearance")
        self.settings = settings_instance

    def build(self, page_route, **kwargs):
        if page_route != self.route:
            return
        content = [
            ft.Text("Choose your preferred theme:", size=16, font_family="Inter"),
            ft.RadioGroup(
                value=self.settings.appearance_theme,
                on_change=self._change_theme,
                content=ft.Row([
                    ft.Radio(value="light", label="Light Theme"),
                    ft.Radio(value="dark", label="Dark Theme"),
                ])
            ),
            ft.TextButton("Back to Settings", on_click=lambda e: self.page.go("/settings"))
        ]
        return super().build("Appearance", content)

    def _change_theme(self, e):
        self.settings.appearance_theme = e.control.value
        # Apply theme change to the page
        self.page.theme_mode = ft.ThemeMode.LIGHT if self.settings.appearance_theme == "light" else ft.ThemeMode.DARK
        self.page.update()
        print(f"Theme changed to: {self.settings.appearance_theme}")


class DefaultCurrencyController(Controller):
    def __init__(self, page, settings_instance):
        super().__init__(page, settings_instance, "/settings/default_currency")
        self.settings = settings_instance

    def build(self, page_route, **kwargs):
        if page_route != self.route:
            return
        content = [
            ft.Text("Set your default currency:", size=16, font_family="Inter"),
            ft.Dropdown(
                value=self.settings.default_currency,
                options=[
                    ft.dropdown.Option("USD"),
                    ft.dropdown.Option("EUR"),
                    ft.dropdown.Option("GBP"),
                    ft.dropdown.Option("JPY"),
                ],
                on_change=self._change_currency,
                width=200
            ),
            ft.TextButton("Back to Settings", on_click=lambda e: self.page.go("/settings"))
        ]
        return super().build("Default Currency", content)

    def _change_currency(self, e):
        self.settings.default_currency = e.control.value
        self.page.update()
        print(f"Default currency set to: {self.settings.default_currency}")


# --- Main Settings Controller (updated for navigation) ---

class SettingsController(Controller):
    """
    Controller for the Settings page, managing various settings sections
    like Expense Categories, Data Management, and Preferences.
    """

    def __init__(self, page, page_route, settings_instance):
        super().__init__(page, settings_instance, page_route)
        self.page = page
        self.route = page_route
        self.settings = settings_instance  # Store the shared settings instance

    def build(self, page_route, **kwargs):
        """
        Builds the UI for the Settings page based on the provided image.
        It includes sections for Expense Categories, Data Management, and Preferences.
        """
        if page_route != self.route:
            return

        settings_content = [
            # Expense Categories Section
            ft.Text("Expense Categories", size=20, weight=ft.FontWeight.BOLD, font_family="Inter"),
            self._create_setting_item(
                "Manage Categories",
                ", ".join(self.settings.categories),  # Display current categories
                lambda e: self.page.go("/settings/manage_categories")  # Navigate
            ),
            # Data Management Section
            ft.Text("Data Management", size=20, weight=ft.FontWeight.BOLD, font_family="Inter"),
            self._create_setting_item(
                "Import Data",
                "",  # No subtitle for Import Data
                lambda e: self.page.go("/settings/import_data")  # Navigate
            ),
            self._create_setting_item(
                "Export Data",
                "",  # No subtitle for Export Data
                lambda e: self.page.go("/settings/export_data")  # Navigate
            ),
            # Preferences Section
            ft.Text("Preferences", size=20, weight=ft.FontWeight.BOLD, font_family="Inter"),
            self._create_setting_item(
                "Appearance",
                f"Current: {self.settings.appearance_theme.capitalize()}",  # Display current theme
                lambda e: self.page.go("/settings/appearance")  # Navigate
            ),
            self._create_setting_item(
                "Default Currency",
                f"Current: {self.settings.default_currency}",  # Display current currency
                lambda e: self.page.go("/settings/default_currency")  # Navigate
            ),
        ]
        return super().build("Settings", settings_content)

    def _create_setting_item(self, title, subtitle, on_click):
        """
        Helper method to create a consistent setting item row with a title,
        optional subtitle, and a right arrow icon.
        Adds highlight functionality on hover/click.
        """
        setting_item_container = ft.Container(
            content=Row(
                [
                    Column(
                        [
                            ft.Text(title, size=16, font_family="Inter"),
                            ft.Text(subtitle, size=12, color=ft.colors.GREY_600,
                                    font_family="Inter") if subtitle else ft.Container(),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Icon(ft.icons.KEYBOARD_ARROW_RIGHT_OUTLINED),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(10),
            border_radius=ft.border_radius.all(8),
            on_click=on_click,
            on_hover=lambda e: self._on_setting_item_hover(e, setting_item_container),
            bgcolor=ft.colors.TRANSPARENT,
            ink=True,
        )
        return setting_item_container

    def _on_setting_item_hover(self, e, container):
        """
        Handles the hover effect for setting items.
        Changes background color on hover and resets it on exit.
        """
        if e.data == "true":
            container.bgcolor = ft.colors.GREY_100
        else:
            container.bgcolor = ft.colors.TRANSPARENT
        container.page.update()

    def _refresh(self):
        """
        Refreshes the content of the settings page.
        """
        self.page.update()

