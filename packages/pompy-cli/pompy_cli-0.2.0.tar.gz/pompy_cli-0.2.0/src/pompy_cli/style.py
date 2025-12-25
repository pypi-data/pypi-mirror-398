class Ansi:
    FG_BLACK = "30"
    FG_RED = "31"
    FG_GREEN = "32"
    FG_YELLOW = "33"
    FG_BLUE = "34"
    FG_PURPLE = "35"
    FG_CYAN = "36"
    FG_WHITE = "37"

    BG_BLACK = "40"
    BG_RED = "41"
    BG_GREEN = "42"
    BG_YELLOW = "43"
    BG_BLUE = "44"
    BG_PURPLE = "45"
    BG_CYAN = "46"
    BG_WHITE = "47"
    
    FG_BLACK_HI = "90"
    FG_RED_HI = "91"
    FG_GREEN_HI = "92"
    FG_YELLOW_HI = "93"
    FG_BLUE_HI = "94"
    FG_PURPLE_HI = "95"
    FG_CYAN_HI = "96"
    FG_WHITE_HI = "97"
    
    BG_BLACK_HI = "100"
    BG_RED_HI = "101"
    BG_GREEN_HI = "102"
    BG_YELLOW_HI = "103"
    BG_BLUE_HI = "104"
    BG_PURPLE_HI = "105"
    BG_CYAN_HI = "106"
    BG_WHITE_HI = "107"

    BOLD = "1"
    UNDERLINE = "4"
    RESET = "\033[0m"


def style(str, *, color="", decoration="", padding=0) -> str:
    if not color and not decoration:
        return str
    opening = "\033["
    if decoration:
        opening += decoration + ";"
    return opening + color + "m" + padding * " " + str + padding * " " + Ansi.RESET