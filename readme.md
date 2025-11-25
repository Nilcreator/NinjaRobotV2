# NinjaRobot V2 🥷🤖

**NinjaRobot V2** is an advanced, AI-powered bipedal robot built on the Raspberry Pi platform. It combines precise servo control for movement, sensor integration for environmental awareness, and Google's Gemini AI for natural voice interaction.

Designed for makers, educators, and hobbyists, this project demonstrates how to build a fully functional robot with web control, voice capabilities, and autonomous behaviors.

---

## 🛠️ Hardware Requirements

To build NinjaRobot V2, you will need the following components:

| Component | Description | Quantity |
|-----------|-------------|----------|
| **Raspberry Pi** | Zero 2W (Recommended), 3B+, or 4 | 1 |
| **Expansion Board** | DFRobot IO Expansion HAT (or compatible PCA9685 board) | 1 |
| **Servos** | Micro Servos (SG90 or MG90S) | 4 |
| **Ultrasonic Sensor** | HC-SR04 | 1 |
| **Buzzer** | Active Buzzer Module | 1 |
| **Microphone** | **INMP441** (I2S MEMS Microphone) | 1 |
| **Speaker** | USB Speaker or 3.5mm Speaker (for voice response) | 1 |
| **Power Supply** | 2x 18650 Li-ion Batteries (or 5V/3A Power Bank) | 1 |
| **MicroSD Card** | 16GB or larger (Class 10) | 1 |

---

## 🔌 Hardware Setup & Wiring

Connect the components to the DFRobot IO Expansion HAT as follows.

### 1. Servos (Movement)
Connect the servos to the PWM/Servo headers on the HAT.

| Servo Function | Channel on HAT | Description |
|----------------|----------------|-------------|
| **Head Pan** | **0** | Rotates head left/right |
| **Head Tilt** | **1** | Tilts head up/down |
| **Left Arm/Leg** | **2** | Controls left side movement |
| **Right Arm/Leg** | **3** | Controls right side movement |

### 2. Ultrasonic Sensor (Distance)
Connect the HC-SR04 sensor to the GPIO headers.

| HC-SR04 Pin | Raspberry Pi GPIO (BCM) | Physical Pin |
|-------------|-------------------------|--------------|
| VCC | 5V | - |
| **Trig** | **GPIO 21** | Pin 40 |
| **Echo** | **GPIO 22** | Pin 15 |
| GND | GND | - |

> **⚠️ IMPORTANT:** The HC-SR04 Echo pin outputs 5V. You **MUST** use a voltage divider (1kΩ/2kΩ resistors) to drop it to 3.3V before connecting to the Raspberry Pi GPIO 22 to avoid damaging the Pi.

### 4. INMP441 Microphone (I2S)
The INMP441 is a high-quality I2S microphone. Connect it to the GPIO headers.

| INMP441 Pin | Raspberry Pi GPIO (BCM) | Physical Pin | Description |
|-------------|-------------------------|--------------|-------------|
| **VDD** | 3.3V | Pin 1 | Power |
| **GND** | GND | Pin 6 | Ground |
| **SCK** | **GPIO 18** | Pin 12 | I2S Bit Clock (BCLK) |
| **WS** | **GPIO 19** | Pin 35 | I2S Word Select (LRCLK) |
| **SD** | **GPIO 20** | Pin 38 | I2S Data In (DIN) |
| **L/R** | GND | - | Select Left Channel |

#### ⚠️ Critical: Enabling I2S Audio
To use the INMP441, you must enable I2S in the Raspberry Pi OS.

1.  **Edit the config file**:
    ```bash
    sudo nano /boot/config.txt
    ```
    *(Note: On Bookworm, this might be `/boot/firmware/config.txt`)*

2.  **Uncomment/Add these lines**:
    ```ini
    # Enable I2S
    dtparam=i2s=on
    ```

3.  **Compile/Install the I2S Module** (Recommended for INMP441):
    The easiest way is often to use a pre-compiled overlay or a simple installer script.
    However, for a quick start, try adding this to `config.txt` if you have a generic I2S overlay:
    ```ini
    dtoverlay=googlevoicehat-soundcard
    ```
    *If that doesn't work, you may need to compile a specific loader for the INMP441. See online guides for "Raspberry Pi INMP441 setup".*

4.  **Reboot**:
    ```bash
    sudo reboot
    ```

5.  **Verify**:
    ```bash
    arecord -l
    ```
    You should see your I2S microphone listed.

---

## 🚀 Step-by-Step Installation Guide

Follow these steps to set up your NinjaRobot V2 from scratch. No advanced programming knowledge is required!

### Step 1: Prepare the Raspberry Pi
1. Download and install **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)**.
2. Insert your MicroSD card into your computer.
3. Open Raspberry Pi Imager:
    *   **Device**: Choose your Pi model (e.g., Raspberry Pi Zero 2 W).
    *   **OS**: Choose **Raspberry Pi OS (Legacy, 64-bit) Bullseye**.
        *   *Note: "Legacy" is recommended for best compatibility with GPIO libraries.*
    *   **Storage**: Select your SD card.
4. Click **Next** and choose **Edit Settings**:
    *   Set **Hostname**: `ninjarobot`
    *   Enable **SSH** (Password authentication).
    *   Set **Username**: `pi` and **Password**: `ninja` (or your preferred password).
    *   Configure **Wireless LAN** (SSID and Password).
5. Click **Save** and **Yes** to write the OS.
6. Once finished, insert the SD card into the Pi and power it on.

### Step 2: System Setup
1. Open a terminal on your computer and connect to the Pi:
   ```bash
   ssh pi@ninjarobot.local
   ```
2. Update the system and install required tools:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git i2c-tools python3-pip libasound2-dev portaudio19-dev
   ```
3. Enable I2C interface:
   ```bash
   sudo raspi-config
   # Go to Interface Options -> I2C -> Yes -> Finish
   ```

### Step 3: Install the Project
1. Install **uv** (a fast Python tool manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   ```
2. Clone the NinjaRobot repository:
   ```bash
   git clone https://github.com/Nilcreation/NinjaRobotV2.git
   cd NinjaRobotV2
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```

### Step 4: Configuration
1. Create the configuration file:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file to add your Google Gemini API Key:
   ```bash
   nano .env
   ```
   *   Change `GEMINI_API_KEY=""` to `GEMINI_API_KEY="your_actual_api_key_here"`.
   *   (Get a free key from [Google AI Studio](https://aistudio.google.com/)).
   *   Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## 🎮 Testing & Usage

### 1. Run the Integration Test
Before running the main robot, verify that all hardware is connected correctly.
```bash
uv run python tests/integration_test.py
```
*   **Success**: You should see "Integration Test Complete" and hear the servos move briefly.
*   **Failure**: Check the error messages (e.g., "I2C device not found" means check wiring).

### 2. Start the NinjaRobot
Run the main application:
```bash
uv run python src/ninja_robot/main.py
```
You will see: `Starting NinjaRobot V2...`

### 3. Web Control
1. Open a browser on your computer/phone connected to the same WiFi.
2. Go to: `http://ninjarobot.local:5000`
3. You will see the **Control Dashboard**.
    *   **Walk/Run**: Make the robot move.
    *   **Hello**: Wave hand.
    *   **Rest**: Return to neutral position.
    *   **Distance**: See real-time sensor readings.

### 4. Voice Control
*   Speak clearly to the USB microphone.
*   Say commands like *"Walk forward"*, *"Stop"*, or ask questions like *"Who are you?"*.
*   The robot will respond using its AI voice (via Gemini).

---

## 🧩 Features Explanation

*   **Core Logic (`src/ninja_robot/`)**:
    *   `brain.py`: The central commander that coordinates movement, sensors, and voice.
    *   `movement.py`: Handles complex servo gaits (walking, running) using a threaded controller.
    *   `sensors.py`: Manages the ultrasonic sensor and buzzer.
*   **Web Interface (`src/ninja_robot/web/`)**:
    *   A lightweight Flask app that serves the UI and handles API requests.
*   **Voice Module (`src/ninja_robot/voice/`)**:
    *   `gemini_client.py`: Connects to Google's Gemini API for intelligent conversation.
    *   `speech.py`: Handles Speech-to-Text (STT) and Text-to-Speech (TTS).

---

**Happy Building!** 🚀
