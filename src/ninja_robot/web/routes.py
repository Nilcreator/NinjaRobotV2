from typing import Any
from flask import Blueprint, render_template, request, jsonify, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index() -> str:
    """Renders the main control dashboard."""
    return render_template("index.html")


@main_bp.route("/api/command", methods=["POST"])
def send_command() -> Any:
    """API endpoint to receive commands."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    command = data.get("command")
    params = data.get("params", {})

    if not command:
        return jsonify({"error": "No command provided"}), 400

    # Access the robot brain attached to the app
    brain = current_app.robot_brain  # type: ignore

    result = brain.execute_command(command, params)
    return jsonify({"result": result})


@main_bp.route("/api/status", methods=["GET"])
def get_status() -> Any:
    """API endpoint to get robot status (e.g. distance, AI response)."""
    brain = current_app.robot_brain  # type: ignore
    # For now, just return distance as a status check
    dist = brain.sensors.measure_distance() if brain.sensors else -1
    ai_response = brain.last_ai_response
    return jsonify({
        "distance": dist,
        "ai_response": ai_response
    })


# --- Legacy Routes for Gamepad UI ---

@main_bp.route("/command", methods=["POST"])
def handle_controller_command() -> Any:
    """Handles commands from the gamepad UI."""
    data = request.json
    if not data:
        return jsonify({"message": "No data", "status": "error"}), 400

    command = data.get("command")
    speed = data.get("speed", "normal")

    brain = current_app.robot_brain  # type: ignore

    # Map legacy commands if necessary, or pass through
    # Brain now handles stepback, turnleft_step, etc.
    msg = brain.execute_command(command, {"speed": speed})

    return jsonify({
        "message": msg,
        "status": "success" if "Error" not in msg else "error",
        "interpretation": {"action_type": "direct_control", "command": command}
    })


@main_bp.route("/voice-command-text", methods=["POST"])
def handle_voice_command_text() -> Any:
    """Handles transcribed text from the Web Speech API."""
    data = request.json
    if not data:
        return jsonify({"message": "No data", "status": "error"}), 400

    text = data.get("command_text", "")
    # lang = data.get("language_code", "en-US")  # Unused for now

    brain = current_app.robot_brain  # type: ignore

    # TODO: Integrate Gemini here for true NLU
    # For now, simple keyword matching or pass to brain if it matches a command
    # Or better, use the GeminiClient if available

    response_text = "Voice command received."
    interpretation = {"original_text": text}

    # Simple keyword check for demo purposes
    # Ideally, we'd call brain.process_natural_language(text)

    # Check for direct commands in text
    lower_text = text.lower()
    cmd = None
    if "stop" in lower_text:
        cmd = "stop"
    elif "walk" in lower_text:
        cmd = "walk"
    elif "run" in lower_text:
        cmd = "run"
    elif "hello" in lower_text:
        cmd = "hello"
    elif "rest" in lower_text:
        cmd = "rest"

    if cmd:
        msg = brain.execute_command(cmd)
        response_text = f"Executed: {msg}"
        interpretation["command"] = cmd
    else:
        response_text = f"I heard: {text} (AI processing not fully linked yet)"

    return jsonify({
        "message": response_text,
        "status": "success",
        "interpretation": interpretation
    })
