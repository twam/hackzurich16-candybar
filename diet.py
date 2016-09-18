#!/usr/bin/env python2
import pickle
from datetime import datetime, date


DIETS = {'fdcff1ff-c97c-4132-81f9-4563fe260ea4': {'max_per_day': 1}}

CONSUMED = {}
with open('consumed.pkl', 'rb') as f:
    CONSUMED = pickle.load(f)


def consume(userId, force=False):
    today = date.today().strftime('%Y%m%d')
    if userId not in CONSUMED:
        CONSUMED[userId] = {}
    if today not in CONSUMED[userId]:
        CONSUMED[userId][today] = 0

    if force:
        CONSUMED[userId][today] += 1
        return True
    else:
        if userId in DIETS:
            diet = DIETS[userId]
            consumed = CONSUMED[userId][today]
            if consumed < diet['max_per_day']:
                CONSUMED[userId][today] += 1
                return True
            else:
                return False
        else:
            CONSUMED[userId][today] += 1
            return True

# with open('consumed.pkl', 'wb') as f:
#    pickle.dump(CONSUMED, f, pickle.HIGHEST_PROTOCOL)


#consume('9b638f33-5aea-45e4-9175-7b08dbca1deb', True)
