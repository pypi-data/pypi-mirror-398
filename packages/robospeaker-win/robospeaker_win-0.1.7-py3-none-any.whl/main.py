from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
import win32com.client


def main():
    console = Console()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        console.print(Markdown("# Welcome to the [RoboSpeaker]! 🤖"), style="bold cyan")
        while True:
            text = console.input("What do u want me to speak (/exit to exit): ")
            if text.lower() == "/exit":
                console.print("\n[bold red]Exiting...[/] Goodbye! 👋")
                break
            speaker.Speak(text)
            print("")
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/] Goodbye! 👋")
if __name__ == "__main__":
    main()
