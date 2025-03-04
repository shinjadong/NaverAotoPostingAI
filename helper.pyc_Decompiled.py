# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: helper.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from datetime import datetime
from googlespread import *
from chromehelper import *
from claude_assistant import *
import logging
import atexit
from posting_keyword import *
from gpt_assistant import *
from googlesearch import *
from selenium.common.exceptions import TimeoutException, InvalidArgumentException

class Helper:
    def __init__(self):
        logging.basicConfig(filename=f'{DEBUG_DIR}keyword-upload-app.log', level=logging.ERROR)
        self.account_li = {}

    def end_program(self):
        input(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] 프로그램이 종료되었습니다.")

    def print_message(self, text):
        print(text)

    def print_sheets(self):
        worksheets = self.gspread.get_sheets()
        worksheets = [worksheet.title for worksheet in worksheets if worksheet.title not in ['워드프레스 계정', '네이버 계정'] and '할당량' not in worksheet.title]
        for idx, worksheet_title in enumerate(worksheets):
            title = worksheet_title
            print(f'{idx + 1}. {title}')
        self.print_separator()
        target = input(' → 번호 입력: ').strip()
        while not (target.isdigit() and int(target) >= 1 and (int(target) <= len(worksheets))):
            target = input('입력이 잘못되었습니다. 다시 입력해주세요 (ex. \'1\'): ')
        worksheet_name = worksheets[int(target) - 1]
        return worksheet_name

    def distribute_posts(self):
        posts = list(range(len(self.gspread.target_li)))
        n = len(posts) // len(self.account_li)
        remainder = len(posts) % len(self.account_li)
        distribution = []
        index = 0
        for i in range(len(self.account_li)):
            if i < remainder:
                account_posts = posts[index:index + n + 1]
                index += n + 1
            else:  # inserted
                account_posts = posts[index:index + n]
                index += n
            distribution.append(account_posts)
        for idx, (key, value) in enumerate(self.account_li.items()):
            value['posting_idx'] = distribution[idx]

    def start_program(self):
        print(f"[{datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] 프로그램 실행 시작 (~{VALID_DATE})\n")
        self.gspread = Gspread(self.print_message)
        print('키워드 시트를 선택해주세요.')
        sheet_name = self.print_sheets()
        self.gspread.set_target_worksheet(sheet_name)
        self.gspread.set_target_li()
        self.print_naver_accounts()
        self.distribute_posts()
        engine = ENGINE
        if not engine:
            print('\n')
            print('AI 엔진을 선택해주세요.')
            print('1. ChatGPT [gpt-4o-mini]')
            print('2. ClaudeAI [claude-3-5-sonnet]')
            self.print_separator()
            engine = input(' → 번호 입력: ').strip()
            while not engine.isdigit() and engine not in ('1', '2'):
                engine = input('입력이 잘못되었습니다. 다시 입력해주세요 (1/2): ')
            if engine == '1':
                engine = 'CHATGPT'
            else:  # inserted
                engine = 'CLAUDE'
        if SELECT_MODE:
            print('\n')
            print('실행 모드를 선택해주세요.')
            print('1. 원고 생성 + 업로드')
            print('2. 원고 생성')
            print('3. 업로드')
            self.print_separator()
            self.mode = input(' → 번호 입력: ').strip()
            while not self.mode.isdigit() and self.mode not in ('1', '2', '3'):
                self.mode = input('입력이 잘못되었습니다. 다시 입력해주세요 (1/2/3): ')
            if self.mode == '1':
                self.mode = 'all'
            else:  # inserted
                if self.mode == '2':
                    self.mode = 'generate_content'
                else:  # inserted
                    self.mode = 'upload_posting'
        else:  # inserted
            self.mode = 'all'
        print('\n\n')
        if self.mode == 'all':
            print(f'총 {len(self.gspread.target_li)}개 키워드에 대한 포스팅을 시작합니다.\n\n')
        else:  # inserted
            if self.mode == 'generate_content':
                self.gspread.reset_target_li(self.mode)
                print(f'총 {len(self.gspread.target_li)}개 키워드에 대한 포스팅 원고를 생성합니다.\n\n')
            else:  # inserted
                self.gspread.reset_target_li(self.mode)
                print(f'총 {len(self.gspread.target_li)}개 키워드에 대한 포스팅을 시작합니다.\n\n')
        self.image_helper = ImageHelper()
        self.chrome_helper = ChromeHelper(self.print_message, self.get_random_backlink)
        atexit.register(self.close_driver)
        if engine == 'CHATGPT':
            self.assistant = GPTAssistant()
        else:  # inserted
            self.assistant = ClaudeHelper()

    def print_naver_accounts(self):
        naver_accounts = self.gspread.get_naver_account_info()
        if MULTI_LOGIN:
            self.print_message('\n\n포스팅 계정을 선택해주세요. (ex: 2~3, 5)\n')
            self.print_message('0. 전체')
            for idx, account in enumerate(naver_accounts):
                naver_id = account['네이버 ID']
                naver_blog_id = account['네이버 블로그 ID']
                print(f'{idx + 1}. {naver_id} (https://blog.naver.com/{naver_blog_id})')
            self.print_separator()
            target_accounts_num = input('\n번호 입력: ')
            target_accounts_num = [t.strip() for t in target_accounts_num.split(',')]
            remove_li = []
            for i in range(len(target_accounts_num)):
                target_account = target_accounts_num[i]
                find_range = re.findall('(\\d+)~(\\d+)', target_account)
                if find_range:
                    target_accounts_num += [str(i) for i in range(int(find_range[0][0]), int(find_range[0][1]) + 1)]
                    remove_li.append(target_account)
            print(f" → selected: {', '.join(target_accounts_num)}\n")
            target_accounts_num = sorted([int(t) for t in list(set(target_accounts_num) - set(remove_li))])
            if 0 in target_accounts_num:
                for value in naver_accounts:
                    if '썸네일 이미지' in value:
                        sumnail_template = value['썸네일 이미지']
                    else:  # inserted
                        sumnail_template = ''
                    if '타이틀 색상' in value:
                        text_color = value['타이틀 색상']
                    else:  # inserted
                        text_color = ''
                    self.account_li[value['네이버 ID']] = {'pw': value['네이버 PW'], 'blog_id': value['네이버 블로그 ID'], 'posting_idx': [], 'sumnail_template': sumnail_template, 'text_color': text_color}
            else:  # inserted
                for target_num in target_accounts_num:
                    value = naver_accounts[int(target_num) - 1]
                    if '썸네일 이미지' in value:
                        sumnail_template = value['썸네일 이미지']
                    else:  # inserted
                        sumnail_template = ''
                    if '타이틀 색상' in value:
                        text_color = value['타이틀 색상']
                    else:  # inserted
                        text_color = ''
                    self.account_li[value['네이버 ID']] = {'pw': value['네이버 PW'], 'blog_id': value['네이버 블로그 ID'], 'posting_idx': [], 'sumnail_template': sumnail_template, 'text_color': text_color}
        else:  # inserted
            self.print_message('\n\n포스팅 계정을 선택해주세요.')
            for idx, account in enumerate(naver_accounts):
                naver_id = account['네이버 ID']
                naver_blog_id = account['네이버 블로그 ID']
                print(f'{idx + 1}. {naver_id} (https://blog.naver.com/{naver_blog_id})')
            self.print_separator()
            target_accounts_num = input('\n번호 입력: ')
            if target_accounts_num not in [str(i + 1) for i in range(len(naver_accounts))]:
                target_accounts_num = input('잘못된 값입니다. 다시 입력해주세요 (ex. 1): ')
            target_accounts_num = int(target_accounts_num)
            value = naver_accounts[target_accounts_num - 1]
            if '썸네일 이미지' in value:
                sumnail_template = value['썸네일 이미지']
            else:  # inserted
                sumnail_template = ''
            if '타이틀 색상' in value:
                text_color = value['타이틀 색상']
            else:  # inserted
                text_color = ''
            self.account_li[value['네이버 ID']] = {'pw': value['네이버 PW'], 'blog_id': value['네이버 블로그 ID'], 'posting_idx': [], 'sumnail_template': sumnail_template, 'text_color': text_color}

    def close_driver(self):
        if hasattr(self.chrome_helper, 'driver') and self.chrome_helper.driver:
            self.chrome_helper.driver.quit()

    def get_random_backlink(self):
        random_link = []
        if len(self.gspread.nblog_published_link_li) >= 1:
            random_link = list(set(random.choices(self.gspread.nblog_published_link_li, k=2)))
        return random_link

    def print_separator(self):
        print('---------------------------------------------------------------------------')

    def change_ip(self):
        max_try = 0
        while max_try < 3:
            max_try += 1
            try:
                app = Application(backend='win32').connect(title='키워드 기반 자동 포스팅 프로그램')
                windows = app.windows(title='키워드 기반 자동 포스팅 프로그램')
                macro_window = windows[0]
                time.sleep(2)
                macro_window.set_focus()
            except:
                logging.error('An error occurred', exc_info=True)
        else:  # inserted
            time.sleep(1)
            current_ip = requests.get('http://ip.jsontest.com').json()['ip']
            keyboard.send_keys('%a')
            time.sleep(0.5)
            new_ip = requests.get('http://ip.jsontest.com').json()['ip']
            if current_ip!= new_ip:
                return (True, new_ip)
            time.sleep(0.5)
            keyboard.send_keys('%a')
            time.sleep(0.5)
            new_ip = requests.get('http://ip.jsontest.com').json()['ip']
            if current_ip!= new_ip:
                return (True, new_ip)
        return (False, None)

    def upload_posting(self):
        for key, value in self.account_li.items():
            if HAIIP:
                self.print_message('IP를 변경합니다.')
                result, new_ip = self.change_ip()
                if result:
                    self.print_message(f' → 성공 (IP: {new_ip})\n')
                else:  # inserted
                    self.print_message(' → 실패 (Hai-ip 실행 여부를 체크해주세요)\n')
            for posting_idx in value['posting_idx']:
                try:
                    keyword = self.gspread.target_li[posting_idx]
                    print(f'[{posting_idx + 1}. {keyword}]')
                    if self.mode in ['all', 'generate_content']:
                        self.print_message('\n이미지 생성을 시작합니다.')
                        self.image_helper.create_image(keyword, value['sumnail_template'], value['text_color'])
                        self.print_message(' → 완료 ✅ \n')
                        self.print_message('블로그 원고 생성을 시작합니다.')
                        self.assistant.create_content(keyword)
                        self.print_message(' → 완료 ✅ \n')
                    if self.mode in ['all', 'upload_posting']:
                        self.print_message('포스팅 업로드를 시작합니다.')
                        self.chrome_helper.upload_nblog_post(keyword, key, value)
                    self.gspread.set_result_gspread(keyword, self.mode)
                    self.print_separator()
                except WebDriverException as e:
                    pass  # postinserted
            else:  # inserted
                try:
                    self.chrome_helper.driver.quit()
                    self.chrome_helper.naver_logged_in = False
        except:
            pass  # postinserted
        pass
        if 'HTTP Error 429' in str(e):
            logging.error('An error occured', exc_info=True)
            print(str(e))
            print('30분 대기 후 다시 시작합니다.')
            try:
                self.close_driver()
                self.chrome_helper.naver_logged_in = False
            except:
                pass
            time.sleep(1800)
        else:  # inserted
            logging.error('An error occured', exc_info=True)
            print('\n\n로딩 시간이 초과되었습니다 :( \n\n')
            self.close_driver()
            self.chrome_helper.naver_logged_in = False
            print('\n다음 포스팅을 진행합니다.')
        except InvalidArgumentException as e:
            print('\n\n잘못된 url 값입니다. 링크를 확인해주세요 :( \n\n')
            self.close_driver()
            self.chrome_helper.naver_logged_in = False
            print('\n다음 포스팅을 진행합니다.')
        except TimeoutException as e:
            logging.error('An error occured', exc_info=True)
            print('\n\n로딩 시간이 초과되었습니다 :( \n\n')
            self.close_driver()
            self.chrome_helper.naver_logged_in = False
            print('\n다음 포스팅을 진행합니다.')
        except Exception as e:
            if hasattr(self.chrome_helper, 'driver') and self.chrome_helper.driver:
                now = datetime.now().strftime('%Y%m%d_%H%M%S')
                self.chrome_helper.driver.save_screenshot(f'{DEBUG_DIR}{now}_error.png')
            logging.error('An error occurred', exc_info=True)
            print('\n\n에러 발생 :(\n\n')
            print(f'{e}')
            self.close_driver()
            self.chrome_helper.naver_logged_in = False
            print('\n다음 포스팅을 진행합니다.')