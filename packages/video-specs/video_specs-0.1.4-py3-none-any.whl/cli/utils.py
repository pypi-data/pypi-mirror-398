from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()


def banner(message: str, success: bool = False) -> Align:
	style = "bold blue_violet" if not success else "bold green"
	border_style = "yellow3" if not success else "green"
	console.clear()
	console.print(
		Panel(
			Align.center(Text(message.upper(), style=style)),
			border_style=border_style,
			padding=(1, 1),
		)
	)

def success_banner(message: str) -> Align:
	return banner(message, success=True)