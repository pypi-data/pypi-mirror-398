from pompy_cli import util
from pompy_cli.prompt import Option, prompt_bool, prompt_int, prompt_opt, prompt_str
from pompy_cli.Header import Header
from pompy_cli.style import Ansi, style

class CLIContext:
    def __init__(
            self, *, 
            header: Header | None = None, 
            color1: str = "",
            color2: str = Ansi.FG_CYAN,
            color3: str = Ansi.FG_PURPLE,
            separator: str = "-"
            ):
        self.color1 = color1
        self.color2 = color2
        self.color3 = color3
        self.separator = separator
        self.header = header
        self.is_cleared = False

    def clear(self):
        util.clear()
        if self.header:
            self.header.render()
        self.is_cleared = True
    
    def input(self, text:str, *, allow_empty:bool=False):
        util.get_input(text, color=self.color3, allow_empty=allow_empty)
    
    def print(self, str, *, 
            separate=False, clear=False, color=None,
            padding=0
        ):
        if clear and not self.is_cleared:
            self.clear()
        elif separate:
            self.print_separator()
        if color:
            str = style(str, color=color, padding=padding)
        elif self.color1:
            str = style(str, color=self.color1, padding=padding)
        print(str)
        self.is_cleared = False

    def print_separator(self):
        if self.separator:
            print(style(self.separator * 40, color=self.color2) + "\n")
    
    def prompt_str(self, text, *,
            allow_empty=False, case_sensitive=False, trim=True,
            separate=False, clear=False, color=None,
        ):
        self.print(text, separate=separate, clear=clear, color=color)
        return prompt_str(
            ctx=True, case_sensitive=case_sensitive, trim=trim, allow_empty=allow_empty
            )

    def prompt_bool(self, text, *,
            separate=False, clear=False, color=None,
        ):
        self.print(text, separate=separate, clear=clear, color=color)
        return prompt_bool(ctx=True,)

    def prompt_int(self, text, *, 
            min:int=0, max:int=None,
            separate=False, clear=False, color=None,
        ):
        self.print(text, separate=separate, clear=clear, color=color)
        return prompt_int(ctx=True, min=min, max=max)
    
    def prompt_opt(self, text, *, 
            options:list[Option],
            separate=False, clear=False, color=None,
        ):
        self.print(text, separate=separate, clear=clear, color=color)
        return prompt_opt(ctx=True, options=options)