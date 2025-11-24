import sys
import os
import time

# Add src to path so we can import ninja_robot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# pylint: disable=wrong-import-position
from ninja_robot.brain import RobotBrain  # noqa: E402
from ninja_robot.logger import setup_logger  # noqa: E402
from ninja_robot.voice.gemini_client import GeminiClient  # noqa: E402
# pylint: enable=wrong-import-position

logger = setup_logger(__name__)


def run_integration_test() -> None:
    """
    Runs a diagnostic check on all robot subsystems.
    """
    logger.info("Starting Integration Test...")

    # 1. Initialize Brain
    try:
        brain = RobotBrain()
        if not brain.initialize():
            logger.error("Brain initialization failed!")
            return
        logger.info("Brain initialized successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Exception during Brain init: %s", e)
        return

    # 2. Check Sensors
    if brain.sensors:
        dist = brain.sensors.measure_distance()
        logger.info("Sensor Check: Distance = %s cm", dist)
    else:
        logger.warning("SensorManager not available.")

    # 3. Check Movement (Dry Run)
    if brain.movement:
        logger.info("Movement Check: Sending 'rest' command...")
        brain.movement.rest()
        time.sleep(1)
        logger.info("Movement Check: Sending 'hello' command...")
        brain.movement.hello()
        time.sleep(1)
        logger.info("Movement Check: Resetting servos...")
        brain.movement.reset_servos()
    else:
        logger.warning("MovementController not available.")

    # 4. Check Voice (Gemini)
    try:
        client = GeminiClient()
        if client.check_connection():
            logger.info("Gemini API Check: Connection Successful.")
        else:
            logger.warning("Gemini API Check: Connection Failed (Check API Key).")
    except ImportError:
        logger.warning("Could not import GeminiClient.")

    logger.info("Integration Test Complete.")


if __name__ == "__main__":
    run_integration_test()
