from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings and configuration.
    Values can be overridden by environment variables or a .env file.
    """

    # API Keys
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API Key")

    # Hardware Configuration - I2C
    I2C_BUS: int = Field(1, description="I2C Bus Number")
    PCA9685_ADDRESS: int = Field(0x10, description="PCA9685 PWM Driver Address")

    # Hardware Configuration - GPIO (BCM)
    # Servos (Channels on PCA9685)
    # Mapping: s1=Left Leg, s2=Right Leg, s3=Left Foot, s4=Right Foot
    SERVO_LEFT_LEG_CHANNEL: int = Field(0, description="Left Leg Servo Channel (s1)")
    SERVO_RIGHT_LEG_CHANNEL: int = Field(1, description="Right Leg Servo Channel (s2)")
    SERVO_LEFT_FOOT_CHANNEL: int = Field(2, description="Left Foot Servo Channel (s3)")
    SERVO_RIGHT_FOOT_CHANNEL: int = Field(
        3, description="Right Foot Servo Channel (s4)"
    )
    # Calibration
    SERVO_CALIBRATION_FILE: str = Field(
        "servo.json", description="Path to servo calibration file"
    )

    # Sensors & Actuators (GPIO Pins - BCM)
    ULTRASONIC_TRIG_PIN: int = Field(21, description="Ultrasonic Trigger Pin")
    ULTRASONIC_ECHO_PIN: int = Field(22, description="Ultrasonic Echo Pin")
    BUZZER_PIN: int = Field(23, description="Active Buzzer Pin")

    # Audio Configuration
    MICROPHONE_DEVICE_INDEX: int | None = Field(
        None, description="Specific index of the microphone device"
    )
    MICROPHONE_DEVICE_NAME: str = Field(
        "inmp441", description="Substring to match for microphone device name"
    )

    # Logging
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    DEBUG: bool = Field(False, description="Enable debug mode")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Global settings instance
settings = Settings()
