import os

import flet as ft
from flet.core.row import Row

from models.Constants import EDIT_ITEM, ADD_NEW_ITEM
from models.ExpenseData import ExpenseData, generate_dummy_expenses
from pages.AppendExpense import AppendExpense, OnResultCallback
from pages.Dashboard import DashboardController
from pages.Expenses import TransactionsController
# Import the Settings class and all controller classes from pages.Settings
from pages.Settings import SettingsController, ManageCategoriesController, ImportDataController, ExportDataController, \
    AppearanceController, DefaultCurrencyController, Settings
from pages.view_helpers import Container
from pages.Reports import ReportsController


def main(page: ft.Page):
    build_kwargs = {}

    def on_result_callback(action, expense):
        if action == EDIT_ITEM:
            page.go("/new")
            build_kwargs["EDIT_EXPENSE"] = expense

        elif action == ADD_NEW_ITEM:
            if expense.id is None:
                expense_data.add_expense(expense)
            else:
                expense_data.remove_expense(expense)
                expense_data.add_expense(expense)

    page.title = "Expense Tracker"
    page.window.icon = os.getcwd() + "/assets/favicon.ico"
    page.vertical_alignment = ft.CrossAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START

    content_container = ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    expense_data = ExpenseData(page)
    expense_data.load_expenses()

    # Create a single instance of Settings to be shared across all settings-related controllers
    app_settings = Settings(page)

    dashboard = DashboardController(page, app_settings, expense_data, "/")
    transactions = TransactionsController(page, app_settings, expense_data, OnResultCallback(on_result_callback), "/expenses")
    append_expense = AppendExpense(page, app_settings, OnResultCallback(on_result_callback), "/new")

    # Initialize SettingsController and all sub-controllers with the shared app_settings instance
    settings = SettingsController(page, "/settings", app_settings)
    manage_categories_controller = ManageCategoriesController(page, app_settings)
    import_data_controller = ImportDataController(page, app_settings)
    export_data_controller = ExportDataController(page, app_settings)
    appearance_controller = AppearanceController(page, app_settings)
    default_currency_controller = DefaultCurrencyController(page, app_settings)

    # Navbar (doesn't change)
    def nav_bar():
        return ft.Row(  # Outer Row to hold the new text and your existing row
            [
                ft.Image(
                    src=f"assets/favicon.png",
                    width=36,
                    height=36,
                    fit=ft.ImageFit.CONTAIN,
                ),

                ft.Text("Expense Tracker",  # Your new text
                        weight=ft.FontWeight.BOLD,  # Optional: make the text bold
                        size=18),  # Optional: adjust font size
                ft.Container(expand=True),  # This is the spacer: it expands to fill available space
                ft.Row(  # This row contains the navigation buttons
                    [
                        ft.TextButton("Dashboard", on_click=lambda _: page.go("/")),
                        ft.TextButton("Transactions", on_click=lambda _: page.go("/expenses")),
                        # ft.TextButton("Reports", on_click=lambda _: page.go("/reports")),
                        ft.TextButton("Settings", on_click=lambda _: page.go("/settings")),
                        ft.IconButton(ft.Icons.ADD, on_click=lambda _: page.go("/new"))
                    ],
                    alignment=ft.MainAxisAlignment.END  # Align buttons to the end within their row
                )
            ],
            alignment=ft.MainAxisAlignment.START,  # Align items to the start, letting the spacer push the buttons
            # The parent Column's horizontal_alignment=ft.CrossAxisAlignment.STRETCH
            # will ensure this Row still fills the width.
        )

    # Handles route changes
    def route_change(e):
        content_container.controls.clear()
        # Define a default margin for all content pages for consistency
        # default_margin = ft.margin.only(left=20, top=10, bottom=10) # This was not used, can be removed if not needed elsewhere

        # List of all page controllers, including the new settings sub-controllers
        all_page_controllers = [
            dashboard,
            transactions,
            append_expense,
            settings,
            manage_categories_controller,
            import_data_controller,
            export_data_controller,
            appearance_controller,
            default_currency_controller,
        ]

        found_controller = False
        for page_controller in all_page_controllers:
            build = page_controller.build(page.route, **build_kwargs)

            if build:
                content_container.controls.append(build)
                found_controller = True
                break

        if not found_controller:
            # Handle unknown routes, e.g., show a 404 page
            content_container.controls.append(
                Container(
                    ft.Column([
                        ft.Text("404 - Page Not Found", size=30, color=ft.colors.RED_500, font_family="Inter"),
                        ft.ElevatedButton("Go to Dashboard", on_click=lambda e: page.go("/"), font_family="Inter")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    margin=ft.margin.only(top=50)
                )
            )

        page.update()

        # Refresh specific controllers if needed after route change
        # This part should be handled carefully to avoid unnecessary updates
        if page.route == "/expenses":
            transactions.refresh()
        # Add similar refresh calls for other controllers if they have dynamic content
        # For example, if categories are managed and you want the main settings page
        # to reflect changes immediately upon returning:
        if page.route == "/settings":
            settings._refresh()  # Call refresh on the main settings page

    # Main app layout (stays constant)
    page.add(
        ft.Column(
            [
                Container(nav_bar(), margin=ft.margin.only(left=40, right=40)),
                ft.Divider(thickness=0.5),
                content_container,
                Row(height=10)
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.START  # Stretch column content horizontally
        )
    )

    page.on_route_change = route_change
    page.go("/")  # Initial route
    page.theme_mode = app_settings.appearance_theme
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLACK12)


ft.app(target=main, assets_dir="assets")