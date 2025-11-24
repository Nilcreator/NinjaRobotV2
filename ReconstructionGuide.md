# NinjaRobotV2 Reconstruction Guide

This document provides a comprehensive analysis of the NinjaRobotV2 project and outlines a detailed plan for reconstructing and optimizing the codebase for the Raspberry Pi Zero 2W platform.

## 1. Project Overview

**NinjaRobotV2** is a voice-controlled, quadrupedal robot project designed for the Raspberry Pi platform. It integrates:
-   **Locomotion:** 4-servo leg mechanism for walking, running, and turning.
-   **AI Interaction:** Google Gemini API for natural language command interpretation and conversational capabilities.
-   **Web Control:** A Flask-based web interface for manual control and status monitoring.
-   **Sensory Feedback:** Ultrasonic distance sensing for obstacle detection and an active buzzer for audio feedback.

The project aims to provide an interactive, educational robot platform. The current codebase is functional but requires optimization for robustness, maintainability, and performance on the resource-constrained Raspberry Pi Zero 2W.

## 2. Current System Details

### 2.1 Hardware Configuration

-   **Core Controller:** Raspberry Pi Zero 2W (Quad-core ARM Cortex-A53, 512MB RAM).
-   **Expansion Board:** DFRobot IO Expansion HAT (communicates via I2C at address `0x10`).
-   **Actuators:** 4x SG90 Micro Servos (connected to PWM channels on the HAT).
-   **Sensors:**
    -   HC-SR04 Ultrasonic Sensor (GPIO).
    -   INMP441 I2S Microphone (Optional/Future).
-   **Audio:** Active Buzzer (PWM).
-   **Power:** 5V High-Current Supply (2.5A+ recommended).

### 2.2 System Requirements & Dependencies
**Critical for Pi Zero 2W:**
-   **OS:** Raspberry Pi OS (32-bit recommended for performance).
-   **System Packages (`apt`):** `python3-dev`, `python3-pip`, `python3-venv`, `build-essential`, `libasound2-dev`, `portaudio19-dev`, `libportaudio2`, `libportaudiocpp0`, `ffmpeg`, `flac`, `libatlas-base-dev`, `python3-smbus`.
-   **Rust Compiler:** Required for compiling `pydantic-core` (dependency of `google-generativeai`).
-   **Swap Space:** Temporary increase to 1GB+ is required during installation of Python libraries.

### 2.2 GPIO & Wiring Map

| Component | Pin / Port | Type | Description |
| :--- | :--- | :--- | :--- |
| **Servos** | | | |
| Right Leg/Hip | HAT PWM 0 | PWM | Controls right leg lift/position |
| Left Leg/Hip | HAT PWM 1 | PWM | Controls left leg lift/position |
| Right Foot | HAT PWM 2 | PWM | Controls right foot rotation |
| Left Foot | HAT PWM 3 | PWM | Controls left foot rotation |
| **Sensors** | | | |
| Ultrasonic Trig | GPIO 21 | Output | Trigger pulse for distance |
| Ultrasonic Echo | GPIO 22 | Input | Echo pulse for distance |
| **Audio** | | | |
| Buzzer | GPIO 23 | PWM | Audio feedback signal |
| **Comms** | | | |
| I2C SDA | GPIO 2 | I2C | Data line for HAT |
| I2C SCL | GPIO 3 | I2C | Clock line for HAT |

### 2.3 File Structure & Code Architecture

The current project structure is flat, with mixed responsibilities:

-   **`ninja_core.py`**: The central "brain". Initializes hardware, handles Gemini API calls, manages global state (`model`, `hardware_initialized`), and coordinates threads.
-   **`web_interface.py`**: Entry point for the web server. Imports `ninja_core` to trigger actions. Uses global variables to track status.
-   **`Ninja_Movements_v1.py`**: Contains procedural movement logic (`walk`, `run`, `turn`). Directly controls the `DFRobot` board instance (global).
-   **`DFRobot_RaspberryPi_Expansion_Board.py`**: **Local Vendor Library.** This is specific to the DFRobot HAT and is *not* installed via pip. It must be preserved in the project root.
-   **`smbus2`**: Python dependency required for the DFRobot library to communicate via I2C.
-   **`Ninja_Buzzer.py`**: Defines sound patterns and controls the buzzer.
-   **`Ninja_Distance.py`**: Handles ultrasonic sensor reading.

**Critique:**
-   **Global State:** Heavy reliance on global variables makes debugging and state management difficult.
-   **Hardcoded Configuration:** API keys, pin numbers, and tuning parameters are scattered across files.
-   **Concurrency:** Threading is used but lacks robust synchronization (potential race conditions with `stop_movement` flags).
-   **Error Handling:** Basic `try-except` blocks; lacks structured logging or auto-recovery mechanisms for hardware glitches.

## 3. Proposed Improvements

To enhance robustness for the Raspberry Pi Zero 2W, we propose the following improvements:

### 3.1 Architecture & Code Quality
-   **Object-Oriented Design (OOP):** Refactor `ninja_core`, `movements`, and `sensors` into classes (e.g., `RobotController`, `MovementManager`, `SensorSuite`) to encapsulate state and reduce global variable usage.
-   **Configuration Management:** Externalize all settings (API keys, pins, servo limits) into a `config.yaml` or `.env` file. This prevents hardcoding and simplifies tuning.
-   **Dependency Management:** Create a strict `requirements.txt` to ensure reproducible environments.

### 3.2 Robustness & Performance
-   **Graceful Degradation:** Ensure the web interface remains responsive even if hardware (I2C/GPIO) fails or is disconnected.
-   **I2C Recovery:** Implement retry logic for I2C communication to handle transient errors common on the Pi.
-   **Resource Management:** Use context managers (`with` statements) for GPIO and file handling to ensure proper cleanup.
-   **Logging:** Replace `print` statements with the Python `logging` module for better debugging and runtime monitoring.

### 3.3 Deployment & Maintenance
-   **Linting & Formatting:** Enforce `pylint` and `black` formatting to maintain code quality.
-   **Setup Script:** Provide a `setup.sh` to automate system dependency installation (Rust, libraries).

## 4. Detailed Execution Plan

This plan is divided into phases. **Crucially, a linting and static analysis step is mandatory at the end of each phase to ensure no regressions.**

### Phase 1: Standardization & Configuration
**Goal:** Clean up the codebase and separate configuration from logic.
1.  **Create `requirements.txt`:** List all Python dependencies (`google-generativeai`, `Flask`, `smbus2`, `RPi.GPIO`, etc.) with versions. *Note: `DFRobot_RaspberryPi_Expansion_Board.py` is local and not listed here.*
2.  **Implement `config.py`:** Create a configuration module that loads from `.env` or defaults. Move all pins, keys, and constants here.
3.  **Setup Logging:** Replace `print()` with a structured logger configuration.
4.  **Mandatory Linting:** Run `pylint` and `flake8`. Fix all P1/P2 errors (syntax, undefined variables).

### Phase 2: Core Refactoring (OOP)
**Goal:** Encapsulate logic to remove global state.
1.  **Refactor `Ninja_Movements_v1.py`:** Create a `MovementController` class. It should own the `board` instance.
2.  **Refactor `ninja_core.py`:** Create a `RobotBrain` class that coordinates the `MovementController` and Gemini API.
3.  **Update `web_interface.py`:** Instantiate the `RobotBrain` class instead of importing globals.
4.  **Mandatory Linting:** Run `pylint`. Ensure a score > 7.0/10. Verify no circular imports.

### Phase 3: Robustness & Error Handling
**Goal:** Make the robot resilient to hardware faults.
1.  **I2C Retry Logic:** Wrap `DFRobot` calls in a retry decorator to handle `OSError: [Errno 121] Remote I/O error`.
2.  **Thread Safety:** Use `threading.Event` and `threading.Lock` for movement control instead of boolean flags.
3.  **Gemini Fallback:** Handle API timeouts gracefully; provide offline fallback responses if possible (or just specific error sounds).
4.  **Mandatory Linting:** Run `pylint` and `mypy` (type checking) to catch type-related bugs.

### Phase 4: Optimization for Pi Zero 2W
**Goal:** Tune for the specific hardware constraints.
1.  **Startup Optimization:** Lazy load heavy libraries (like `google.generativeai`) only when needed, or initialize them in a background thread to speed up web server boot.
2.  **Swap Management:** Verify swap configuration in `setup.sh` to prevent OOM kills during operation.
3.  **Mandatory Linting:** Final code quality check. Aim for `pylint` score > 9.0.

### Phase 5: Documentation & Verification
**Goal:** Ensure the system is usable and maintainable.
1.  **Update `readme.md`:** Reflect the new architecture and setup instructions.
2.  **Verification Script:** Create a `verify_hardware.py` script to test individual components (Servo, Mic, I2C) in isolation.
3.  **Final Review:** User acceptance testing.
