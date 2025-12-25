from style import Ansi, style
from CLIContext import CLIContext
from Header import Header
from prompt import Option

def demo_context():
    ctx = CLIContext(
        header=Header("Pompy CLI Demo"),
        color2=Ansi.FG_BLUE,
        color3=Ansi.FG_CYAN,
    )
    ctx.print("Hello! This is a demo of the CLIContext class.", clear=True)
    ctx.input("(Press anything to continue.)", allow_empty=True)
    opt = ctx.prompt_opt("What demo would you like to run? (enter 'help' if you don't know)", options=[
        Option("boolean", "b", ("bool",), "Run the boolean demo."),
        Option("integer", "i", ("int",), "Run the integer demo."),
        Option("string", "s", ("str",), "Run the string demo."),
    ], clear=True)

    # ctx.print("It supports colored output and headers.", color=Ansi.BG_YELLOW, padding=1)
    # name = ctx.prompt_str("What's your name?")
    # ctx.print(f"That's your name huh, {style(name.title(), color=Ansi.BG_YELLOW, padding=1)}.", separate=True)
    # ctx.print("Now we'll clear the screen.")
    # ctx.input("(Press anything to continue.)")
    # ctx.print("See you later!", clear=True)


if __name__ == "__main__":
    demo_context()