import datetime
from typing import List

import flet as ft
from flet.core.row import Row

from models.Constants import ADD_NEW_ITEM
from models.ExpenseData import ExpenseModel
from pages.view_helpers import Controller

class FocusController:
    def __init__(self, register_control: List, on_focus_callback=None):

        for control in register_control:
            control.on_focus = self.on_focus

        self.on_focus = on_focus_callback
        self.old = None

    def on_focus(self, e: ft.OnFocusEvent):

        if self.on_focus is not None:
            self.on_focus(e, self.old)
            self.old = e

class OnResultCallback:
    def __init__(self, on_result_callback):
        self.on_result_callback = on_result_callback

    def __call__(self, action, expense_model):
        self.on_result_callback(action, expense_model)

class AppendExpense(Controller):
    """
    Controller for the "Add New Expense" view, handling UI interactions
    and updating the ExpenseModel.
    """

    def __init__(self, page: ft.Page, app_settings, on_result_callback: OnResultCallback, page_route):
        super().__init__(page, app_settings, page_route)

        # Initialize the ExpenseModel with a unique ID
        self.expense_model = ExpenseModel()
        self.on_result_callback = on_result_callback

        # --- UI Controls Initialization ---
        # Date TextField (read-only, updated by DatePicker)
        self._date_text_field = ft.TextField(
            label="Date",
            read_only=True,
            border_radius=ft.border_radius.all(8)  # Rounded corners
        )

        # Category Dropdown
        self._category_dropdown = ft.Dropdown(  # Corrected from DropdownM2 to Dropdown
            width=250,  # Adjusted width for better fit
            label="Category",
            options=[
                ft.dropdown.Option("Groceries"),
                ft.dropdown.Option("Transport"),
                ft.dropdown.Option("Utilities"),
                ft.dropdown.Option("Entertainment"),
                ft.dropdown.Option("Dining Out"),
                ft.dropdown.Option("Healthcare"),
                ft.dropdown.Option("Education"),
                ft.dropdown.Option("Shopping"),
                ft.dropdown.Option("Other"),
            ],
            on_change=self._on_category_change,  # Event handler to update model
            border_radius=ft.border_radius.all(8)  # Rounded corners
        )

        # Amount TextField (numeric input only)
        self._amount_text_field = ft.TextField(
            label="Amount",
            keyboard_type=ft.KeyboardType.NUMBER,  # Restrict to numbers
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]", replacement_string=""),
            # Allow numbers and decimal point
            on_change=self._on_amount_change,  # Event handler to update model and validate
            prefix_text=f"{self.app_settings.default_currency} ",  # Optional: Currency prefix
            border_radius=ft.border_radius.all(8)  # Rounded corners
        )

        # Description TextField (multiline)
        self._description_text_field = ft.TextField(
            label="Description (Optional)",
            multiline=True,
            min_lines=3,
            max_lines=7,  # Allow more lines for detailed descriptions
            expand=True,  # Allows it to take available horizontal space
            hint_text="Enter description here (e.g., 'Weekly grocery shopping at SuperMart')",
            hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
            on_change=self._on_description_change,  # Event handler to update model
            border_radius=ft.border_radius.all(8)  # Rounded corners
        )

        # Add Expense Button
        self._add_expense_button = ft.ElevatedButton(
            "Add Expense",
            on_click=self._on_add_expense_click,
            icon=ft.Icons.ADD,  # Added an icon for better UX
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8))),  # Rounded corners
        )

        # DatePicker instance (will be created and added to page overlay in build)
        self._date_picker = None

        # --- Register Model Change Listeners (Optional, for two-way binding or debugging UI updates) ---
        # These are here to demonstrate how you could update the UI if the model changes programmatically.
        # For this app, UI drives the model, so these are mostly for demonstration.
        # self.expense_model.register_on_value_change("date", self._update_date_ui)
        # self.expense_model.register_on_value_change("category", self._update_category_ui)
        # self.expense_model.register_on_value_change("amount", self._update_amount_ui)
        # self.expense_model.register_on_value_change("description", self._update_description_ui)

    # --- Event Handlers for UI Component Changes ---
    def _on_date_change(self, e: ft.ControlEvent):
        """
        Handles the date selection from the DatePicker.
        Updates the model's date and the date TextField's value.
        """
        if e.control.value:
            selected_date = e.control.value
            # Store date in ISO-MM-DD format in the model for consistency
            self.expense_model.date = selected_date.strftime("%Y-%m-%d")
            # Update the UI TextField to display the selected date
            self._date_text_field.value = selected_date.strftime("%Y-%m-%d")
            self.page.update()  # Update the page to reflect the new date in the TextField
            print(f"DEBUG: Model Date updated: {self.expense_model.date}")

    def _on_category_change(self, e: ft.ControlEvent):
        """
        Handles category selection from the Dropdown.
        Updates the model's category.
        """
        self.expense_model.category = e.control.value
        print(f"DEBUG: Model Category updated: {self.expense_model.category}")

    def _on_amount_change(self, e: ft.ControlEvent):
        """
        Handles amount input from the TextField.
        Updates the model's amount after validating it as a number.
        """
        try:
            amount_val = float(e.control.value)
            self.expense_model.amount = amount_val
            e.control.error_text = None  # Clear any previous error message
        except ValueError:
            # If input is not a valid number, set amount to None and show error
            self.expense_model.amount = None
            e.control.error_text = "Please enter a valid number (e.g., 12.34)"
        self.page.update()  # Update the page to show/clear error text
        print(f"DEBUG: Model Amount updated: {self.expense_model.amount}")

    def _on_description_change(self, e: ft.ControlEvent):
        """
        Handles description input from the TextField.
        Updates the model's description.
        """
        self.expense_model.description = e.control.value
        print(f"DEBUG: Model Description updated: {self.expense_model.description}")

    def _on_add_expense_click(self, e: ft.ControlEvent):
        """
        Handles the "Add Expense" button click.
        Prints the current state of the ExpenseModel to the console for verification.
        """
        # In a real application, you would save this model to a database
        # or pass it to another part of your application.
        print("\n--- Current Expense Model State ---")
        print(f"ID: {self.expense_model.id}")
        print(f"Date: {self.expense_model.date}")
        print(f"Category: {self.expense_model.category}")
        print(f"Amount: {self.expense_model.amount}")
        print(f"Description: {self.expense_model.description}")
        print("-----------------------------------\n")

        # Example: Navigate back to the home page after adding
        self.page.go("/")

        self.on_result_callback(ADD_NEW_ITEM, self.expense_model)

        # --- Callbacks for Model Changes to Update UI (Passive) ---

    # These methods demonstrate how you could update UI elements if the model
    # were to be changed programmatically (e.g., loaded from a database).
    # For this "add new expense" flow, the UI directly drives the model,
    # so these might not seem strictly necessary, but they are good for
    # demonstrating proper two-way data binding principles.
    def _update_date_ui(self, name: str, value: str):
        self._date_text_field.value = value
        self.page.update()

    def _update_category_ui(self, name: str, value: str):
        self._category_dropdown.value = value
        self.page.update()

    def _update_amount_ui(self, name: str, value: float):
        self._amount_text_field.value = str(value) if value is not None else ""
        self.page.update()

    def _update_description_ui(self, name: str, value: str):
        self._description_text_field.value = value
        self.page.update()

    # --- Build Method for Flet View ---
    def build(self, route: str, **kwargs):
        """
        Builds the Flet UI for the "Add New Expense" view.
        """
        if route != "/new":
            return  # Only build if the route matches

        edit_mode = False

        if "EDIT_EXPENSE" in kwargs.keys():
            self.expense_model = kwargs["EDIT_EXPENSE"]

            self._date_text_field.value = self.expense_model.date
            self._category_dropdown.value = self.expense_model.category
            self._amount_text_field.value = str(self.expense_model.amount) if self.expense_model.amount is not None else ""
            self._description_text_field.value = self.expense_model.description

            edit_mode = True

        # Initialize the DatePicker and add it to the page's overlay.
        # This must be done here or in `main` so it can be opened.
        self._date_picker = ft.DatePicker(
            first_date=datetime.datetime(year=2000, month=1, day=1),
            last_date=datetime.datetime(year=2030, month=12, day=31),  # Extended range
            on_change=self._on_date_change,
            on_dismiss=lambda e: print("DatePicker dismissed")  # Simplified dismissal logging
        )
        self.page.overlay.append(self._date_picker)
        self.page.update()  # Update the page to include the date picker in the overlay

        # Define the layout of the form
        form_controls = [
            ft.Row(  # Date selection row
                controls=[
                    self._date_text_field,
                    ft.Row(expand=True),  # Spacer
                    ft.ElevatedButton(
                        "Pick date",
                        icon=ft.Icons.CALENDAR_MONTH,
                        on_click=lambda _: self.page.open(self._date_picker),  # Open the DatePicker
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(8)))
                        # Rounded corners
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10
            ),
            self._category_dropdown,
            self._amount_text_field,
            self._description_text_field,
            ft.Row(  # Add Expense button row
                controls=[self._add_expense_button],
                alignment=ft.MainAxisAlignment.END,
                spacing=10
            )
        ]

        self._category_dropdown.options.clear()

        for category in self.app_settings.categories:
            self._category_dropdown.options.append(ft.dropdown.Option(category))

        title = "Edit Expense" if edit_mode else "Add New Expense"

        if edit_mode:
            self._add_expense_button.text = "Update Expense"
            if self.expense_model.category not in self.app_settings.categories:
                self._category_dropdown.options.append(self.expense_model.category)

        # Use the base Controller's build method to create the main view
        container = super().build(title, form_controls)
        return container