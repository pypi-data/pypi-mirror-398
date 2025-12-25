import os
from pompy_cli.style import style, Ansi

def clear():
    os.system('cls||clear')

def get_input(text, color=Ansi.FG_CYAN, *, allow_empty:bool=False):
    user_input = input(style(text + " ", color=color))
    if not allow_empty:
        while not user_input:
            print(style("Try entering something.", color=Ansi.FG_RED))
            user_input = input(style(text + " ", color=color))
    return user_input