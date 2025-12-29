import win32com.client

def main():
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    print("Welcome to the RoboSpeaker! 🤖")
    while True:
        text = input("What do u want me to speak(/exit to exit): ")
        if text.lower() == "/exit":
            break
        speaker.Speak(text)

if __name__ == "__main__":
    main()
