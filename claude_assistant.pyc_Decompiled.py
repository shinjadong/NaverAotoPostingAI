# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: claude_assistant.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from settings import *
import anthropic
import base64
from anthropic import InternalServerError, APIStatusError, APITimeoutError, APIConnectionError, APIResponseValidationError
import sys
import time
import re
import json

class ClaudeHelper:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:  # inserted
            application_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(application_path, 'data/클로드 학습 데이터/guide.md'), 'r', encoding='utf-8') as f:
            self.guide = f.read()
        with open(os.path.join(application_path, 'data/클로드 학습 데이터/info1.md'), 'r', encoding='utf-8') as f:
            self.info1 = f.read()
        with open(os.path.join(application_path, 'data/클로드 학습 데이터/output1.md'), 'r', encoding='utf-8') as f:
            self.output1 = f.read()
        with open(os.path.join(application_path, 'data/클로드 학습 데이터/info2.md'), 'r', encoding='utf-8') as f:
            self.info2 = f.read()
        with open(os.path.join(application_path, 'data/클로드 학습 데이터/output2.md'), 'r', encoding='utf-8') as f:
            self.output2 = f.read()

    def create_content(self, keyword):
        example_message = f'<examples><example><INFO>{self.info1}</INFO><ideal_output>{self.output1}</ideal_output></example><example><INFO>{self.info2}</INFO><ideal_output>{self.output2}</ideal_output></example></examples>'
        text = f'- [키워드]: {keyword.main_keyword}\n- [이미지 개수]: {keyword.photo_cnt}'
        try:
            message = self.client.messages.create(model='claude-3-5-sonnet-20241022', max_tokens=8192, temperature=0, system=f'{self.guide}', messages=[{'role': 'user', 'content': [{'type': 'text', 'text': example_message}, {'type': 'text', 'text': '원고 가이드를 참고하여 네이버 블로그 원고 글을 써주세요. 글자수는 한글 음절수 기준, 최소 2000자여야 합니다.'}, {'type': 'text', 'text': text}]}])
        except InternalServerError as e:
            pass  # postinserted
        else:  # inserted
            with open('./DEBUG/결과1.txt', 'w', encoding='utf-8') as f:
                f.write(message.content[0].text)
        blog_content = message.content[0].text
        if SELECT_MODE:
            with open(f"{CONTENTS_DIR}{keyword.main_keyword.replace('?', '')}.txt", 'w', encoding='utf-8') as f:
                f.write(blog_content)
        keyword.nblog_content = blog_content
        return blog_content
            print('클로드 API 내부 서버 응답 에러 → 3분 대기 후 재시도합니다')
            time.sleep(180)
            return (None, None)
        except APIStatusError as e:
            if e.status_code in ['429', 429]:
                print('API 할당량이 초과되었습니다.')
                return ((-1), (-1))
        except Exception as e:
            print(e)