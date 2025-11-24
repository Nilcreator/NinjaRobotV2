import time
from typing import Optional, List, Union, cast
from .logger import setup_logger
from .config import settings

logger = setup_logger(__name__)

# Try to import smbus2, but handle failure for non-Linux/dev environments
try:
    import smbus2  # type: ignore

    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False
    logger.warning("smbus2 not found. Running in MOCK mode.")


class ExpansionBoard:
    """
    Driver for DFRobot Raspberry Pi Expansion Board via I2C (PCA9685 based).
    """

    # Registers
    _REG_SLAVE_ADDR = 0x00
    _REG_PID = 0x01
    _REG_VID = 0x02
    _REG_PWM_CONTROL = 0x03
    _REG_PWM_FREQ = 0x04
    _REG_PWM_DUTY1 = 0x06
    _REG_PWM_DUTY2 = 0x08
    _REG_PWM_DUTY3 = 0x0A
    _REG_PWM_DUTY4 = 0x0C
    _REG_ADC_CTRL = 0x0E
    _REG_ADC_VAL1 = 0x0F
    _REG_ADC_VAL2 = 0x11
    _REG_ADC_VAL3 = 0x13
    _REG_ADC_VAL4 = 0x15

    _REG_DEF_PID = 0xDF
    _REG_DEF_VID = 0x10

    def __init__(self, bus_id: int = 1, address: int = 0x10):
        self._bus_id = bus_id
        self._address = address
        self._is_pwm_enabled = False
        self._bus: Optional["smbus2.SMBus"] = None

        if not SMBUS_AVAILABLE:
            raise RuntimeError("smbus2 is not available. Use MockExpansionBoard.")

        try:
            self._bus = smbus2.SMBus(bus_id)
            logger.info("Connected to I2C bus %s", bus_id)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to connect to I2C bus %s: %s", bus_id, e)
            raise

    def begin(self) -> bool:
        """Initialize the board."""
        try:
            pid = self._read_bytes(self._REG_PID, 1)
            vid = self._read_bytes(self._REG_VID, 1)

            if not pid or not vid:
                logger.error("Failed to read PID/VID from board.")
                return False

            if pid[0] != self._REG_DEF_PID:
                logger.error(
                    "Invalid PID: %#x, expected %#x", pid[0], self._REG_DEF_PID
                )
                return False
            if vid[0] != self._REG_DEF_VID:
                logger.error(
                    "Invalid VID: %#x, expected %#x", vid[0], self._REG_DEF_VID
                )
                return False

            self.set_pwm_disable()
            self.set_pwm_duty_all(0.0)
            self.set_adc_disable()
            logger.info("Expansion Board initialized successfully.")
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Initialization failed: %s", e)
            return False

    def _write_bytes(self, reg: int, data: List[int]) -> None:
        try:
            if self._bus:
                self._bus.write_i2c_block_data(self._address, reg, data)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("I2C Write Error (Reg %#x): %s", reg, e)

    def _read_bytes(self, reg: int, length: int) -> List[int]:
        try:
            if self._bus:
                return cast(
                    List[int], self._bus.read_i2c_block_data(self._address, reg, length)
                )
            return [0] * length
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("I2C Read Error (Reg %#x): %s", reg, e)
            return [0] * length

    def set_pwm_enable(self) -> None:
        self._write_bytes(self._REG_PWM_CONTROL, [0x01])
        self._is_pwm_enabled = True
        time.sleep(0.01)

    def set_pwm_disable(self) -> None:
        self._write_bytes(self._REG_PWM_CONTROL, [0x00])
        self._is_pwm_enabled = False
        time.sleep(0.01)

    def set_pwm_frequency(self, freq: int) -> None:
        if not 1 <= freq <= 1000:
            logger.error("Invalid frequency: %s. Must be 1-1000 Hz.", freq)
            return

        was_enabled = self._is_pwm_enabled
        self.set_pwm_disable()
        self._write_bytes(self._REG_PWM_FREQ, [freq >> 8, freq & 0xFF])
        time.sleep(0.01)

        if was_enabled:
            self.set_pwm_enable()

    def set_pwm_duty(self, channel: int, duty: float) -> None:
        """
        Set duty cycle for a specific channel (1-4).
        Duty is 0.0 to 100.0.
        """
        if not 1 <= channel <= 4:
            logger.error("Invalid PWM channel: %s. Must be 1-4.", channel)
            return
        if not 0.0 <= duty <= 100.0:
            logger.error("Invalid duty cycle: %s. Must be 0-100.", duty)
            return

        reg = self._REG_PWM_DUTY1 + (channel - 1) * 2
        duty_int = int(duty)
        duty_dec = int((duty * 10) % 10)
        self._write_bytes(reg, [duty_int, duty_dec])

    def set_pwm_duty_all(self, duty: float) -> None:
        """Set duty cycle for all channels."""
        for i in range(1, 5):
            self.set_pwm_duty(i, duty)

    def set_adc_enable(self) -> None:
        self._write_bytes(self._REG_ADC_CTRL, [0x01])

    def set_adc_disable(self) -> None:
        self._write_bytes(self._REG_ADC_CTRL, [0x00])

    def get_adc_value(self, channel: int) -> int:
        """Get ADC value for channel 1-4."""
        if not 1 <= channel <= 4:
            logger.error("Invalid ADC channel: %s. Must be 1-4.", channel)
            return 0

        reg = self._REG_ADC_VAL1 + (channel - 1) * 2
        data = self._read_bytes(reg, 2)
        return (data[0] << 8) | data[1]


class MockExpansionBoard:
    """Mock driver for testing without hardware."""

    def __init__(self, bus_id: int = 1, address: int = 0x10):
        logger.info(
            "Initialized MockExpansionBoard on Bus %s, Addr %#x", bus_id, address
        )
        self._is_pwm_enabled = False

    def begin(self) -> bool:
        logger.info("MockExpansionBoard initialized.")
        return True

    def set_pwm_enable(self) -> None:
        self._is_pwm_enabled = True
        logger.debug("PWM Enabled")

    def set_pwm_disable(self) -> None:
        self._is_pwm_enabled = False
        logger.debug("PWM Disabled")

    def set_pwm_frequency(self, freq: int) -> None:
        logger.debug("Set PWM Frequency: %s Hz", freq)

    def set_pwm_duty(self, channel: int, duty: float) -> None:
        logger.debug("Set PWM Channel %s Duty: %s%%", channel, duty)

    def set_pwm_duty_all(self, duty: float) -> None:
        logger.debug("Set All PWM Channels Duty: %s%%", duty)

    def set_adc_enable(self) -> None:
        logger.debug("ADC Enabled")

    def set_adc_disable(self) -> None:
        logger.debug("ADC Disabled")

    def get_adc_value(self, channel: int) -> int:
        logger.debug("Read ADC Channel %s", channel)
        return 512  # Return dummy middle value


def get_board() -> Union[ExpansionBoard, MockExpansionBoard]:
    """Factory to return the appropriate board driver."""
    if SMBUS_AVAILABLE:
        try:
            return ExpansionBoard(settings.I2C_BUS, settings.PCA9685_ADDRESS)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to initialize real board: %s. Falling back to Mock.", e
            )
            return MockExpansionBoard(settings.I2C_BUS, settings.PCA9685_ADDRESS)
    else:
        return MockExpansionBoard(settings.I2C_BUS, settings.PCA9685_ADDRESS)
