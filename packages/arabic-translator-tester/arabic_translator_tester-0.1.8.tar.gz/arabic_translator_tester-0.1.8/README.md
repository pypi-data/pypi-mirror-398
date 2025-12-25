Arabic Translator Tester
Arabic Translator Tester is a Python-based project designed for offline Arabic speech-to-English translation. The project combines Vosk for Arabic speech recognition and Argos Translate for language translation, allowing users to convert spoken Arabic audio into English text without requiring an internet connection.

This repository is structured to work both as:

✅ A standalone GitHub project
✅ A publishable Python package on PyPI
🚀 Key Features
🔊 Offline Arabic Speech Recognition using Vosk
🌍 Arabic → English Translation using Argos Translate
📴 Works completely offline (no API keys required)
🧩 Can be used as a Python library or via CLI
🐍 Compatible with Python 3.9+ (tested with Python 3.12)
⚙ Dependencies
This project relies on the following core technologies:

Vosk – Offline speech recognition engine
Argos Translate – Offline neural machine translation
Python Standard Libraries
All dependencies are automatically installed via pip.

🧠 How It Works
Audio Input: Arabic speech is provided as an audio file or microphone input
Speech Recognition: Vosk converts Arabic speech into Arabic text
Translation: Argos Translate converts Arabic text into English
Output: Translated English text is returned to the user
The entire pipeline runs locally, ensuring privacy, speed, and offline usability.

🧪 Usage Examples
Python Library Usage
from arabic_translator_tester import translate_audio

result = translate_audio("sample_arabic.wav")
print(result)
CLI Usage
arabic-translator-tester sample_arabic.wav
🔨 Building the Package (For PyPI)
To build the package locally:

pip install build twine
python -m build
This will generate a dist/ folder containing .whl and .tar.gz files.

🚀 Publishing to PyPI
twine upload dist/*
Make sure to:

Increment the version in pyproject.toml
Use a unique package name on PyPI
Use a PyPI API token for authentication
🔁 Updating the Package
Update code
Increase version number
Rebuild and upload
python -m build
twine upload dist/*
📜 License
This project is licensed under the MIT License. You are free to use, modify, and distribute this software.

🤝 Contributing
Contributions are welcome!



