import random
from datetime import datetime, timedelta

import flet as ft
import numpy as np


class OnValueChange:

    def __init__(self, callback, registered):
        self.callback = callback
        self.registered = registered

    def is_registered(self, name):
        if name in self.registered:
            return True
        if name == self.registered:
            return True

        return False

    def __call__(self, name, value):
        return self.callback(name, value)

class ExpenseModel:
    def __init__(self, id=None, description=None, amount=None, category=None, date=None):

        self.on_value_change: OnValueChange = None

        self.id = id
        self.description = description
        self.amount = amount
        self.category = category
        self.date = date

    def on_value_change(self, callback):
        self.on_value_change = callback

    def __setattr__(self, name, value):
        self.__dict__[name] = value

        if self.on_value_change is None:
            return

        if self.on_value_change.is_registered(name):
            self.on_value_change(name, value)

    def to_json(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "date": self.date
        }

    def from_json(self, data):
        self.id = data["id"]

        try:
            self.description = data["description"]
        except:
            pass

        self.amount = int(data["amount"])
        self.category = data["category"]
        self.date = data["date"]

    def __str__(self):
        return str(self.to_json())

class ExpenseData:

    def __init__(self, page: ft.Page):
        self.expenses = []
        self.page = page

        self.expense_id_prefix = "expense_"

        self.total = 0
        self.update_callbacks = []

        self.update_value()

    def get_new_id(self):
        id = 0

        for expense in self.expenses:
            if expense.id == id:
                id += 1

        return id

    def load_expenses(self):
        for key in self.page.client_storage.get_keys(self.expense_id_prefix):

            expense = ExpenseModel()
            expense.from_json(self.page.client_storage.get(key))
            self.expenses.append(expense)

        self.update_value()

    def add_expense(self, expense: ExpenseModel):
        expense.id = expense.id if expense.id is not None else self.get_new_id()

        self.expenses.append(expense)
        self.page.client_storage.set(f"{self.expense_id_prefix}{expense.id}", expense.to_json())

        self.update_value()

    def remove_expense(self, expense: ExpenseModel):
        if expense not in self.expenses:
            print("Expense not found")
            return

        self.expenses.remove(expense)
        self.page.client_storage.remove(f"{self.expense_id_prefix}{expense.id}")

        self.update_value()

    def save_expense(self, expense: ExpenseModel):
        self.page.client_storage.set(f"{self.expense_id_prefix}{expense.id}", expense.to_json())

    def update_value(self):
        self.total = sum([expense.amount for expense in self.expenses])
        self.categories = {}

        for expense in self.expenses:
            if expense.category in self.categories:
                self.categories[expense.category] += expense.amount
            else:
                self.categories[expense.category] = expense.amount

        for update_calback in self.update_callbacks:
            update_calback()

    def get_category_data(self):
        return self.categories

    def register_on_data_change(self, callback):
        self.update_callbacks.append(callback)

def generate_dummy_expenses(num_records=1000):
    categories = [
        "Groceries", "Transport", "Utilities", "Entertainment",
        "Dining Out", "Healthcare", "Education", "Shopping", "Other"
    ]

    # 25 creative description options
    descriptions = [
        "Weekly stock-up at the supermarket", "Fuel for the weekend road trip", "Monthly electricity bill",
        "Concert tickets for favorite band", "Dinner at that new Italian place", "Prescription refill",
        "Online course subscription", "New pair of running shoes", "Coffee and a good book",
        "Public transport fare", "Internet service fee", "Streaming service subscription",
        "Lunch with colleagues", "Doctor's visit co-pay", "Textbooks for next semester",
        "Impulse buy from online store", "Movie night with friends", "Uber ride to the airport",
        "Water and refuse collection", "Gaming console purchase", "Takeaway pizza",
        "Dental check-up", "Art class fees", "Gardening supplies", "Donation to charity"
    ]

    expenses = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime.now()

    for i in range(num_records):
        # Generate random date within a range
        time_difference = end_date - start_date
        random_days = random.randint(0, time_difference.days)
        random_date = start_date + timedelta(days=random_days)
        random_date = random_date.strftime("%Y-%m-%d")

        # Generate random amount (e.g., between 5 and 500)
        random_amount = round(random.uniform(5, 500), 2)

        # Choose a random category
        random_category = random.choice(categories)

        # Choose a random creative description
        random_description = random.choice(descriptions)

        expense = ExpenseModel(
            id=i,
            description=random_description,
            amount=random_amount,
            category=random_category,
            date=random_date
        )
        expenses.append(expense)
    return expenses