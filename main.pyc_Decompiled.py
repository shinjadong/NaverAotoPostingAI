# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: main.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from settings import *
from helper import *
if datetime.now().strftime('%Y%m%d %H:%M:%S') > VALID_DATE:
    print('유효기간이 만료되었습니다.')
    input(' / 01028564885으로 연락 부탁드립니다.')
logging.basicConfig(filename=f'{DEBUG_DIR}keyword-upload-app.log', level=logging.ERROR)
try:
    helper = Helper()
    helper.start_program()
    helper.upload_posting()
    helper.end_program()
except Exception as e:
    print(e)
    logging.error('An error occurred', exc_info=True)
    input(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] 에러 발생으로 프로그램이 종료되었습니다 :(")