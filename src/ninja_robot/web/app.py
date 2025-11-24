from flask import Flask
from ..brain import RobotBrain
from ..logger import setup_logger
from .routes import main_bp

logger = setup_logger(__name__)


def create_app() -> Flask:
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    # Initialize Robot Brain and attach to app context
    # This ensures we have a single instance running
    app.robot_brain = RobotBrain()  # type: ignore
    if not app.robot_brain.initialize():  # type: ignore
        logger.error("Failed to initialize Robot Brain during app startup.")

    app.register_blueprint(main_bp)

    @app.teardown_appcontext
    def shutdown_brain(_exception: object = None) -> None:
        # We don't want to shut down the brain on every request teardown,
        # only when the app stops. Flask doesn't have a built-in "app stop" hook
        # that is reliable across all servers, but for a simple script,
        # we handle cleanup in the main entry point (main.py) usually.
        # So we leave this empty or use atexit in main.py.
        pass

    return app
