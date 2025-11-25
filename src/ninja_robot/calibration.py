"""
Interactive CLI tool for calibrating robot servos.
"""
import sys
import tty
import termios
import json
import os
from typing import Dict, Any

# Ensure we can import ninja_robot when running as a script
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# pylint: disable=wrong-import-position
from ninja_robot.config import settings
from ninja_robot.movement import MovementController
from ninja_robot.logger import setup_logger

logger = setup_logger(__name__)


def get_key() -> str:
    """Reads a single keypress from stdin."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Handle arrow keys
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


class CalibrationTool:
    """
    Manages the interactive calibration process.
    """

    def __init__(self) -> None:
        self.movement = MovementController()
        # Disable obstacle detection during calibration to prevent interference
        self.movement.set_obstacle_callback(lambda: False)

        self.calibration_file = settings.SERVO_CALIBRATION_FILE
        self.calibration_data: Dict[str, Dict[str, int]] = self._load_calibration()

        # Default structure if empty
        self.servos = {
            "s1": {
                "channel": settings.SERVO_HEAD_PAN_CHANNEL,
                "name": "Head Pan (s1)"
            },
            "s2": {
                "channel": settings.SERVO_HEAD_TILT_CHANNEL,
                "name": "Head Tilt (s2)"
            },
            "s3": {
                "channel": settings.SERVO_LEFT_ARM_CHANNEL,
                "name": "Left Arm (s3)"
            },
            "s4": {
                "channel": settings.SERVO_RIGHT_ARM_CHANNEL,
                "name": "Right Arm (s4)"
            },
        }

    def _load_calibration(self) -> Dict[str, Any]:
        """Loads existing calibration data from file."""
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r', encoding='utf-8') as f:
                    data: Dict[str, Any] = json.load(f)
                    return data
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error loading calibration file: {e}")
        return {}

    def save_calibration(self) -> None:
        """Saves current calibration data to file."""
        try:
            with open(self.calibration_file, 'w', encoding='utf-8') as f:
                json.dump(self.calibration_data, f, indent=4)
            print(f"\nCalibration saved to {self.calibration_file}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error saving calibration: {e}")

    def calibrate_servo(self, servo_key: str) -> None:
        """Runs the interactive calibration loop for a single servo."""
        servo = self.servos[servo_key]
        channel = int(str(servo["channel"]))  # Explicit cast for mypy
        name = servo["name"]

        # Get current calibration or defaults
        cal = self.calibration_data.get(
            str(channel), {"min": 0, "center": 90, "max": 180}
        )

        current_pos_name = "center"
        current_angle = int(cal[current_pos_name])

        print(f"\n--- Calibrating {name} ---")
        print("Controls:")
        print("  c: Select Center Position")
        print("  v: Select Minimum Position")
        print("  x: Select Maximum Position")
        print("  Up/Down Arrow: Adjust Angle (+/- 1)")
        print("  Enter: Save Current Position Value")
        print("  q: Return to Menu")

        # Move to initial position
        self.movement.move_servo(channel, current_angle)

        while True:
            print(f"\rCurrent: {current_pos_name.upper()} = {current_angle}°      ",
                  end="", flush=True)

            key = get_key()

            if key == 'q':
                break
            if key == '\r':  # Enter
                cal[current_pos_name] = current_angle
                self.calibration_data[str(channel)] = cal
                print(f"\nSaved {current_pos_name} as {current_angle}")
            elif key == 'c':
                current_pos_name = "center"
                current_angle = int(cal["center"])
            elif key == 'v':
                current_pos_name = "min"
                current_angle = int(cal["min"])
            elif key == 'x':
                current_pos_name = "max"
                current_angle = int(cal["max"])
            elif key == '\x1b[A':  # Up Arrow
                current_angle = min(180, current_angle + 1)
            elif key == '\x1b[B':  # Down Arrow
                current_angle = max(0, current_angle - 1)

            # Update servo
            self.movement.move_servo(channel, current_angle)

    def run(self) -> None:
        """Main menu loop."""
        print("=== NinjaRobot Servo Calibration Tool ===")
        while True:
            print("\nSelect Servo to Calibrate:")
            for key, s in self.servos.items():
                print(f"  {key}: {s['name']}")
            print("  q: Quit (Save & Exit)")

            choice = input("Enter choice: ").strip().lower()

            if choice == 'q':
                self.save_calibration()
                self.movement.stop()
                print("Exiting.")
                break
            if choice in self.servos:
                self.calibrate_servo(choice)
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    try:
        tool = CalibrationTool()
        tool.run()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\nError: {e}")
