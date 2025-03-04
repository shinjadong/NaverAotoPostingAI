# 외부 파일인 settings.py의 모든 설정값을 가져옵니다
from settings import *
# 외부 파일인 helper.py의 모든 함수들을 가져옵니다
from helper import *
# 현재 날짜와 시간이 VALID_DATE보다 이후인지 확인합니다 (라이센스 유효성 검사)
if datetime.now().strftime('%Y%m%d %H:%M:%S') > VALID_DATE:
    # 유효기간이 만료되었다는 메시지를 출력합니다
    print('유효기간이 만료되었습니다.')
    # 사용자에게 연락처를 안내하며 입력을 기다립니다
    input(' / 01028564885으로 연락 부탁드립니다.')
# 로깅 설정을 초기화합니다 - 에러 로그를 DEBUG_DIR 경로의 keyword-upload-app.log 파일에 저장합니다
logging.basicConfig(filename=f'{DEBUG_DIR}keyword-upload-app.log', level=logging.ERROR)
try:
    # Helper 클래스의 인스턴스를 생성합니다
    helper = Helper()
    # 프로그램을 시작하는 메서드를 호출합니다
    helper.start_program()
    # 게시물 업로드 기능을 수행하는 메서드를 호출합니다
    helper.upload_posting()
    # 프로그램을 종료하는 메서드를 호출합니다
    helper.end_program()
except Exception as e:
    # 예외 발생 시 예외 메시지를 출력합니다
    print(e)
    # 예외의 상세 정보를 로그 파일에 기록합니다
    logging.error('An error occurred', exc_info=True)
    # 사용자에게 에러 발생 시간과 함께 프로그램 종료 메시지를 보여주고 입력을 기다립니다
    input(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] 에러 발생으로 프로그램이 종료되었습니다 :(")


