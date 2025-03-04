# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: posting_keyword.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

class Keyword:

    def __init__(self, row_no, main_keyword, photo_cnt, reserved_time, insert_youtube_yn, last_text, posting_title, place_keyword, nblog_content):
        self.row_no = row_no
        self.main_keyword = main_keyword
        self.photo_cnt = photo_cnt
        self.reserved_time = reserved_time
        self.insert_youtube_yn = insert_youtube_yn
        self.last_text = last_text
        self.posting_title = posting_title
        self.place_keyword = place_keyword
        self.google_search_result = []
        self.nblog_content = nblog_content

    def __repr__(self):
        return self.main_keyword