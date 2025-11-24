import os
import tempfile
import time
from typing import Optional
import speech_recognition as sr  # type: ignore
from gtts import gTTS  # type: ignore
from ..logger import setup_logger

logger = setup_logger(__name__)

# Try to import pygame for audio playback
try:
    import pygame  # type: ignore

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame not found. Audio playback will be disabled.")


class SpeechManager:
    """
    Manages Text-to-Speech (TTS) and Speech-to-Text (STT).
    """

    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.microphone: Optional[sr.Microphone] = None

        if PYGAME_AVAILABLE:
            pygame.mixer.init()

        try:
            self.microphone = sr.Microphone()
            logger.info("SpeechManager initialized.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize microphone: %s", e)
            self.microphone = None

    def listen(self) -> Optional[str]:
        """
        Listens for audio input and converts it to text.
        Returns the recognized text or None if failed.
        """
        if not self.microphone:
            logger.error("Microphone not available.")
            return None

        try:
            with self.microphone as source:
                logger.info("Listening...")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

            logger.info("Recognizing...")
            text = str(self.recognizer.recognize_google(audio))
            logger.info("Heard: %s", text)
            return text
        except sr.WaitTimeoutError:
            logger.info("Listening timed out.")
            return None
        except sr.UnknownValueError:
            logger.info("Could not understand audio.")
            return None
        except sr.RequestError as e:
            logger.error("Speech recognition service error: %s", e)
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Unexpected error during listening: %s", e)
            return None

    def speak(self, text: str) -> None:
        """
        Converts text to speech and plays it.
        """
        if not text:
            return

        if not PYGAME_AVAILABLE:
            logger.warning("Cannot speak: pygame not available. Text: %s", text)
            return

        logger.info("Speaking: %s", text)
        try:
            tts = gTTS(text=text, lang="en")

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_filename = fp.name

            tts.save(temp_filename)

            # Play audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            # Clean up
            pygame.mixer.music.unload()
            os.remove(temp_filename)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("TTS failed: %s", e)
