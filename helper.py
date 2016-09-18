#!/usr/bin/env python2
import uuid
import requests
import json
import pickle
import time

import argparse
import base64
from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
from diet import *

ITEMS = ['dark chocolate', 'milk chocolate', 'candy bar']

SPEECH_KEY = 'xxx'
SPEAKER_RECOGNITION_KEY = 'xxx'
FACE_KEY = 'xxx'
GOOGLE_SPEECH_KEY = 'xxx'

INSTANCE_ID = uuid.uuid4()

USERS = {}
with open('users.pkl', 'rb') as f:
    USERS = pickle.load(f)

def dispense(app, index, sudo, user):
    """index refers to ITEMS"""

    if consume(user, sudo):
	if sudo:
	        app.update_status('With great power, comes great responsiblity!\nDispensing %s' % ITEMS[index])
	else:
	        app.update_status('Dispensing %s' % ITEMS[index])
        app.spirals.push_sweet(index)
    else:
        app.update_status("I'm sorry. I cannot do that!")
	time.sleep(3)

def call_speech(wav):
    # First request to get ephemeral access token
    url = 'https://oxford-speech.cloudapp.net/token/issueToken'
    data = 'grant_type=client_credentials&client_id={0}&client_secret={0}&scope=https://speech.platform.bing.com'.format(
        SPEECH_KEY)
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=data, headers=headers)
    access_token = response.json()['access_token']

    # Second request to parse recording
    url = 'https://speech.platform.bing.com/recognize?scenarios=smd&appid=D4D52672-91D7-4C74-8AD8-42B1D98141A5&locale=en-US&version=3.0&format=json&device.os=Linux&instanceid={}&requestid={}'.format(
        INSTANCE_ID, uuid.uuid4())
    data = wav
    headers = {'content-type': 'audio/wav; codec="audio/pcm"; samplerate=16000'}
    headers['authorization'] = 'Bearer {}'.format(access_token)
    response = requests.post(url, data=data, headers=headers)
    return response.json()

# Source: https://cloud.google.com/speech/docs/rest-tutorial
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?'
                 'version={apiVersion}')


def call_speech_google(audio_sample_path):
    with open(audio_sample_path) as f:
        speech_content = base64.b64encode(f.read())

    credentials = GoogleCredentials.from_stream('Hack Zurich 2016 1003-3324a84aaa80.json').create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)

    service = discovery.build('speech', 'v1beta1', http=http, discoveryServiceUrl=DISCOVERY_URL)

    service_request = service.speech().syncrecognize(
        body={
            'config': {
                'encoding': 'LINEAR16',  # raw 16-bit signed LE samples
                'sampleRate': 16000,  # 16 khz
                'languageCode': 'en-US',  # a BCP-47 language tag
                'speechContext': {
                  'phrases': [
                    'sudo'
                  ],
                },
            },
            'audio': {
                'content': speech_content.decode('UTF-8')
            }
        })
    response = service_request.execute()
    return response

# Source: https://cloud.google.com/vision/docs/face-tutorial
DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'
def call_face_sentiment_google(img_path):
    with open(img_path) as f:
        image_content = f.read()


    credentials = GoogleCredentials.from_stream('Hack Zurich 2016 1003-3324a84aaa80.json')
    service = discovery.build('vision', 'v1', credentials=credentials,
                           discoveryServiceUrl=DISCOVERY_URL)

    batch_request = [{
        'image': {
            'content': base64.b64encode(image_content).decode('UTF-8')
            },
        'features': [{
            'type': 'FACE_DETECTION',
            'maxResults': 10,
            }]
        }]

    request = service.images().annotate(body={
        'requests': batch_request,
        })
    response = request.execute()

    return response

# steps:
# 1. Create a new profile for new user
# 2. Enroll user with an audio sample
# 3. Use recognition on a sample to identify speaker



def call_speaker_create_profile():
    url = 'https://api.projectoxford.ai/spid/v1.0/identificationProfiles'
    data = 'locale=en-US'
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    headers['Ocp-Apim-Subscription-Key'] = SPEAKER_RECOGNITION_KEY
    response = requests.post(url, data=data, headers=headers)
    identificationProfileId = response.json()['identificationProfileId']
    return identificationProfileId


def call_speaker_create_enrollment(identificationProfileId, wav):
    url = 'https://api.projectoxford.ai/spid/v1.0/identificationProfiles/{}/enroll?shortAudio=true'.format(
        identificationProfileId)
    data = wav
    headers = {'content-type': 'audio/wav; codec="audio/pcm"; samplerate=16000'}
    headers['Ocp-Apim-Subscription-Key'] = SPEAKER_RECOGNITION_KEY
    response = requests.post(url, data=data, headers=headers)
    # FIXME check result code


def call_speaker_recognition(identificationProfileIds, wav):
    url = 'https://api.projectoxford.ai/spid/v1.0/identify?identificationProfileIds={}&shortAudio=true'.format(
        identificationProfileIds)
    data = wav
    headers = {'content-type': 'audio/wav; codec="audio/pcm"; samplerate=16000'}
    headers['Ocp-Apim-Subscription-Key'] = SPEAKER_RECOGNITION_KEY
    response = requests.post(url, data=data, headers=headers)
    return response.headers


def call_speaker_operation_status(operation_location):
    url = operation_location
    headers = {'Ocp-Apim-Subscription-Key': SPEAKER_RECOGNITION_KEY}
    response = requests.get(url, headers=headers)
    return response.json()


def call_speaker_recognition_polling(identificationProfileIds, wav):
    response_headers = call_speaker_recognition(identificationProfileIds, wav)
    while True:
        status = call_speaker_operation_status(response_headers['Operation-Location'])
        if status['status'] == 'failed':
            return None
        elif status['status'] == 'succeeded':
            return status['processingResult']['identifiedProfileId']


def call_face_detect(img):
    url = 'https://api.projectoxford.ai/face/v1.0/detect?returnFaceId=true&returnFaceLandmarks=false'
    data = img
    headers = {'content-type': 'application/octet-stream'}
    headers['Ocp-Apim-Subscription-Key'] = FACE_KEY
    response = requests.post(url, data=data, headers=headers)
    return response.json()


def call_face_verify(faceId1, faceId2):
    url = 'https://api.projectoxford.ai/face/v1.0/verify'
    data = json.dumps({'faceId1': faceId1, 'faceId2': faceId2})
    headers = {'content-type': 'application/json'}
    headers['Ocp-Apim-Subscription-Key'] = FACE_KEY
    response = requests.post(url, data=data, headers=headers)
    return response.json()

# Enrollment:
# Take photo -> faceId
# Create Speaker profile -> identificationProfileId
# Record audio, enroll


def enroll_user(name, photo_path, audio_sample_path):
    # face
    with open(photo_path) as f:
        faces = call_face_detect(f.read())
        faceId = faces[0]['faceId']
    # voice
    identificationProfileId = call_speaker_create_profile()
    with open(audio_sample_path) as f:
        call_speaker_create_enrollment(identificationProfileId, f.read())
    # DB
    USERS[identificationProfileId] = {'name': name, 'faceId': faceId}

# Detection:
# Record audio
#   -> Speaker identification -> identifiedProfileId -> local profile
#wav = open('/home/epg/halde/HackZurich/test_hello_google.wav').read()
#call_speaker_recognition_polling('017d3907-8509-42ec-9e7f-f0b7d5215f63', wav)
#   -> Text recognition -> Parse intent
# Take photo
#   -> verify against enrolled faceId


def verify_user(photo_path, audio_sample_path):
    with open(audio_sample_path) as f:
        recognizedProfileId = call_speaker_recognition_polling(','.join(USERS.keys()), f.read())
        if recognizedProfileId and recognizedProfileId in USERS:
            name = USERS[recognizedProfileId]['name']
            faceId = USERS[recognizedProfileId]['faceId']
            with open(photo_path) as f:
                faces = call_face_detect(f.read())
		if len(faces) == 0:
			return False, "No faces detected"
                newFaceId = faces[0]['faceId']
            faceVerifyResult = call_face_verify(faceId, newFaceId)
            if faceVerifyResult['isIdentical']:
                return True, recognizedProfileId
            else:
                return False, 'Face verification failed'
        else:
            return False, 'Unknown user'


def perform_audio_action(app, photo_path, audio_sample_path, user):
    res = call_speech_google(audio_sample_path)
    if 'results' in res:
        text = res['results'][0]['alternatives'][0]['transcript']
    else:
        text = ""

    print "Speech recognition:", text

    # 'fix' google's bad sudo detection :D
    SUDO=['sudo', 'zero', 'zulu']

    # Check for sudo
    sudo = False
    for index, item in enumerate(SUDO):
	if item in text.lower():
		sudo = True

    # test for exact match
    for index, item in enumerate(ITEMS):
        if item in text.lower():
            dispense(app, index, sudo, user)
            return
    # if no exact match but 'chocolate' requested, use Google sentiment analysis to decide type of chocolate served
    if 'chocolate' in text.lower():
        res = call_face_sentiment_google(photo_path)
        joyLikelihood = res['responses'][0]['faceAnnotations'][0]['joyLikelihood']
	print "JoyLikelihood:", joyLikelihood
        if joyLikelihood == 'VERY_LIKELY' or joyLikelihood == 'LIKELY':
            dispense(app, 1, sudo, user)
        else:
            dispense(app, 0, sudo, user)
