from typing import Optional, Callable
from .logger import setup_logger
from .movement import MovementController
from .sensors import SensorManager

logger = setup_logger(__name__)


class RobotBrain:
    """
    High-level coordinator for the NinjaRobot.
    Manages movement, sensors, and overall state.
    """

    def __init__(self) -> None:
        self.movement: Optional[MovementController] = None
        self.sensors: Optional[SensorManager] = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initializes all robot subsystems."""
        try:
            logger.info("Initializing Robot Brain...")
            self.movement = MovementController()
            self.sensors = SensorManager()
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
        }

        if cmd in handlers:
            return handlers[cmd]()

        if cmd == "distance":
            if self.sensors:
                dist = self.sensors.measure_distance()
                return f"Distance: {dist} cm"
            return "Error: Sensors not available."

        return f"Unknown command: {cmd}"
