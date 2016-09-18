#!/usr/bin/env python

# Simple demo of of the PCA9685 PWM servo/LED controller library.
# This will move channel 0 from min to max position repeatedly.
# Author: Tony DiCola
# License: Public Domain
from __future__ import division
import time

# Import the PCA9685 module.
import Adafruit_PCA9685



# Uncomment to enable debug output.
#import logging
#logging.basicConfig(level=logging.DEBUG)

# Initialise the PCA9685 using the default address (0x40).
pwm = Adafruit_PCA9685.PCA9685()

# Alternatively specify a different address and/or bus:
#pwm = Adafruit_PCA9685.PCA9685(address=0x41, busnum=2)

# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096

# Helper function to make setting a servo pulse width simpler.

# Set frequency to 60hz, good for servos.
pwm.set_pwm_freq(60)

def enable_slot(slot, duration):
	#pwm.set_pwm(slot, 0, servo_min)
	#time.sleep(duration)
	pwm.set_pwm(slot, 0, servo_max)
	time.sleep(duration)
	pwm.set_pwm(slot, 0, 0)


t=0.8
enable_slot(0,t)
enable_slot(1,t)
enable_slot(2,t)
enable_slot(3,t)
