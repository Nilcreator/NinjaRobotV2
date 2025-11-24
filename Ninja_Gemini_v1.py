# -*- coding:utf-8 -*-

'''!
  @file Ninja_Gemini_v1.py
  @brief Main interface for controlling the Ninja Robot using natural language (Google Gemini API),
         integrating movement, sound, and distance sensing.
  @copyright Copyright (c) 2024 Your Name/Assistant
  @license The MIT License (MIT)
  @author Your Name/Assistant
  @version V1.1 (Corrected for google-generativeai library)
  @date 2024-05-23
'''

import sys
import os
import time
import re  # Import regular expression module
import threading
import json
import RPi.GPIO as GPIO # Needed for global cleanup
import google.generativeai as genai  # Import Google Gemini library

# --- Configuration ---

# Gemini Setup using google-generativeai
# API Authentication
# Insert your API key here. If left empty, it will try Application Default Credentials (ADC).
# Get API Key: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY = "Input your Google API Key here!!"  # <----------- input your API key

# Configure the Gemini client
try:
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 5:
        print("Configuring Gemini using API Key.")
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        print("API Key not found or too short. Attempting to use Application Default Credentials (ADC).")
        # ADC will be used automatically if `genai.configure()` is not called with an API key.
        # Ensure ADC is set up (e.g., `gcloud auth application-default login`) if not using an API key.
        # No explicit configuration needed here for ADC if library handles it automatically.
        pass # Let the library handle ADC

    # Choose a known valid model name
    # Check available models: https://ai.google.dev/models/gemini
    GEMINI_MODEL_NAME = "gemini-2.0-flash-lite" # Using 1.5 Flash latest
    print(f"Loading Gemini model: {GEMINI_MODEL_NAME}")
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    print("Gemini model loaded successfully.")

except Exception as e:
     print(f"Error configuring or loading Gemini model: {e}")
     print("Please ensure you have a valid API key or ADC setup.")
     sys.exit(1)


# Robot Hardware Configuration
DISTANCE_THRESHOLD_CM = 5.0 # Stop distance in cm (adjust as needed)

# --- Add project root to sys.path for module imports ---
# Assumes all Ninja*.py files and DFRobot library files are in the same directory
# If DFRobot lib is in a subdirectory, adjust path accordingly
# sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) # If needed

# --- Import Robot Modules ---
try:
    import Ninja_Movements_v1 as movements
    import Ninja_Buzzer as buzzer
    import Ninja_Distance as distance
    # The DFRobot library is imported *within* Ninja_Movements_v1
except ImportError as e:
    print(f"Error importing robot modules: {e}")
    print("Ensure Ninja_Movements_v1.py, Ninja_Buzzer.py, Ninja_Distance.py are in the same directory.")
    sys.exit(1)

# --- Global Variables ---
# Removed vertexai specific variables
movement_thread = None
distance_check_thread = None
is_continuous_moving = False
buzzer_pwm = None
keep_distance_checking = False # Flag to control the distance checker loop

# --- Initialization Functions ---

# Removed initialize_vertex_ai() function as setup is now done globally for genai

def initialize_hardware():
    """Initializes Servos, Buzzer, and Distance Sensor."""
    global buzzer_pwm
    print("Initializing hardware components...")
    try:
        # Servos (via movements module)
        movements.init_board_and_servo()

        # Buzzer
        buzzer.setup() # Sets up GPIO BCM mode and pin
        # Ensure buzzer pin setup doesn't conflict if distance sensor also uses GPIO setup
        # Both modules use GPIO.BCM, which is good. buzzer.setup() sets warnings off.
        buzzer_pwm = GPIO.PWM(buzzer.BUZZER_PIN, 440) # Use default frequency initially
        buzzer_pwm.start(0) # Start silent

        # Distance Sensor
        # Make sure setup_sensor doesn't reset GPIO mode if already set by buzzer
        # RPi.GPIO handles this; subsequent setup calls on pins are fine.
        distance.setup_sensor() # Sets up GPIO BCM mode and pins

        print("Hardware initialization complete.")
        play_robot_sound('hello')
        movements.reset_servos() # Start in a known position
        time.sleep(1)

    except Exception as e:
        print(f"An error occurred during hardware initialization: {e}")
        print("Attempting GPIO cleanup...")
        # Cleanup is handled globally at the end, but good to log the error source.
        GPIO.cleanup() # Try to clean up if setup fails mid-way
        sys.exit(1)

# --- Cleanup Function ---

def cleanup_all():
    """Stops all actions and cleans up resources."""
    global keep_distance_checking, movement_thread, distance_check_thread, is_continuous_moving
    print("\n--- Initiating Cleanup ---")

    # 1. Stop Distance Checking Thread
    print("Stopping distance checker...")
    keep_distance_checking = False
    if distance_check_thread and distance_check_thread.is_alive():
        distance_check_thread.join(timeout=1.0) # Wait for thread to finish
    if distance_check_thread and distance_check_thread.is_alive():
        print("Warning: Distance check thread did not terminate gracefully.")
    distance_check_thread = None

    # 2. Stop Movement (sets stop_movement flag and waits for thread)
    print("Stopping movement...")
    if is_continuous_moving: # Only stop if it was supposed to be moving
         movements.stop() # This should also signal the movement_thread
         time.sleep(0.5) # Give thread time to react to stop flag
    # Ensure thread object is handled correctly
    if movement_thread and movement_thread.is_alive():
         print("Waiting for movement thread to finish...")
         movement_thread.join(timeout=1.0) # Wait for thread to finish
    if movement_thread and movement_thread.is_alive():
         print("Warning: Movement thread did not terminate gracefully after stop().")
    movement_thread = None
    is_continuous_moving = False # Reset state *after* confirming thread stopped/timeout

    print("Putting robot to rest...")
    # Ensure movements object is still valid before calling rest
    if movements.servo:
        movements.rest() # Go to rest pose
    else:
        print("Warning: Servo object not available, cannot move to rest.")


    # 3. Stop Buzzer
    if buzzer_pwm:
        print("Stopping buzzer...")
        buzzer_pwm.stop()

    # 4. Cleanup GPIO (Handles both buzzer and distance sensor pins)
    # Both buzzer.cleanup() and distance.cleanup_gpio() likely call GPIO.cleanup().
    # Calling it once here is sufficient and safer.
    print("Cleaning up GPIO...")
    # Check if GPIO has been initialized before cleaning up
    # Note: RPi.GPIO doesn't have a standard way to check if 'initialized'
    # We assume if the script ran this far, some setup occurred.
    # Adding a check for buzzer_pwm might be a proxy, but cleanup is generally safe.
    try:
         GPIO.cleanup()
         print("GPIO cleanup successful.")
    except Exception as e:
         print(f"Error during GPIO cleanup: {e}")


# --- Gemini Interaction ---

def get_gemini_interpretation(user_command):
    """Sends the command to Gemini (using google-generativeai) and parses the JSON response."""
    global model # Use the globally initialized model

    if not model:
        print("Error: Gemini model not initialized.")
        return None

    # --- Prompt for Gemini (same as before) ---
    prompt = f"""
Analyze the following user command directed at a robot and determine the intended action(s).
The robot has functions for movement and making sounds.

Available Movement Functions:
- 'hello': A specific wave/wiggle sequence.
- 'walk': Continuous forward walking. Speed options: 'normal', 'fast', 'slow'.
- 'stepback': Continuous backward walking. Speed options: 'normal', 'fast', 'slow'.
- 'run': Continuous forward running (tire mode). Speed options: 'normal', 'fast', 'slow'.
- 'runback': Continuous backward running (tire mode). Speed options: 'normal', 'fast', 'slow'.
- 'turnleft_step': Perform ONE step turning left.
- 'turnright_step': Perform ONE step turning right.
- 'rotateleft': Continuous counter-clockwise rotation (tire mode). Speed options: 'normal', 'fast', 'slow'.
- 'rotateright': Continuous clockwise rotation (tire mode). Speed options: 'normal', 'fast', 'slow'.
- 'stop': Stop any ongoing continuous movement.
- 'reset_servos': Return to standard standing position.
- 'rest': Go to lowered resting position.
- 'set_servo_angle': Set a specific servo (0-3) to an angle (0-180). (Parse ID and Angle if possible)

Available Sound Keywords (map to these keywords):
- 'hello'
- 'thanks' (or 'thank you')
- 'no'
- 'yes'
- 'danger'
- 'exciting'
- 'happy'
- 'right' (for turn sound)
- 'left' (for turn sound)
- 'scared'
- (Add others from Ninja_Buzzer SOUND_MAP if needed)

Output Format:
Return ONLY a valid JSON object describing the action. Do NOT include ```json ... ``` markers or any other text. Use the following keys:
- "action_type": "move", "sound", "combo" (move and sound), "servo", or "unknown".
- "move_function": (string) Name of the movement function to call (e.g., "walk", "hello"). Required if action_type is "move" or "combo".
- "speed": (string) "fast", "slow", or "normal". Optional, defaults to "normal" for continuous movements.
- "sound_keyword": (string) The keyword for the sound to play (e.g., "hello", "danger"). Required if action_type is "sound" or "combo".
- "servo_id": (int) Servo ID (0-3). Required if action_type is "servo".
- "servo_angle": (int) Servo angle (0-180). Required if action_type is "servo".
- "error": (string) Description if the command is unclear or cannot be mapped. Set action_type to "unknown".

Examples:
User: "Say hello" -> {{"action_type": "combo", "move_function": "hello", "sound_keyword": "hello"}}
User: "Walk forward quickly" -> {{"action_type": "move", "move_function": "walk", "speed": "fast"}}
User: "Make a happy sound" -> {{"action_type": "sound", "sound_keyword": "happy"}}
User: "Stop moving" -> {{"action_type": "move", "move_function": "stop"}}
User: "Turn left" -> {{"action_type": "combo", "move_function": "turnleft_step", "sound_keyword": "left"}}
User: "Set servo 1 to 90 degrees" -> {{"action_type": "servo", "servo_id": 1, "servo_angle": 90}}
User: "What time is it?" -> {{"action_type": "unknown", "error": "Cannot determine time."}}

User Command: "{user_command}"

Analyze the command and provide ONLY the JSON output:
"""

    print(f"Sending to Gemini: '{user_command}'")
    try:
        # Configure generation parameters (optional) for google-generativeai
        generation_config = genai.types.GenerationConfig(
            temperature=0.2, # Lower temperature for more deterministic mapping
            max_output_tokens=1024
        )
        # Make the API call using the global 'model' object
        response = model.generate_content(
            prompt,
            generation_config=generation_config # Pass config here
        )

        # Debug: Print raw response parts if needed
        # print("Gemini Raw Response:", response)
        # print("Gemini Prompt Feedback:", response.prompt_feedback)

        # Extract and parse JSON from response.text
        response_text = response.text.strip()

        # Attempt to directly parse the text, assuming Gemini adheres to "ONLY JSON output" instruction
        try:
            action_data = json.loads(response_text)
            print(f"Gemini Interpretation: {action_data}")
            return action_data
        except json.JSONDecodeError as e:
             # Fallback: If direct parsing fails, try finding JSON within potential markdown
            print(f"Direct JSON parsing failed: {e}. Trying to extract from markdown.")
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                 json_str = json_match.group(1)
                 try:
                      action_data = json.loads(json_str)
                      print(f"Gemini Interpretation (extracted): {action_data}")
                      return action_data
                 except json.JSONDecodeError as e_inner:
                      print(f"Error: Extracted text was not valid JSON: {e_inner}")
                      print(f"Extracted: {json_str}")
                      return {"action_type": "unknown", "error": "Invalid JSON response from AI."}
            else:
                 print("Error: Could not find or parse JSON object in Gemini response.")
                 print(f"Received: {response_text}")
                 return {"action_type": "unknown", "error": "Could not parse AI response."}

    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        # Log specific API errors if available in the exception object
        return {"action_type": "unknown", "error": f"API communication error: {e}"}


# --- Sound Playing Helper ---

def play_robot_sound(sound_keyword):
    """Plays a sound based on the keyword using the buzzer module."""
    if not buzzer_pwm:
        print("Error: Buzzer not initialized.")
        return

    print(f"Playing sound for keyword: '{sound_keyword}'")
    sound_action = buzzer.SOUND_MAP.get(sound_keyword)

    if sound_action == buzzer.SOUND_SCARED_IDENTIFIER:
        buzzer.play_scared_sound(buzzer_pwm)
    elif sound_action == buzzer.SOUND_EXCITING_IDENTIFIER:
         buzzer.play_exciting_trill(buzzer_pwm)
    elif isinstance(sound_action, list):
        # Add a check to ensure pwm object is valid before passing
        if buzzer_pwm:
             buzzer.play_sequence(buzzer_pwm, sound_action)
        else:
             print("Error: Buzzer PWM object invalid.")
    else:
        print(f"Warning: No sound defined for keyword '{sound_keyword}' in Ninja_Buzzer.")
        # Play a default 'unknown' beep?
        # Check if 'no' exists before calling recursively
        if 'no' in buzzer.SOUND_MAP:
            play_robot_sound('no')
        else:
            print("Warning: Default 'no' sound not found either.")


# --- Distance Checking Thread ---

def distance_checker():
    """Thread function to periodically check distance during movement."""
    global keep_distance_checking, is_continuous_moving
    print("Distance checker thread started.")
    last_warning_time = 0
    warning_interval = 2.0 # Minimum seconds between warnings

    while keep_distance_checking:
        # Only check if the robot is supposed to be moving continuously
        # Check is_continuous_moving flag *before* accessing hardware
        if is_continuous_moving and not movements.stop_movement:
            dist = distance.measure_distance()

            # Check distance validity BEFORE comparing
            if dist == -2: # GPIO error
                 print("Distance sensor GPIO error. Stopping checker.")
                 keep_distance_checking = False # Stop checking if sensor fails
                 # Optionally, stop the robot as well? Depends on desired behavior.
                 # if is_continuous_moving:
                 #    print("Stopping movement due to sensor error.")
                 #    movements.stop()
                 #    is_continuous_moving = False
                 break
            elif dist == -1: # Timeout
                 # Measurement timed out, maybe too far or sensor error
                 # print("Distance sensor timeout.")
                 pass # Continue checking
            elif dist < DISTANCE_THRESHOLD_CM: # Valid distance, check threshold
                print(f"!!! OBSTACLE DETECTED at {dist:.1f} cm !!!")
                current_time = time.time()
                if current_time - last_warning_time > warning_interval:
                     play_robot_sound('danger') # Play danger sound
                     last_warning_time = current_time

                print("Stopping movement due to obstacle.")
                # Ensure stop is called only once effectively
                if is_continuous_moving: # Check flag again before stopping
                    movements.stop() # Set flag, stop servos, reset position
                    is_continuous_moving = False # Update state
                keep_distance_checking = False # Stop checking for this movement
                break # Exit the checker loop for this movement

        # Pause before next check if still checking
        if keep_distance_checking:
            time.sleep(0.15) # Check distance approx 6-7 times per second

    print("Distance checker thread finished.")


# --- Action Execution ---

def execute_action(action_data):
    """Executes the robot action based on the parsed data from Gemini."""
    global movement_thread, distance_check_thread, is_continuous_moving, keep_distance_checking

    action_type = action_data.get("action_type", "unknown")

    # --- Stop previous continuous actions if starting a new one ---
    # Check if the new action IS NOT 'stop' itself and if something is already running
    move_func_name = action_data.get("move_function") # Get move func early
    is_new_continuous = action_type in ["move", "combo"] and move_func_name in [
        "walk", "stepback", "run", "runback", "rotateleft", "rotateright"
    ]
    is_new_finite_move = action_type in ["move", "combo", "servo"] and not is_new_continuous and move_func_name != "stop"

    if (is_new_continuous or is_new_finite_move) and is_continuous_moving:
        print("Stopping previous continuous movement before starting new action.")
        # Stop distance checker first
        keep_distance_checking = False
        if distance_check_thread and distance_check_thread.is_alive():
             print("Waiting for distance thread...")
             distance_check_thread.join(timeout=0.5)
        distance_check_thread = None
        # Stop movement thread
        movements.stop() # Signal thread and stop servos
        if movement_thread and movement_thread.is_alive():
             print("Waiting for movement thread...")
             movement_thread.join(timeout=1.0)
        movement_thread = None
        is_continuous_moving = False
        time.sleep(0.2) # Short pause after stopping

    # --- Execute the requested action ---
    sound_keyword = action_data.get("sound_keyword")
    speed = action_data.get("speed", "normal")

    # 1. Handle Sound (if part of combo or sound-only)
    if action_type in ["sound", "combo"] and sound_keyword:
        play_robot_sound(sound_keyword)
        # Add a small delay after sound if it's a combo, before movement starts
        if action_type == "combo":
            time.sleep(0.2)

    # 2. Handle Movement
    if action_type in ["move", "combo"] and move_func_name:
        target_func = getattr(movements, move_func_name, None)

        if target_func:
            print(f"Executing movement: {move_func_name} (Speed: {speed})")

            # Check if it's a continuous movement function
            if move_func_name in ["walk", "stepback", "run", "runback", "rotateleft", "rotateright"]:
                # Ensure not already moving (should be stopped by logic above, but double check)
                if not is_continuous_moving:
                    is_continuous_moving = True
                    movements.stop_movement = False # Ensure flag is reset
                    movement_thread = threading.Thread(target=target_func, args=(speed, None), daemon=True)
                    movement_thread.start()

                    # Start distance checker thread for these movements
                    keep_distance_checking = True
                    distance_check_thread = threading.Thread(target=distance_checker, daemon=True)
                    distance_check_thread.start()
                else:
                    print("Warning: Tried to start continuous move while already moving.")

            elif move_func_name == "stop":
                 # Explicit stop command
                 print("Executing stop command.")
                 keep_distance_checking = False # Stop checker if running
                 if distance_check_thread and distance_check_thread.is_alive():
                     distance_check_thread.join(timeout=0.5)
                 movements.stop() # Call the stop function
                 if movement_thread and movement_thread.is_alive():
                     movement_thread.join(timeout=1.0)
                 is_continuous_moving = False # Ensure state is updated

            elif move_func_name in ["turnleft_step", "turnright_step"]:
                 # These are single-step, execute directly (ensure not continuously moving)
                 if not is_continuous_moving:
                     target_func(speed, None)
                 else:
                     print("Warning: Cannot perform turn step while continuous movement active. Stop first.")
                     play_robot_sound('no')
            else:
                 # Other finite movements (hello, reset, rest)
                 if not is_continuous_moving:
                      target_func() # Assumes no speed argument needed
                 else:
                     print(f"Warning: Cannot perform '{move_func_name}' while continuous movement active. Stop first.")
                     play_robot_sound('no')

        else:
            print(f"Error: Movement function '{move_func_name}' not found in Ninja_Movements_v1.")
            play_robot_sound('no')

    # 3. Handle Servo Command
    elif action_type == "servo":
         if not is_continuous_moving:
            servo_id = action_data.get("servo_id")
            servo_angle = action_data.get("servo_angle")
            if servo_id is not None and servo_angle is not None:
                # Validate types just in case Gemini returns strings
                try:
                    servo_id = int(servo_id)
                    servo_angle = int(servo_angle)
                    print(f"Setting servo {servo_id} to {servo_angle} degrees.")
                    movements.set_servo_angle(servo_id, servo_angle)
                except ValueError:
                    print("Error: Invalid servo ID or angle format received from AI.")
                    play_robot_sound('no')
            else:
                print("Error: Missing servo_id or servo_angle for servo action.")
                play_robot_sound('no')
         else:
             print("Warning: Cannot set individual servo while continuous movement active. Stop first.")
             play_robot_sound('no')


    # 4. Handle Unknown / Error
    elif action_type == "unknown":
        error_msg = action_data.get("error", "Command not understood.")
        print(f"AI Error/Unknown Command: {error_msg}")
        play_robot_sound('no') # Play a sound indicating confusion

    else:
        # This case should ideally not be reached if Gemini follows the prompt
        print(f"Warning: Unhandled action_type '{action_type}'.")
        play_robot_sound('no')


# --- Main Execution Loop ---

if __name__ == "__main__":
    try:
        # Initialization (Hardware first, then AI if hardware is ok)
        initialize_hardware()
        # AI Initialization is done globally now. Check if model loaded.
        if not model:
             print("Exiting due to Gemini model initialization failure.")
             sys.exit(1)


        print("\n--- Ninja Robot Interface (using google-generativeai) ---")
        print("Enter your commands in natural language (e.g., 'walk fast', 'say hello', 'stop').")
        print("Type 'exit' or 'quit' to stop.")
        print("-----------------------------")

        while True:
            try:
                command = input("🤖> ").strip()
                if not command:
                    continue
                if command.lower() in ["exit", "quit"]:
                    break

                # Get interpretation from Gemini
                action_data = get_gemini_interpretation(command)

                # Execute the action
                if action_data:
                    execute_action(action_data)
                else:
                    # Handle case where Gemini interaction failed completely
                    print("Failed to get interpretation from AI.")
                    play_robot_sound('no') # Sound for error

                time.sleep(0.1) # Small delay between commands

            except EOFError: # Handle Ctrl+D
                 print("\nEOF detected.")
                 break

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Initiating shutdown...")
        play_robot_sound('sleepy')

    except Exception as e:
        print("\nAn unexpected error occurred in the main loop!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Ensure cleanup is always called
        cleanup_all()
        print("Program terminated.")
