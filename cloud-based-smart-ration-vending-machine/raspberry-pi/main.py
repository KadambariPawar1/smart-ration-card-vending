# ---------------- IMPORTS ----------------

import RPi.GPIO as GPIO
GPIO.setwarnings(False)

import time
import serial
import os
import datetime

from hx711 import HX711
from pyfingerprint.pyfingerprint import PyFingerprint

import firebase_admin
from firebase_admin import credentials, db

from RPLCD.i2c import CharLCD

GPIO.setmode(GPIO.BCM)

time.sleep(5)

# ---------------- LCD ----------------

lcd = None

for i in range(5):

    try:

        lcd = CharLCD(
            i2c_expander='PCF8574',
            address=0x27,
            port=1,
            cols=16,
            rows=2
        )

        time.sleep(1)

        lcd.clear()

        break

    except:

        time.sleep(1)

def lcd_safe_print(a="", b=""):

    try:

        lcd.home()

        lcd.write_string("                ")

        lcd.cursor_pos = (1,0)

        lcd.write_string("                ")

        lcd.cursor_pos = (0,0)

        lcd.write_string(str(a)[:16])

        lcd.cursor_pos = (1,0)

        lcd.write_string(str(b)[:16])

    except Exception as e:

        print("LCD Error:", e)

lcd_safe_print("SMART RATION", "BOOTING...")
time.sleep(2)

# ---------------- FIREBASE ----------------

firebase_ok = False

try:

    cred = credentials.Certificate(
        "/home/rpi/vending/serviceAccountKey.json"
    )

    firebase_admin.initialize_app(cred,{
        'databaseURL':
        'https://smart-vending-machine-f1d77-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

    firebase_ok = True

    print("Firebase Ready")

except Exception as e:

    print("Firebase Error:", e)

# ---------------- SAFE SERIAL ----------------

def open_serial(port, baud):

    for i in range(10):

        try:

            s = serial.Serial(port, baud, timeout=1)

            print(port, "Connected")

            return s

        except Exception as e:

            print("Waiting for", port)

            time.sleep(2)

    print(port, "FAILED")

    return None

# ---------------- RFID ----------------

rfid = open_serial('/dev/ttyUSB0',9600)

# ---------------- GSM ----------------

gsm = open_serial('/dev/ttyUSB1',9600)

if gsm:

    try:

        gsm.write(b'AT\r')

        time.sleep(1)

        print(gsm.readline())

    except:

        print("GSM Not Responding")

# ---------------- FINGERPRINT ----------------

finger = None

for i in range(10):

    try:

        finger = PyFingerprint(
            '/dev/serial0',
            57600,
            0xFFFFFFFF,
            0x00000000
        )

        if finger.verifyPassword():

            print("Fingerprint Ready")

            break

    except Exception as e:

        print("Waiting Fingerprint")

        time.sleep(2)

if finger is None:

    print("Fingerprint Failed")

# ---------------- SERVO ----------------

SERVO_WHEAT = 18
SERVO_RICE = 12

GPIO.setup(SERVO_WHEAT, GPIO.OUT)
GPIO.setup(SERVO_RICE, GPIO.OUT)

servo_wheat = GPIO.PWM(SERVO_WHEAT,50)
servo_rice = GPIO.PWM(SERVO_RICE,50)

servo_wheat.start(0)
servo_rice.start(0)

def move_servo(servo, angle):

    try:

        duty = 2 + (angle / 18)

        servo.ChangeDutyCycle(duty)

        time.sleep(0.8)

        servo.ChangeDutyCycle(0)

        time.sleep(0.3)

    except Exception as e:

        print("Servo Error:", e)

# ---------------- HX711 ----------------

hx_ok = False

try:

    hx_wheat = HX711(16,6)
    hx_rice = HX711(13,19)

    hx_wheat.set_reading_format("MSB","MSB")
    hx_rice.set_reading_format("MSB","MSB")

    hx_wheat.set_reference_unit(372)
    hx_rice.set_reference_unit(413)

    hx_wheat.reset()
    hx_rice.reset()

    print("Keep containers")

    time.sleep(5)

    hx_wheat.tare()
    hx_rice.tare()

    hx_ok = True

    print("HX711 Ready")

except Exception as e:

    print("HX711 Error:", e)

# ---------------- KEYPAD ----------------

keys = [
['1','2','3','A'],
['4','5','6','B'],
['7','8','9','C'],
['*','0','#','D']
]

row_pins = [17,27,22,23]
col_pins = [24,25,8,7]

for r in row_pins:

    GPIO.setup(r,GPIO.OUT)

    GPIO.output(r,GPIO.HIGH)

for c in col_pins:

    GPIO.setup(c,GPIO.IN,pull_up_down=GPIO.PUD_UP)

# ---------------- SHUTDOWN BUTTON ----------------

SHUTDOWN_PIN = 21

GPIO.setup(SHUTDOWN_PIN,GPIO.IN,pull_up_down=GPIO.PUD_UP)

def check_shutdown():

    try:

        if GPIO.input(SHUTDOWN_PIN) == 0:

            lcd_safe_print("System","Shutting Down")

            time.sleep(2)

            os.system("sudo shutdown now")

    except:

        pass

# ---------------- SMS ----------------

def send_sms(number):

    if gsm is None:

        print("GSM Not Available")

        return

    try:

        if not number.startswith("+91"):

            number = "+91" + number

        now = datetime.datetime.now()

        month = now.strftime("%B").upper()
        year = now.strftime("%Y")
        time_now = now.strftime("%H:%M:%S")

        msg = f"""Dear User,
Ration for {month} {year}
Collected at {time_now}
Thank You"""

        gsm.write(b'AT\r')
        time.sleep(1)

        gsm.write(b'AT+CMGF=1\r')
        time.sleep(1)

        cmd = f'AT+CMGS="{number}"\r'

        gsm.write(cmd.encode())

        time.sleep(1)

        gsm.write(msg.encode())

        time.sleep(1)

        gsm.write(bytes([26]))

        time.sleep(5)

        print("SMS Sent")

    except Exception as e:

        print("SMS Error:", e)

# ---------------- RFID ----------------

def scan_rfid():

    if rfid is None:

        return None

    try:

        if rfid.in_waiting:

            tag = rfid.read(12).decode().strip()

            if len(tag) == 12:

                print("RFID:", tag)

                return tag

    except Exception as e:

        print("RFID Error:", e)

    return None

# ---------------- FINGERPRINT ----------------

def verify_fingerprint(fid):

    if finger is None:

        lcd_safe_print("Fingerprint","Unavailable")

        time.sleep(2)

        return False

    try:

        lcd_safe_print("Place Finger","")

        start = time.time()

        while not finger.readImage():

            if time.time() - start > 10:

                lcd_safe_print("Fingerprint","Timeout")

                time.sleep(2)

                return False

        finger.convertImage(0x01)

        result = finger.searchTemplate()

        position = result[0]
        accuracy = result[1]

        print("Matched Position:", position)
        print("Accuracy:", accuracy)
        print("Database Fingerprint ID:", fid)

        if position == -1:

            lcd_safe_print("Fingerprint","Not Found")

            time.sleep(2)

            return False

        # DIRECT MATCH WITH FIREBASE

        if position == fid:

            lcd_safe_print("Fingerprint","Verified")

            time.sleep(2)

            return True

        lcd_safe_print("Fingerprint","Mismatch")

        time.sleep(2)

        return False

    except Exception as e:

        print("Fingerprint Error:", e)

        lcd_safe_print("Fingerprint","Error")

        time.sleep(2)

        return False

# ---------------- KEYPAD INPUT ----------------

def get_ration_id():

    data = ""

    lcd_safe_print("Enter Ration ID","")

    while True:

        check_shutdown()

        for i,row in enumerate(row_pins):

            GPIO.output(row,GPIO.LOW)

            for j,col in enumerate(col_pins):

                if GPIO.input(col) == 0:

                    key = keys[i][j]

                    time.sleep(0.3)

                    if key == "#":

                        return data

                    elif key == "*":

                        data = ""

                        lcd_safe_print("Enter Ration ID","")

                    else:

                        data += key

                        lcd.cursor_pos = (1,0)

                        lcd.write_string("                ")

                        lcd.cursor_pos = (1,0)

                        lcd.write_string(data[:16])

                    time.sleep(0.2)

            GPIO.output(row,GPIO.HIGH)

# ---------------- DISPENSE WHEAT ----------------

def dispense_wheat(target):

    if not hx_ok:

        print("HX711 Not Available")

        return

    try:

        move_servo(servo_wheat,45)

        while True:

            weight = hx_wheat.get_weight_A(5)

            if abs(weight) < 30:

                weight = 0

            weight = round(weight)

            print("Wheat:", weight)

            lcd_safe_print(
                "Dispensing",
                f"Wheat:{weight}g"
            )

            if weight >= target:

                move_servo(servo_wheat,90)

                break

    except Exception as e:

        print("Wheat Error:", e)

# ---------------- DISPENSE RICE ----------------

def dispense_rice(target):

    if not hx_ok:

        print("HX711 Not Available")

        return

    try:

        move_servo(servo_rice,70)

        while True:

            weight = hx_rice.get_weight_A(5)

            if abs(weight) < 30:

                weight = 0

            weight = round(weight)

            print("Rice:", weight)

            lcd_safe_print(
                "Dispensing",
                f"Rice:{weight}g"
            )

            if weight >= target:

                move_servo(servo_rice,130)

                break

    except Exception as e:

        print("Rice Error:", e)

# ---------------- DATABASE ----------------

def get_user_by_rfid(tag):

    if not firebase_ok:

        return None

    try:

        ref = db.reference("users/" + tag)

        return ref.get()

    except Exception as e:

        print("Firebase Error:", e)

        return None

def get_user_by_ration(rid):

    if not firebase_ok:

        return None,None

    try:

        ref = db.reference("users")

        users = ref.get()

        if users is None:

            return None,None

        for uid,data in users.items():

            if data['ration_card_id'] == rid:

                return uid,data

    except Exception as e:

        print("Firebase Error:", e)

    return None,None

# ---------------- MAIN LOOP ----------------

while True:

    try:

        check_shutdown()

        lcd_safe_print(
            "Scan RFID or",
            "Press Keypad"
        )

        user = None
        uid = None

        ration_mode = False

        while True:

            check_shutdown()

            tag = scan_rfid()

            if tag:

                user = get_user_by_rfid(tag)

                uid = tag

                break

            for i,row in enumerate(row_pins):

                GPIO.output(row,GPIO.LOW)

                for j,col in enumerate(col_pins):

                    if GPIO.input(col) == 0:

                        ration_mode = True

                        break

                GPIO.output(row,GPIO.HIGH)

                if ration_mode:

                    break

            if ration_mode:

                break

            time.sleep(0.1)

        if ration_mode:

            rid = get_ration_id()

            uid,user = get_user_by_ration(rid)

        if user:

            lcd_safe_print("User Found","")

            time.sleep(2)

            verified = verify_fingerprint(
                user['fingerprint_id']
            )

            if verified:

                dispense_wheat(
                    user['wheat_quota']
                )

                dispense_rice(
                    user['rice_quota']
                )

                send_sms(
                    user['mobile']
                )

                try:

                    ref = db.reference(
                        "users/" + uid
                    )

                    ref.update({
                        "last_dispense_time":
                        datetime.datetime.now().strftime(
                        "%d-%m-%Y %H:%M:%S")
                    })

                except Exception as e:

                    print("Update Error:", e)

                lcd_safe_print("Thank You","")

                time.sleep(3)

        else:

            lcd_safe_print("Invalid User","")

            time.sleep(2)

    except Exception as e:

        print("MAIN LOOP ERROR:", e)

        lcd_safe_print(
            "System Error",
            "Recovering..."
        )

        time.sleep(3)