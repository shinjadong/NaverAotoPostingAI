# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: settings.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import os
DEBUG = False
MULTI_LOGIN = False
SELECT_MODE = False
VALID_DATE = '20250121 23:59:59'
HAIIP = False
ENGINE = 'CHATGPT'
BACKLINK_YN = True
ADVERTISE_ON = False
ADVERTISEMENT_TEXT = ''
ADVERTISEMENT_LINK = ''
LAST_ADD_IMG = []
NBLOG = True
WORDPRESS = False
IMAGE_CHANGE = False
LOGO_FILE_NAME = ''
OPENAI_API_KEY = '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'
KEYWORD_NBLOG_ASSISTANT_ID = 'asst_8QXgkPTCG1Zo3OVBEfR5QhFt'
CLAUDE_API_KEY = ''
CREDENTIALS_JSON_FILE_NAME = 'keyword_upload_helper.json'
GOOGLE_SEARCH_API_KEY = ''
GOOGLE_CSE_ID = ''
PHOTO_DIR = './photos/'
DEBUG_DIR = './DEBUG/'
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)
if SELECT_MODE:
    CONTENTS_DIR = './원고/'
    if not os.path.exists(CONTENTS_DIR):
        os.makedirs(CONTENTS_DIR)