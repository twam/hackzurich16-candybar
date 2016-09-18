#!/usr/bin/env python

from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.resolution = (480,640)
camera.start_preview()
sleep(3)
camera.capture('/home/hack16//image.jpg')
camera.stop_preview()
