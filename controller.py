#!/usr/bin/python

import sys, time
import RPi.GPIO as GPIO
import urllib
import datetime

cam_url = 'http://192.168.43.1:8080/photoaf.jpg'

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) # Disable "Ports already in use" warning

pins = {
    4:  {'name': 'MTR_1', 'state': GPIO.HIGH, "use": GPIO.OUT},
    7:  {'name': 'LDR_1', 'state': GPIO.HIGH, "use": GPIO.IN},
    8:  {'name': 'LDR_2', 'state': GPIO.HIGH, "use": GPIO.IN},
    23: {'name': 'LDR_3', 'state': GPIO.HIGH, "use": GPIO.IN},
    24: {'name': 'LDR_4', 'state': GPIO.HIGH, "use": GPIO.IN},
    25: {'name': 'LDR_5 ', 'state': GPIO.HIGH, "use": GPIO.IN},
    17: {'name': 'MTR_2', 'state': GPIO.HIGH, "use": GPIO.OUT},
}

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, pins[pin]["state"])

for pin in pins: # Setup individual pins and states.
    print "setting pin %s" % pin
    if pins[pin]["use"] == GPIO.OUT:
        GPIO.setup(pin, pins[pin]["use"])
        GPIO.output(pin, pins[pin]["state"])
    else:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

motor_state = False
captured = False

def start_motor(channel):
    global motor_state
    if motor_state == False:
        GPIO.output(4, GPIO.LOW) # Motor on
        motor_state = True

def take_photo(channel):
    global motor_state
    global captured

    if motor_state == True and captured == False:
        GPIO.output(4, GPIO.HIGH) # Motor off
        time.sleep(3)
        try:
            now = datetime.datetime.now() 
            file_name  = "shot_%s.jpg" % now.isoformat()
            urllib.urlretrieve(cam_url, file_name)
        except Exception as ex:
            print("Cannot connect! to android " + str(ex))
        captured = True
        time.sleep(5)
        GPIO.output(4, GPIO.LOW)

def stop_motor(channel):
    global motor_state
    global captured
    if motor_state == True and captured == True:
        time.sleep(5)
        GPIO.output(4, GPIO.HIGH)
        motor_state = False
        captured = False

GPIO.add_event_detect(7,  GPIO.FALLING, callback=start_motor, bouncetime=200)
GPIO.add_event_detect(8,  GPIO.FALLING, callback=start_motor, bouncetime=200)
GPIO.add_event_detect(23, GPIO.FALLING, callback=take_photo,  bouncetime=200)
GPIO.add_event_detect(25, GPIO.FALLING, callback=stop_motor,  bouncetime=200)

try:
    while(True):
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()
GPIO.cleanup()
