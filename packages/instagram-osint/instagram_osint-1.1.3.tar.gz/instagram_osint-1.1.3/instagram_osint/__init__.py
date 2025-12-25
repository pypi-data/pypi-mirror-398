"""
## Instagram OSINT Tool
A powerful Instagram scraping and OSINT utility

- Made by Junaid (https://abujuni.dev)
- Original Script by sc1341 (https://0xd33r.com)

Version: 1.1.3
"""

__version__ = "1.1.3"
__author__ = "Junaid"
__email__ = "contact@abujuni.dev"
__url__ = "https://abujuni.dev"


from .instagramOSINT import InstagramOSINT, colors
from .cli import InstagramCLI, main as cli_main

__all__ = ["InstagramOSINT", "InstagramCLI", "colors", "cli_main", "cli"]

cli = InstagramCLI
