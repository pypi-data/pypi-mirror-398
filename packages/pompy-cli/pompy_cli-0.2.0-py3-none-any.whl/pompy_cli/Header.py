from dataclasses import dataclass, field
from pompy_cli.style import style, Ansi

@dataclass
class Line:
    width: int = 1
    style: str = "o-|o"


@dataclass
class Box:
    color: Ansi = field(default_factory= lambda: Ansi.FG_CYAN)
    left: Line = field(default_factory= lambda: Line(1))
    right: Line = field(default_factory= lambda: Line(1))
    top: Line = field(default_factory= lambda: Line(1))
    bottom: Line = field(default_factory= lambda: Line(1))
    padding_x: int = 2
    padding_y: int = 0
    margin_top: int = 0
    margin_bottom: int = 1
    margin_left: int = 0
    margin_right: int = 0


@dataclass
class Header:
    title: str
    color: Ansi = None
    borders: Box = field(default_factory= lambda:Box())

    def render(self,*, subtitle="", display_title=True):
        print("\n" * self.borders.margin_top, end="")
        for _ in range(self.borders.top.width):
            print(style(
                self.borders.top.style[0] +
                self.borders.top.style[1] * (len(self.title) + self.borders.padding_x * 2) +
                self.borders.top.style[3]
            , color=self.borders.color))
        for _ in range(self.borders.padding_y):
            print(style(
                self.borders.left.style[2] * self.borders.left.width +
                " " * (len(self.title) + self.borders.padding_x * 2) +
                self.borders.right.style[2] * self.borders.right.width
            , color=self.borders.color))
        print(
            style(self.borders.left.style[2] * self.borders.left.width +
            self.borders.padding_x * " ", color=self.borders.color) +
            style(self.title, color=self.color) +
            style(self.borders.padding_x * " " +
            self.borders.right.style[2] * self.borders.right.width, color=self.borders.color)
        )
        for _ in range(self.borders.padding_y):
            print(style(
                self.borders.left.style[2] * self.borders.left.width +
                " " * (len(self.title) + self.borders.padding_x * 2) +
                self.borders.right.style[2] * self.borders.right.width
            ), color=self.borders.color)
        for _ in range(self.borders.bottom.width):
            print(style(
                self.borders.bottom.style[0] +
                self.borders.bottom.style[1] * (len(self.title) + self.borders.padding_x * 2) +
                self.borders.bottom.style[3]
            , color=self.borders.color))
        print("\n" * self.borders.margin_bottom, end="")