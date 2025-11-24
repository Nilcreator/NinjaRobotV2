# -*- coding:utf-8 -*-

'''!
  @file ninja_core.py
  @brief Core logic for controlling the Ninja Robot using Google Gemini API,
         integrating movement, sound, and distance sensing.
         Supports English/Japanese commands with keyword activation.
  @copyright Copyright (c) 2024 Your Name/Assistant
  @license The MIT License (MIT)
  @author Your Name/Assistant
  @version V1.4 (Keyword activation, Japanese support, General Q&A)
  @date 2024-05-24
'''
# ... (imports and previous configurations remain largely the same) ...
import sys
import os
import time
import re
import threading
import json
import RPi.GPIO as GPIO
import google.generativeai as genai

# --- Configuration ---
GOOGLE_API_KEY = "Input your Google API Key here!"  # <----------- REPLACE WITH YOUR ACTUAL API KEY
GEMINI_MODEL_NAME = "gemini-2.0-flash-lite" # Or your preferred model

DISTANCE_THRESHOLD_CM = 15.0 # Increased threshold slightly

# Activation Keywords (lowercase for easy checking)
ENGLISH_KEYWORD = "ninja"
JAPANESE_KEYWORDS = ["忍者", "ニンジャ", "にんじゃ"] # Katakana, Kanji, Hiragana

# --- Import Robot Modules ---
try:
    import Ninja_Movements_v1 as movements
    import Ninja_Buzzer as buzzer
    import Ninja_Distance as distance
except ImportError as e:
    print(f"Error importing robot modules: {e}")
    sys.exit(1)

# --- Global Variables ---
model = None
movement_thread = None
distance_check_thread = None
is_continuous_moving = False
buzzer_pwm = None
keep_distance_checking = False
hardware_initialized = False

# ... (initialize_gemini, initialize_hardware, cleanup_all, play_robot_sound, distance_checker remain mostly the same) ...
# Ensure GOOGLE_API_KEY is actually checked or used in initialize_gemini
def initialize_gemini():
    """Initializes the Gemini model."""
    global model
    if model:
        print("Gemini already initialized.")
        return True

    print(f"Initializing Gemini model: {GEMINI_MODEL_NAME}...")
    try:
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY" or len(GOOGLE_API_KEY) < 10:
            print("Error: GOOGLE_API_KEY is not set or is a placeholder.")
            print("Please set your actual Google Gemini API key in ninja_core.py")
            model = None
            return False

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        print("Gemini model loaded successfully.")
        return True
    except Exception as e:
        print(f"Error configuring or loading Gemini model: {e}")
        model = None
        return False

def initialize_hardware():
    """Initializes Servos, Buzzer, and Distance Sensor."""
    global buzzer_pwm, hardware_initialized
    if hardware_initialized:
        print("Hardware already initialized.")
        return True

    print("Initializing hardware components...")
    try:
        movements.init_board_and_servo()
        buzzer.setup()
        buzzer_pwm = GPIO.PWM(buzzer.BUZZER_PIN, 440)
        buzzer_pwm.start(0)
        distance.setup_sensor()
        hardware_initialized = True
        print("Hardware components initialized.")
        movements.reset_servos()
        play_robot_sound('hello')
        time.sleep(1)
        print("Hardware initialization and setup complete.")
        return True
    except Exception as e:
        print(f"An error occurred during hardware initialization: {e}")
        try: GPIO.cleanup()
        except Exception: pass
        hardware_initialized = False
        return False

def cleanup_all():
    global keep_distance_checking, movement_thread, distance_check_thread, is_continuous_moving, hardware_initialized, buzzer_pwm
    print("\n--- Initiating Cleanup ---")
    if hardware_initialized: # Only play if hardware was meant to be up
        play_robot_sound("sleepy")

    keep_distance_checking = False
    if distance_check_thread and distance_check_thread.is_alive():
        distance_check_thread.join(timeout=0.5)
    distance_check_thread = None

    if is_continuous_moving or (movement_thread and movement_thread.is_alive()):
        movements.stop()
    if movement_thread and movement_thread.is_alive():
        movement_thread.join(timeout=1.0)
    movement_thread = None
    is_continuous_moving = False

    if hardware_initialized:
        try:
            if movements.servo: movements.rest()
        except Exception as rest_e: print(f"Error during rest: {rest_e}")
        if buzzer_pwm:
            try: buzzer_pwm.stop()
            except Exception: pass
        try: GPIO.cleanup()
        except Exception as gpio_e: print(f"Error during GPIO cleanup: {gpio_e}")
    hardware_initialized = False
    buzzer_pwm = None


def play_robot_sound(sound_keyword):
    if not hardware_initialized or not buzzer_pwm:
        print("Error: Hardware/Buzzer not initialized for sound.")
        return
    sound_action = buzzer.SOUND_MAP.get(sound_keyword.lower()) # Ensure keyword is lower
    # ... (rest of play_robot_sound logic) ...
    try:
        if sound_action == buzzer.SOUND_SCARED_IDENTIFIER:
            buzzer.play_scared_sound(buzzer_pwm)
        elif sound_action == buzzer.SOUND_EXCITING_IDENTIFIER:
             buzzer.play_exciting_trill(buzzer_pwm)
        elif isinstance(sound_action, list):
            buzzer.play_sequence(buzzer_pwm, sound_action)
        else:
            print(f"Warning: No sound for '{sound_keyword}'.")
    except Exception as e:
        print(f"Error playing sound '{sound_keyword}': {e}")

def distance_checker():
    global keep_distance_checking, is_continuous_moving
    # ... (distance_checker logic from previous version, ensure it calls play_robot_sound correctly)
    print("Distance checker thread started.")
    last_warning_time = 0
    warning_interval = 2.0

    while keep_distance_checking:
        if not is_continuous_moving or movements.stop_movement:
            if movements.stop_movement: print("Distance checker noticed movement stop flag.")
            break # Exit if no longer moving or explicitly stopped

        if not hardware_initialized:
            print("Distance checker: Hardware no longer initialized. Stopping check.")
            break

        dist = distance.measure_distance()

        if dist == -2: # GPIO error
             print("Distance sensor GPIO error. Stopping checker.")
             # Consider stopping movement if sensor fails critically
             # if is_continuous_moving: movements.stop(); is_continuous_moving = False;
             break
        elif dist != -1 and 0 <= dist < DISTANCE_THRESHOLD_CM: # Valid reading and obstacle detected
            print(f"!!! OBSTACLE DETECTED at {dist:.1f} cm !!!")
            current_time = time.time()
            if current_time - last_warning_time > warning_interval:
                 play_robot_sound('danger')
                 last_warning_time = current_time
            if is_continuous_moving: # Check again before stopping
                movements.stop()
                is_continuous_moving = False # Update state immediately
            break # Stop checking for this movement instance

        time.sleep(0.15) # Check frequency
    print("Distance checker thread finished.")
    keep_distance_checking = False # Ensure flag is reset on exit


# --- Gemini Interaction (Modified) ---
def process_user_command_with_gemini(user_command_full, language_code='en-US'):
    """
    Processes user command. Checks for keyword.
    If keyword, interprets for robot action.
    If no keyword, gets a conversational response.
    """
    global model
    if not model:
        print("Error: Gemini model not initialized.")
        return {"action_type": "unknown", "error": "Gemini model not ready."}

    user_command_lower = user_command_full.lower()
    command_for_action = None
    is_robot_command = False

    # Check for English keyword
    if ENGLISH_KEYWORD in user_command_lower:
        is_robot_command = True
        # Extract command part after "ninja"
        command_for_action = user_command_full[user_command_lower.find(ENGLISH_KEYWORD) + len(ENGLISH_KEYWORD):].strip()
        # Remove leading punctuation like comma or space
        if command_for_action and command_for_action[0] in [',', ' ']:
            command_for_action = command_for_action[1:].strip()
        print(f"Robot command (EN): '{command_for_action}'")

    # Check for Japanese keywords
    if not is_robot_command:
        for jp_keyword in JAPANESE_KEYWORDS:
            if jp_keyword in user_command_full: # Japanese is case-sensitive in this check
                is_robot_command = True
                command_for_action = user_command_full[user_command_full.find(jp_keyword) + len(jp_keyword):].strip()
                if command_for_action and command_for_action[0] in ['、', ' ', '　']: # Japanese comma, space, full-width space
                    command_for_action = command_for_action[1:].strip()
                print(f"Robot command (JP): '{command_for_action}'")
                break

    if is_robot_command:
        if not command_for_action: # Keyword was said alone
            return {"action_type": "sound", "sound_keyword": "yes"} # Acknowledge keyword

        # --- Prompt for Robot Action ---
        prompt = f"""
Analyze the following user command (which was preceded by an activation word like "Ninja" or "忍者") for a robot.
The command could be in English or Japanese. Determine the intended robot action(s).

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

Available Sound Keywords (map to these keywords):
- 'hello', 'thanks', 'no', 'yes', 'danger', 'exciting', 'happy', 'right', 'left', 'scared'

Output Format:
Return ONLY a valid JSON object. Do NOT include ```json ... ``` markers.
Keys: "action_type" ("move", "sound", "combo", "unknown"), "move_function", "speed", "sound_keyword", "error".

Examples (Intent, not exact phrasing):
User (EN): "move forward" -> {{"action_type": "move", "move_function": "walk", "speed": "normal"}}
User (EN): "look to your right-hand side" -> {{"action_type": "combo", "move_function": "turnright_step", "sound_keyword": "right"}}
User (JP): "前に進んで" (mae ni susunde - move forward) -> {{"action_type": "move", "move_function": "walk", "speed": "normal"}}
User (JP): "右を向いて" (migi o muite - look right) -> {{"action_type": "combo", "move_function": "turnright_step", "sound_keyword": "right"}}
User (EN): "make a happy sound" -> {{"action_type": "sound", "sound_keyword": "happy"}}
User (JP): "止まれ" (tomare - stop) -> {{"action_type": "move", "move_function": "stop"}}

User Command (after keyword): "{command_for_action}"
Language of command: {"Japanese" if language_code == 'ja-JP' else "English"}

Provide ONLY the JSON output:
"""
        instruction_type = "Robot Action"
    else:
        # --- Prompt for General Conversational Response ---
        prompt = f"""
You are a friendly and helpful AI assistant integrated into a small robot.
The user has spoken to you without using the robot's activation keyword ("Ninja" or "忍者").
Respond conversationally to the following user query.
Keep your response concise and suitable for a small robot to "say" (it will be text-to-speech).
Respond in the likely language of the query.

User Query: "{user_command_full}"

Your conversational response (text only, no JSON):
"""
        instruction_type = "General Query"

    print(f"Sending to Gemini ({instruction_type}): '{command_for_action if is_robot_command else user_command_full}'")
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.3 if is_robot_command else 0.7, # More deterministic for actions
            max_output_tokens=150 if is_robot_command else 300
        )
        response = model.generate_content(prompt, generation_config=generation_config)
        response_text = response.text.strip()

        if is_robot_command:
            try:
                action_data = json.loads(response_text)
                print(f"Gemini Robot Action: {action_data}")
                return action_data
            except json.JSONDecodeError:
                # Try extracting from markdown (as in previous version)
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
                if json_match:
                    try:
                        action_data = json.loads(json_match.group(1))
                        print(f"Gemini Robot Action (extracted): {action_data}")
                        return action_data
                    except json.JSONDecodeError:
                        print(f"Error: Extracted JSON invalid. Response: {response_text}")
                        return {"action_type": "unknown", "error": "Invalid JSON from AI (extracted)."}
                print(f"Error: Could not parse JSON for robot action. Response: {response_text}")
                return {"action_type": "unknown", "error": "Could not parse AI response for action."}
        else:
            # General query response
            print(f"Gemini Conversational Response: {response_text}")
            return {"action_type": "conversation", "response_text": response_text}

    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")
        error_type = "API error for robot action." if is_robot_command else "API error for conversation."
        return {"action_type": "unknown", "error": error_type}


# --- Action Execution (Modified) ---
def execute_action(action_data, original_command_language='en-US'):
    """Executes robot action or handles conversational response."""
    global movement_thread, distance_check_thread, is_continuous_moving, keep_distance_checking

    action_type = action_data.get("action_type", "unknown")

    if action_type == "conversation":
        response_text = action_data.get("response_text", "I'm not sure how to respond to that.")
        print(f"CONVERSATIONAL: {response_text}")
        # Here, you would send `response_text` to a Text-to-Speech engine.
        # For now, we'll just print it.
        # If you have gTTS or similar integrated with the buzzer, you could use it.
        # For simplicity, let's play a generic "thinking" or "acknowledgement" sound.
        play_robot_sound('yes') # Or a new sound like 'SOUND_ACKNOWLEDGE'
        # The web interface will need to display this response_text.
        return # No further robot hardware action

    # --- Logic for Robot Hardware Actions ---
    if not hardware_initialized:
        print("Error: Hardware not initialized. Cannot execute robot action.")
        play_robot_sound('no')
        return

    move_func_name = action_data.get("move_function")
    sound_keyword = action_data.get("sound_keyword")
    speed = action_data.get("speed", "normal")

    # Stop previous continuous actions if necessary (same logic as before)
    is_new_continuous = action_type in ["move", "combo"] and move_func_name in [
        "walk", "stepback", "run", "runback", "rotateleft", "rotateright"
    ]
    is_new_finite_move = action_type in ["move", "combo", "servo"] and not is_new_continuous and move_func_name != "stop"

    if (is_new_continuous or is_new_finite_move) and is_continuous_moving:
        print("Stopping previous continuous movement.")
        keep_distance_checking = False
        if distance_check_thread and distance_check_thread.is_alive(): distance_check_thread.join(timeout=0.5)
        distance_check_thread = None
        movements.stop()
        if movement_thread and movement_thread.is_alive(): movement_thread.join(timeout=1.0)
        movement_thread = None
        is_continuous_moving = False
        time.sleep(0.2)

    # Execute sound and/or movement (largely same as before)
    try:
        if action_type in ["sound", "combo"] and sound_keyword:
            play_robot_sound(sound_keyword)
            if action_type == "combo": time.sleep(0.2) # Delay if sound is part of combo

        if action_type in ["move", "combo"] and move_func_name:
            target_func = getattr(movements, move_func_name, None)
            if target_func:
                print(f"Executing movement: {move_func_name} (Speed: {speed})")
                if move_func_name in ["walk", "stepback", "run", "runback", "rotateleft", "rotateright"]:
                    if not is_continuous_moving:
                        is_continuous_moving = True
                        movements.stop_movement = False
                        movement_thread = threading.Thread(target=target_func, args=(speed, None), daemon=True)
                        movement_thread.start()
                        # Start distance checker only for forward movements
                        if move_func_name in ["walk", "run"]:
                            keep_distance_checking = True
                            distance_check_thread = threading.Thread(target=distance_checker, daemon=True)
                            distance_check_thread.start()
                        else:
                            keep_distance_checking = False # No distance check for backward/rotate
                    else: print("Warning: Tried to start continuous move while already moving.")
                elif move_func_name == "stop":
                    print("Executing stop command.")
                    keep_distance_checking = False
                    if distance_check_thread and distance_check_thread.is_alive(): distance_check_thread.join(timeout=0.5)
                    movements.stop()
                    if movement_thread and movement_thread.is_alive(): movement_thread.join(timeout=1.0)
                    is_continuous_moving = False
                else: # Finite movements like hello, turn_step, reset_servos, rest
                    if not is_continuous_moving: target_func() # Assumes no speed for these, or handled by default
                    else:
                        print(f"Warning: Cannot perform '{move_func_name}' while continuous. Stop first.")
                        play_robot_sound('no')
            else:
                print(f"Error: Movement function '{move_func_name}' not found.")
                play_robot_sound('no')
        elif action_type == "servo":
            # ... (servo logic remains the same) ...
             if not is_continuous_moving:
                servo_id_raw = action_data.get("servo_id")
                servo_angle_raw = action_data.get("servo_angle")
                # ... (rest of servo logic)
             else:
                 print("Warning: Cannot set servo while continuous. Stop first.")
                 play_robot_sound('no')

        elif action_type == "unknown" and "error" in action_data:
            print(f"AI Error/Unknown Command: {action_data['error']}")
            play_robot_sound('no')
        # No explicit 'else' for unhandled action_type if it's not "conversation",
        # as "unknown" should cover errors from Gemini for robot commands.

    except Exception as e:
        print(f"Unexpected error during action execution: {e}")
        try: movements.stop(); is_continuous_moving = False; keep_distance_checking = False
        except: pass
        import traceback
        traceback.print_exc()

# ... (get_robot_status remains the same) ...
def get_robot_status():
    if not hardware_initialized: return "Hardware Not Initialized"
    if is_continuous_moving:
        if movement_thread and movement_thread.is_alive(): return "Moving..."
        else: return "Movement stopped unexpectedly."
    return "Idle"

# --- Main test block (if running ninja_core.py directly) ---
if __name__ == "__main__":
    if not initialize_gemini():
        sys.exit("Failed to initialize Gemini. Exiting.")
    if not initialize_hardware():
        sys.exit("Failed to initialize hardware. Exiting.")

    print("\n--- Ninja Robot Core Test Interface ---")
    print("Prefix commands with 'Ninja ' (EN) or '忍者 ' (JP) to control the robot.")
    print("Other inputs will be treated as general questions.")
    print("Type 'exit' or 'quit' to stop.")
    print("------------------------------------")

    try:
        while True:
            command_full = input("🎤> ").strip()
            if not command_full:
                continue
            if command_full.lower() in ["exit", "quit"]:
                break

            # Determine language (simple heuristic for testing)
            lang = 'ja-JP' if any(k in command_full for k in JAPANESE_KEYWORDS) else 'en-US'

            action_data = process_user_command_with_gemini(command_full, language_code=lang)

            if action_data:
                execute_action(action_data, original_command_language=lang)
            else:
                print("Failed to get any response from AI.")
                play_robot_sound('no')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected.")
    finally:
        cleanup_all()
        print("Program terminated.")
