import win32com.client

speaker = win32com.client.Dispatch("SAPI.SpVoice")
say = speaker.Speak

if __name__ == "__main__":
    speak = True
    while speak==True:
        print("Welcome to the RoboSpeaker! 🤖")
        text = input("What do u want me to speak(/exit to exit): ")
        if text.lower() == "/exit":
            speak = False
            exit()
        say(text)
    