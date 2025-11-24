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
    """API endpoint to get robot status (e.g. distance)."""
    brain = current_app.robot_brain  # type: ignore
    # For now, just return distance as a status check
    dist = brain.sensors.measure_distance() if brain.sensors else -1
    return jsonify({"distance": dist})
