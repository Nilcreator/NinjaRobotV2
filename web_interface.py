# -*- coding:utf-8 -*-
# Filename: web_interface.py

import time
import atexit
import os
import json
from flask import Flask, render_template, request, jsonify # Removed redirect, url_for, flash as not used here

import ninja_core

app = Flask(__name__)
app.secret_key = os.urandom(24) # Still good practice for sessions if you add them

last_command_details = {"type": "N/A", "content": ""}
last_interpretation_or_response = {} # Can hold action JSON or conversational text
last_status_message = "System Initializing..."

COMMAND_TO_SOUND_MAP = {
    "run": "exciting", "runback": "scared", "stepback": "scared",
    "rotateright": "right", "rotateleft": "left",
    "turnright_step": "right", "turnleft_step": "left",
    "hello": "hello", "rest": "thanks", "stop": "no",
}
SOUND_DELAY = 0.3

print("--- Initializing Robot Core from Web Interface ---")
gemini_ok = ninja_core.initialize_gemini()
hardware_ok = ninja_core.initialize_hardware()

if not gemini_ok:
    last_status_message = "CRITICAL ERROR: Gemini AI failed to initialize. Voice commands will not work."
    print(last_status_message)
if not hardware_ok:
    last_status_message = "CRITICAL ERROR: Robot hardware failed to initialize. Robot will not move or make sounds."
    print(last_status_message)
if gemini_ok and hardware_ok:
    last_status_message = "System Initialized. Ready for commands."

atexit.register(ninja_core.cleanup_all)

def create_direct_action_data(command_name, speed="normal"):
    action_type = "move"
    action_data = {"action_type": action_type, "move_function": command_name, "speed": speed}
    if command_name in ['hello', 'stop', 'reset_servos', 'rest']: # No speed for these
         action_data.pop("speed", None)
    return action_data

@app.route('/')
def index():
    # Ensure last_interpretation_or_response is always a dict for json.dumps if it was a string
    interp_data_for_template = last_interpretation_or_response
    if isinstance(last_interpretation_or_response, str): # If it was a conversational string
        interp_data_for_template = {"conversational_response": last_interpretation_or_response}

    try:
        interp_str = json.dumps(interp_data_for_template, indent=2, ensure_ascii=False)
    except TypeError:
        interp_str = "{}"
    return render_template('index.html',
                           status=last_status_message,
                           last_command_type=last_command_details["type"],
                           last_command_content=last_command_details["content"],
                           interpretation=interp_str, # This will now show action JSON or conversational_response
                           robot_state=ninja_core.get_robot_status())

@app.route('/controller_command', methods=['POST'])
def handle_controller_command():
    global last_status_message, last_command_details, last_interpretation_or_response
    if not request.is_json: return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.get_json()
    command_name = data.get('command', '').strip()
    speed = data.get('speed', 'normal').strip()
    print(f"CONTROLLER_CMD: Received: {command_name}, Speed: {speed}")

    last_command_details = {"type": "Controller", "content": f"{command_name} ({speed})"}

    if not hardware_ok:
         last_status_message = "Error: Hardware not initialized."
         last_interpretation_or_response = {"error": last_status_message}
         return jsonify({"status": "error", "message": last_status_message, "interpretation": last_interpretation_or_response}), 500
    if not command_name:
        last_status_message = "Empty controller command."
        last_interpretation_or_response = {"error": last_status_message}
        return jsonify({"status": "warning", "message": last_status_message, "interpretation": last_interpretation_or_response}), 400

    sound_keyword = COMMAND_TO_SOUND_MAP.get(command_name)
    if sound_keyword:
        ninja_core.play_robot_sound(sound_keyword)
        time.sleep(SOUND_DELAY)

    action_data = create_direct_action_data(command_name, speed)
    last_interpretation_or_response = action_data # Store the direct action structure

    flash_category = "info"
    try:
        ninja_core.execute_action(action_data) # Pass the direct action
        time.sleep(0.1)
        last_status_message = f"Controller action '{command_name}' initiated."
        flash_category = "success"
    except Exception as e:
        last_status_message = f"Error executing controller command '{command_name}': {e}"
        flash_category = "error"
        print(f"ERROR executing controller cmd: {e}")
        try: ninja_core.movements.stop()
        except: pass

    return jsonify({
        "status": flash_category,
        "message": last_status_message,
        "interpretation": last_interpretation_or_response
        })

@app.route('/voice_command_text', methods=['POST'])
def handle_voice_command_text():
    global last_status_message, last_command_details, last_interpretation_or_response
    if not request.is_json: return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    data = request.get_json()
    command_text = data.get('command_text', '').strip()
    language_code = data.get('language_code', 'en-US') # Get language from client
    print(f"VOICE_CMD_TEXT: Received: '{command_text}', Lang: {language_code}")

    last_command_details = {"type": f"Voice ({language_code})", "content": command_text}

    if not hardware_ok and not gemini_ok : # If both fail, very limited
        last_status_message = "Error: Hardware and AI not initialized."
        last_interpretation_or_response = {"error": last_status_message}
        return jsonify({"status": "error", "message": last_status_message, "interpretation": last_interpretation_or_response}), 500
    if not command_text:
        last_status_message = "Empty voice command."
        last_interpretation_or_response = {"error": last_status_message}
        return jsonify({"status": "warning", "message": last_status_message, "interpretation": last_interpretation_or_response}), 200
    if not gemini_ok:
        last_status_message = "Error: Gemini AI not initialized. Cannot process voice."
        last_interpretation_or_response = {"error": last_status_message}
        return jsonify({"status": "error", "message": last_status_message, "interpretation": last_interpretation_or_response}), 500


    # Process with Gemini (handles keyword, action, or conversation)
    # The process_user_command_with_gemini now returns the action_data or conversational_data
    processed_data = ninja_core.process_user_command_with_gemini(command_text, language_code)
    last_interpretation_or_response = processed_data # This can be action JSON or conversational dict

    flash_category = "info"
    final_status_msg = "Processing complete."

    if processed_data.get("action_type") == "conversation":
        final_status_msg = "AI Response: " + processed_data.get("response_text", "No response.")
        flash_category = "info"
        # TTS would happen here in ninja_core or be triggered here based on response_text
        # ninja_core.play_robot_sound('yes') # Acknowledge understanding
    elif processed_data.get("action_type") != "unknown" and hardware_ok:
        # This is a robot action command
        # Play sound based on Gemini's interpretation (if any)
        sound_to_play = processed_data.get("sound_keyword")
        if not sound_to_play and processed_data.get("move_function"): # Fallback to command map if Gemini didn't specify sound
            sound_to_play = COMMAND_TO_SOUND_MAP.get(processed_data.get("move_function"))

        if sound_to_play:
            ninja_core.play_robot_sound(sound_to_play)
            # Add delay only if there's also a move function to give sound time
            if processed_data.get("move_function"):
                time.sleep(SOUND_DELAY)

        try:
            ninja_core.execute_action(processed_data, original_command_language=language_code)
            final_status_msg = f"Voice action likely initiated: {processed_data.get('move_function') or processed_data.get('sound_keyword') or 'task'}"
            flash_category = "success"
        except Exception as e:
            final_status_msg = f"Error executing voice action: {e}"
            flash_category = "error"
            print(f"ERROR executing voice action: {e}")
            try: ninja_core.movements.stop()
            except: pass
    elif processed_data.get("action_type") == "unknown":
        final_status_msg = "AI could not determine a valid action: " + processed_data.get("error", "")
        flash_category = "warning"
        if hardware_ok: ninja_core.play_robot_sound('no')
    else: # Catch-all for unexpected processed_data structure or if hardware_ok is false for an action
        final_status_msg = "Could not fully process voice command."
        flash_category = "warning"
        if hardware_ok: ninja_core.play_robot_sound('no')


    last_status_message = final_status_msg
    return jsonify({
        "status": flash_category,
        "message": final_status_msg,
        "interpretation": last_interpretation_or_response
        })


if __name__ == '__main__':
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        print(f"INFO: Web server will be accessible at http://{ip_address}:5000")
    except Exception:
        ip_address = "0.0.0.0"
        print("INFO: Could not determine local IP. Server running on http://0.0.0.0:5000 (try http://<your_pi_hostname>.local:5000)")

    app.run(host='0.0.0.0', port=5000, debug=False) # debug=False for less console noise in use
