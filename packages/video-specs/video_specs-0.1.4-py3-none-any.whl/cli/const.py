from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

LOGO = Align.center(
	Panel.fit(
		Text(
			"""
                                                                                                             
             _|        _|                                                                                    
 _|      _|        _|_|_|    _|_|      _|_|                  _|_|_|  _|_|_|      _|_|      _|_|_|    _|_|_|  
 _|      _|  _|  _|    _|  _|_|_|_|  _|    _|  _|_|_|_|_|  _|_|      _|    _|  _|_|_|_|  _|        _|_|      
   _|  _|    _|  _|    _|  _|        _|    _|                  _|_|  _|    _|  _|        _|            _|_|  
     _|      _|    _|_|_|    _|_|_|    _|_|                _|_|_|    _|_|_|      _|_|_|    _|_|_|  _|_|_|    
                                                                     _|                                      
                                                                     _|                                      
            """,
			style="blue_violet"
		),
		border_style="yellow3",
		padding=(1, 6)
	)
)
