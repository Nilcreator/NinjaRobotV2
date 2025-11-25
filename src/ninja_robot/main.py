from ninja_robot.web.app import create_app
from ninja_robot.config import settings
from ninja_robot.logger import setup_logger

logger = setup_logger(__name__)

def main():
    """Entry point for the NinjaRobot application."""
    logger.info("Starting NinjaRobot V2...")

    app = create_app()
    # Run the Flask app
    # host='0.0.0.0' allows access from other devices
    # port=5000 is default
    # debug=False for production-like behavior on Pi
    try:
        app.run(host='0.0.0.0', port=5000, debug=settings.DEBUG)
    finally:
        logger.info("Shutting down NinjaRobot V2...")
        if hasattr(app, 'robot_brain'):
            brain = app.robot_brain # type: ignore
            if brain:
                brain.movement.rest()
                if brain.speech:
                    brain.speech.speak("Goodbye")
                logger.info("Cleanup complete.")

if __name__ == "__main__":
    main()
