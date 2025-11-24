# Build Your Own Voice-Controlled Ninja Robot (Raspberry Pi & Gemini)

![Robot Concept](https://via.placeholder.com/600x300.png?text=Ninja+Robot+Concept) <!-- Optional: Replace with an image of your robot -->

This tutorial guides you through building and programming a voice-controlled robot based on a Raspberry Pi Zero. It utilizes the DFRobot IO Expansion HAT, various sensors and actuators (servos, I2S microphone, ultrasonic sensor, buzzer), and Google's Gemini AI for natural language processing. The robot can be controlled via a web interface (controller buttons or browser microphone) or by speaking directly to its onboard microphone.

---

## Table of Contents

*   [Part 1: English Tutorial](#part-1-english-tutorial)
    *   [1. Introduction](#1-introduction)
    *   [2. Hardware Requirements](#2-hardware-requirements)
    *   [3. Hardware Assembly](#3-hardware-assembly)
    *   [4. Software Setup on Raspberry Pi](#4-software-setup-on-raspberry-pi)
    *   [4.A. How to Get a Google Gemini API Key](#4a-how-to-get-a-google-gemini-api-key)
    *   [5. Code Setup](#5-code-setup)
    *   [6. Configuration](#6-configuration)
    *   [7. Running the Application](#7-running-the-application)
    *   [8. Using the Interface](#8-using-the-interface)
    *   [9. Troubleshooting](#9-troubleshooting)
    *   [10. Stopping the Application](#10-stopping-the-application)
*   [Part 2: Japanese Tutorial (日本語チュートリアル)](#part-2-japanese-tutorial-日本語チュートリアル)
    *   [1. はじめに (Introduction)](#1-はじめに-introduction-jp)
    *   [2. 必要なハードウェア (Hardware Requirements)](#2-必要なハードウェア-hardware-requirements-jp)
    *   [3. ハードウェアの組み立て (Hardware Assembly)](#3-ハードウェアの組み立て-hardware-assembly-jp)
    *   [4. Raspberry Pi のソフトウェアセットアップ (Software Setup on Raspberry Pi)](#4-raspberry-pi-のソフトウェアセットアップ-software-setup-on-raspberry-pi-jp)
    *   [4.A. Google Gemini APIキーの取得方法 (How to Get a Google Gemini API Key)](#4a-google-gemini-apiキーの取得方法-how-to-get-a-google-gemini-api-key-jp)
    *   [5. コードのセットアップ (Code Setup)](#5-コードのセットアップ-code-setup-jp)
    *   [6. 設定 (Configuration)](#6-設定-configuration-jp)
    *   [7. アプリケーションの実行 (Running the Application)](#7-アプリケーションの実行-running-the-application-jp)
    *   [8. インターフェースの使用方法 (Using the Interface)](#8-インターフェースの使用方法-using-the-interface-jp)
    *   [9. トラブルシューティング (Troubleshooting)](#9-トラブルシューティング-troubleshooting-jp)
    *   [10. アプリケーションの停止 (Stopping the Application)](#10-アプリケーションの停止-stopping-the-application-jp)

---

## Part 1: English Tutorial

### 1. Introduction

This project creates an interactive robot controllable via natural language commands. It integrates movement, sound feedback, basic obstacle detection, and AI-powered command interpretation using Google Gemini. You'll assemble the hardware, set up the Raspberry Pi environment, configure the code, and run a web server to interact with the robot.

### 2. Hardware Requirements

*   **Raspberry Pi Zero:** W or WH model recommended for built-in WiFi/Bluetooth.
*   **Micro SD Card:** 16GB+ recommended (due to swap usage during setup), Class 10, flashed with Raspberry Pi OS.
*   **Power Supply:** Stable 5V, >= 2.5A micro USB power supply. **Crucial for stability during compilation!**
*   **DFRobot IO Expansion HAT for Raspberry Pi Zero:** Compatible with Raspberry Pi Zero GPIO layout.
*   **INMP441 I2S Microphone Module:** For onboard voice input (Note: This tutorial primarily focuses on browser microphone input via the web UI. Integrating the INMP441 for direct robot voice input would be an advanced extension).
*   **HC-SR04 Ultrasonic Distance Sensor:** For obstacle detection.
*   **Active Buzzer Module:** For audio feedback sounds.
*   **SG90 Servos (x4):** Standard hobby servos (or adjust code for different servos).
*   **Robot Chassis/Frame:** Suitable for mounting the components and allowing servo movement.
*   **Jumper Wires:** Assorted Female-to-Female (F/F) and Male-to-Female (M/F).
*   **Computer:** For initial setup and accessing the web UI.
*   **(Optional):** USB Keyboard, Mouse, HDMI Monitor/Adapter for non-headless setup.

### 3. Hardware Assembly

**⚠️ IMPORTANT: Always disconnect the power supply from the Raspberry Pi before connecting or disconnecting any components!**

1.  **Mount HAT:** Carefully align the DFRobot IO Expansion HAT onto the Raspberry Pi Zero's 40-pin GPIO header and press down firmly and evenly.
2.  **Connect Servos:**
    *   Connect the 4 servos to the dedicated servo ports on the Expansion HAT (usually marked S0-S3 or similar).
    *   Ensure correct polarity: Signal (usually Yellow/Orange), VCC/+ (Red), GND/- (Brown/Black).
    *   Note which physical servo corresponds to which port number (0-3). The default code assumes:
        *   Servo 0: Right Leg/Hip
        *   Servo 1: Left Leg/Hip
        *   Servo 2: Right Foot/Ankle
        *   Servo 3: Left Foot/Ankle
3.  **Connect I2S Microphone (INMP441) - Optional for current UI focus:**
    *   *(This step is for future expansion if you wish to use the onboard mic directly with a script like `Ninja_Voice_Control.py`. The current web interface primarily uses the browser's microphone.)*
    *   Use jumper wires to connect the module to the HAT's GPIO breakout pins (refer to HAT documentation for pin mapping).
    *   `VDD` -> HAT `3.3V`
    *   `GND` -> HAT `GND`
    *   `SCK` -> HAT `GPIO 18` (I2S BCLK)
    *   `WS` -> HAT `GPIO 19` (I2S LRCLK/FS)
    *   `SD` -> HAT `GPIO 20` (I2S DIN / Data Out from Mic)
    *   `L/R` -> HAT `GND` (Selects Left channel for mono processing)
4.  **Connect Ultrasonic Sensor (HC-SR04):**
    *   Connect to the HAT's GPIO breakout pins.
    *   `VCC` -> HAT `5V` (Check sensor datasheet; some may work on 3.3V)
    *   `Trig` -> HAT `GPIO 21`
    *   `Echo` -> HAT `GPIO 22`
    *   `GND` -> HAT `GND`
5.  **Connect Buzzer:**
    *   Connect to the HAT's GPIO breakout pins.
    *   `Signal/IO` -> HAT `GPIO 23`
    *   `VCC/+` -> HAT `3.3V` (or `5V` depending on module)
    *   `GND/-` -> HAT `GND`
6.  **Assemble Robot:** Mount the Pi/HAT assembly, servos, sensor, and buzzer onto your robot chassis. Organize wiring to prevent snags during movement.

### 4. Software Setup on Raspberry Pi

This section involves steps that can take a **very long time** on a Raspberry Pi Zero, especially installing Rust and Python packages. Ensure a stable power supply and be patient.

1.  **Install OS:** Use Raspberry Pi Imager to flash Raspberry Pi OS (Lite or Desktop, **32-bit recommended** for Pi Zero compatibility and performance) onto the SD card. Use the advanced options (⚙️ icon) to pre-configure hostname, enable SSH, set user/password, and configure WiFi.

2.  **First Boot & Connect:**
    Insert SD card, connect power. Wait a few minutes for the first boot. Connect via SSH from your computer (`ssh your_username@your_pi_hostname.local` or `ssh your_username@<PI_IP_ADDRESS>`).

    *   **SSH Connection Issue Troubleshooting (Man-in-the-middle warning):**
        If you encounter an error like "IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!" or "REMOTE HOST IDENTIFICATION HAS CHANGED", it usually means the Pi's SSH key has changed (e.g., after an OS reinstall) and your computer remembers the old one.
        *   **Option 1 (Recommended for specific IP):** Remove the old key for the specific IP address from your `known_hosts` file. On your computer (not the Pi), run:
            ```bash
            ssh-keygen -R <PI_IP_ADDRESS>
            # Example: ssh-keygen -R 192.168.1.101
            ```
        *   **Option 2 (Manual Edit - Advanced):** Manually edit your `known_hosts` file. On your computer, open the file (path depends on your OS, typically `~/.ssh/known_hosts` for Linux/macOS, or `%USERPROFILE%\.ssh\known_hosts` on Windows). Find and delete the line corresponding to your Pi's IP address or hostname.
        *   After resolving, try connecting via SSH again.

3.  **System Update & Essential Tools:** Bring the OS and packages up to date and install `curl` and `git`:
    ```bash
    sudo apt update
    sudo apt full-upgrade -y
    sudo apt install -y curl git
    sudo reboot
    ```
    *(Reconnect via SSH after reboot)*

4.  **Enable I2S Interface (for Microphone - if using onboard mic in future):**
    *   Edit the boot configuration file:
        ```bash
        sudo nano /boot/firmware/config.txt # For newer Pi OS (Bookworm onwards)
        # If the above file doesn't exist, try:
        # sudo nano /boot/config.txt       # For older Pi OS (Bullseye or earlier)
        ```
    *   Add these lines at the very end:
        ```text
        # Enable I2S audio interface for Microphone
        dtparam=i2s=on
        dtoverlay=googlevoicehat-soundcard
        ```
    *   Save (`Ctrl+X`, `Y`, `Enter`) and reboot:
        ```bash
        sudo reboot
        ```
    *(Reconnect via SSH after reboot)*

5.  **Enable I2C Interface (for HAT Communication):**
    *   Use the Raspberry Pi Configuration tool:
        ```bash
        sudo raspi-config
        ```
    *   Navigate to `Interface Options` -> `I2C`.
    *   Select `<Yes>` to enable the I2C interface, then `<Ok>`.
    *   If prompted to reboot, select `<Yes>`. Otherwise, exit `raspi-config` and reboot manually:
        ```bash
        sudo reboot
        ```
    *(Reconnect via SSH after reboot)*

6.  **Install Core System Dependencies:** Install libraries needed for Python, audio processing, and I2C communication:
    ```bash
    sudo apt install -y python3-dev python3-pip python3-venv build-essential libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg flac libatlas-base-dev python3-smbus
    ```

7.  **Install/Update Rust Compiler:**
    Some Python libraries (like `pydantic-core`, a dependency for `google-generativeai`) require a Rust compiler. We'll use `rustup` to install the latest version.
    **This step will take a considerable amount of time (30 mins to 1+ hour).**
    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```
    *   When prompted, choose `1) Proceed with installation (default)`.
    *   After installation, configure your current shell:
        ```bash
        source "$HOME/.cargo/env"
        ```
    *   To make it permanent for future sessions, add it to your `.bashrc`:
        ```bash
        echo 'source "$HOME/.cargo/env"' >> ~/.bashrc
        ```
    *   Verify the installation (close and reopen terminal, or `source ~/.bashrc`):
        ```bash
        rustc --version
        cargo --version
        ```
        You should see version numbers (e.g., `rustc 1.7X.X ...`).

8.  **Configure Swap Space (Crucial for Pi Zero):**
    Compiling some Python packages (especially those with Rust components) is memory-intensive and can fail on the Pi Zero's limited RAM. We'll temporarily increase swap space.
    ```bash
    echo "CONF_SWAPSIZE=1024" | sudo tee /etc/dphys-swapfile # Sets swap to 1GB
    # For 2GB swap (if your SD card is large enough and you encounter issues with 1GB):
    # echo "CONF_SWAPSIZE=2048" | sudo tee /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    ```
    *   Verify swap (look for total swap around 1G or 2G):
        ```bash
        free -h
        ```
9. **Create Project Directory & Virtual Environment:**
    ```bash
    mkdir ~/NinjaRobot # Or your preferred project name
    cd ~/NinjaRobot
    python -m venv .venv # Create virtual environment named .venv
    source .venv/bin/activate # Activate the environment
    ```
    *(Your terminal prompt should now start with `(.foldernane)`)*

10. **Install Python Libraries (including `smbus2` for DFRobot HAT):**
    With Rust, swap, and system dependencies configured, we can now install the Python packages.
    `smbus2` is a Python module used for I2C communication, often required by HAT libraries like the DFRobot one.
    **This entire step will take a very long time (potentially 1-2+ hours) due to compilation on the Pi Zero.** Be patient.
    ```bash
    pip install --upgrade pip
    pip install smbus smbus2 # For I2C communication, important for DFRobot HAT. Try smbus if smbus2 does not work
    pip install RPi.GPIO google-generativeai SpeechRecognition gTTS pygame Flask google-cloud-speech
    ```
    *   **Note on PyAudio:** If `SpeechRecognition` or `google-cloud-speech` later complains about PyAudio, and the `apt` packages in step 4.6 didn't cover it, you might need to install it explicitly:
        `pip install pyaudio` (ensure system dependencies from step 4.6 are installed first).

11. **Revert Swap Space (Optional but Recommended):**
    After the intensive compilation is done, you can revert swap to a smaller default to reduce SD card wear.
    ```bash
    echo "CONF_SWAPSIZE=100" | sudo tee /etc/dphys-swapfile # Sets swap back to 100MB (default)
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    # You might need to reboot for changes to fully apply or if errors occur.
    # sudo reboot
    ```

### 4.A. How to Get a Google Gemini API Key

To use Google Gemini for natural language processing, you'll need an API key. The easiest way for personal projects is through Google AI Studio.

1.  **Go to Google AI Studio:**
    Open your web browser and navigate to [https://aistudio.google.com/](https://aistudio.google.com/).
2.  **Sign In:**
    Sign in with your Google account.
3.  **Agree to Terms:**
    You may need to agree to the terms of service if it's your first time.
4.  **Get API Key:**
    *   Once in AI Studio, look for a button or link that says **"Get API key"** (often on the left sidebar or a prominent button).
    *   Click on it. You might be taken to a new page or a dialog will appear.
5.  **Create API Key in a New Project:**
    *   You'll likely be prompted to **"Create API key in new project"** or associate it with an existing Google Cloud project. For simplicity, creating one in a new project via AI Studio is straightforward for this tutorial.
    *   Click the button to create the key.
6.  **Copy Your API Key:**
    Your new API key will be displayed. It's a long string of letters and numbers.
    *   **Copy this key immediately and save it somewhere secure and private.** You will need it for the robot's configuration (Step 6.1).
    *   **Treat this key like a password.** Do not share it publicly or commit it to public code repositories.
7.  **Done:**
    You now have a Gemini API key. The free tier is usually generous enough for development and personal use, but be aware of usage limits. For more extensive use or production applications, you'd manage billing through Google Cloud Platform.

    *You will use this API key in the "Configuration" section (Step 6.1) of this tutorial.*

### 5. Code Setup

1.  **Download/Copy Code Files:** Ensure you are in your project directory (`~/NinjaRobot`). Place the following Python files into this directory. You can typically download these from the project's GitHub repository.
    *   `Ninja_Movements_v1.py`
    *   `Ninja_Buzzer.py`
    *   `Ninja_Distance.py`
    *   `ninja_core.py`
    *   `Ninja_Gemini_v1.py` (or the script you are using as the main entry point for text-based voice control, if different)
    *   `web_interface.py` (The Flask web server)
    *   `DFRobot_RaspberryPi_Expansion_Board.py`
        *   **Important Note:** `DFRobot_RaspberryPi_Expansion_Board.py` is a local library file specific to this DFRobot HAT. Ensure this file is downloaded from the project repository and placed directly in your `~/NinjaRobot/` project folder. It is **not** installed via `pip`. If you are using a different HAT (e.g., a generic PCA9685-based board), you will need different libraries and code adjustments.

2.  **Create `templates` Directory:** Inside the project directory (`~/NinjaRobot`):
    ```bash
    mkdir templates
    ```
3.  **Create `index.html`:** Create the file `index.html` inside the `templates` directory. Paste the HTML/CSS/JavaScript code for the web interface (as provided in previous steps, with the two Mic buttons) into this file.

### 6. Configuration

1.  **Google Gemini API Key in `ninja_core.py` (and `Ninja_Gemini_v1.py` if using directly):**
    *   Activate your virtual environment if not already active:
        ```bash
        cd ~/NinjaRobot
        source .venv/bin/activate
        ```
    *   Edit `nano ninja_core.py`.
    *   Locate the line: `GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"` (or similar placeholder).
    *   Replace the placeholder with your actual key obtained in **Step 4.A**.
    *   **If you are also running `Ninja_Gemini_v1.py` directly for testing, update the API key there as well.**
    *   **IMPORTANT:** Keep your API key secure.
    *   Save the file(s).
2.  **(Optional) Robot Mic Sensitivity Tuning (If using `Ninja_Voice_Control.py` for onboard mic):**
    *   *(This section is for advanced users extending the project to use the physical INMP441 mic directly with a script like `Ninja_Voice_Control.py`. The web interface uses the browser's mic.)*
    *   If that script has trouble hearing or triggers on noise, edit `Ninja_Voice_Control.py`.
    *   Find `recognizer.energy_threshold = 500`. Adjust as needed.

### 7. Running the Application

1.  **Activate Environment:** Navigate to your project directory and activate the virtual environment:
    ```bash
    cd ~/NinjaRobot
    source .venv/bin/activate
    ```
2.  **Find Pi's IP Address:**
    ```bash
    hostname -I | awk '{print $1}'
    ```
    *(Note the IP address shown, e.g., 192.168.1.XX)*
3.  **Start the Web Server:**
    ```bash
    python3 web_interface.py
    ```
    *(Look for lines indicating it's running on `http://0.0.0.0:5000`)*
4.  **Access Web Interface:** On another device (phone, computer) on the **same WiFi network**, open a web browser and go to:
    `http://<YOUR_PI_IP_ADDRESS>:5000`
    *(Replace `<YOUR_PI_IP_ADDRESS>` with the actual IP)*

### 8. Using the Interface

The web interface provides several ways to control your Ninja robot:

*   **D-Pad:**
    *   **Up/Down/Left/Right:** Controls robot movement. The exact action (e.g., walk vs. run, step turn vs. rotate) depends on the currently selected "Mode" (Walk/Run).
*   **Center Buttons:**
    *   **Walk / Run:** Selects the movement mode for the D-Pad. The active mode button will be highlighted.
    *   **Stop:** Stops any ongoing robot movement.
    *   **Rest:** Commands the robot to go into its resting pose.
    *   **Mic (EN):** Click to activate voice recognition using your browser's microphone for **English** commands. Speak after the button changes to "Listening...". The robot will attempt to interpret commands prefixed with "Ninja". Other phrases will be treated as general questions for Gemini to answer.
    *   **Mic (JP):** Click to activate voice recognition using your browser's microphone for **Japanese** commands. Speak after the button changes to "聞いています..." (Listening...). The robot will attempt to interpret commands prefixed with "忍者" (or "ニンジャ", "にんじゃ"). Other phrases will be treated as general questions.
*   **Action Buttons (Right Side - Y, X, B, A):**
    *   **Y:** Sets robot speed to "Fast".
    *   **X:** Sets robot speed to "Normal".
    *   **A:** Sets robot speed to "Slow".
    *   **B:** Triggers the "Hello" action (robot waves/wiggles).
*   **Status Area:**
    *   Displays the current robot state (e.g., Idle, Moving), selected mode and speed, the last command sent, and the interpretation or conversational response from Google Gemini.

### 9. Troubleshooting

*   **`ModuleNotFoundError: No module named 'smbus'` or `'smbus2'`:** Ensure I2C is enabled (step 4.5), `python3-smbus` was installed via `apt` (step 4.6), AND `smbus2` was installed via `pip` in your virtual environment (step 4.10).
*   **`ImportError: DFRobot_RaspberryPi_Expansion_Board` or similar:** Ensure the `DFRobot_RaspberryPi_Expansion_Board.py` file is in your `~/NinjaRobot` directory (see step 5.1 note).
*   **Other Python Errors (`NameError`, `ImportError`):** Ensure all libraries from step 4.10 are installed in the active virtual environment (`.venv`). Check file locations within `~/NinjaRobot`.
*   **`pydantic-core` build error / Rust related:** Ensure Rust was installed correctly (step 4.7) and that swap was active during `pip install` (step 4.8). If it persists, check `rustc --version`. You may need to clean pip's cache (`pip cache purge`) and try installing `pydantic-core` by itself (`pip install pydantic-core`) with more swap.
*   **Out of Memory / SIGKILL:** This is likely due to insufficient swap during compilation (steps 4.8 and 4.10). Ensure swap was configured correctly. Try with even more swap (e.g., 2GB if your SD card allows).
*   **Hardware/Core Init Failures:** Review hardware connections (Step 3). Check `web_interface.py` or `ninja_core.py` console output for errors during startup (e.g., I2C address issues for the HAT, API key problems).
*   **Voice Recognition Issues (Browser Mic):**
    *   Ensure your browser has permission to access the microphone.
    *   Check your computer's microphone settings.
    *   A stable internet connection is required for Web Speech API and Gemini.
    *   If using HTTPS, ensure your certificate is valid. Some browsers restrict mic access on insecure HTTP, though localhost is often an exception.
*   **Gemini Errors / "Could not parse AI response":**
    *   Verify your API Key is correct in `ninja_core.py` (and other relevant scripts) and that the Gemini API is enabled in your Google Cloud project associated with the key.
    *   Check the console output from `web_interface.py` or `ninja_core.py` for more detailed error messages from the Gemini API.
    *   Ensure the `GEMINI_MODEL_NAME` in `ninja_core.py` is a valid and accessible model for your API key.
*   **Robot Movement Issues:** Verify servo connections (Step 3.2). Check angles in `Ninja_Movements_v1.py`. Ensure adequate power supply.
*   **Web Interface Unresponsive:** Ensure Flask server (`web_interface.py`) is running on the Pi. Check Pi's IP address and network connection. Check browser console (usually F12) for JavaScript errors.

### 10. Stopping the Application

*   Go to the terminal running `web_interface.py`.
*   Press `Ctrl+C`.
*   The `atexit` cleanup function in `web_interface.py` (which calls `ninja_core.cleanup_all()`) should automatically:
    *   Stop any ongoing movement.
    *   Command the robot to its resting pose.
    *   Play a "sleepy" sound.
    *   Release GPIO resources.

---
---

## Part 2: Japanese Tutorial (日本語チュートリアル)

### 1. はじめに (Introduction) {#1-はじめに-introduction-jp}

このプロジェクトでは、自然言語コマンドで制御可能なインタラクティブ・ロボットを作成します。移動、サウンドフィードバック、基本的な障害物検出、そしてGoogle Geminiを使用したAIによるコマンド解釈を統合します。ハードウェアの組み立て、Raspberry Pi環境のセットアップ、コードの設定、そしてロボットと対話するためのウェブサーバーの実行を行います。

### 2. 必要なハードウェア (Hardware Requirements) {#2-必要なハードウェア-hardware-requirements-jp}

*   **Raspberry Pi Zero:** WiFi/Bluetooth内蔵のWまたはWHモデル推奨。
*   **Micro SDカード:** 16GB以上推奨（セットアップ時のスワップ使用のため）、Class 10、Raspberry Pi OS書き込み済み。
*   **電源:** 安定した5V、2.5A以上のmicro USB電源。**コンパイル中の安定性のために非常に重要です！**
*   **DFRobot IO Expansion HAT for Raspberry Pi Zero:** Raspberry Pi Zero GPIOレイアウト互換のもの。
*   **INMP441 I2S マイクモジュール:** オンボード音声入力用（注意：このチュートリアルは主にWeb UI経由のブラウザマイク入力に焦点を当てています。INMP441を直接使用するのは高度な拡張となります）。
*   **HC-SR04 超音波距離センサー:** 障害物検出用。
*   **アクティブブザーモジュール:** 音声フィードバック用。
*   **SG90 サーボ (x4):** 標準的なホビーサーボ（異なる場合はコード調整）。
*   **ロボットシャーシ/フレーム:** コンポーネント搭載とサーボ動作に適したもの。
*   **ジャンパーワイヤー:** メス-メス(F/F)およびオス-メス(M/F)各種。
*   **コンピュータ:** 初期設定およびWeb UIアクセス用。
*   **(オプション):** USBキーボード、マウス、HDMIモニター/アダプター（ヘッドレスでない場合）。

### 3. ハードウェアの組み立て (Hardware Assembly) {#3-ハードウェアの組み立て-hardware-assembly-jp}

**⚠️ 重要: 部品の接続・切断前には、必ずRaspberry Piの電源を切断してください！**

1.  **HATの取り付け:** DFRobot IO Expansion HATをPi Zeroの40ピンGPIOヘッダーに慎重に合わせ、均等にしっかりと押し込みます。
2.  **サーボの接続:**
    *   4つのサーボをHATのサーボポート（S0-S3等）に接続します。
    *   極性（信号：黄/橙、VCC/+：赤、GND/-：茶/黒）に注意。
    *   どの物理サーボがどのポート番号（0-3）に対応するかメモします。デフォルトコードの想定：
        *   Servo 0: 右脚/股関節
        *   Servo 1: 左脚/股関節
        *   Servo 2: 右足/足首
        *   Servo 3: 左足/足首
3.  **I2Sマイク(INMP441)の接続 - 現在のUIではオプション:**
    *   *(このステップは、将来的にオンボードマイクを`Ninja_Voice_Control.py`のようなスクリプトで直接使用する場合の拡張用です。現在のWebインターフェースは主にブラウザのマイクを使用します。)*
    *   ジャンパー線でモジュールをHATのGPIOブレイクアウトピンに接続（HAT資料参照）。
    *   `VDD` -> HAT `3.3V`
    *   `GND` -> HAT `GND`
    *   `SCK` -> HAT `GPIO 18` (I2S BCLK)
    *   `WS` -> HAT `GPIO 19` (I2S LRCLK/FS)
    *   `SD` -> HAT `GPIO 20` (I2S DIN / マイクからのデータ出力)
    *   `L/R` -> HAT `GND` (左チャンネル選択)
4.  **超音波センサー(HC-SR04)の接続:**
    *   HATのGPIOブレイクアウトピンに接続。
    *   `VCC` -> HAT `5V` (センサーによっては3.3V可 - データシート確認)
    *   `Trig` -> HAT `GPIO 21`
    *   `Echo` -> HAT `GPIO 22`
    *   `GND` -> HAT `GND`
5.  **ブザーの接続:**
    *   HATのGPIOブレイクアウトピンに接続。
    *   `Signal/IO` -> HAT `GPIO 23`
    *   `VCC/+` -> HAT `3.3V` (または `5V`)
    *   `GND/-` -> HAT `GND`
6.  **ロボットの組み立て:** Pi/HAT、サーボ、センサー、ブザーをシャーシに取り付けます。配線が動作を妨げないように整理します。

### 4. Raspberry Pi のソフトウェアセットアップ (Software Setup on Raspberry Pi) {#4-raspberry-pi-のソフトウェアセットアップ-software-setup-on-raspberry-pi-jp}

このセクションには、Raspberry Pi Zeroでは**非常に時間のかかる**手順が含まれています（特にRustのインストールとPythonパッケージのインストール）。安定した電源を確保し、辛抱強く作業してください。

1.  **OSのインストール:** Raspberry Pi ImagerでRaspberry Pi OS (LiteまたはDesktop、Pi Zeroの互換性とパフォーマンスのため**32-bit推奨**) をSDカードに書き込みます。詳細オプション(⚙️)でホスト名、SSH有効化、ユーザー/パスワード、WiFiを設定します。

2.  **初回起動と接続:**
    SDカードを挿入し電源接続。数分待って起動後、SSHで接続 (`ssh <ユーザー名>@<ホスト名>.local` または `ssh <ユーザー名>@<IPアドレス>`)。

    *   **SSH接続問題のトラブルシューティング (中間者攻撃の警告):**
        「IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!」や「REMOTE HOST IDENTIFICATION HAS CHANGED」のようなエラーが表示された場合、通常はPiのSSHキーが変更された（例：OS再インストール後など）が、お使いのコンピュータが古いキーを記憶していることが原因です。
        *   **オプション1 (特定のIPアドレスに推奨):** お使いのコンピュータ（Piではありません）で、`known_hosts` ファイルから特定のIPアドレスの古いキーを削除します。
            ```bash
            ssh-keygen -R <PiのIPアドレス>
            # 例: ssh-keygen -R 192.168.1.101
            ```
        *   **オプション2 (手動編集 - 上級者向け):** お使いのコンピュータで `known_hosts` ファイルを手動で編集します。ファイルを開き（OSによってパスは異なりますが、Linux/macOSでは通常 `~/.ssh/known_hosts`、Windowsでは `%USERPROFILE%\.ssh\known_hosts`）、PiのIPアドレスまたはホスト名に対応する行を見つけて削除します。
        *   解決後、再度SSHで接続してみてください。

3.  **システムアップデートと必須ツール:** OSとパッケージを最新化し、`curl` と `git` をインストールします：
    ```bash
    sudo apt update
    sudo apt full-upgrade -y
    sudo apt install -y curl git
    sudo reboot
    ```
    *(再起動後、SSH再接続)*

4.  **I2Sインターフェースの有効化 (マイク用 - 将来オンボードマイクを使用する場合):**
    *   ブート設定ファイルを編集：
        ```bash
        sudo nano /boot/firmware/config.txt # 新しいPi OS (Bookworm以降) の場合
        # 上記ファイルが存在しない場合:
        # sudo nano /boot/config.txt       # 古いPi OS (Bullseye以前) の場合
        ```
    *   ファイルの末尾に以下を追加：
        ```text
        # Enable I2S audio interface for Microphone
        dtparam=i2s=on
        dtoverlay=googlevoicehat-soundcard
        ```
    *   保存 (`Ctrl+X`, `Y`, `Enter`) して再起動：
        ```bash
        sudo reboot
        ```
    *(再起動後、SSH再接続)*

5.  **I2Cインターフェースの有効化 (HAT通信用):**
    *   Raspberry Pi 設定ツールを使用：
        ```bash
        sudo raspi-config
        ```
    *   `Interface Options` -> `I2C` に移動します。
    *   `<Yes>` を選択してI2Cインターフェースを有効にし、`<Ok>` を選択します。
    *   再起動を促されたら `<Yes>` を選択します。そうでない場合は `raspi-config` を終了し、手動で再起動します：
        ```bash
        sudo reboot
        ```
    *(再起動後、SSH再接続)*

6.  **コアシステム依存関係のインストール:** Python、オーディオ処理、I2C通信に必要なライブラリをインストール：
    ```bash
    sudo apt install -y python3-dev python3-pip python3-venv build-essential libasound2-dev portaudio19-dev libportaudio2 libportaudiocpp0 ffmpeg flac libatlas-base-dev python3-smbus
    ```

7.  **Rustコンパイラのインストール/アップデート:**
    一部のPythonライブラリ（`google-generativeai`の依存関係である`pydantic-core`など）はRustコンパイラを必要とします。`rustup`を使用して最新バージョンをインストールします。
    **このステップにはかなりの時間がかかります（30分～1時間以上）。**
    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```
    *   プロンプトが表示されたら、`1) Proceed with installation (default)` を選択します。
    *   インストール後、現在のシェルを設定します：
        ```bash
        source "$HOME/.cargo/env"
        ```
    *   将来のセッションのために永続化するには、`.bashrc` に追加します：
        ```bash
        echo 'source "$HOME/.cargo/env"' >> ~/.bashrc
        ```
    *   インストールを確認します（ターミナルを閉じて再度開くか、`source ~/.bashrc` を実行）：
        ```bash
        rustc --version
        cargo --version
        ```
        バージョン番号（例：`rustc 1.7X.X ...`）が表示されるはずです。

8.  **スワップ領域の設定 (Pi Zeroでは非常に重要):**
    一部のPythonパッケージ（特にRustコンポーネントを含むもの）のコンパイルはメモリを大量に消費し、Pi Zeroの限られたRAMでは失敗する可能性があります。一時的にスワップ領域を増やします。
    ```bash
    echo "CONF_SWAPSIZE=1024" | sudo tee /etc/dphys-swapfile # スワップを1GBに設定
    # 2GBスワップの場合 (SDカードの容量が十分で、1GBで問題が発生する場合):
    # echo "CONF_SWAPSIZE=2048" | sudo tee /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    ```
    *   スワップを確認します（合計スワップが1Gまたは2G程度になっているか）：
        ```bash
        free -h
        ```
9. **プロジェクトディレクトリと仮想環境の作成:**
    ```bash
    mkdir ~/NinjaRobot # または好きなプロジェクト名
    cd ~/NinjaRobot
    python -m venv .venv # 仮想環境作成
    source .venv/bin/activate # 環境を有効化
    ```
    *(ターミナルプロンプトの先頭に `(.venv)` が表示されます)*

10. **Pythonライブラリのインストール (DFRobot HAT用の `smbus2` を含む):**
    Rust、スワップ、およびシステム依存関係を設定したので、Pythonパッケージをインストールできます。
    `smbus2` はI2C通信に使用されるPythonモジュールで、DFRobotのようなHATライブラリでしばしば必要とされます。
    **このステップ全体はPi Zeroでのコンパイルのため非常に時間がかかります（1～2時間以上かかる可能性があります）。** 辛抱強く待ってください。
    ```bash
    pip install --upgrade pip
    pip install smbus2 # I2C通信用、DFRobot HATに重要. smbus2が使えなければ、smbusを試してください
    pip install RPi.GPIO google-generativeai SpeechRecognition gTTS pygame Flask google-cloud-speech
    ```
    *   **PyAudioに関する注意:** もし後で `SpeechRecognition` や `google-cloud-speech` がPyAudioについてエラーを出す場合で、ステップ4.6の `apt` パッケージでカバーされていなかった場合は、明示的にインストールする必要があるかもしれません：
        `pip install pyaudio` （まずステップ4.6のシステム依存関係がインストールされていることを確認してください）。

11. **スワップ領域の復元 (任意だが推奨):**
    集中的なコンパイルが完了したら、SDカードの消耗を減らすためにスワップをより小さなデフォルト値に戻すことができます。
    ```bash
    echo "CONF_SWAPSIZE=100" | sudo tee /etc/dphys-swapfile # スワップを100MB (デフォルト) に戻す
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    # 変更を完全に適用するため、またはエラーが発生した場合は再起動が必要な場合があります。
    # sudo reboot
    ```

### 4.A. Google Gemini APIキーの取得方法 (How to Get a Google Gemini API Key) {#4a-google-gemini-apiキーの取得方法-how-to-get-a-google-gemini-api-key-jp}

自然言語処理にGoogle Geminiを使用するには、APIキーが必要です。個人プロジェクトで最も簡単な方法は、Google AI Studio経由です。

1.  **Google AI Studioへ移動:**
    ウェブブラウザを開き、[https://aistudio.google.com/](https://aistudio.google.com/) にアクセスします。
2.  **サインイン:**
    お使いのGoogleアカウントでサインインします。
3.  **利用規約に同意:**
    初めて利用する場合は、利用規約への同意が必要になることがあります。
4.  **APIキーの取得:**
    *   AI Studioに入ったら、「**APIキーを取得**」（多くは左側のサイドバーまたは目立つボタンにあります）というボタンまたはリンクを探します。
    *   それをクリックします。新しいページに移動するか、ダイアログが表示される場合があります。
5.  **新しいプロジェクトでAPIキーを作成:**
    *   おそらく、「**新しいプロジェクトでAPIキーを作成**」するか、既存のGoogle Cloudプロジェクトに関連付けるよう求められます。このチュートリアルでは、AI Studio経由で新しいプロジェクトで作成するのが簡単です。
    *   ボタンをクリックしてキーを作成します。
6.  **APIキーをコピー:**
    新しいAPIキーが表示されます。これは長い文字列です。
    *   **このキーをすぐにコピーし、安全でプライベートな場所に保存してください。** ロボットの設定（ステップ6.1）で必要になります。
    *   **このキーはパスワードのように扱ってください。** 公開したり、公開コードリポジトリにコミットしたりしないでください。
7.  **完了:**
    これでGemini APIキーを取得できました。無料枠は通常、開発や個人利用には十分ですが、使用制限に注意してください。より広範な使用や本番アプリケーションの場合は、Google Cloud Platformを通じて請求を管理します。

    *このAPIキーは、本チュートリアルの「設定」(ステップ6.1)セクションで使用します。*

### 5. コードのセットアップ (Code Setup) {#5-コードのセットアップ-code-setup-jp}

1.  **コードファイルのダウンロード/コピー:** プロジェクトディレクトリ (`~/NinjaRobot`) にいることを確認してください。以下のPythonファイルをこのディレクトリに配置します。通常、これらはプロジェクトのGitHubリポジトリからダウンロードできます。
    *   `Ninja_Movements_v1.py`
    *   `Ninja_Buzzer.py`
    *   `Ninja_Distance.py`
    *   `ninja_core.py`
    *   `Ninja_Gemini_v1.py` (または、テキストベースの音声制御のメインエントリーポイントとして使用しているスクリプトが異なる場合)
    *   `web_interface.py` (Flask Webサーバー)
    *   `DFRobot_RaspberryPi_Expansion_Board.py`
        *   **重要事項:** `DFRobot_RaspberryPi_Expansion_Board.py` は、このDFRobot HATに固有のローカルライブラリファイルです。このファイルがプロジェクトリポジトリからダウンロードされ、`~/NinjaRobot/` プロジェクトフォルダに直接配置されていることを確認してください。これは `pip` ではインストールされません。異なるHAT（例：汎用のPCA9685ベースのボード）を使用している場合は、異なるライブラリとコードの調整が必要になります。

2.  **`templates` ディレクトリの作成:** プロジェクトディレクトリ内 (`~/NinjaRobot`)：
    ```bash
    mkdir templates
    ```
3.  **`index.html` の作成:** `templates` ディレクトリ内に `index.html` ファイルを作成し、Webインターフェース用のHTML/CSS/JavaScriptコード（以前のステップで提供された、2つのマイクボタンを持つバージョン）をペーストします。

### 6. 設定 (Configuration) {#6-設定-configuration-jp}

1.  **`ninja_core.py` 内のGoogle Gemini APIキー (および直接使用する場合は `Ninja_Gemini_v1.py` も):**
    *   仮想環境が有効でない場合は有効にします：
        ```bash
        cd ~/NinjaRobot
        source .venv/bin/activate
        ```
    *   `nano ninja_core.py` を編集します。
    *   `GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"` (または同様のプレースホルダー) の行を探します。
    *   プレースホルダーを**ステップ4.A**で取得した実際のキーに置き換えます。
    *   **`Ninja_Gemini_v1.py` を直接テストで使用している場合は、そちらのAPIキーも更新してください。**
    *   **重要:** APIキーは安全に保管してください。
    *   ファイルを保存します。
2.  **(オプション) Robot Mic 感度調整 (オンボードマイクで `Ninja_Voice_Control.py` を使用する場合):**
    *   *(このセクションは、物理的なINMP441マイクを`Ninja_Voice_Control.py`のようなスクリプトで直接使用するようにプロジェクトを拡張する上級ユーザー向けです。Webインターフェースはブラウザのマイクを使用します。)*
    *   そのスクリプトが聞き取りにくい、またはノイズで誤作動する場合は、`Ninja_Voice_Control.py`を編集します。
    *   `recognizer.energy_threshold = 500` を見つけて必要に応じて調整します。

### 7. アプリケーションの実行 (Running the Application) {#7-アプリケーションの実行-running-the-application-jp}

1.  **環境の有効化:** プロジェクトディレクトリに移動し、仮想環境を有効化：
    ```bash
    cd ~/NinjaRobot
    source .venv/bin/activate
    ```
2.  **PiのIPアドレス確認:**
    ```bash
    hostname -I | awk '{print $1}'
    ```
    *(表示されたIPアドレスをメモ)*
3.  **Webサーバーの起動:**
    ```bash
    python3 web_interface.py
    ```
    *(`http://0.0.0.0:5000` で実行中といったメッセージを確認)*
4.  **Webインターフェースへのアクセス:** （Piと同じWiFi上の）他のデバイスのブラウザで以下にアクセス：
    `http://<YOUR_PI_IP_ADDRESS>:5000`
    *( `<YOUR_PI_IP_ADDRESS>` を実際のIPに置換)*

### 8. インターフェースの使用方法 (Using the Interface) {#8-インターフェースの使用方法-using-the-interface-jp}

Webインターフェースは、Ninjaロボットを制御するためのいくつかの方法を提供します。

*   **D-Pad (十字キー):**
    *   **上/下/左/右:** ロボットの移動を制御します。正確なアクション（例：歩行対走行、ステップターン対回転）は、現在選択されている「モード」（Walk/Run）によって異なります。
*   **中央ボタン:**
    *   **Walk / Run:** D-Padの移動モードを選択します。アクティブなモードボタンが強調表示されます。
    *   **Stop:** 進行中のロボットの動きをすべて停止します。
    *   **Rest:** ロボットに休憩ポーズをとるよう命令します。
    *   **Mic (EN):** クリックすると、ブラウザのマイクを使用して**英語**のコマンドの音声認識を有効にします。ボタンが「Listening...」に変わったら話しかけてください。ロボットは「Ninja」で始まるコマンドを解釈しようとします。それ以外のフレーズは、Geminiが応答するための一般的な質問として扱われます。
    *   **Mic (JP):** クリックすると、ブラウザのマイクを使用して**日本語**のコマンドの音声認識を有効にします。ボタンが「聞いています...」に変わったら話しかけてください。ロボットは「忍者」（または「ニンジャ」、「にんじゃ」）で始まるコマンドを解釈しようとします。それ以外のフレーズは、一般的な質問として扱われます。
*   **アクションボタン (右側 - Y, X, B, A):**
    *   **Y:** ロボットの速度を「Fast」に設定します。
    *   **X:** ロボットの速度を「Normal」に設定します。
    *   **A:** ロボットの速度を「Slow」に設定します。
    *   **B:** 「Hello」アクション（ロボットが手を振る/身をくねらせる）をトリガーします。
*   **ステータスエリア:**
    *   現在のロボットの状態（例：アイドル、移動中）、選択されたモードと速度、最後に送信されたコマンド、Google Geminiからの解釈または会話応答を表示します。

### 9. トラブルシューティング (Troubleshooting) {#9-トラブルシューティング-troubleshooting-jp}

*   **`ModuleNotFoundError: No module named 'smbus'` または `'smbus2'`:** I2Cが有効になっているか（ステップ4.5）、`python3-smbus` が `apt` でインストールされているか（ステップ4.6）、かつ `smbus2` が仮想環境に `pip` でインストールされているか（ステップ4.10）を確認してください。
*   **`ImportError: DFRobot_RaspberryPi_Expansion_Board` など:** `DFRobot_RaspberryPi_Expansion_Board.py` ファイルが `~/NinjaRobot` ディレクトリにあるか確認してください（ステップ5.1の注意参照）。
*   **その他のPythonエラー (`NameError`, `ImportError`):** ステップ4.10のすべてのライブラリが有効な仮想環境 (`.venv`) にインストールされているか確認してください。`~/NinjaRobot` 内のファイル配置を確認してください。
*   **`pydantic-core` のビルドエラー / Rust関連:** Rustが正しくインストールされたか（ステップ4.7）、`pip install` 中にスワップが有効だったか（ステップ4.8）を確認。問題が続く場合は `rustc --version` を確認。pipのキャッシュをクリア (`pip cache purge`) し、より多くのスワップで `pydantic-core` 単体をインストール (`pip install pydantic-core`) してみる必要があるかもしれません。
*   **メモリ不足 / SIGKILL:** コンパイル中のスワップ不足が原因である可能性が高いです（ステップ4.8および4.10）。スワップが正しく設定されているか確認してください。さらに多くのスワップ（SDカードが許せば2GBなど）で試してみてください。
*   **ハードウェア/コア初期化失敗:** ハードウェア接続（ステップ3）を再確認。`web_interface.py` または `ninja_core.py` のコンソール出力で起動時のエラー（例：HATのI2Cアドレスの問題、APIキーの問題）を確認してください。
*   **音声認識問題 (ブラウザマイク):**
    *   ブラウザがマイクへのアクセス許可を持っていることを確認してください。
    *   コンピュータのマイク設定を確認してください。
    *   Web Speech APIとGeminiには安定したインターネット接続が必要です。
    *   HTTPSを使用している場合は、証明書が有効であることを確認してください。一部のブラウザは安全でないHTTPでのマイクアクセスを制限しますが、localhostはしばしば例外です。
*   **Geminiエラー / "Could not parse AI response":**
    *   `ninja_core.py`（および関連スクリプト）のAPIキーが正しいこと、およびキーに関連付けられたGoogle CloudプロジェクトでGemini APIが有効になっていることを確認してください。
    *   Gemini APIからの詳細なエラーメッセージについては、`web_interface.py` または `ninja_core.py` のコンソール出力を確認してください。
    *   `ninja_core.py` の `GEMINI_MODEL_NAME` が、APIキーに対して有効でアクセス可能なモデルであることを確認してください。
*   **ロボット動作問題:** サーボ接続確認（ステップ3.2）。`Ninja_Movements_v1.py` の角度定義確認。電源供給確認。
*   **Web UI無応答:** Flaskサーバー(`web_interface.py`)がPiで実行中か確認。IPアドレスとネットワーク接続確認。ブラウザコンソール（通常F12）でJavaScriptエラー確認。

### 10. アプリケーションの停止 (Stopping the Application) {#10-アプリケーションの停止-stopping-the-application-jp}

*   `web_interface.py` を実行しているターミナルで `Ctrl+C` を押します。
*   `web_interface.py` の `atexit` クリーンアップ関数（`ninja_core.cleanup_all()` を呼び出します）が自動的に以下を実行するはずです：
    *   進行中のすべての移動を停止します。
    *   ロボットを休憩ポーズに移行させます。
    *   「sleepy」サウンドを再生します。
    *   GPIOリソースを解放します。
