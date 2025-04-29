import pyttsx3
import re
import threading
import logging

# Setup logging (consistent with main.py and display.py)
logging.basicConfig(
    filename='output.txt',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    filemode='a'
)
logger = logging.getLogger()

class TextToSpeech:
    def __init__(self, rate: int = 160):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        logger.info("TextToSpeech initialized with rate=%d", rate)

    def clean_text(self, text: str) -> str:
        """
        Simplify punctuation for better espeak compatibility.
        """
        text = re.sub(r'[\U00010000-\U0010FFFF]', '', text)  # Remove emojis
        text = re.sub(r'[^\w\s\'-.!?]', '', text)  # Remove unsupported punctuation
        text = text.replace("...", ".")
        return text

    def speak(self, text: str):
        """
        Speaks the given text using pyttsx3 in a separate thread.
        Handles long text by splitting into sentences.
        """
        def _speak_in_thread(text_to_speak):
            try:
                logger.debug("[TTS] Speaking: %s", text_to_speak)
                print("[TTS] Speaking:", text_to_speak)
                cleaned_text = self.clean_text(text_to_speak)
                logger.debug("Cleaned text: %s", cleaned_text)
                print(cleaned_text)
                for part in cleaned_text.split(". "):
                    if part.strip():
                        logger.debug("Speaking part: %s", part.strip())
                        self.engine.say(part.strip())
                        self.engine.runAndWait()
            except Exception as e:
                logger.error("TTS speak error: %s", str(e), exc_info=True)

        # Run in a separate thread
        threading.Thread(target=_speak_in_thread, args=(text,), daemon=True).start()

    def save_to_file(self, text: str, filename: str):
        """
        Saves spoken text to a WAV file in a separate thread.
        """
        def _save_in_thread(text_to_save, file_to_save):
            try:
                cleaned_text = self.clean_text(text_to_save)
                logger.debug("Saving cleaned text to file: %s", cleaned_text)
                self.engine.save_to_file(cleaned_text, file_to_save)
                self.engine.runAndWait()
                logger.info("[TTS] Saved to %s", file_to_save)
                print(f"[TTS] Saved to {file_to_save}")
            except Exception as e:
                logger.error("TTS save_to_file error: %s", str(e), exc_info=True)

        # Run in a separate thread
        threading.Thread(target=_save_in_thread, args=(text, filename), daemon=True).start()

# Example usage:
if __name__ == "__main__":
    tts = TextToSpeech()
    message = "Hey there! Just wanted to pop in and say I'm here for you if you need anything at all. Remember to take things one step at a time, okay?"
    tts.speak(message)
