from pompy_cli import util
from pompy_cli.style import style, Ansi
from collections.abc import Iterable
from dataclasses import dataclass, field
import sys

@dataclass
class Option:
    long: str
    short: str
    aliases: Iterable[str] = field(default_factory=tuple)
    description: str = "No description."
    def __str__(self):
        return (
            style(f"[{self.short.upper()}] {self.long.title()}:", color=Ansi.FG_YELLOW) + \
            f" {self.description}\n" + \
            f"(aliases: {', '.join(self.aliases)})\n"
            )

def display_help(options:Iterable[Option]):
    print()
    for opt in options:
        print(opt)


def prompt_str(text:str="", *, ctx:bool=False, 
        case_sensitive:bool=False, allow_empty:bool=False, trim:bool=True, min:int=0
        ):
    if not ctx and text:
        print(text)
    while True:
        user_input = util.get_input("[Enter any string.]")
        if trim:
            user_input = user_input.strip()
        if not allow_empty and not user_input:
            print(style("Try entering something.", color=Ansi.FG_RED))
        elif len(user_input) < min:
            print(style(f"Please enter at least {min} characters.", color=Ansi.FG_RED))
        elif not case_sensitive:
            return user_input.lower()
        else:
            return user_input


def prompt_bool(text:str="", *, ctx:bool=False):
    if not ctx and text:
        print(text)
    user_input = util.get_input("[y, n]").strip().lower()
    while True:
        if user_input in ("y", "yes", "1", "true"):
            return True
        elif user_input in ("n", "no", "0", "false"):
            return False
        print(style("It's a yes or no question.", color=Ansi.FG_RED))
        user_input = util.get_input("(Y|N)").strip().lower()


def prompt_opt(text:str="", *, ctx:bool=False, 
        options=list[Option], help:bool=True, quit:bool=True
        ):
    if not ctx and text:
        print(text)
    if help:
        options.append(
            Option("help", "h", ("man", "about"), "Display a help message."),
        )
    if quit:
        options.append(
            Option("quit", "q", ("exit", "close"), "Quit the program.")
        )
    display = f"[{", ".join([opt.short.upper() for opt in options])}]"
    
    while True:
        user_input = util.get_input(display).strip().lower()
        if help and user_input in ("help", "h", "man", "about"):
            display_help(options)
            user_input = ""
            continue
        if quit and user_input in ("quit", "q", "exit", "close"):
            sys.exit()
        for opt in options:
            if user_input in (opt.short, opt.long, *opt.aliases):
                return opt.long
        print(style("That's not a valid option.", color=Ansi.FG_RED))


def prompt_int(text:str="", *, ctx:bool=False, 
        min:int, max:int
        ):
    if not ctx and text:
        print(text)
    display = "["
    if min is not None:
        display += str(min)
        if max is not None:
            display += f"-{max}]"
        else:
            display += " or higher]"
    elif max is not None:
        display += f"up to {max}]"
    else:
        display += "any integer]"
    while True:
        user_input = util.get_input(display).strip()
        if not user_input:
            print(style(f"Try entering something.", color=Ansi.FG_RED))
            continue
        try:
            user_input = int(user_input)
            if min is not None and user_input < min:
                print(style(f"Please enter a number bigger than {min}.", color=Ansi.FG_RED))
            elif max is not None and user_input > max:
                print(style(f"Please enter a number smaller than {max}.", color=Ansi.FG_RED))
            else:
                return user_input
        except ValueError:
            print(style("Please only enter numbers.", color=Ansi.FG_RED))