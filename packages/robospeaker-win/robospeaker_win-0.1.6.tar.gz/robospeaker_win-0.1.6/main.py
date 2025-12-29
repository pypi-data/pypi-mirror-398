from rich.console import Console
from rich.theme import Theme
import win32com.client


def main():
    console = Console()
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    console.print("Welcome to the [bold green]RoboSpeaker[/]! 🤖", style="bold cyan")
    while True:
        text = console.input("What do u want me to speak (/exit to exit): ")
        if text.lower() == "/exit":
            break
        speaker.Speak(text)
        print("")
if __name__ == "__main__":
    main()
