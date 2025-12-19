#!/usr/bin/env python3
import time
import os
import sys
import warnings
from gpiozero import Servo

# --- Configuration ---
# BCM GPIO pins for each of the four motors (Single PWM Pin Control)
FRONT_LEFT_PIN = 27
FRONT_RIGHT_PIN = 17
REAR_LEFT_PIN = 22
REAR_RIGHT_PIN = 23

CONTROL_FILE_PATH = "/home/pi/node_red_output/control_data.json"
LOOP_DELAY_SECONDS = 0.5 

# --- Speed Settings ---
# Values range from -1.0 to 1.0. 
# Adjust these if the motors spin too fast or in the wrong direction.
MAX_SPEED = 0.5  
TURN_SPEED = 0.4
FORWARD = MAX_SPEED
BACKWARD = -MAX_SPEED

# --- Motor Initialization ---
def init_motor(pin):
    """Initializes a Servo object and starts it in a detached state."""
    try:
        # Suppress the PWM Software Fallback warning in the console
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # initial_value=None ensures the motor starts 'Detached' (no signal/stopped)
            motor = Servo(pin, initial_value=None)
        return motor
    except Exception as e:
        print(f"Error initializing motor on pin {pin}: {e}")
        sys.exit(1)

# Initialize the 4 motors
motor_fl = init_motor(FRONT_LEFT_PIN)
motor_fr = init_motor(FRONT_RIGHT_PIN)
motor_rl = init_motor(REAR_LEFT_PIN)
motor_rr = init_motor(REAR_RIGHT_PIN)
all_motors = [motor_fl, motor_fr, motor_rl, motor_rr]

# --- Helper Function for Motor Control ---
def set_speeds(fl_val, fr_val, rl_val, rr_val):
    """
    Sets motor speeds. 
    If value is 0.0, it detaches the pin to ensure a perfect stop.
    """
    vals = [fl_val, fr_val, rl_val, rr_val]
    
    for i, motor in enumerate(all_motors):
        if vals[i] == 0.0:
            # Setting value to None or calling detach() stops the PWM signal
            motor.value = None 
        else:
            # Assigning a value (-1.0 to 1.0) re-attaches and sends the PWM signal
            motor.value = vals[i]

# --- Control Logic Function ---
def steer_vehicle(control_word: int):
    """
    Implements the 9-state logic (0-8) for motor steering.
    Note: Right side motors are often physically inverted; 
    the signs here assume Right-Side forward is the opposite of Left-Side.
    """
    # Default values (Stop/Detached)
    fl, fr, rl, rr = 0.0, 0.0, 0.0, 0.0
    action = ""

    if control_word == 1:
        fl, fr, rl, rr = FORWARD*1.45, -FORWARD, FORWARD*1.45, -FORWARD
        action = "FORWARD"
    elif control_word == 2:
        fl, fr, rl, rr = BACKWARD, -BACKWARD*1.3, BACKWARD, -BACKWARD*1.3
        action = "BACKWART"
    elif control_word == 3:
        fl, fr, rl, rr = FORWARD*1.5, -BACKWARD*1.5, BACKWARD*0.5, -FORWARD*0.5
        action = "LEFT"
    elif control_word == 4:
        fl, fr, rl, rr = BACKWARD*0.5, -FORWARD*0.5, FORWARD*1.5, -BACKWARD*1.5
        action = "RIGHT"
    elif control_word == 5:
        fl, fr, rl, rr = BACKWARD*1.5, -FORWARD*1.5, BACKWARD*1.5, -FORWARD*1.5
        action = "TURN-LEFT"
    elif control_word == 6:
        fl, fr, rl, rr = FORWARD*1.5, -BACKWARD*1.5, FORWARD*1.5, -BACKWARD*1.5
        action = "TURN-RIGHT"
    elif control_word == 7:
        fl, fr, rl, rr = 0.0, -FORWARD*0.5, FORWARD*1.5, 0.0
        action = "DIAGONAL-LEFT"
    elif control_word == 8:
        fl, fr, rl, rr = FORWARD*1.5, -0.0, 0.0, -FORWARD*0.5
        action = "DIAGONAL-RIGHT"
    else:
        # Covers 0 and any invalid input
        fl, fr, rl, rr = 0.0, 0.0, 0.0, 0.0
        action = "STOP (Detached)"
        
    set_speeds(fl, fr, rl, rr)
    return action

# --- Main Loop ---
def main():
    """Reads a plain digit from the file and updates motor state every 0.5s."""
    os.system('clear') 
    
    print("--- ROS 2 Jazzy GPIO Control Node (gpio_control_node.py) ---")
    print(f"File Path: {CONTROL_FILE_PATH}")
    print(f"Mode: 4-Motor PWM with Signal Detach for Neutral Safety")
    
    line_count = 0 

    try:
        while True:
            control_word = 0 
            
            # 1. Read the file as raw text
            try:
                if os.path.exists(CONTROL_FILE_PATH):
                    with open(CONTROL_FILE_PATH, 'r') as f:
                        content = f.read().strip()
                        if content.isdigit():
                            control_word = int(content)
                else:
                    sys.stderr.write(f"\r[ERROR] File not found at {CONTROL_FILE_PATH}\n")
            except Exception as e:
                sys.stderr.write(f"\r[ERROR] Error reading file: {e}\n")

            # 2. Update motor states
            action = steer_vehicle(control_word)

            # 3. Output to bash (Overwriting the previous line)
            for _ in range(line_count):
                print('\033[A\033[K', end='')
            
            print(f"[{time.strftime('%H:%M:%S')}] Word: {control_word} -> **{action}**")
            line_count = 1 
            
            # 4. Wait
            time.sleep(LOOP_DELAY_SECONDS)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Stopping motors...")
    finally:
        # Safety: Detach all motors on exit
        for motor in all_motors:
            motor.value = None
            motor.close()
        print("[INFO] Cleanup complete. Script finished.")

if __name__ == '__main__':
    main()
