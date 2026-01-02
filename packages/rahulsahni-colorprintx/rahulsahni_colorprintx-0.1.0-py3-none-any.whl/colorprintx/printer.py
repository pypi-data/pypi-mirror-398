COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "reset": "\033[0m"
}

def cprint(text, color="reset"):
    color_code = COLORS.get(color, COLORS["reset"])
    print(f"{color_code}{text}{COLORS['reset']}")
