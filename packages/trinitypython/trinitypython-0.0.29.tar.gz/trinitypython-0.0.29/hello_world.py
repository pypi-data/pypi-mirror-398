from datetime import datetime
from random import randint, choice
from trinitypython.uiutils import menu_based_app


def show_date():
    print(datetime.now().strftime("%Y-%m-%d"))


def show_time():
    print(datetime.now().strftime("%H:%M:%S"))


def show_date_and_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def show_random_number():
    print(randint(1, 100))


def show_random_color():
    print(choice(['red', 'blue', 'green']))


ar = [
    ["Random", "Random Integer", show_random_number],
    ["Random", "Random Color", show_random_color],
    ["Date", "Show Date", show_date],
    ["Date", "Show Time", show_time],
    ["Date", "Show Date and Time", show_date_and_time]
]

menu_based_app.start(ar)