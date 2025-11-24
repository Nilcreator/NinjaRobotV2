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
    app.run(host='0.0.0.0', port=5000, debug=settings.DEBUG)

if __name__ == "__main__":
    main()
