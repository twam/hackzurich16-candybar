#!/usr/bin/env python

import io
from Tkinter import *
from PIL import Image, ImageTk
from picamera import PiCamera
import Adafruit_PCA9685
import time
import sys
import traceback
from helper import *
from mic import *

class Spirals:
	def __init__(self):
		self.pwm = Adafruit_PCA9685.PCA9685()

		# Set frequency to 60hz, good for servos.
		self.pwm.set_pwm_freq(60)

		self.SERVO_MIN = 150  # Min pulse length out of 4096
		self.SERVO_MAX = 600  # Max pulse length out of 4096
		self.DURATION = 0.8

	def push_sweet(self, slot):
		self.pwm.set_pwm(slot, 0, self.SERVO_MAX)
		time.sleep(self.DURATION)
		self.pwm.set_pwm(slot, 0, 0)

	def switch_all_off(self):
		for i in range(0, 4):
			self.pwm.set_pwm(i, 0, 0)

class App:
	def __init__(self, root, spirals):
		self.spirals = spirals
		self.root = root

		frame = Frame(root)
		frame.grid(row=0, column=0, sticky=N+S+E+W)
		Grid.rowconfigure(root, 0, weight=1)
		Grid.columnconfigure(root, 0, weight=1)

		self.PAD = 20
		self.HEIGHT = root.winfo_screenheight()
		self.WIDTH = root.winfo_screenwidth()
		self.IMAGE_HEIGHT = 640
		self.IMAGE_WIDTH = 480
		self.IMAGE_RATIO = float(self.IMAGE_WIDTH)/float(self.IMAGE_HEIGHT)
		self.LABEL_WIDTH = self.WIDTH-2*self.PAD
		self.LABEL_HEIGHT = int(self.LABEL_WIDTH/self.IMAGE_RATIO)

		image = Image.open('idle.jpg')
		image = image.resize((self.LABEL_WIDTH, self.LABEL_HEIGHT), Image.ANTIALIAS)
		self.photo = ImageTk.PhotoImage(image)

		self.label = Label(frame, width=self.LABEL_WIDTH, height=self.LABEL_HEIGHT, image=self.photo)
		self.label.grid(row=0, column=0, padx=self.PAD, pady=self.PAD)

		self.button = Button(frame, text="START ORDER", font=('Verdana', 24, 'bold'), command=self.takepicture)
		self.button.grid(row=1, column=0, padx=self.PAD, pady=self.PAD, sticky=N+S+E+W)

		self.status = Label(frame, text='Ready to go!', font=('Verdana', 16, 'bold'))
		self.status.grid(row=2, column=0, padx=self.PAD, pady=self.PAD)

		Grid.rowconfigure(frame, 1, weight=1)

	def update_status(self, text):
		print "Status: ", text
		self.status.configure(text=text)
		self.root.update()

	def takepicture(self):
		self.button.configure(state=DISABLED)

		self.update_status('Taking picture ...')
		stream = io.BytesIO()
		with PiCamera() as camera:
			camera.resolution = (self.IMAGE_WIDTH, self.IMAGE_HEIGHT)
			camera.hflip = True
			camera.start_preview(fullscreen=False, window=(self.PAD, self.PAD, self.LABEL_WIDTH, self.LABEL_HEIGHT))
			time.sleep(3)
			camera.capture(stream, format='jpeg')
			camera.stop_preview()
		stream.seek(0)
		image = Image.open(stream)
		image.save('camera.jpg')
		image = image.resize((self.LABEL_WIDTH, self.LABEL_HEIGHT), Image.ANTIALIAS)
		self.photo = ImageTk.PhotoImage(image)
		self.label.configure(image=self.photo)

		self.root.update()

		rec_mic(self, filename='mic.wav')

		self.update_status('Authenticating ...')
		suc, msg = verify_user('camera.jpg', 'mic.wav')

		print "Authentification: ", suc, msg

		if suc:
			self.update_status('Welcome %s' % USERS[msg]['name'])
			perform_audio_action(app, 'camera.jpg', 'mic.wav', msg)
		else:
			self.update_status('Sorry dude! No service to strangers!')
			time.sleep(3)
#			self.update_status(msg)

#		self.update_status('Delivering sweets ...')
#		self.spirals.push_sweet(0)

		image = Image.open('idle.jpg')
		image = image.resize((self.LABEL_WIDTH, self.LABEL_HEIGHT), Image.ANTIALIAS)
		self.photo = ImageTk.PhotoImage(image)
                self.label.configure(image=self.photo)

		self.button.configure(state=NORMAL)
		self.update_status('Ready to go!')

# hack to make ctrl+c work (http://stackoverflow.com/questions/13784232/keyboardinterrupt-taking-a-while)
def check():
	root.after(50, check)

# init motors
spirals = Spirals()

try:
	root=Tk()
	w, h = root.winfo_screenwidth(), root.winfo_screenheight()
	app = App(root, spirals)
	root.overrideredirect(1)
	root.config(cursor="none")
	root.geometry("%dx%d+0+0" % (w, h))
	root.focus_set()
	root.bind("<Escape>", lambda e: e.widget.quit())
	root.after(50, check)
	root.mainloop()

except Exception as e:
	# switch all motors off (just in case)
	spirals.switch_all_off()

	traceback.print_exc()
	if (len(e.args) > 0):
		sys.exit(e.args[0])
	else:
		sys.exit("Unknown error: %s" % sys.exc_info()[0])
