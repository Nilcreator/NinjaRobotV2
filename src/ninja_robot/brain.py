from typing import Optional, Callable
from .logger import setup_logger
from .movement import MovementController
from .sensors import SensorManager
from .voice.gemini_client import GeminiClient
from .voice.speech import SpeechManager

logger = setup_logger(__name__)


class RobotBrain:
    """
    High-level coordinator for the NinjaRobot.
    Manages movement, sensors, and overall state.
    """

    def __init__(self) -> None:
        self.movement: Optional[MovementController] = None
        self.sensors: Optional[SensorManager] = None
        self.voice: Optional[GeminiClient] = None
        self.speech: Optional[SpeechManager] = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initializes all robot subsystems."""
        try:
            logger.info("Initializing Robot Brain...")
            self.movement = MovementController()
            self.sensors = SensorManager()
            
            try:
                self.voice = GeminiClient()
                logger.info("Voice (Gemini) initialized.")
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.warning("Voice (Gemini) initialization failed: %s", e)

            try:
                self.speech = SpeechManager()
                logger.info("Speech Manager initialized.")
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.warning("Speech Manager initialization failed: %s", e)

            self._initialized = True
            logger.info("Robot Brain initialized successfully.")

            # Startup signal
            if self.sensors:
                self.sensors.buzz(0.1)

            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize Robot Brain: %s", e)
            return False

    def shutdown(self) -> None:
        """Safely shuts down the robot."""
        logger.info("Shutting down Robot Brain...")
        if self.movement:
            self.movement.stop()
            self.movement.reset_servos()

        if self.sensors:
            self.sensors.cleanup()
            
        self.voice = None
        self.speech = None

        self._initialized = False
        logger.info("Shutdown complete.")

    def execute_command(self, command: str, params: Optional[dict] = None) -> str:
        """
        Executes a high-level command (e.g., from Voice or Web UI).
        """
        if not self._initialized or not self.movement:
            return "Error: Robot not initialized."

        # Ensure mypy knows self.movement is not None
        movement = self.movement
        assert movement is not None

        cmd = command.lower().strip()
        params = params or {}
        speed = params.get('speed', 'normal')

        logger.info("Executing command: %s (params: %s)", cmd, params)

        def do(action: Callable[[], None], msg: str) -> str:
            action()
            return msg

        handlers = {
            "stop": lambda: do(movement.stop, "Stopped."),
            "walk": lambda: do(lambda: movement.walk(speed), f"Walking ({speed})."),
            "run": lambda: do(lambda: movement.run(speed), f"Running ({speed})."),
            "hello": lambda: do(movement.hello, "Waving hello."),
            "rest": lambda: do(movement.rest, "Resting."),
            "reset": lambda: do(movement.reset_servos, "Reset to stand."),
            "stepback": lambda: do(
                lambda: movement.stepback(speed), f"Stepping back ({speed})."
            ),
            "runback": lambda: do(
                lambda: movement.runback(speed), f"Running back ({speed})."
            ),
            "rotateleft": lambda: do(
                lambda: movement.rotate_left(speed), f"Rotating left ({speed})."
            ),
            "rotateright": lambda: do(
                lambda: movement.rotate_right(speed), f"Rotating right ({speed})."
            ),
            "turnleft_step": lambda: do(
                lambda: movement.turn_left_step(speed), "Turning left (step)."
            ),
            "turnright_step": lambda: do(
                lambda: movement.turn_right_step(speed), "Turning right (step)."
            ),
        }

        if cmd in handlers:
            return handlers[cmd]()

        if cmd == "distance":
            if self.sensors:
                dist = self.sensors.measure_distance()
                return f"Distance: {dist} cm"
            return "Error: Sensors not available."

        return f"Unknown command: {cmd}"
