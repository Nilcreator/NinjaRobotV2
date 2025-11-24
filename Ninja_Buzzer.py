import RPi.GPIO as GPIO
import time
import random

# --- Configuration ---
BUZZER_PIN = 23  # BCM pin number (D25 on the HAT)

# Define note frequencies (Hz) - Ensure all needed notes are here
NOTES = {
    'C3': 131, 'D3': 147, 'E3': 165, 'F3': 175, 'G3': 196, 'A3': 220, 'B3': 247,
    'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 494,
    'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880, 'B5': 988,
    'C6': 1047,'D6': 1175,'E6': 1319,'F6': 1397,'G6': 1568,'A6': 1760,'B6': 1976,
    'C#6': 1109, 'A#5': 932, 'D#6': 1245, # Sharps for effects
    'C7': 2093, 'D7': 2349, 'G7': 3136,
    'REST': 0 # Represents a pause
}

# --- Sound Sequences & Definitions based on User Descriptions ---

# hello => Beep boop beep! (Mid-tone, Low-tone, Mid-tone)
SOUND_HELLO = [('C5', 0.12), ('REST', 0.05), ('G4', 0.18), ('REST', 0.05), ('C5', 0.12)]

# thanks => whirr beep (Simulate 'whirr' with a low tremble/buzz, then a clear beep)
# Let's use a mini-tremble effect directly in the sequence for simplicity
SOUND_THANKS = [
    ('A3', 0.05), ('B3', 0.05), ('A3', 0.05), ('B3', 0.05), ('A3', 0.05), # Low 'whirr'
    ('REST', 0.08),
    ('E5', 0.18) # Clear 'beep'
]

# no => noo (Lower pitch, falling tone)
SOUND_NO = [('G4', 0.15), ('E4', 0.15), ('C4', 0.3)] # Descending, drawn out slightly

# yes => beep (Simple, clear, mid-high tone)
SOUND_YES = [('E5', 0.15)] # Single clear beep

# danger => beep beeep (with higher tone) (Short beep, then longer higher beep)
SOUND_DANGER = [('C5', 0.1), ('REST', 0.06), ('A5', 0.35)] # Higher and longer second beep

# exciting => brrrr bzzz (with higher tone) - Needs special function for high trill/buzz
SOUND_EXCITING_IDENTIFIER = "play_exciting_trill"

# happy => sing a song (Short cheerful melody - e.g., major scale fragment)
SOUND_HAPPY = [
    ('C5', 0.12), ('D5', 0.12), ('E5', 0.12), ('F5', 0.12), ('G5', 0.20), ('E5', 0.15), ('C5', 0.15)
] # Simple ascending/descending tune

# turn right => zzzz brr (Sustained mid buzz, then lower shorter buzz)
SOUND_TURN_RIGHT = [('A4', 0.3), ('REST', 0.08), ('D4', 0.18)] # Mid sustained, short low

# turn left => beep brrap (Clear beep, then short sharp lower sound/fall)
SOUND_TURN_LEFT = [('G5', 0.1), ('REST', 0.06), ('D4', 0.08), ('B3', 0.12)] # High beep, sharp low fall


# --- Include other sounds if needed, or keep the list focused ---
SOUND_SCARED_IDENTIFIER = "play_scared_function" # Keep existing special function if desired
# SOUND_SLEEPY = ... (add back if needed)
# SOUND_DANGER = ... (add back if needed)
# ... etc

# --- Map input words (lowercase) to the NEW sound sequences/identifiers ---
SOUND_MAP = {
    "hello": SOUND_HELLO,
    "thanks": SOUND_THANKS,
    "thank you": SOUND_THANKS,
    "no": SOUND_NO,
    "yes": SOUND_YES,
    "danger": SOUND_DANGER, # Synonym
    "exciting": SOUND_EXCITING_IDENTIFIER,
    "happy": SOUND_HAPPY,
    "right": SOUND_TURN_RIGHT,
    "turn right": SOUND_TURN_RIGHT,
    "left": SOUND_TURN_LEFT,
    "turn left": SOUND_TURN_LEFT,

    # Add back other sounds as needed
    "scared": SOUND_SCARED_IDENTIFIER,
    # "sleepy": SOUND_SLEEPY,
    # "danger": SOUND_DANGER,
    # "ok": SOUND_OKAY, # Define SOUND_OKAY if needed
    # ... and so on
}

# --- Functions ---
def setup():
    """Set up GPIO mode and buzzer pin."""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    print("GPIO setup complete.")

def play_sequence(pwm, sequence):
    """Plays a standard sequence of (note, duration) tuples."""
    associated_words = [k for k, v in SOUND_MAP.items() if v == sequence]
    print(f"Playing sequence for '{associated_words[0] if associated_words else 'Unknown'}' ({len(sequence)} notes)...")
    for note, duration in sequence:
        frequency = NOTES.get(note, 0)
        if frequency == 0:
            pwm.ChangeDutyCycle(0)
        else:
            pwm.ChangeFrequency(frequency)
            pwm.ChangeDutyCycle(50) # Standard volume
        time.sleep(duration)
        if frequency != 0 and sequence.index((note, duration)) < len(sequence) - 1:
             pwm.ChangeDutyCycle(0)
             time.sleep(0.015) # Slightly longer gap might help definition
    pwm.ChangeDutyCycle(0)
    print("Sequence finished.")

def play_scared_sound(pwm, total_duration=1.0, tremble_freq1='A#5', tremble_freq2='B5', duty_cycle=30):
    """Plays a trembling sound (quietly)."""
    # (Keep this function as it was, if 'scared' is in SOUND_MAP)
    print("Playing scared sound...")
    freq1 = NOTES.get(tremble_freq1, 932)
    freq2 = NOTES.get(tremble_freq2, 988)
    start_time = time.time()
    tremble_interval = 0.03
    while time.time() - start_time < total_duration:
        pwm.ChangeFrequency(freq1); pwm.ChangeDutyCycle(duty_cycle); time.sleep(tremble_interval)
        if time.time() - start_time >= total_duration: break
        pwm.ChangeFrequency(freq2); pwm.ChangeDutyCycle(duty_cycle); time.sleep(tremble_interval)
        if time.time() - start_time >= total_duration: break
    pwm.ChangeDutyCycle(0)
    print("Scared sound finished.")

# --- NEW SPECIAL FUNCTION for Exciting ---
def play_exciting_trill(pwm, total_duration=0.8, trill_freq1='C#6', trill_freq2='D#6', duty_cycle=50):
    """Plays a fast, high-pitched trill/buzz."""
    print("Playing exciting trill...")
    freq1 = NOTES.get(trill_freq1, 1109) # High notes
    freq2 = NOTES.get(trill_freq2, 1245) # High notes
    start_time = time.time()
    # Use a very short interval for a fast buzz/trill effect
    trill_interval = 0.02

    while time.time() - start_time < total_duration:
        pwm.ChangeFrequency(freq1)
        pwm.ChangeDutyCycle(duty_cycle) # Normal volume
        time.sleep(trill_interval)
        if time.time() - start_time >= total_duration: break

        pwm.ChangeFrequency(freq2)
        pwm.ChangeDutyCycle(duty_cycle) # Normal volume
        time.sleep(trill_interval)
        if time.time() - start_time >= total_duration: break

    pwm.ChangeDutyCycle(0) # Silence after trill
    print("Exciting trill finished.")

def cleanup():
    """Clean up GPIO resources."""
    GPIO.cleanup()
    print("\nGPIO cleaned up.")

# --- Main Execution ---
if __name__ == "__main__":
    pwm_buzzer = None
    try:
        setup()
        pwm_buzzer = GPIO.PWM(BUZZER_PIN, 440)
        pwm_buzzer.start(0) # Start silent

        print("\n--- Robot Sound Player (Custom Sounds) ---")
        available_commands = sorted(list(SOUND_MAP.keys()))
        print("Enter a word to play its sound.")
        print("Available words:", ", ".join(available_commands))
        print("Type 'quit' or 'exit' to stop.")
        print("-------------------------------------------")

        while True:
            try:
                command = input("Enter word: ").strip().lower()

                if command in ["quit", "exit"]:
                    print("Exiting...")
                    break

                sound_action = SOUND_MAP.get(command)

                # --- Updated Logic to handle different actions ---
                if sound_action == SOUND_SCARED_IDENTIFIER:
                    play_scared_sound(pwm_buzzer, total_duration=1.2)
                elif sound_action == SOUND_EXCITING_IDENTIFIER:
                    play_exciting_trill(pwm_buzzer, total_duration=0.8) # Call the new function
                elif isinstance(sound_action, list):
                    play_sequence(pwm_buzzer, sound_action) # Play standard sequence
                else:
                    print(f"Unknown command: '{command}'. Please choose from the list.")

                time.sleep(0.2)

            except EOFError:
                 print("\nExiting...")
                 break

    except KeyboardInterrupt:
        print("\nPlayback stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if pwm_buzzer:
            pwm_buzzer.stop()
        cleanup()
