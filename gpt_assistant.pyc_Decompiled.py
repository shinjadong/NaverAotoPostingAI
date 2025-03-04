# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: gpt_assistant.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from settings import *
from openai import OpenAI
import time
from datetime import datetime
import json

class GPTAssistant:

    def __init__(self) -> None:
        self.nblog_assistant_id = KEYWORD_NBLOG_ASSISTANT_ID
        self.client = OpenAI(api_key=OPENAI_API_KEY, default_headers={'OpenAI-Beta': 'assistants=v2'})

    def create_content(self, keyword):
        thread_id = self.create_thread()
        self.create_message(keyword, thread_id)
        run_id = self.run_assistant(thread_id)
        while True:
            status = self.check_run_status(thread_id, run_id)
            if status == 'completed':
                break
            time.sleep(3)
        content = self.get_assistant_message(thread_id)
        if SELECT_MODE:
            with open(f"{CONTENTS_DIR}{keyword.main_keyword.replace('?', '')}.txt", 'w', encoding='utf-8') as f:
                f.write(content)
                keyword.nblog_content = content

    def create_thread(self):
        thread = self.client.beta.threads.create()
        return thread.id

    def create_message(self, keyword, thread_id):
        content = '2000자 이상의 한글로 된 블로그 포스팅을 guide.md 따라 적어줘. info1.md와 output1.md를 참고하면 어떻게 써야할지 알 수 있을거야. 한글 기준 총 글자수 꼭 2000자 이상으로 써줘.\n제목은 많은 traffic을 유도할 수 있고 핵심을 요약한 것으로 써줘. 제목의 시작 또는 앞부분에 메인 키워드를 배치해줘. (예시: 철분 부족 증상 원인 음식 보충법과 예방 팁).\n딱 주어진 개수 만큼의 이미지를 써줘. 부연 설명 없이 원고만 써줘.'
        content += f'\n\n- [키워드]: {keyword.main_keyword}\n- [이미지 개수]: {keyword.photo_cnt}'
        thread_message = self.client.beta.threads.messages.create(thread_id, role='user', content=content)

    def run_assistant(self, thread_id):
        run = self.client.beta.threads.runs.create(thread_id=thread_id, assistant_id=self.nblog_assistant_id, max_completion_tokens=10000)
        return run.id

    def check_run_status(self, thread_id, run_id):
        run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        return run.status

    def get_assistant_message(self, thread_id):
        thread_messages = self.client.beta.threads.messages.list(thread_id)
        return thread_messages.data[0].content[0].text.value