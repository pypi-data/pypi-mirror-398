from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

LOGO = Align.center(
	Panel.fit(
		Text(
			"""
                                                                
             ▄▄                                                 
      ▀▀     ██                                                 
██ ██ ██  ▄████ ▄█▀█▄ ▄███▄       ▄█▀▀▀ ████▄ ▄█▀█▄ ▄████ ▄█▀▀▀ 
██▄██ ██  ██ ██ ██▄█▀ ██ ██ ▀▀▀▀▀ ▀███▄ ██ ██ ██▄█▀ ██    ▀███▄ 
 ▀█▀  ██▄ ▀████ ▀█▄▄▄ ▀███▀       ▄▄▄█▀ ████▀ ▀█▄▄▄ ▀████ ▄▄▄█▀ 
                                        ██                      
                                        ▀▀                      
            """,
			style="yellow3"
		),
		border_style="blue_violet",
		padding=(1, 6)
	)
)
