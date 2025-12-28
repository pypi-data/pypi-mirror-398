"""A festive terminal Christmas card for the Python community"""

import random
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich import box

# Festive Python code snippets
SNIPPETS = [
    '''while True:
    spread_joy()''',

    '''joy, peace, *rest = open("presents")
# rest is just socks again''',

    '''sleigh += [elf.wrap(gift) for gift in gifts]''',

    '''class Verdict(StrEnum):
    NAUGHTY = "naughty"
    NICE = "nice"

def check(name: str) -> Verdict:
    return Verdict.NICE  # it's Christmas''',

    '''await uma.open(presents)  # worth the wait''',

    '''try:
    work()
except Holidays:
    rest()
finally:
    eat_cookies()''',

    '''"Fa" + "la" * 8''',

    '''@with_loved_ones
def celebrate():
    pass  # just be present''',

    '''class Reindeer:
    nose = "normal"

class Rudolf(Reindeer):
    nose = "glowing"''',

    '''if dec_25:
    raise Spirits''',

    '''class Santa(type):
    """He knows when you're awake"""''',
]

def print_tree(console):
    """Print a colorful ASCII Christmas tree"""
    ornament_colors = ["bold red", "bold blue", "bold yellow", "bold magenta", "bold cyan"]

    tree = Text()
    # Each line has leading spaces to align relative to the 11-char base
    tree.append("     ")
    tree.append("*", style="bold yellow")
    tree.append("\n")

    tree.append("    /", style="green")
    tree.append("*", style=random.choice(ornament_colors))
    tree.append("\\", style="green")
    tree.append("\n")

    tree.append("   /", style="green")
    tree.append("o", style=random.choice(ornament_colors))
    tree.append("*", style="green")
    tree.append("o", style=random.choice(ornament_colors))
    tree.append("\\", style="green")
    tree.append("\n")

    tree.append("  /", style="green")
    tree.append("*", style=random.choice(ornament_colors))
    tree.append("o*o", style="green")
    tree.append("*", style=random.choice(ornament_colors))
    tree.append("\\", style="green")
    tree.append("\n")

    tree.append(" /", style="green")
    tree.append("o", style=random.choice(ornament_colors))
    tree.append("*o*o*", style="green")
    tree.append("o", style=random.choice(ornament_colors))
    tree.append("\\", style="green")
    tree.append("\n")

    tree.append("/", style="green")
    tree.append("*", style=random.choice(ornament_colors))
    tree.append("o*o*o*o", style="green")
    tree.append("*", style=random.choice(ornament_colors))
    tree.append("\\", style="green")
    tree.append("\n")

    tree.append("     ")
    tree.append("|", style="rgb(139,69,19)")

    from rich.align import Align
    console.print(Align.center(tree))

# Rich-compatible Pygments themes (good contrast in terminals)
THEMES = [
    "monokai", "dracula", "nord", "gruvbox-dark", "one-dark",
    "material", "native", "vim", "rrt", "fruity", "igor",
    "lovelace", "algol_nu", "friendly_grayscale", "rainbow_dash",
]


def make_snowfall(width=50):
    """Create a line of random snowflakes"""
    snowflakes = ["*", ".", "+", "~"]
    line = ""
    for _ in range(width):
        if random.random() < 0.12:
            line += random.choice(snowflakes)
        else:
            line += " "
    return line


def render_card():
    """Render the full Christmas card to terminal"""
    console = Console()

    # Pick random snippet and theme
    snippet = random.choice(SNIPPETS)
    theme = random.choice(THEMES)

    # Create syntax-highlighted code
    syntax = Syntax(snippet, "python", theme=theme, line_numbers=False)

    # Build the card
    console.print()
    print_tree(console)
    console.print(f"[white]{make_snowfall(50)}[/white]", justify="center")
    console.print()
    console.print(Panel(syntax, border_style="dim", box=box.ROUNDED))
    console.print()
    console.print(f"[white]{make_snowfall(50)}[/white]", justify="center")
    console.print()

    # Message
    console.print("[bright_white]Wishing the Python community[/bright_white]", justify="center")
    console.print("[bright_white]a joyful holiday season and[/bright_white]", justify="center")
    console.print("[bright_white]a wonderful new year![/bright_white]", justify="center")
    console.print()
    console.print("[white]With love & gratitude,[/white]", justify="center")
    console.print("[bold]Audrey & Daniel Roy Greenfeld[/bold]", justify="center")
    console.print("[dim]@audreyfeldroy & @pydanny[/dim]", justify="center")
    console.print()
    console.print(f"[dim italic]theme: {theme}[/dim italic]", justify="center")
    console.print()


def main():
    """CLI entry point"""
    render_card()


if __name__ == "__main__":
    main()
