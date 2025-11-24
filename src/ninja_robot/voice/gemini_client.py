import google.generativeai as genai  # type: ignore
from ..config import settings
from ..logger import setup_logger

logger = setup_logger(__name__)


class GeminiClient:
    """
    Client for interacting with Google's Gemini API.
    """

    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self._initialized = False

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. Voice features will be limited.")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-pro")
            self._initialized = True
            logger.info("GeminiClient initialized.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize GeminiClient: %s", e)
            self._initialized = False

    def generate_response(self, prompt: str) -> str:
        """
        Generates a response from Gemini based on the prompt.
        """
        if not self._initialized:
            return "I'm sorry, my voice brain is not connected."

        try:
            # Add system context to the prompt
            context = (
                "You are NinjaRobot, a helpful and friendly robot assistant. "
                "Keep your responses concise (under 2 sentences) and suitable for "
                "speech synthesis. "
                "If asked to perform an action, confirm it briefly."
            )
            full_prompt = f"{context}\nUser: {prompt}\nRobot:"

            response = self.model.generate_content(full_prompt)
            return str(response.text).strip()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Gemini generation failed: %s", e)
            return "I had trouble thinking of a response."

    def check_connection(self) -> bool:
        """Checks if the Gemini API is reachable."""
        if not self._initialized:
            return False
        try:
            self.model.generate_content("Test")
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False
