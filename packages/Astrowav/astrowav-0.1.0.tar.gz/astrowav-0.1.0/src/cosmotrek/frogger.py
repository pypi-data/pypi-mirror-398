import sys
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for cross-platform compatibility
init(autoreset=True)

class ChatLogger:
    """
    A minimal logger for visualizing AI/LLM conversations in the terminal.
    """
    
    def __init__(self, show_time=True):
        self.show_time = show_time

    def _timestamp(self):
        if self.show_time:
            return f"{Style.DIM}[{datetime.now().strftime('%H:%M:%S')}] "
        return ""

    def system(self, message):
        """Used for internal system thoughts or prompts."""
        print(f"{self._timestamp()}{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} {message}")

    def user(self, message):
        """Used for user inputs."""
        print(f"{self._timestamp()}{Fore.GREEN}[USER]{Style.RESET_ALL} {Style.BRIGHT}{message}")

    def bot(self, name, message):
        """Used for AI responses. Pass the agent name (e.g., 'Coder', 'Reviewer')."""
        print(f"{self._timestamp()}{Fore.CYAN}[{name.upper()}]{Style.RESET_ALL} {message}")

    def tool(self, tool_name, result):
        """Used when an agent uses a tool (e.g., 'Search', 'Calculator')."""
        print(f"{self._timestamp()}{Fore.MAGENTA}[TOOL: {tool_name}]{Style.RESET_ALL} {Style.DIM}{result}")

    def error(self, message):
        """Used for exceptions or failures."""
        print(f"{self._timestamp()}{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

    def success(self, message):
        """Used for task completion."""
        print(f"{self._timestamp()}{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.RESET_ALL} {message}")