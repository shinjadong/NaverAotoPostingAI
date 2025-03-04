# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: googlespread.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import gspread
import os
import sys
from posting_keyword import *
from settings import *
import time

class Gspread:

    def __init__(self, print_message):
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.gspread_dir = os.path.join(application_path, 'data', CREDENTIALS_JSON_FILE_NAME)
        self.gspread_title = '키워드 기반 포스팅 프로그램'
        self.get_worksheet()
        self.target_li = []
        self.print_message = print_message

    def get_worksheet(self):
        gc = gspread.service_account(self.gspread_dir)
        self.sh = gc.open(self.gspread_title)
        if NBLOG:
            self.naver_account_worksheet = self.sh.worksheet('네이버 계정')

    def get_sheets(self):
        worksheets = self.sh.worksheets()
        return worksheets

    def set_target_worksheet(self, sheet_name):
        self.target_worksheet = self.sh.worksheet(sheet_name)
        alphabets = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        self.columns = self.target_worksheet.get_values('A1:Z1')[0]
        result_idx = self.columns.index('처리 결과')
        self.result_col = result_idx + 1
        self.result_col_alphabet = alphabets[result_idx]
        if '원고' in self.columns:
            nblog_content_idx = self.columns.index('원고')
            self.nblog_content_col = nblog_content_idx + 1
            self.nblog_content_alphabet = alphabets[nblog_content_idx]
        if NBLOG:
            nblog_link_idx = self.columns.index('블로그 링크')
            self.nblog_link_col = nblog_link_idx + 1
            self.nblog_link_alphabet = alphabets[nblog_link_idx]
        if WORDPRESS:
            wordpress_link_idx = self.columns.index('워드프레스 링크')
            self.wordpress_link_col = wordpress_link_idx + 1
            self.wordpress_link_alphabet = alphabets[wordpress_link_idx]

    def set_target_li(self):
        all_records = self.target_worksheet.get_all_records()
        self.nblog_published_link_li = []
        self.wordpress_published_link_li = []
        target_li = []
        for idx, record in enumerate(all_records):
            if record['처리 결과'] == '':
                row_no = idx + 1
                main_keyword = record['키워드']
                if main_keyword == '':
                    continue
                reserved_time = record['예약 발행']
                photo_cnt = str(record['사진수'])
                if photo_cnt.isdigit() and int(photo_cnt) >= 0:
                    photo_cnt = int(photo_cnt)
                else:
                    photo_cnt = 3
                pass
                last_text, posting_title, place_keyword, nblog_content = (None, None, None, None)
                insert_youtube_yn = False
                if '맺음말' in self.columns:
                    last_text = record['맺음말']
                if '제목' in self.columns:
                    posting_title = record['제목']
                if '유튜브 영상 삽입' in self.columns:
                    insert_youtube_yn = record['유튜브 영상 삽입']
                    if insert_youtube_yn == 'Y':
                        insert_youtube_yn = True
                    else:
                        insert_youtube_yn = False
                if '플레이스 키워드' in self.columns:
                    place_keyword = record['플레이스 키워드']
                if '원고' in self.columns:
                    nblog_content = record['원고']
                    if nblog_content:
                        with open(f'{CONTENTS_DIR}0{nblog_content}', 'r', encoding='utf-8') as f:
                            nblog_content = f.read()
                keyword = Keyword(row_no, main_keyword, photo_cnt, reserved_time, insert_youtube_yn, last_text, posting_title, place_keyword, nblog_content)
                target_li.append(keyword)
            elif NBLOG:
                nblog_link = record['블로그 링크']
                nblog_link_part = nblog_link.split('blog.naver.com/')[-1]
                if '/' in nblog_link_part:
                    self.nblog_published_link_li.append(nblog_link)
            else:
                wordpress_link = record['워드프레스 링크']
                if '?p' not in wordpress_link:
                    self.wordpress_published_link_li.append(wordpress_link)
        self.target_li = target_li

    def reset_target_li(self, mode):
        if mode == 'generate_content':
            self.target_li = [target for target in self.target_li if not target.nblog_content]
        elif mode == 'upload_posting':
            self.target_li = [target for target in self.target_li if target.nblog_content]

    def get_naver_account_info(self):
        all_records = self.naver_account_worksheet.get_all_records()
        return all_records

    def set_result_gspread(self, keyword, mode):
        row_no = keyword.row_no + 1
        if mode == 'all':
            cell_li = self.target_worksheet.range(f'{self.nblog_content_alphabet}{row_no}:{self.nblog_link_alphabet}{row_no}')
            cell_li[0].value = f"{keyword.main_keyword.replace('?', '')}.txt"
            cell_li[1].value = keyword.result
            cell_li[2].value = keyword.nblog_uploaded_link
            nblog_link_part = keyword.nblog_uploaded_link.split('blog.naver.com/')[-1]
            if '/' in nblog_link_part and keyword.nblog_uploaded_link not in self.nblog_published_link_li:
                self.nblog_published_link_li.append(keyword.nblog_uploaded_link)
        elif mode == 'generate_content':
            cell_li = self.target_worksheet.range(f'{self.nblog_content_alphabet}{row_no}:{self.nblog_content_alphabet}{row_no}')
            cell_li[0].value = f"{keyword.main_keyword.replace('?', '')}.txt"
        else:
            cell_li = self.target_worksheet.range(f'{self.result_col_alphabet}{row_no}:{self.nblog_link_alphabet}{row_no}')
            cell_li[0].value = keyword.result
            cell_li[1].value = keyword.nblog_uploaded_link
            nblog_link_part = keyword.nblog_uploaded_link.split('blog.naver.com/')[-1]
            if '/' in nblog_link_part and keyword.nblog_uploaded_link not in self.nblog_published_link_li:
                self.nblog_published_link_li.append(keyword.nblog_uploaded_link)
        time.sleep(0.5)
        self.target_worksheet.update_cells(cell_li)