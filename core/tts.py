import pyttsx3
import re

class TextToSpeech:
    def __init__(self, rate: int = 160):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)

    def clean_text(self, text: str) -> str:
        """
        Simplify punctuation for better espeak compatibility.
        """
        text = re.sub(r'[\U00010000-\U0010FFFF]', '', text)
        text = re.sub(r'[^\w\s.!?]', '', text)  # remove unsupported punctuation
        text = text.replace("...", ".")
        return text

    def speak(self, text: str):
        """
        Speaks the given text using pyttsx3.
        Handles long text by splitting into sentences.
        """
        print("[TTS] Speaking:", text)
        cleaned_text = self.clean_text(text)
        print(cleaned_text)
        for part in cleaned_text.split(". "):
            if part.strip():
                self.engine.say(part.strip())
                self.engine.runAndWait()

    def save_to_file(self, text: str, filename: str):
        """
        Saves spoken text to a WAV file.
        """
        cleaned_text = self.clean_text(text)
        self.engine.save_to_file(cleaned_text, filename)
        self.engine.runAndWait()
        print(f"[TTS] Saved to {filename}")


# Example usage:
if __name__ == "__main__":
    tts = TextToSpeech()
    message = "Hey there! Just wanted to pop in and say I'm here for you if you need anything at all. Remember to take things one step at a time, okay?"
    tts.speak(message)
    
