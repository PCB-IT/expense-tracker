import datetime
from typing import List

import flet as ft

from models.Constants import EDIT_ITEM, DELETE_ITEM
from models.ExpenseData import ExpenseModel, ExpenseData
from pages.AppendExpense import OnResultCallback
from pages.view_helpers import Container, Controller


class TransactionsController(Controller):
    """
    Controller for the Reports module, displaying expenses in a searchable,
    filterable, and sortable table with pagination.
    """

    def __init__(self, page: ft.Page, app_settings, expense_data: ExpenseData, on_result_callback: OnResultCallback, page_route):
        super().__init__(page, app_settings, page_route)
        self.expense_data = expense_data
        self.on_result_callback = on_result_callback

        # --- Internal State for Filters and Sort ---
        self._current_search_query: str = ""
        self._current_date_range: str = "All Time"  # Options: "All Time", "This Month", "Last Month", "This Year"
        self._current_category_filter: str = "All Categories"  # Options: "All Categories" or specific category
        self._current_amount_range: str = "All Amounts"  # Options: "All Amounts", "< $50", "$50 - $200", "> $200"
        self._current_sort_by: str = "Date (Newest)"  # Options: "Date (Newest)", "Date (Oldest)", "Amount (High-Low)", "Amount (Low-High)"

        # --- Pagination State ---
        self._current_page: int = 1
        self._items_per_page: int = 10  # Default items per page
        self._total_pages: int = 1
        self._filtered_and_sorted_expenses: List[ExpenseModel] = [] # Store the filtered and sorted list

        # --- UI Components Initialization ---
        self._search_field = ft.TextField(
            label="Search transactions",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=ft.border_radius.all(8),
            on_change=self._on_search_change,
            height=40,  # Make it slightly smaller to fit well
            content_padding=ft.padding.only(left=10, right=10),  # Adjust padding
            text_style=ft.TextStyle(size=14),  # Smaller text for search bar
        )

        self._date_range_dropdown = ft.Dropdown(
            label="Date Range",
            options=[
                ft.dropdown.Option("All Time"),
                ft.dropdown.Option("This Month"),
                ft.dropdown.Option("Last Month"),
                ft.dropdown.Option("This Year"),
            ],
            value=self._current_date_range,
            on_change=self._on_filter_change,
            border_radius=ft.border_radius.all(8),
        )

        self._category_dropdown = ft.Dropdown(
            label="Category",
            options=[ft.dropdown.Option("All Categories")] + [
                ft.dropdown.Option(cat) for cat in sorted(self.expense_data.get_category_data().keys()) if
                cat != "Other"  # Exclude other if it's 0 unless we have real data
            ],
            value=self._current_category_filter,
            on_change=self._on_filter_change,
            border_radius=ft.border_radius.all(8),
        )

        self._amount_range_dropdown = ft.Dropdown(
            label="Amount Range",
            options=[
                ft.dropdown.Option("All Amounts"),
                ft.dropdown.Option(f"< {self.app_settings.default_currency}50"),
                ft.dropdown.Option(f"{self.app_settings.default_currency}50 - {self.app_settings.default_currency}200"),
                ft.dropdown.Option(f"> {self.app_settings.default_currency}200"),
            ],
            value=self._current_amount_range,
            on_change=self._on_filter_change,
            border_radius=ft.border_radius.all(8),
        )

        self._sort_by_dropdown = ft.Dropdown(
            label="Sort By",
            options=[
                ft.dropdown.Option("Date (Newest)"),
                ft.dropdown.Option("Date (Oldest)"),
                ft.dropdown.Option("Amount (High-Low)"),
                ft.dropdown.Option("Amount (Low-High)"),
            ],
            value=self._current_sort_by,
            on_change=self._on_sort_change,
            border_radius=ft.border_radius.all(8),
        )

        self._data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Category")),
                ft.DataColumn(ft.Text("Amount"), numeric=True),
                ft.DataColumn(ft.Text("Description")),  # Allow description to expand
                ft.DataColumn(ft.Text("Actions")),  # New Actions Column Header
            ],
            rows=[],  # Populated dynamically
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=ft.border_radius.all(8),
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200),
            vertical_lines=ft.BorderSide(1, ft.Colors.GREY_200),
            heading_row_color=ft.Colors.GREY_100,
            heading_row_height=40,
            data_row_max_height=50,
            show_checkbox_column=False,
            expand=True,
        )

        # --- Pagination Controls ---
        self._prev_page_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self._on_previous_page,
            tooltip="Previous Page",
            disabled=True,
        )
        self._next_page_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._on_next_page,
            tooltip="Next Page",
            disabled=True,
        )
        self._page_info_text = ft.Text("Page 1 of 1")

        self._items_per_page_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("5", text="5 per page"),
                ft.dropdown.Option("10", text="10 per page"),
                ft.dropdown.Option("25", text="25 per page"),
                ft.dropdown.Option("50", text="50 per page"),
            ],
            value=str(self._items_per_page),
            on_change=self._on_items_per_page_change,
            border_radius=ft.border_radius.all(8),
        )


        # Register listener for changes in expense_data model
        self.expense_data.register_on_data_change(self._refresh_table)

    def _on_search_change(self, e: ft.ControlEvent):
        """Handles changes in the search text field."""
        self._current_search_query = e.control.value.lower()
        self._current_page = 1  # Reset to first page on new search
        self._refresh_table()

    def _on_filter_change(self, e: ft.ControlEvent):
        """Handles changes in the filter dropdowns."""
        if e.control == self._date_range_dropdown:
            self._current_date_range = e.control.value
        elif e.control == self._category_dropdown:
            self._current_category_filter = e.control.value
        elif e.control == self._amount_range_dropdown:
            self._current_amount_range = e.control.value
        self._current_page = 1  # Reset to first page on new filter
        self._refresh_table()

    def _on_sort_change(self, e: ft.ControlEvent):
        """Handles changes in the sort by dropdown."""
        self._current_sort_by = e.control.value
        self._current_page = 1  # Reset to first page on new sort
        self._refresh_table()

    def _on_previous_page(self, e: ft.ControlEvent):
        """Moves to the previous page of transactions."""
        if self._current_page > 1:
            self._current_page -= 1
            self._refresh_table()

    def _on_next_page(self, e: ft.ControlEvent):
        """Moves to the next page of transactions."""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._refresh_table()

    def _on_items_per_page_change(self, e: ft.ControlEvent):
        """Changes the number of items displayed per page."""
        self._items_per_page = int(e.control.value)
        self._current_page = 1  # Reset to first page when changing items per page
        self._refresh_table()

    def _filter_expenses(self, expenses: List[ExpenseModel]) -> List[ExpenseModel]:
        """Applies current filters to the list of expenses."""
        filtered = []
        today = datetime.date.today()

        for expense in expenses:
            # Date Range Filter
            if self._current_date_range != "All Time":
                expense_date = datetime.datetime.strptime(expense.date, "%Y-%m-%d").date() if expense.date else None
                if not expense_date:
                    continue  # Skip if date is missing for date range filter

                if self._current_date_range == "This Month":
                    if not (expense_date.year == today.year and expense_date.month == today.month):
                        continue
                elif self._current_date_range == "Last Month":
                    first_day_current_month = today.replace(day=1)
                    last_day_last_month = first_day_current_month - datetime.timedelta(days=1)
                    first_day_last_month = last_day_last_month.replace(day=1)
                    if not (first_day_last_month <= expense_date <= last_day_last_month):
                        continue
                elif self._current_date_range == "This Year":
                    if not (expense_date.year == today.year):
                        continue

            # Category Filter
            if self._current_category_filter != "All Categories":
                if expense.category != self._current_category_filter:
                    continue

            # Amount Range Filter
            if self._current_amount_range != "All Amounts":
                if expense.amount is None:
                    continue  # Skip if amount is missing for amount range filter

                if self._current_amount_range == f"< {self.app_settings.default_currency}50":
                    if not (expense.amount < 50):
                        continue
                elif self._current_amount_range == f"{self.app_settings.default_currency}50 - {self.app_settings.default_currency}200":
                    if not (50 <= expense.amount <= 200):
                        continue
                elif self._current_amount_range == f"> {self.app_settings.default_currency}200":
                    if not (expense.amount > 200):
                        continue

            # Search Query Filter (description or category)
            if self._current_search_query:
                description_match = expense.description and self._current_search_query in expense.description.lower()
                category_match = expense.category and self._current_search_query in expense.category.lower()
                if not (description_match or category_match):
                    continue

            filtered.append(expense)
        return filtered

    def _sort_expenses(self, expenses: List[ExpenseModel]) -> List[ExpenseModel]:
        """Applies current sort order to the list of expenses."""
        if self._current_sort_by == "Date (Newest)":
            return sorted(expenses, key=lambda x: datetime.datetime.strptime(x.date,
                                                                             "%Y-%m-%d") if x.date else datetime.datetime.min,
                          reverse=True)
        elif self._current_sort_by == "Date (Oldest)":
            return sorted(expenses, key=lambda x: datetime.datetime.strptime(x.date,
                                                                             "%Y-%m-%d") if x.date else datetime.datetime.max)
        elif self._current_sort_by == "Amount (High-Low)":
            return sorted(expenses, key=lambda x: x.amount if x.amount is not None else -float('inf'), reverse=True)
        elif self._current_sort_by == "Amount (Low-High)":
            return sorted(expenses, key=lambda x: x.amount if x.amount is not None else float('inf'))
        return expenses  # Default to no sort if unknown option

    def _refresh_table(self, *args, **kwargs):  # Added *args, **kwargs to match dispatcher signature
        """
        Filters and sorts the expense data, then updates the DataTable rows with pagination.
        This is called whenever the ExpenseData model changes or a filter/sort/pagination UI element changes.
        """

        if self.route != self.page.route:
            return

        all_expenses = self.expense_data.expenses

        self._filtered_and_sorted_expenses = self._sort_expenses(self._filter_expenses(all_expenses))

        # Update the options for the category dropdown in case new categories were added
        current_category_options = [opt.key for opt in self._category_dropdown.options]
        all_categories_from_data = sorted(set(e.category for e in all_expenses if e.category))

        new_category_options = [ft.dropdown.Option("All Categories")] + [
            ft.dropdown.Option(cat) for cat in all_categories_from_data
        ]

        # Only update if there's a change in options to avoid unnecessary redraws
        new_category_keys = {opt.key for opt in new_category_options}
        if new_category_keys != set(current_category_options):
            self._category_dropdown.options = new_category_options
            self._category_dropdown.update()  # Update dropdown specifically

        # --- Pagination Logic ---
        total_items = len(self._filtered_and_sorted_expenses)
        self._total_pages = (total_items + self._items_per_page - 1) // self._items_per_page
        if self._total_pages == 0: # Handle case with no data
            self._total_pages = 1

        # Ensure current_page doesn't exceed total_pages
        if self._current_page > self._total_pages:
            self._current_page = self._total_pages
        if self._current_page < 1 and self._total_pages >= 1: # Ensure current_page is at least 1 if there's data
            self._current_page = 1

        start_index = (self._current_page - 1) * self._items_per_page
        end_index = start_index + self._items_per_page
        expenses_to_display = self._filtered_and_sorted_expenses[start_index:end_index]

        self._data_table.rows.clear()
        for expense in expenses_to_display:
            # Define on_click handlers for Edit and Delete
            def on_edit_click(e, expense_=expense):
                print(f"Edit button clicked for expense ID: {expense_.id}")
                # In a real app, you'd navigate to an edit form or open a dialog
                # self.page.go(f"/edit_expense/{expense_id}")

                self.on_result_callback(EDIT_ITEM, expense_)

            def on_delete_click(e, expense_=expense):
                print(f"Delete button clicked for expense ID: {expense_.id}")
                # In a real app, you'd show a confirmation dialog then delete from model
                # self.expense_data.delete_expense(expense_id) # Assuming delete_expense method exists

                self.expense_data.remove_expense(expense_)
                self.on_result_callback(DELETE_ITEM, expense_)

            self._data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(expense.date if expense.date else "N/A")),
                        ft.DataCell(ft.Text(expense.category if expense.category else "N/A")),
                        ft.DataCell(ft.Text(f"{self.app_settings.default_currency}. {expense.amount:.2f}" if expense.amount is not None else "N/A")),
                        ft.DataCell(ft.Text(expense.description if expense.description else "N/A")),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.TextButton(
                                        "Edit",
                                        on_click=on_edit_click,
                                        style=ft.ButtonStyle(
                                            color=ft.Colors.BLUE_700,
                                            overlay_color=ft.Colors.BLUE_50,
                                            padding=ft.padding.all(5),
                                            shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(4))
                                        )
                                    ),
                                    Container(ft.VerticalDivider(width=1, color=ft.Colors.GREY_300), margin=ft.margin.only(top=10, bottom=10)),
                                    ft.TextButton(
                                        "Delete",
                                        on_click=on_delete_click,
                                        style=ft.ButtonStyle(
                                            color=ft.Colors.RED_700,
                                            overlay_color=ft.Colors.RED_50,
                                            padding=ft.padding.all(5),
                                            shape=ft.RoundedRectangleBorder(radius=ft.border_radius.all(4))
                                        )
                                    ),
                                ],
                                spacing=0,  # Remove spacing between buttons and divider
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            )
                        ),
                    ]
                )
            )

        # Update pagination controls
        self._prev_page_button.disabled = self._current_page == 1
        self._next_page_button.disabled = self._current_page == self._total_pages
        self._page_info_text.value = f"Page {self._current_page} of {self._total_pages}"

        # Update all relevant controls
        self._data_table.update()
        self._prev_page_button.update()
        self._next_page_button.update()
        self._page_info_text.update()
        self.page.update()  # Ensure the page is updated to show changes

    def build(self, route, **kwargs):
        """
        Builds the Flet UI for the Reports view.
        """
        if route != "/expenses":
            return

        # Filters and Sort controls row
        filter_sort_row = ft.Row(
            controls=[
                self._date_range_dropdown,
                self._category_dropdown,
                self._amount_range_dropdown,
                ft.Row(expand=True),  # Spacer to push sort to the right
                self._sort_by_dropdown,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        )

        # Pagination controls row
        pagination_row = ft.Row(
            controls=[
                self._items_per_page_dropdown,
                ft.Row(expand=True),  # Spacer
                self._prev_page_button,
                self._page_info_text,
                self._next_page_button,
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        container_controls = [
            ft.Container(
                content=ft.Column([
                    self._search_field,
                    ft.Divider(height=10, color="transparent"),
                    filter_sort_row,
                    ft.Divider(height=10, color="transparent"),  # Spacer
                    ft.Container(  # Container for the DataTable to give it some padding/styling
                        content=self._data_table,
                        expand=True,  # Allow table to expand vertically
                        padding=ft.padding.all(0),  # DataTable handles its own internal padding
                        border_radius=ft.border_radius.all(8),
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,  # Ensure content respects rounded corners
                    ),
                    ft.Divider(height=10, color="transparent"),  # Spacer
                    pagination_row, # Add the pagination controls here
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),  # Allow the column containing controls to expand
                expand=True,
                padding=20,
                border_radius=ft.border_radius.all(12),
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=5,
                    color=ft.Colors.BLACK12,
                    offset=ft.Offset(0, 3),
                )
            )
        ]

        container = super().build("Transactions", container_controls)
        return container

    def refresh(self):
        self._refresh_table()