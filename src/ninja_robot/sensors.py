import time
from .logger import setup_logger
from .config import settings

logger = setup_logger(__name__)

# Try to import RPi.GPIO, but handle failure for non-Linux/dev environments
try:
    from RPi import GPIO  # type: ignore

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not found. Running in MOCK mode.")


class SensorManager:
    """
    Manages sensors (Ultrasonic) and actuators (Buzzer) connected via GPIO.
    """

    def __init__(self) -> None:
        self.trig_pin = settings.ULTRASONIC_TRIG_PIN
        self.echo_pin = settings.ULTRASONIC_ECHO_PIN
        self.buzzer_pin = settings.BUZZER_PIN
        self.speed_of_sound = 34300  # cm/s
        self.timeout = 0.1  # seconds
        self._initialized = False

        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.trig_pin, GPIO.OUT)
                GPIO.setup(self.echo_pin, GPIO.IN)
                GPIO.setup(self.buzzer_pin, GPIO.OUT)
                GPIO.output(self.trig_pin, False)
                GPIO.output(self.buzzer_pin, False)

                # Allow sensor to settle
                time.sleep(0.5)
                self._initialized = True
                logger.info("SensorManager initialized (GPIO).")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to initialize GPIO: %s", e)
                self._initialized = False
        else:
            self._initialized = True  # Mock mode is always "initialized"
            logger.info("SensorManager initialized (MOCK).")

    def measure_distance(self) -> float:
        """
        Measures distance in cm. Returns -1 on timeout/error.
        """
        if not self._initialized:
            return -2.0

        if not GPIO_AVAILABLE:
            # Mock behavior: return a dummy distance
            return 50.0

        try:
            GPIO.output(self.trig_pin, True)
            time.sleep(0.00001)
            GPIO.output(self.trig_pin, False)

            pulse_start = time.time()
            timeout_start = pulse_start

            while GPIO.input(self.echo_pin) == 0:
                pulse_start = time.time()
                if pulse_start - timeout_start > self.timeout:
                    return -1.0

            pulse_end = time.time()
            timeout_start = pulse_start

            while GPIO.input(self.echo_pin) == 1:
                pulse_end = time.time()
                if pulse_end - pulse_start > self.timeout:
                    return -1.0

            duration = pulse_end - pulse_start
            distance = (duration * self.speed_of_sound) / 2
            return round(distance, 2)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error measuring distance: %s", e)
            return -2.0

    def buzz(self, duration: float = 0.5) -> None:
        """Activates the buzzer for a specific duration."""
        if not self._initialized:
            return

        logger.info("Buzzer ON for %ss", duration)
        if GPIO_AVAILABLE:
            GPIO.output(self.buzzer_pin, True)

        time.sleep(duration)

        if GPIO_AVAILABLE:
            GPIO.output(self.buzzer_pin, False)
        logger.info("Buzzer OFF")

    def cleanup(self) -> None:
        """Cleans up GPIO resources."""
        if GPIO_AVAILABLE and self._initialized:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleaned up.")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error cleaning up GPIO: %s", e)
