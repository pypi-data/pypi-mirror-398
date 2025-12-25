import util
from prompt import prompt_str, prompt_bool, prompt_opt, prompt_int, Option
from style import Ansi, style
from random import randint

def demo_prompts():
    end = False
    while not end:
        util.clear()
        print("Your name is " + style(
            prompt_str("What's your name?", True).title(), 
            color=Ansi.BG_YELLOW, 
            decoration=Ansi.BOLD, 
            padding=1)
            )
        user_input = prompt_bool("Are you enjoying this demo?")
        if user_input:
            print("Please get help.")
        else:
            print("I was worried for a moment.")
        fingers = randint(0, 10)
        user_input = prompt_int("How many fingers am I holding up?", max=10, min=0)
        if user_input == fingers:
            print("Amazing, that's correct! What are the chances? (10%)")
        else:
            print("Bzzzzt!")
        user_input = prompt_opt("Quit or restart?", options=[
            Option("quit", "q", ("exit", "close"), "Quit the program."),
            Option("restart", "r")
        ])
        if user_input == "quit":
            end = True


if __name__ == "__main__":
    demo_prompts()
