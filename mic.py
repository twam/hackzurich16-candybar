#!/usr/bin/env python

import pyaudio
import wave

from ctypes import *
from contextlib import contextmanager


ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so.2')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)

def rec_mic(app, filename="mic.wav", duration = 5):
	CHUNK = 1024
	FORMAT = pyaudio.paInt16
	CHANNELS = 1 #2
	RATE = 16000 #44100
	RECORD_SECONDS = duration
	WAVE_OUTPUT_FILENAME = filename

	#with noalsaerr():
	p = pyaudio.PyAudio()

	stream = p.open(format=FORMAT,
			channels=CHANNELS,
			rate=RATE,
			input=True,
			frames_per_buffer=CHUNK)

	if app != None:
		app.update_status('Recording ...')

	frames = []

	for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		data = stream.read(CHUNK)
		frames.append(data)

	stream.stop_stream()
	stream.close()
	p.terminate()

	wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()

if __name__ == "__main__":
	rec_mic(None, duration = 30)
