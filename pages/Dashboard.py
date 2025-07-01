from collections import namedtuple, defaultdict
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

import flet as ft
from flet.core.canvas.canvas import Canvas
from flet.core.column import Column
from flet.core.row import Row
from flet.core.text import Text

from models.ExpenseData import ExpenseData, ExpenseModel
from pages.view_helpers import Container, Controller

class SizeAwareControl(Canvas):
    def __init__(self, content: Optional[ft.Control] = None, resize_interval: int=100, on_resize: Optional[Callable]=None, **kwargs):
        """
        :param content: A child Control contained by the SizeAwareControl. Defaults to None.
        :param resize_interval: The resize interval. Defaults to 100.
        :param on_resize: The callback function for resizing. Defaults to None.
        :param kwargs: Additional keyword arguments(see Canvas properties).
        """
        super().__init__(**kwargs)
        self.content = content
        self.resize_interval = resize_interval
        self.on_resize = self.__handle_canvas_resize
        self.resize_callback = on_resize
        self.size = (0, 0)

    def __handle_canvas_resize(self, e):
        """
        Called every resize_interval when the canvas is resized.
        If a resize_callback was given, it is called.
        """
        self.size = (int(e.width), int(e.height))
        self.update()
        if self.resize_callback:
            self.resize_callback(e)

class SampleRod(ft.BarChartRod):
    def __init__(self, y: float, hovered: bool = False, prefix=""):
        super().__init__()
        self.hovered = hovered
        self.y = y
        self.color = ft.Colors.BLUE
        self.bg_to_y = 20
        self.bg_color = ft.Colors.TRANSPARENT
        self.border_radius = 0
        self.border_side = ft.BorderSide(width=1, color=ft.Colors.BLACK)
        self.prefix = prefix

    def before_update(self):
        self.tooltip = f"{self.prefix} {self.y}"
        self.to_y = self.y if self.hovered else self.y
        self.color = ft.Colors.WHITE if self.hovered else ft.Colors.PRIMARY
        self.border_side = (
            ft.BorderSide(width=1, color=ft.Colors.PRIMARY)
            if self.hovered
            else ft.BorderSide(width=1, color=ft.Colors.BLACK)
        )
        super().before_update()


class DashboardController(Controller):
    """
    Controller for the Dashboard view, displaying total expenses,
    a breakdown by category using a BarChart, and a line graph for
    past 12 months' costs.
    This controller now listens to changes in the ExpenseData model and
    updates its UI accordingly.
    """

    def __init__(self, page: ft.Page, app_settings, expense_data: ExpenseData, page_route):
        super().__init__(page, app_settings, page_route)

        self.expense_data = expense_data  # The data model

        # --- UI Controls Initialization ---
        # Text control for displaying total expenses
        self._total_expenses_text = ft.Text(
            f"{self.app_settings.default_currency}. {self.expense_data.total:.2f}",
            font_family="Inter",
            weight=ft.FontWeight.BOLD,
            size=21
        )

        # BarChart control for category breakdown
        self._category_chart = ft.BarChart(
            height=200,
            groups_space=20,
            bar_groups=[],  # Will be populated dynamically
            bottom_axis=ft.ChartAxis(
                labels=[],  # Will be populated dynamically
            ),
            on_chart_event=self._on_chart_event,  # Event handler for chart interactions
            interactive=True
        )

        # SizeAwareControl to make the category bar chart responsive
        self._category_canvas = SizeAwareControl(content=self._category_chart, resize_interval=100, on_resize=self._page_resized)

        # LineChart control for past 12 months cost
        self._monthly_cost_chart = ft.LineChart(
            min_y=0,
            min_x=0,
            max_x=11, # 12 months, 0-11 index
            expand=True, # Make it expand to fill available space
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
            border=ft.Border(
                bottom=ft.BorderSide(1, ft.Colors.BLUE_GREY_100),
                left=ft.BorderSide(1, ft.Colors.BLUE_GREY_100),
            ),
            left_axis=ft.ChartAxis(
                labels_size=60,
                title=ft.Text(f"Cost ({self.app_settings.default_currency}.)", size=12),
                title_size=20,
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Month", size=12),
                title_size=20,
            ),
            data_series=[], # Will be populated dynamically
        )
        # We will call _generate_monthly_cost_data inside _on_expense_data_change to ensure it uses potentially updated expense data

        # Register listener for changes in expense_data model
        self.expense_data.register_on_data_change(self._on_expense_data_change)

        # Initial update of the dashboard UI
        self._on_expense_data_change(True) # This will now also call _generate_monthly_cost_data

    def _on_chart_event(self, e: ft.BarChartEvent):
        """
        Handles hover events on the bar chart, changing the appearance of the hovered rod.
        """
        for group_index, group in enumerate(self._category_chart.bar_groups):
            for rod_index, rod in enumerate(group.bar_rods):
                rod.hovered = e.group_index == group_index and e.rod_index == rod_index
        self._category_chart.update()

    def _page_resized(self, e: ft.ControlEvent):
        """
        Callback for when the SizeAwareControl (canvas) is resized.
        Adjusts the width of the chart bars to fit the new canvas width.
        """
        group_space = self._category_chart.groups_space

        print(self._category_canvas.size[0])
        # Calculate available width for bars, accounting for group spacing
        chart_width = self._category_canvas.size[0] - group_space * (len(self._category_chart.bar_groups) - 1) if len(
            self._category_chart.bar_groups) > 1 else self._category_canvas.size[0]

        for group_index, group in enumerate(self._category_chart.bar_groups):
            # Calculate rod width for each group dynamically
            rod_width = chart_width / len(self._category_chart.bar_groups)
            for rod_index, rod in enumerate(group.bar_rods):
                rod.width = rod_width
        self._category_chart.update()

    def _generate_monthly_cost_data(self):
        """
        Generates data for the past 12 months' costs for the line chart,
        aggregating costs from the actual expense_data.
        If no expenses exist for a month, its cost will be 0.
        """
        # Dictionary to store aggregated costs by year-month (e.g., (2024, 6))
        monthly_aggregated_costs = defaultdict(float)

        self._monthly_cost_chart.left_axis = ft.ChartAxis(
                labels_size=60,
                title=ft.Text(f"Cost ({self.app_settings.default_currency}.)", size=12),
                title_size=20,
            )

        # Aggregate expenses by month and year
        for expense in self.expense_data.expenses:
            try:
                expense_date = datetime.strptime(expense.date, "%Y-%m-%d")
                year_month_key = (expense_date.year, expense_date.month)
                monthly_aggregated_costs[year_month_key] += expense.amount
            except ValueError:
                # Handle cases where date format might be incorrect
                print(f"Warning: Could not parse date '{expense.date}' for expense: {expense.description}")

        monthly_costs = []
        months_labels = []
        today = datetime.now()

        # Generate data points for the past 12 months, ensuring chronological order
        for i in range(12):
            # Calculate the target month and year for this data point
            # Start from 11 months ago and go up to the current month
            target_year = today.year
            target_month = today.month - (11 - i)
            while target_month <= 0:
                target_month += 12
                target_year -= 1

            target_date = datetime(target_year, target_month, 1)
            month_name = target_date.strftime("%b")  # Abbreviated month name (e.g., Jan)
            year_short = target_date.strftime("%y")  # Last two digits of the year (e.g., 24)

            # Get the cost for this month, defaulting to 0 if no expenses
            cost = monthly_aggregated_costs.get((target_year, target_month), 0.0)

            monthly_costs.append(ft.LineChartDataPoint(i, cost, tooltip=f"{self.app_settings.default_currency}. {cost:.2f}"))
            months_labels.append(
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Container(ft.Text(f"{month_name} {year_short}", size=10, rotate=-0.785), margin=ft.margin.only(top=10)), # Rotate for better fit
                )
            )

        # Determine max_y dynamically based on actual data, plus a buffer
        max_cost_in_data = max([point.y for point in monthly_costs]) if monthly_costs else 0
        min_cost_in_data = min([point.y for point in monthly_costs]) if monthly_costs else 0

        # Set max_y to a value slightly above the max actual cost, ensuring graph looks good
        self._monthly_cost_chart.max_y = max(700, max_cost_in_data * 1.2)  # Ensure at least 700 or 20% above max
        self._monthly_cost_chart.min_y = max(0, int(min_cost_in_data * 0.8))

        self._monthly_cost_chart.data_series = [
            ft.LineChartData(
                data_points=monthly_costs,
                stroke_width=3,
                curved=True,
            )
        ]
        self._monthly_cost_chart.bottom_axis.labels = months_labels


    def _on_expense_data_change(self, initial=False):
        """
        Callback function executed when the expense_data model notifies of a change.
        Updates the UI elements (total expenses text and bar chart) to reflect new data.
        """

        if self.page.route != "/" and not initial:
            return

        # Update total expenses text
        self._total_expenses_text.value = f"{self.app_settings.default_currency}. {self.expense_data.total:.2f}"

        # Prepare category chart data
        category_data = self.expense_data.get_category_data()

        # Sort categories for consistent chart display (optional, but good practice)
        sorted_categories = sorted(category_data.keys())

        bar_groups = []
        chart_labels = []

        # Map categories to numerical X-axis values
        category_map = {cat: i for i, cat in enumerate(sorted_categories)}

        for category, amount in category_data.items():
            x_value = category_map.get(category)
            if x_value is not None:
                # Create a BarChartGroup for each category
                bar_groups.append(
                    ft.BarChartGroup(
                        x=x_value,
                        bar_rods=[SampleRod(y=amount, prefix=f"{self.app_settings.default_currency}")],  # Use SampleRod with the amount
                        # tooltip=category # You can add a tooltip to the group if needed
                    )
                )
                # Create a ChartAxisLabel for each category
                chart_labels.append(
                    ft.ChartAxisLabel(value=x_value, label=ft.Text(category))
                )

        # Sort bar_groups and chart_labels by x_value to ensure correct order
        bar_groups.sort(key=lambda g: g.x)
        chart_labels.sort(key=lambda l: l.value)

        # Update the chart's bar groups and bottom axis labels
        self._category_chart.bar_groups = bar_groups
        self._category_chart.bottom_axis.labels = chart_labels

        # Regenerate monthly cost data when expense data changes
        self._generate_monthly_cost_data()

        # Trigger update for the Flet page to reflect changes
        self.page.update()

        if not initial:
            self._page_resized(None)

    def build(self, route: str, **kwargs):
        """
        Builds the Flet UI for the Dashboard view.
        """
        if route != "/":
            return  # Only build if the route matches

        # Define the layout for the dashboard
        dashboard_controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Total Expenses (Overall)", color="#121417", font_family="Inter",
                            weight=ft.FontWeight.W_500, size=14),
                    self._total_expenses_text,  # Use the dynamic text control
                ]),
                bgcolor="#F2F2F5",
                expand=True,
                padding=20,
                border_radius=ft.border_radius.all(12)
            ),
            ft.Text("Expenses by Category", color="#121417", font_family="Inter",
                    weight=ft.FontWeight.BOLD, size=20),
            ft.Container(
                content=Column([
                    Text("Category Breakdown", color="#121417", font_family="Inter",
                         weight=ft.FontWeight.W_500, size=14),
                    self._category_canvas  # Use the SizeAwareControl wrapping the chart
                ]),
                border=ft.border.all(1, "#DEE0E3"),
                expand=True,
                padding=20,
                border_radius=ft.border_radius.all(12),
            ),
            # New Container for the Line Chart
            ft.Text("Past 12 Months Cost", font_family="Inter",
                    weight=ft.FontWeight.BOLD, size=20),
            ft.Container( # Changed to ft.Container for consistency and layout control
                content=ft.Column([ # Ensure this Column expands
                    ft.Text("Monthly Cost Trend", color="#121417", font_family="Inter",
                         weight=ft.FontWeight.W_500, size=14),
                    self._monthly_cost_chart, # The new line chart
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, spacing=40), # <-- ADDED THIS
                border=ft.border.all(1, "#DEE0E3"),
                expand=True,
                padding=20,
                height=300, # Still giving it a fixed height for better visibility
                border_radius=ft.border_radius.all(12)
            )
        ]

        self._on_expense_data_change(True)

        # Use the base Controller's build method to create the main view
        container = super().build("Dashboard", dashboard_controls)
        return container

    def _add_dummy_expense(self, e: ft.ControlEvent):
        """
        Adds a dummy expense to the ExpenseData model for demonstration purposes.
        This will trigger the registered listener and update the dashboard UI.
        """
        dummy_expenses = [
            ExpenseModel(description="Coffee", amount=3.50, category="Food", date="2025-06-20"),
            ExpenseModel(description="Bus ticket", amount=2.00, category="Transport", date="2025-06-21"),
            ExpenseModel(description="Movie night", amount=15.00, category="Entertainment", date="2025-06-22"),
            ExpenseModel(description="New T-shirt", amount=25.00, category="Shopping", date="2025-06-23"),
            ExpenseModel(description="More Groceries", amount=40.00, category="Groceries", date="2025-06-24"),
            ExpenseModel(description="Electricity bill", amount=80.00, category="Utilities", date="2025-06-25"),
            ExpenseModel(description="Dinner with friends", amount=35.00, category="Dining Out", date="2025-06-26"),
            ExpenseModel(description="Doctor visit", amount=60.00, category="Healthcare", date="2025-06-27"),
            ExpenseModel(description="Online course fee", amount=100.00, category="Education", date="2025-06-28"),
            ExpenseModel(description="Random item", amount=10.00, category="Other", date="2025-06-29"),
        ]
        import random
        random_expense = random.choice(dummy_expenses)
        self.expense_data.add_expense(random_expense)
        print(f"Added dummy expense: {random_expense.category} - ${random_expense.amount}")

