import RPi.GPIO as GPIO
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURATION ---
# These are the BCM (GPIO) pin numbers, not the physical pin numbers.
# Matches our wiring guide:
GREEN_LED = 17 # Physical Pin 11
YELLOW_LED = 27 # Physical Pin 13
RED_LED = 22   # Physical Pin 15

# Setup Flask server
app = Flask(__name__)
# Allow our HTML file (from a 'file://' origin) to talk to our server
CORS(app) 

# --- GPIO Functions ---
def setup_gpio():
    """Sets up the GPIO pins."""
    GPIO.setmode(GPIO.BCM) # Use BCM pin numbering
    GPIO.setwarnings(False)
    
    pins = [GREEN_LED, YELLOW_LED, RED_LED]
    for pin in pins:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW) # Set all as outputs and turn off

def set_led_status(status):
    """Turns all LEDs off, then turns the correct one on."""
    
    # Turn all LEDs OFF
    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(YELLOW_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)
    
    # Turn the correct one ON
    if status == 'available':
        GPIO.output(GREEN_LED, GPIO.HIGH)
        print("LED: Green ON (Available)")
    elif status == 'charging':
        GPIO.output(YELLOW_LED, GPIO.HIGH)
        print("LED: Yellow ON (Charging)")
    elif status == 'faulty':
        GPIO.output(RED_LED, GPIO.HIGH)
        print("LED: Red ON (Faulty)")
    elif status == 'checked-out' or status == 'off':
        # All lights remain off
        print("LED: All OFF")

# --- API Endpoint ---
@app.route('/set_led', methods=['POST'])
def set_led_route():
    """API endpoint for the HTML file to call."""
    data = request.json
    status = data.get('status')
    
    if not status:
        return jsonify({"success": False, "error": "No status provided"}), 400
        
    set_led_status(status)
    return jsonify({"success": True, "status_set": status})

# --- Main ---
if __name__ == '__main__':
    setup_gpio()
    print("Starting LED Bridge Server...")
    print(f"Wiring: GREEN={GREEN_LED}, YELLOW={YELLOW_LED}, RED={RED_LED}")
    print("Press CTRL+C to exit.")
    
    # Set initial state to Green (Available/Ready)
    set_led_status('available')
    
    try:
        # Run the server on port 5000, accessible from anywhere on the Pi
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("Cleaning up GPIO pins.")
        GPIO.cleanup()
