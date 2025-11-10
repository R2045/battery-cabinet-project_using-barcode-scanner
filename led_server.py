import RPi.GPIO as GPIO
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

# --- CONFIGURATION ---
GREEN_LED = 17  # Physical Pin 11
YELLOW_LED = 27 # Physical Pin 13
RED_LED = 22    # Physical Pin 15
BLINK_SPEED = 0.75 # Blink speed in seconds

# --- Global State (for threads) ---
# We need to store the current state to know what to blink
current_led_state = "available" # e.g., "available", "charging-blink", "faulty-override"
led_on = True # Used for blinking
lock = threading.Lock() # To prevent threads from colliding

# Setup Flask server
app = Flask(__name__)
CORS(app) 

# --- GPIO Functions ---
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    pins = [GREEN_LED, YELLOW_LED, RED_LED]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

def set_leds(green, yellow, red):
    """Helper function to set all 3 LEDs at once."""
    GPIO.output(GREEN_LED, GPIO.HIGH if green else GPIO.LOW)
    GPIO.output(YELLOW_LED, GPIO.HIGH if yellow else GPIO.LOW)
    GPIO.output(RED_LED, GPIO.HIGH if red else GPIO.LOW)

def led_control_loop():
    """
    This function runs in a separate thread.
    It checks the 'current_led_state' variable and updates the LEDs.
    This is what creates the blinking effect.
    """
    global led_on
    while True:
        with lock:
            state = current_led_state
        
        if state == "available":
            set_leds(True, False, False) # Solid Green
            led_on = True
        elif state == "checked-out" or state == "off":
            set_leds(False, False, False) # All Off
            led_on = True
        
        # --- Override States (Solid) ---
        elif state == "available-override":
            set_leds(True, False, False) # Solid Green
            led_on = True
        elif state == "charging-override":
            set_leds(False, True, False) # Solid Yellow
            led_on = True
        elif state == "faulty-override":
            set_leds(False, False, True) # Solid Red
            led_on = True
            
        # --- Summary States (Blinking) ---
        elif state == "charging-blink":
            if led_on:
                set_leds(False, True, False) # Yellow On
            else:
                set_leds(False, False, False) # All Off
            led_on = not led_on
        elif state == "faulty-blink":
            if led_on:
                set_leds(False, False, True) # Red On
            else:
                set_leds(False, False, False) # All Off
            led_on = not led_on
            
        time.sleep(BLINK_SPEED)

# --- API Endpoint ---
@app.route('/set_led', methods=['POST'])
def set_led_route():
    """API endpoint for the HTML file to call."""
    global current_led_state
    data = request.json
    status = data.get('status') # e.g., "available", "charging-blink", "faulty-override"
    
    if not status:
        return jsonify({"success": False, "error": "No status provided"}), 400
    
    with lock:
        current_led_state = status
        
    print(f"LED State changed to: {status}")
    return jsonify({"success": True, "status_set": status})

# --- Main ---
if __name__ == '__main__':
    setup_gpio()
    print("Starting LED Bridge Server (v2 - Summary Mode)...")
    print(f"Wiring: GREEN={GREEN_LED}, YELLOW={YELLOW_LED}, RED={RED_LED}")
    
    # Start the background thread for blinking
    led_thread = threading.Thread(target=led_control_loop, daemon=True)
    led_thread.start()
    
    print("LED Blink Thread started.")
    print("Press CTRL+C to exit.")
    
    try:
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("Cleaning up GPIO pins.")
        GPIO.cleanup()
