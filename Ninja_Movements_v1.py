# -*- coding:utf-8 -*-

'''!
  @file Ninja_Movements_v1.py
  @brief Controls servo movements for a robot using DFRobot Raspberry Pi Expansion HAT.
  @n Provides functions for standing, walking, turning, running, and other actions.
  @n Assumes 4 servos connected:
  @n Servo 0: Right Leg/Hip?
  @n Servo 1: Left Leg/Hip?
  @n Servo 2: Right Foot/Ankle?
  @n Servo 3: Left Foot/Ankle?
  @n (Adjust comments based on your actual robot configuration)
  @copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license     The MIT License (MIT)
  @author      Frank(jiehan.guo@dfrobot.com), Refined by Assistant
  @version     V1.1
  @date        2024-05-22
  @url https://github.com/DFRobot/DFRobot_RaspberryPi_Expansion_Board
'''
# prompt example
# "Move servo 0 to 45 degrees with fast speed"
# "Set servo 1 to 135 degrees with jerky style"
# "All servos to center"
# "Servo 2 to 90, servo 3 to 180"
# "All the servos to zero" (Expect all the servo to be zero)

import sys
import os
import time
import threading # Added import for threading

# Add parent directory to Python path for library access
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

try:
    from DFRobot_RaspberryPi_Expansion_Board import DFRobot_Expansion_Board_IIC as Board
    from DFRobot_RaspberryPi_Expansion_Board import DFRobot_Expansion_Board_Servo as Servo
except ImportError:
    print("Error: DFRobot library not found.")
    print("Please install it using: pip install DFRobot_RaspberryPi_Expansion_Board")
    sys.exit(1)

# --- Global Variables ---
board = None
servo = None
# Global flag to stop continuous movements
stop_movement = False

# --- Initialization and Status ---

def init_board_and_servo():
    """Initializes the I2C board and servo controller."""
    global board, servo
    board = Board(1, 0x10)  # Select i2c bus 1, set address to 0x10
    servo = Servo(board)

    # Loop until board connection is successful
    while board.begin() != board.STA_OK:
        print_board_status()
        print("Board connection failed. Retrying in 2 seconds...")
        time.sleep(2)
    print("Board connection successful.")

    # Initialize servo controller
    servo.begin()
    print("Servo controller initialized.")

def print_board_status():
    """Prints the status of the expansion board."""
    if board is None:
        print("Board not initialized.")
        return
    status = board.last_operate_status
    if status == board.STA_OK:
        print("Board Status: Everything OK")
    elif status == board.STA_ERR:
        print("Board Status: Unexpected Error")
    elif status == board.STA_ERR_DEVICE_NOT_DETECTED:
        print("Board Status: Device Not Detected")
    elif status == board.STA_ERR_PARAMETER:
        print("Board Status: Parameter Error")
    elif status == board.STA_ERR_SOFT_VERSION:
        print("Board Status: Unsupported Board Firmware Version")
    else:
        print(f"Board Status: Unknown Status Code ({status})")

# --- Basic Servo Control ---

def set_servo_angle(servo_id, angle):
    """Moves a specific servo to a target angle."""
    if servo is None:
        print("Error: Servo controller not initialized.")
        return
    # Clamp angle to valid range (0-180)
    angle = max(0, min(180, int(angle)))
    print(f"Moving servo {servo_id} to {angle} degrees.")
    servo.move(servo_id, angle)
    # Add a small delay to allow servo to start moving
    time.sleep(0.05)

def set_all_servos(angle):
    """Moves all servos (0-3) to the same target angle."""
    if servo is None:
        print("Error: Servo controller not initialized.")
        return
    angle = max(0, min(180, int(angle)))
    print(f"Moving all servos to {angle} degrees.")
    for i in range(4):
        servo.move(i, angle)
    time.sleep(0.5) # Give time for all servos to move

# --- Predefined Poses ---

"""Resets all servos to the initial standing position.
   Adjust the angles below to match your robot's stable stand.
   Servo 0: Right Leg/Hip? -> 105 degrees
   Servo 1: Left Leg/Hip?  -> 90 degrees
   Servo 2: Right Foot/Ankle?-> 90 degrees
   Servo 3: Left Foot/Ankle? -> 90 degrees
"""
def reset_servos():
    if servo is None: return
    print("Resetting servos to standing position.")
    servo.move(0, 105)
    servo.move(1, 90)
    servo.move(2, 90)
    servo.move(3, 90)
    time.sleep(0.5)  # Short delay for the servos to reach the position

""" Lowers the robot into a resting or 'tire' mode configuration. """
def rest():
    if servo is None: return
    print("Moving servos to resting position.")
    # Optionally reset to stand first for a smoother transition
    # reset_servos()
    # time.sleep(0.2)
    servo.move(0, 15)   # Lower right leg
    servo.move(1, 180)  # Lower left leg (adjust angle if 180 is too extreme)
    servo.move(2, 90)   # Neutral feet
    servo.move(3, 90)
    time.sleep(1) # Allow time to settle

# --- Predefined Actions ---

"""'Say Hello': Wiggles one leg/foot."""
def hello():
    if servo is None: return
    print("Performing 'hello' action.")
    reset_servos() # Start from stand
    servo.move(0, 175)
    servo.move(1, 135)
    time.sleep(1)
    servo.move(0, 105)
    time.sleep(1)
    # Wiggle right leg/hip (Servo 0)
    wave_speed = 0.01 # Time between angle steps
    for _ in range(2): # Wave twice
        for angle in range(105, 75, -2): # Sweep down
            servo.move(0, angle)
            time.sleep(wave_speed)
        for angle in range(75, 105, 2): # Sweep up
            servo.move(0, angle)
            time.sleep(wave_speed)
    time.sleep(0.5)
    reset_servos()  # Return to stand

# --- Continuous Movements (Use with threading) ---
# Note: The 'style' parameter is currently unused but kept for future expansion.

def _get_walk_params(speed):
    """Helper to get timing parameters based on speed."""
    if speed == 'fast':
        step_delay = 0.15 # Shorter delay between steps
        foot_rotate_delay = 0.3
        lift_angle_adj = 5 # Lift slightly higher/lower for fast steps? (Optional)
    elif speed == 'slow':
        step_delay = 0.4
        foot_rotate_delay = 0.7
        lift_angle_adj = -5
    else: # Normal speed
        step_delay = 0.25
        foot_rotate_delay = 0.5
        lift_angle_adj = 0
    return step_delay, foot_rotate_delay, lift_angle_adj

"""Walk forward continuously, alternating legs."""
def walk(speed=None, style=None):
    global stop_movement
    if servo is None: return
    print(f"Starting walk (Speed: {speed or 'normal'}). Use stop() to halt.")
    step_delay, foot_rotate_delay, lift_adj = _get_walk_params(speed)
    stand_right_leg = 105
    stand_left_leg = 90
    lift_right_leg = 70 # Adjusted lift angle
    lift_left_leg = 125 # Adjusted lift angle

    while not stop_movement:
        # Step 1: Lift Right Leg
        servo.move(0, lift_right_leg + lift_adj)
        time.sleep(step_delay)
        if stop_movement: break

        # Step 2: Rotate feet to shift weight/turn slightly
        servo.move(2, 80) # Right foot rotate
        servo.move(3, 100)# Left foot rotate
        time.sleep(foot_rotate_delay)
        servo.move(2, 90) # Feet back to neutral
        servo.move(3, 90)
        if stop_movement: break

        # Step 3: Place Right Leg Down
        servo.move(0, stand_right_leg)
        time.sleep(step_delay)
        if stop_movement: break

        # Step 4: Lift Left Leg
        servo.move(1, lift_left_leg - lift_adj) # Note the subtraction if lift_adj is positive
        time.sleep(step_delay)
        if stop_movement: break

        # Step 5: Rotate feet
        servo.move(2, 80)
        servo.move(3, 100)
        time.sleep(foot_rotate_delay)
        servo.move(2, 90)
        servo.move(3, 90)
        if stop_movement: break

        # Step 6: Place Left Leg Down
        servo.move(1, stand_left_leg)
        time.sleep(step_delay)
        # Loop repeats

    print("Walk stopped.")
    if stop_movement: # Check if stopped by command vs end of sequence (if applicable)
        reset_servos()

"""Walk backward continuously, alternating legs."""
def stepback(speed=None, style=None):
    global stop_movement
    if servo is None: return
    print(f"Starting step back (Speed: {speed or 'normal'}). Use stop() to halt.")
    step_delay, foot_rotate_delay, lift_adj = _get_walk_params(speed)
    stand_right_leg = 105
    stand_left_leg = 90
    lift_right_leg = 70
    lift_left_leg = 125

    # --- Optional Distance Sensor Check ---
    # Define measure_distance() elsewhere if using a sensor
    # try:
    #     from your_sensor_module import measure_distance # Example import
    # except ImportError:
    #     measure_distance = None
    # ---

    while not stop_movement:
        # --- Optional Distance Check ---
        # if measure_distance:
        #     distance = measure_distance()
        #     if distance != -1 and distance < 10: # Check distance (e.g., 10 cm)
        #         print("Object detected close behind! Stopping stepback.")
        #         stop() # This will set stop_movement = True and break the loop
        #         break
        # ---

        # Step 1: Lift Left Leg
        servo.move(1, lift_left_leg - lift_adj)
        time.sleep(step_delay)
        if stop_movement: break

        # Step 2: Rotate feet (opposite for backward move)
        servo.move(2, 100) # Right foot rotate
        servo.move(3, 80)  # Left foot rotate
        time.sleep(foot_rotate_delay)
        servo.move(2, 90) # Feet back to neutral
        servo.move(3, 90)
        if stop_movement: break

        # Step 3: Place Left Leg Down
        servo.move(1, stand_left_leg)
        time.sleep(step_delay)
        if stop_movement: break

        # Step 4: Lift Right Leg
        servo.move(0, lift_right_leg + lift_adj)
        time.sleep(step_delay)
        if stop_movement: break

        # Step 5: Rotate feet
        servo.move(2, 100)
        servo.move(3, 80)
        time.sleep(foot_rotate_delay)
        servo.move(2, 90)
        servo.move(3, 90)
        if stop_movement: break

        # Step 6: Place Right Leg Down
        servo.move(0, stand_right_leg)
        time.sleep(step_delay)
        # Loop repeats

    print("Step back stopped.")
    if stop_movement:
        reset_servos()


"""Performs *one step* of turning the robot left."""
# For continuous turning, call this repeatedly or modify it with a loop.
def turnleft_step(speed=None, style=None):
    if servo is None: return
    print(f"Performing one turn-left step (Speed: {speed or 'normal'}).")
    step_delay, foot_rotate_delay, lift_adj = _get_walk_params(speed)
    stand_right_leg = 105
    lift_right_leg = 70

    # Lift Right Leg
    servo.move(0, lift_right_leg + lift_adj)
    time.sleep(step_delay)

    # Rotate feet to turn left
    servo.move(2, 70) # Turn right foot inwards more?
    servo.move(3, 70) # Turn left foot inwards? Adjust angles as needed
    time.sleep(foot_rotate_delay)
    servo.move(2, 90) # Feet back to neutral relative to new body angle
    servo.move(3, 90)

    # Place Right Leg Down
    servo.move(0, stand_right_leg)
    time.sleep(step_delay)
    # Optional: Shift weight slightly?
    # reset_servos() # Uncomment if you want it to return fully to stand after one step

"""Performs *one step* of turning the robot right."""
# For continuous turning, call this repeatedly or modify it with a loop.
def turnright_step(speed=None, style=None):
    if servo is None: return
    print(f"Performing one turn-right step (Speed: {speed or 'normal'}).")
    step_delay, foot_rotate_delay, lift_adj = _get_walk_params(speed)
    stand_left_leg = 90
    lift_left_leg = 125

    # Lift Left Leg
    servo.move(1, lift_left_leg - lift_adj)
    time.sleep(step_delay)

    # Rotate feet to turn right
    servo.move(2, 110) # Turn right foot outwards?
    servo.move(3, 110) # Turn left foot outwards more? Adjust angles as needed
    time.sleep(foot_rotate_delay)
    servo.move(2, 90) # Feet back to neutral relative to new body angle
    servo.move(3, 90)

    # Place Left Leg Down
    servo.move(1, stand_left_leg)
    time.sleep(step_delay)
    # Optional: Shift weight slightly?
    # reset_servos() # Uncomment if you want it to return fully to stand after one step


def _get_run_params(speed):
    """Helper to get run parameters based on speed."""
    # For standard servos (0-180), speed control in 'run' mode
    # usually involves how *fast* you command small angle changes,
    # or setting fixed offset angles. These are likely feet/wheels.
    # If using *continuous rotation servos*, the value sent (0-180)
    # controls speed and direction (90 is stop). The DFRobot library's
    # servo.move() might not be ideal for continuous servos.
    # Assuming standard servos acting as wheels/feet:
    if speed == 'fast':
        # Larger angle offset from 90 = faster rotation? Or just faster command rate?
        # Let's assume angle offset represents speed for standard servos.
        angle_offset = 40 # e.g., 90+40=130, 90-40=50
    elif speed == 'slow':
        angle_offset = 15 # e.g., 90+15=105, 90-15=75
    else: # Normal speed
        angle_offset = 25 # e.g., 90+25=115, 90-25=65
    return angle_offset

"""Change to the 'tire' mode, and move forward continuously."""
def run(speed=None, style=None):
    global stop_movement
    if servo is None: return
    print(f"Starting run forward (Speed: {speed or 'normal'}). Use stop() to halt.")
    angle_offset = _get_run_params(speed)

    # Lower into run configuration
    servo.move(0, 15)
    servo.move(1, 180) # Adjust if 180 is too extreme
    time.sleep(0.5)

    # Assuming servo 2 is right wheel/foot, servo 3 is left wheel/foot
    # Forward: Right wheel CW (angle < 90), Left wheel CCW (angle > 90)
    right_wheel_angle = 90 - angle_offset
    left_wheel_angle = 90 + angle_offset

    while not stop_movement:
        servo.move(2, right_wheel_angle)
        servo.move(3, left_wheel_angle)
        # Need a small delay or the loop will be too fast, adjust as needed
        time.sleep(0.05)

    print("Run forward stopped.")
    if stop_movement:
        # Stop wheels
        servo.move(2, 90)
        servo.move(3, 90)
        time.sleep(0.2)
        # Return to standing or resting position
        reset_servos() # Or call rest()

"""Change to the 'tire' mode, and move backward continuously."""
def runback(speed=None, style=None):
    global stop_movement
    if servo is None: return
    print(f"Starting run backward (Speed: {speed or 'normal'}). Use stop() to halt.")
    angle_offset = _get_run_params(speed)

    # Lower into run configuration
    servo.move(0, 15)
    servo.move(1, 180)
    time.sleep(0.5)

    # Backward: Right wheel CCW (angle > 90), Left wheel CW (angle < 90)
    right_wheel_angle = 90 + angle_offset
    left_wheel_angle = 90 - angle_offset

    while not stop_movement:
        servo.move(2, right_wheel_angle)
        servo.move(3, left_wheel_angle)
        time.sleep(0.05) # Adjust delay as needed

    print("Run backward stopped.")
    if stop_movement:
        servo.move(2, 90)
        servo.move(3, 90)
        time.sleep(0.2)
        reset_servos()

"""Change to the 'tire' mode, and rotate counter-clockwise (left) continuously."""
def rotateleft(speed=None, style=None):
    global stop_movement
    if servo is None: return
    print(f"Starting rotate left (CCW) (Speed: {speed or 'normal'}). Use stop() to halt.")
    angle_offset = _get_run_params(speed)

    servo.move(0, 15)
    servo.move(1, 180)
    time.sleep(0.5)

    # Rotate Left (CCW): Both wheels forward -> Right CW (<90), Left CCW (>90)
    # Wait, rotate left should be Right forward, Left backward
    # Right wheel CW (<90), Left wheel CW (<90) ?? No, that's moving right arc
    # Rotate Left: Right wheel FORWARD (CW, <90), Left wheel BACKWARD (CW, <90)? -> NO
    # Rotate Left: Right wheel FORWARD (CW, <90), Left wheel BACKWARD (CCW, >90)? -> NO
    # Rotate Left: Right wheel FORWARD (CW, <90), Left wheel FORWARD (CCW, >90) -> This is RUN FWD
    # Rotate Left: Right wheel BACKWARD (CCW, >90), Left wheel FORWARD (CCW, >90) -> YES!

    right_wheel_angle = 90 + angle_offset # Backward
    left_wheel_angle = 90 + angle_offset  # Forward

    while not stop_movement:
        servo.move(2, right_wheel_angle)
        servo.move(3, left_wheel_angle)
        time.sleep(0.05)

    print("Rotate left stopped.")
    if stop_movement:
        servo.move(2, 90)
        servo.move(3, 90)
        time.sleep(0.2)
        reset_servos()


"""Change to the 'tire' mode, and rotate clockwise (right) continuously."""
def rotateright(speed=None, style=None):
    global stop_movement
    if servo is None: return
    print(f"Starting rotate right (CW) (Speed: {speed or 'normal'}). Use stop() to halt.")
    angle_offset = _get_run_params(speed)

    servo.move(0, 15)
    servo.move(1, 180)
    time.sleep(0.5)

    # Rotate Right (CW): Right wheel BACKWARD (CCW, >90), Left wheel FORWARD (CCW, >90) -> NO Left forward is CCW
    # Rotate Right (CW): Right wheel FORWARD (CW, <90), Left wheel BACKWARD (CW, <90)? -> YES!

    right_wheel_angle = 90 - angle_offset # Forward
    left_wheel_angle = 90 - angle_offset  # Backward

    while not stop_movement:
        servo.move(2, right_wheel_angle)
        servo.move(3, left_wheel_angle)
        time.sleep(0.05)

    print("Rotate right stopped.")
    if stop_movement:
        servo.move(2, 90)
        servo.move(3, 90)
        time.sleep(0.2)
        reset_servos()


# --- Control Functions ---

"""Stops any continuous movement and resets servos to standing position."""
def stop():
    global stop_movement
    print("Stopping continuous movement...")
    stop_movement = True
    # Give threads a moment to see the flag
    time.sleep(0.1)
    # Ensure wheels/feet are stopped if in run mode (redundant if reset_servos() is called)
    if servo:
        servo.move(2, 90)
        servo.move(3, 90)
    # Reset to a known stable state
    reset_servos()
    print("Movement stopped and servos reset.")


def start_continuous_movement(movement_func, speed = None, style = None):
    """Starts a movement function (like walk, run) in a separate thread."""
    global stop_movement
    if servo is None:
        print("Error: Servos not initialized.")
        return None

    # Ensure any previous movement thread is stopped conceptually
    # (The actual thread termination depends on the thread seeing stop_movement)
    stop() # Reset flag and position before starting new move
    time.sleep(0.1) # Short delay
    stop_movement = False # Reset flag for the new movement

    print(f"Starting continuous movement: {movement_func.__name__}")
    # Create and start the thread
    thread = threading.Thread(target=movement_func, args=(speed, style), daemon=True)
    # Using daemon=True allows the main program to exit even if this thread is running.
    # Be careful with cleanup if the main thread exits abruptly.
    thread.start()
    return thread # Return thread object if needed


# --- Main Execution Block ---

if __name__ == "__main__":
    movement_thread = None
    try:
        init_board_and_servo()
        reset_servos() # Start in a known position

        print("\n--- Robot Movement Test ---")
        print("Commands:")
        print("  hello   - Perform wave action")
        print("  walk    - Start walking forward (normal speed)")
        print("  runfast - Start running forward (fast)")
        print("  rotleft - Start rotating left")
        print("  stop    - Stop current continuous movement")
        print("  reset   - Reset to standing position")
        print("  rest    - Move to resting position")
        print("  s [id] [angle] - Set servo <id> to <angle>")
        print("  exit    - Exit the program")
        print("---------------------------")

        while True:
            command = input("Enter command: ").strip().lower().split()
            if not command:
                continue

            action = command[0]

            if action == "exit":
                stop() # Ensure servos are stopped before exiting
                print("Exiting.")
                break
            elif action == "hello":
                stop() # Stop any background movement first
                hello()
            elif action == "walk":
                movement_thread = start_continuous_movement(walk)
            elif action == "stepback":
                 movement_thread = start_continuous_movement(stepback)
            elif action == "run":
                movement_thread = start_continuous_movement(run)
            elif action == "runfast":
                movement_thread = start_continuous_movement(run, speed='fast')
            elif action == "runback":
                 movement_thread = start_continuous_movement(runback)
            elif action == "rotleft":
                movement_thread = start_continuous_movement(rotateleft)
            elif action == "rotright":
                 movement_thread = start_continuous_movement(rotateright)
            elif action == "turnleft":
                 stop()
                 turnleft_step() # Single step turn
            elif action == "turnright":
                 stop()
                 turnright_step() # Single step turn
            elif action == "stop":
                stop()
                movement_thread = None # Clear thread reference
            elif action == "reset":
                stop() # Stop movement before resetting
                reset_servos()
            elif action == "rest":
                stop() # Stop movement before resting
                rest()
            elif action == "s" and len(command) == 3:
                try:
                    servo_id = int(command[1])
                    angle = int(command[2])
                    if 0 <= servo_id <= 3 and 0 <= angle <= 180:
                        stop() # Stop continuous movement if setting individual servo
                        set_servo_angle(servo_id, angle)
                    else:
                        print("Invalid servo ID (0-3) or angle (0-180).")
                except ValueError:
                    print("Invalid number format. Use: s <id> <angle>")
            else:
                print("Unknown command.")

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping and cleaning up.")
        stop() # Ensure servos are stopped
        rest() # return to rest status
        # Optionally go to rest position on exit
        # rest()

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        stop() # Try to stop servos on error

    finally:
        print("Final cleanup: Ensuring servos are stopped.")
        # The stop() function should handle resetting/stopping servos.
        # No GPIO.cleanup() needed as GPIO library wasn't directly used here.
        if board:
             print("Board object exists (though communication might be closed).")
        # Consider if the DFRobot library has its own cleanup/close method, though often not explicitly required.
