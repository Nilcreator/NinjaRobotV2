# -*- coding:utf-8 -*-

'''!
  @file Ninja_Distance_v1.py
  @brief Measures distance using an HC-SR04 ultrasonic sensor connected to Raspberry Pi GPIO pins.
  @n Assumes connection via DFRobot IO Expansion HAT (or directly to Pi).
  @n Prints the distance in centimeters or indicates a timeout/error.
  @copyright Copyright (c) 2023 YOUR NAME/ORGANIZATION HERE (if applicable)
  @license The MIT License (MIT)
  @author Your Name/Assistant
  @version V1.1
  @date 2024-05-22
'''

import RPi.GPIO as GPIO
import time

# --- Configuration ---
# Use BCM pin numbering (referring to GPIO numbers, not physical pin numbers)
GPIO_MODE = GPIO.BCM

# Define GPIO pins connected to the sensor
TRIG_PIN = 21  # BCM GPIO pin connected to Trig
ECHO_PIN = 22  # BCM GPIO pin connected to Echo

# Speed of sound in cm/s (approx. at 20°C)
SPEED_OF_SOUND = 34300
# Timeout duration in seconds (e.g., 0.1 seconds)
# Sensor range is typically ~4m. Max time for 4m round trip = (400*2)/34300 = ~0.023s
# A slightly longer timeout is safer. 0.1s allows for ~17m range detection theoretically.
MEASUREMENT_TIMEOUT = 0.1

# Flag to track if GPIO has been set up
gpio_initialized = False

# --- Functions ---

def setup_sensor():
    """Sets up the GPIO pins for the ultrasonic sensor."""
    global gpio_initialized
    try:
        GPIO.setmode(GPIO_MODE)
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        # Ensure trigger pin is low initially
        GPIO.output(TRIG_PIN, False)
        print("Waiting for sensor to settle...")
        time.sleep(1) # Allow sensor to settle after setup
        gpio_initialized = True
        print("GPIO setup complete.")
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        gpio_initialized = False

def measure_distance():
    """
    Measures the distance using the ultrasonic sensor.
    Returns:
        float: Distance in centimeters.
        -1: If a timeout occurs (no echo received or echo too long).
        -2: If GPIO was not initialized successfully.
    """
    if not gpio_initialized:
        print("Error: GPIO not initialized.")
        return -2

    try:
        # --- Send Trigger Pulse ---
        GPIO.output(TRIG_PIN, True)
        # Wait 10 microseconds (us)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, False)

        # --- Wait for Echo Start ---
        pulse_start_time = time.time()
        timeout_start = pulse_start_time
        # Wait for ECHO pin to go HIGH, but timeout if it takes too long
        while GPIO.input(ECHO_PIN) == 0:
            pulse_start_time = time.time()
            if pulse_start_time - timeout_start > MEASUREMENT_TIMEOUT:
                # print("Timeout: Echo pulse never started.")
                return -1 # Timeout: Echo never started

        # --- Wait for Echo End ---
        pulse_end_time = pulse_start_time
        timeout_start = pulse_start_time # Reset timeout watch starting from pulse start
        # Wait for ECHO pin to go LOW, but timeout if it takes too long
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end_time = time.time()
            # Check overall duration timeout OR if pulse is unexpectedly long
            if pulse_end_time - pulse_start_time > MEASUREMENT_TIMEOUT:
                # print("Timeout: Echo pulse took too long.")
                return -1 # Timeout: Echo lasted too long

        # --- Calculate Distance ---
        pulse_duration = pulse_end_time - pulse_start_time
        # Distance = (Time * Speed of Sound) / 2 (for round trip)
        distance = (pulse_duration * SPEED_OF_SOUND) / 2

        # Simple sanity check (optional: filter out readings too close/far)
        # if distance < 2 or distance > 400:
        #     return -3 # Reading out of typical sensor range

        return distance

    except RuntimeError as e:
        # Catch errors like GPIO not set up
        print(f"RuntimeError during measurement: {e}")
        return -2
    except Exception as e:
        print(f"Unexpected error during measurement: {e}")
        return -2 # General error signal


def cleanup_gpio():
    """Resets GPIO pins to default state."""
    print("\nCleaning up GPIO...")
    GPIO.cleanup()
    print("GPIO cleanup complete.")

# --- Main Execution ---

if __name__ == "__main__":
    try:
        setup_sensor()

        if gpio_initialized:
            print("Starting distance measurements (Ctrl+C to exit)...")
            while True:
                dist = measure_distance()

                if dist == -1:
                    print("Measurement timed out (No object detected or error).")
                elif dist == -2:
                    print("Measurement failed (GPIO Error).")
                    break # Stop if GPIO has issues
                elif dist == -3:
                    print("Measurement out of range.") # If using the optional range check
                else:
                    # Print distance rounded to 2 decimal places
                    print(f"Distance: {dist:.2f} cm")

                # Wait a bit before the next measurement
                time.sleep(0.5) # Read sensor twice per second

    except KeyboardInterrupt:
        print("\nMeasurement stopped by user.")

    finally:
        # Always attempt to clean up GPIO, regardless of how the script exits
        if gpio_initialized:
             cleanup_gpio()
        else:
             print("GPIO was not initialized, skipping cleanup.")
