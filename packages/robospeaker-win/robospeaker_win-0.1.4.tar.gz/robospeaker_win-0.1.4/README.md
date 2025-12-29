# 🤖 RoboSpeaker

A lightweight, zero-configuration Text-to-Speech (TTS) utility tailored for Windows. **RoboSpeaker** leverages the native Windows SAPI (Speech API) to provide a seamless vocal interface for your Python scripts or manual text input.

---

## ✨ Features
- **Instant Vocalization**: Real-time conversion of text into speech.
- **Minimalist Interface**: Simple command-line loop for recurring inputs.
- **Native Windows Integration**: Uses Microsoft's Speech API for reliable performance without heavy external libraries.
- **Escape Commands**: Easy `/exit` command to terminate the session instantly.

## 🛠️ Requirements
- **OS**: Windows (Required for `SAPI.SpVoice`).
- **Python**: 3.11 or higher.
- **Dependencies**: `pywin32` (for `win32com.client`).

## 🚀 Getting Started

### 1. Installation

Choose your preferred package manager to install **RoboSpeaker**:

#### Using `pip`
```bash
pip install robospeaker-win
```

#### Using `pipx` (Recommended for CLI tools)
```bash
pipx install robospeaker-win
```

#### Using `uv` (Fastest)
```bash
uv tool install robospeaker-win
```

### 2. Usage
If installed via `pipx` or `uv tool`, you can run it from anywhere:
```bash
robospeaker
```

Or run the script directly if you cloned the repo:
```bash
python main.py
```
Once started, simply type the text you wish to hear. Type `/exit` to stop the 🤖.

---

## 📝 Usage Example
```text
Welcome to the RoboSpeaker! 🤖
What do u want me to speak(/exit to exit): Hello World!
[RoboSpeaker speaks: "Hello World!"]
```

## ⚖️ License
This project is open-source. Feel free to use and modify it for your own vocal automation needs.