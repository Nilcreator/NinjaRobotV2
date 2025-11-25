import time
import threading
from typing import Optional, Tuple, Callable
from .logger import setup_logger
from .config import settings
from .hat_driver import get_board

logger = setup_logger(__name__)


class MovementController:
    """
    Controls the robot's servo movements, including atomic actions and continuous gaits.
    """

    def __init__(self) -> None:
        self.board = get_board()
        self._stop_event = threading.Event()
        self._movement_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        if not self.board.begin():
            logger.error("Failed to initialize Expansion Board for MovementController.")
            raise RuntimeError("Board initialization failed")
        # Enable PWM for servos
        self.board.set_pwm_enable()
        self.board.set_pwm_frequency(50)  # Standard servo frequency

        self.obstacle_callback: Optional[Callable[[], bool]] = None
        logger.info("MovementController initialized.")

    def set_obstacle_callback(self, callback: Callable[[], bool]) -> None:
        """Sets the callback for checking obstacles."""
        self.obstacle_callback = callback

    def _get_walk_params(self, speed: str) -> Tuple[float, float, int]:
        """Helper to get timing parameters based on speed."""
        if speed == "fast":
            return 0.15, 0.3, 5
        if speed == "slow":
            return 0.4, 0.7, -5
        return 0.25, 0.5, 0

    def _get_run_params(self, speed: str) -> int:
        """Helper to get run parameters based on speed."""
        if speed == "fast":
            return 40
        if speed == "slow":
            return 15
        return 25

    def stop(self) -> None:
        """Stops any running continuous movement and resets to stand."""
        logger.info("Stopping movement...")
        self._stop_event.set()

        if self._movement_thread and self._movement_thread.is_alive():
            self._movement_thread.join(timeout=2.0)

        with self._lock:
            # Ensure wheels/feet are stopped
            # Servo 2 (Left Arm/Foot?) - Check mapping
            self.board.set_pwm_duty(
                settings.SERVO_LEFT_ARM_CHANNEL + 1, self._angle_to_duty(90)
            )
            # Servo 3
            self.board.set_pwm_duty(
                settings.SERVO_RIGHT_ARM_CHANNEL + 1, self._angle_to_duty(90)
            )
            self.reset_servos()

        logger.info("Movement stopped.")

    def _start_thread(self, target: Callable, args: tuple = ()) -> None:
        """Starts a movement function in a separate thread."""
        self.stop()  # Stop existing movement
        self._stop_event.clear()
        self._movement_thread = threading.Thread(target=target, args=args, daemon=True)
        self._movement_thread.start()

    def _angle_to_duty(self, angle: int) -> float:
        """Converts angle (0-180) to PWM duty cycle (0.0-100.0) for SG90/MG90s."""
        # Generic calculation: 0.5ms to 2.5ms pulse width usually maps to 0-180
        # Period at 50Hz is 20ms.
        # Duty = (PulseWidth / Period) * 100
        # 0 deg = 0.5ms / 20ms = 2.5%
        # 180 deg = 2.5ms / 20ms = 12.5%
        # Formula: Duty = 2.5 + (angle / 180) * 10
        return (0.5 + (angle / 90.0)) / 20 * 100

    def move_servo(self, channel: int, angle: int) -> None:
        """Moves a single servo to a specific angle."""
        # Channel is 0-indexed from config (0-3), driver expects 1-4
        if not 0 <= angle <= 180:
            logger.warning("Angle %s out of range (0-180). Clamping.", angle)
            angle = max(0, min(180, angle))

        duty = self._angle_to_duty(angle)
        self.board.set_pwm_duty(channel + 1, duty)

    def reset_servos(self) -> None:
        """Resets servos to standing position."""
        with self._lock:
            self.move_servo(settings.SERVO_HEAD_PAN_CHANNEL, 90)  # Servo 0
            self.move_servo(settings.SERVO_HEAD_TILT_CHANNEL, 90)  # Servo 1
            self.move_servo(settings.SERVO_LEFT_ARM_CHANNEL, 90)  # Servo 2
            self.move_servo(settings.SERVO_RIGHT_ARM_CHANNEL, 90)  # Servo 3
            time.sleep(0.5)

    def rest(self) -> None:
        """Moves robot to resting position."""
        self.stop()
        with self._lock:
            self.move_servo(settings.SERVO_HEAD_PAN_CHANNEL, 25)
            self.move_servo(settings.SERVO_HEAD_TILT_CHANNEL, 170)
            self.move_servo(settings.SERVO_LEFT_ARM_CHANNEL, 90)
            self.move_servo(settings.SERVO_RIGHT_ARM_CHANNEL, 90)
            time.sleep(1)

    def hello(self) -> None:
        """Performs a wave action."""
        self.stop()
        with self._lock:
            self.reset_servos()
            self.move_servo(settings.SERVO_HEAD_PAN_CHANNEL, 175)
            self.move_servo(settings.SERVO_HEAD_TILT_CHANNEL, 135)
            time.sleep(1)
            self.move_servo(settings.SERVO_HEAD_PAN_CHANNEL, 105)
            time.sleep(1)

            wave_speed = 0.01
            for _ in range(2):
                for angle in range(105, 75, -2):
                    self.move_servo(settings.SERVO_HEAD_PAN_CHANNEL, angle)
                    time.sleep(wave_speed)
                for angle in range(75, 105, 2):
                    self.move_servo(settings.SERVO_HEAD_PAN_CHANNEL, angle)
                    time.sleep(wave_speed)
            time.sleep(0.5)
            self.reset_servos()

    def turn_left_step(self, speed: str = "normal") -> None:
        """Performs one step of turning left."""
        self.stop()
        step_delay, foot_delay, lift_adj = self._get_walk_params(speed)
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        with self._lock:
            # Lift Left Leg
            self.move_servo(s1, 125 - lift_adj)
        time.sleep(step_delay)

        with self._lock:
            # Rotate feet to turn left (was right logic)
            self.move_servo(s2, 110)
            self.move_servo(s3, 110)
        time.sleep(foot_delay)

        with self._lock:
            # Feet back to neutral
            self.move_servo(s2, 90)
            self.move_servo(s3, 90)
            # Place Left Leg Down
            self.move_servo(s1, 90)
        time.sleep(step_delay)

    def turn_right_step(self, speed: str = "normal") -> None:
        """Performs one step of turning right."""
        self.stop()
        step_delay, foot_delay, lift_adj = self._get_walk_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        with self._lock:
            # Lift Right Leg
            self.move_servo(s0, 70 + lift_adj)
        time.sleep(step_delay)

        with self._lock:
            # Rotate feet to turn right (was left logic)
            self.move_servo(s2, 70)
            self.move_servo(s3, 70)
        time.sleep(foot_delay)

        with self._lock:
            # Feet back to neutral
            self.move_servo(s2, 90)
            self.move_servo(s3, 90)
            # Place Right Leg Down
            self.move_servo(s0, 105)
        time.sleep(step_delay)

    def stepback(self, speed: str = "normal") -> None:
        self._start_thread(self._stepback_loop, (speed,))

    def _stepback_loop(self, speed: str) -> None:
        # Swapped with walk logic
        step_delay, foot_delay, lift_adj = self._get_walk_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        while not self._stop_event.is_set():
            if self.obstacle_callback and self.obstacle_callback():
                logger.warning("Obstacle detected! Stopping stepback.")
                self.reset_servos()
                break

            with self._lock:
                self.move_servo(s0, 70 + lift_adj)  # Lift Right Leg
            time.sleep(step_delay)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s2, 80)
                self.move_servo(s3, 100)
            time.sleep(foot_delay)
            with self._lock:
                self.move_servo(s2, 90)
                self.move_servo(s3, 90)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s0, 105)  # Place Right Leg
            time.sleep(step_delay)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s1, 125 - lift_adj)  # Lift Left Leg
            time.sleep(step_delay)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s2, 80)
                self.move_servo(s3, 100)
            time.sleep(foot_delay)
            with self._lock:
                self.move_servo(s2, 90)
                self.move_servo(s3, 90)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s1, 90)  # Place Left Leg
            time.sleep(step_delay)

    # --- Continuous Movements ---

    def walk(self, speed: str = "normal") -> None:
        self._start_thread(self._walk_loop, (speed,))

    def _walk_loop(self, speed: str) -> None:
        # Swapped with stepback logic
        step_delay, foot_delay, lift_adj = self._get_walk_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        while not self._stop_event.is_set():
            if self.obstacle_callback and self.obstacle_callback():
                logger.warning("Obstacle detected! Stopping walk.")
                self.reset_servos()
                break

            with self._lock:
                self.move_servo(s1, 125 - lift_adj)  # Lift Left
            time.sleep(step_delay)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s2, 100)
                self.move_servo(s3, 80)
            time.sleep(foot_delay)
            with self._lock:
                self.move_servo(s2, 90)
                self.move_servo(s3, 90)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s1, 90)  # Place Left
            time.sleep(step_delay)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s0, 70 + lift_adj)  # Lift Right
            time.sleep(step_delay)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s2, 100)
                self.move_servo(s3, 80)
            time.sleep(foot_delay)
            with self._lock:
                self.move_servo(s2, 90)
                self.move_servo(s3, 90)
            if self._stop_event.is_set():
                break

            with self._lock:
                self.move_servo(s0, 105)  # Place Right
            time.sleep(step_delay)

    def run(self, speed: str = "normal") -> None:
        self._start_thread(self._run_loop, (speed,))

    def _run_loop(self, speed: str) -> None:
        angle_offset = self._get_run_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        with self._lock:
            self.move_servo(s0, 15)
            self.move_servo(s1, 180)
        time.sleep(0.5)

        # Swapped logic for run
        right_angle = 90 + angle_offset
        left_angle = 90 - angle_offset

        while not self._stop_event.is_set():
            if self.obstacle_callback and self.obstacle_callback():
                logger.warning("Obstacle detected! Stopping run.")
                self.reset_servos()
                break

            with self._lock:
                self.move_servo(s2, right_angle)
                self.move_servo(s3, left_angle)
            time.sleep(0.05)

    def runback(self, speed: str = "normal") -> None:
        self._start_thread(self._runback_loop, (speed,))

    def _runback_loop(self, speed: str) -> None:
        angle_offset = self._get_run_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        with self._lock:
            self.move_servo(s0, 15)
            self.move_servo(s1, 180)
        time.sleep(0.5)

        # Swapped logic for runback
        right_angle = 90 - angle_offset
        left_angle = 90 + angle_offset

        while not self._stop_event.is_set():
            if self.obstacle_callback and self.obstacle_callback():
                logger.warning("Obstacle detected! Stopping runback.")
                self.reset_servos()
                break

            with self._lock:
                self.move_servo(s2, right_angle)
                self.move_servo(s3, left_angle)
            time.sleep(0.05)

    def rotate_left(self, speed: str = "normal") -> None:
        self._start_thread(self._rotate_left_loop, (speed,))

    def _rotate_left_loop(self, speed: str) -> None:
        angle_offset = self._get_run_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        with self._lock:
            self.move_servo(s0, 15)
            self.move_servo(s1, 180)
        time.sleep(0.5)

        # Swapped logic for rotate left
        right_angle = 90 - angle_offset
        left_angle = 90 - angle_offset

        while not self._stop_event.is_set():
            with self._lock:
                self.move_servo(s2, right_angle)
                self.move_servo(s3, left_angle)
            time.sleep(0.05)

    def rotate_right(self, speed: str = "normal") -> None:
        self._start_thread(self._rotate_right_loop, (speed,))

    def _rotate_right_loop(self, speed: str) -> None:
        angle_offset = self._get_run_params(speed)
        s0 = settings.SERVO_HEAD_PAN_CHANNEL
        s1 = settings.SERVO_HEAD_TILT_CHANNEL
        s2 = settings.SERVO_LEFT_ARM_CHANNEL
        s3 = settings.SERVO_RIGHT_ARM_CHANNEL

        with self._lock:
            self.move_servo(s0, 15)
            self.move_servo(s1, 180)
        time.sleep(0.5)

        # Swapped logic for rotate right
        right_angle = 90 + angle_offset
        left_angle = 90 + angle_offset

        while not self._stop_event.is_set():
            with self._lock:
                self.move_servo(s2, right_angle)
                self.move_servo(s3, left_angle)
            time.sleep(0.05)
