# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: chromehelper.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from itertools import zip_longest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import re
from bs4 import BeautifulSoup as bs
from datetime import datetime
from imagehelper import *
import pyperclip
from settings import *
from pywinauto import keyboard
from pywinauto import Application
from selenium.common.exceptions import WebDriverException
import time
import random
import json
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import requests

class ChromeHelper:
    def __init__(self, print_message, get_random_backlink):
        self.print_message = print_message
        self.get_random_backlink = get_random_backlink
        self.naver_logged_in = False
        if IMAGE_CHANGE:
            self.image_helper = ImageHelper()

    def create_driver(self):
        options = Options()
        options.add_argument('--guest')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--incognito')
        options.add_experimental_option('prefs', {'profile.default_content_setting_values.notifications': 1})
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        options.add_experimental_option('detach', True)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('prefs', {'profile.default_content_setting_values.clipboard': 1})
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--disable-user-media-security=true')
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        options.add_argument('user-agent=' + user_agent)
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.actions = ActionChains(self.driver)
        self.driver.implicitly_wait(10)
        self.naver_logged_in = False

    def naver_login(self, naver_id, naver_pw):
        if self.check_driver():
            self.driver.quit()
        self.create_driver()
        self.driver.get('https://nid.naver.com/nidlogin.login')
        time.sleep(2)
        app = Application(backend='uia').connect(title_re='.*네이버.*로그인.*', visible_only=False, found_index=0)
        windows = app.windows()
        naver_login_window = windows[0]
        naver_login_window.set_focus()
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'switch')))
        switch = self.driver.find_element(By.ID, 'switch')
        if switch.get_attribute('value') == 'off':
            switch_label = self.driver.find_element(By.XPATH, './/label[@for=\'switch\']')
            switch_label.click()
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'id_label')))
        id_input = self.driver.find_element(By.ID, 'id_label')
        self.click_element(id_input)
        self.random_sleep()
        pyperclip.copy(naver_id)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'id')))
        id_input = self.driver.find_element(By.ID, 'id')
        id_input.send_keys(Keys.CONTROL, 'v')
        self.random_sleep()
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'pw_label')))
        pw_input = self.driver.find_element(By.ID, 'pw_label')
        self.click_element(pw_input)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'pw')))
        pw_input = self.driver.find_element(By.ID, 'pw')
        pyperclip.copy(naver_pw)
        pw_input.send_keys(Keys.CONTROL, 'v')
        self.random_sleep()
        naver_login_window.set_focus()
        keyboard.send_keys('{ENTER}')
        time.sleep(3)
        current_url = self.driver.current_url
        if 'login' not in current_url:
            self.logged_in_id = naver_id
            return True
        return False

    def check_driver(self):
        try:
            self.driver.title
            return True
        except:
            return False

    def prepare_before_post(self, naver_id, naver_pw, naver_blog_id):
        logged_in = True
        if not self.naver_logged_in:
            logged_in = False
            for _ in range(10):
                result = self.naver_login(naver_id, naver_pw)
                if result:
                    logged_in = True
                    break
        if not logged_in:
            self.print_message('로그인 시도 10회 실패하였습니다. 다음 포스팅을 진행합니다.')
            return
        self.naver_logged_in = True
        write_url = f'https://blog.naver.com/{naver_blog_id}?Redirect=Write&'
        self.driver.get(write_url)
        WebDriverWait(self.driver, 10).until(EC.url_contains(naver_blog_id))
        app = Application(backend='uia').connect(title_re='.*네이버.*블로그.*', visible_only=False, found_index=0)
        windows = app.windows()
        naver_login_window = windows[0]
        naver_login_window.set_focus()
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, './/iframe[@id=\'mainFrame\']')))
        iframe = self.driver.find_element(By.XPATH, './/iframe[@id = \'mainFrame\']')
        self.driver.switch_to.frame(iframe)
        time.sleep(3)
        body_html = self.driver.page_source
        body_soup = bs(body_html, 'html.parser')
        while body_soup.find_all('div', class_=re.compile('loadingtext.*')):
            time.sleep(2)
            body_html = self.driver.page_source
            body_soup = bs(body_html, 'html.parser')
        time.sleep(3)
        body_html = self.driver.page_source
        body_soup = bs(body_html, 'html.parser')
        cancel_btn = body_soup.find('button', {'class': 'se-popup-button se-popup-button-cancel'})
        if cancel_btn:
            cancel_btn = self.driver.find_element(By.CLASS_NAME, 'se-popup-button.se-popup-button-cancel')
            cancel_btn.click()
            time.sleep(1)
        body_html = self.driver.page_source
        body_soup = bs(body_html, 'html.parser')
        cancel_btn = body_soup.find('button', {'class': 'se-popup-dim se-popup-dim-white'})
        if cancel_btn:
            cancel_btn = self.driver.find_elements(By.CLASS_NAME, 'se-popup-button.se-popup-button-cancel')
            if cancel_btn:
                cancel_btn[0].click()
                time.sleep(1)
            else:  # inserted
                cancel_text = self.driver.find_elements(By.XPATH, './/span[text()=\'취소\']')
                if cancel_text:
                    cancel_text = cancel_text[0]
                    cancel_btn = cancel_text.find_element(By.XPATH, 'parent::button[1]')
                    cancel_btn.click()
                    time.sleep(1)
        if body_soup.find('h1', string='도움말'):
            close_btn = self.driver.find_element(By.XPATH, './/button[@class=\'se-help-panel-close-button\']')
            close_btn.click()
            self.random_sleep()
        self.set_text()

    def set_text(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'font-size\' and @aria-haspopup=\'true\']')))
        font_size_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'font-size\' and @aria-haspopup=\'true\']')
        font_size_icon.click()
        time.sleep(0.5)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'font-size\' and @data-value=\'fs16\']')))
        font_size_btn = self.driver.find_element(By.XPATH, './/button[@data-name=\'font-size\' and @data-value=\'fs16\']')
        font_size_btn.click()
        time.sleep(0.5)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'font-family\' and @aria-haspopup=\'true\']')))
        font_family_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'font-family\' and @aria-haspopup=\'true\']')
        font_family_icon.click()
        time.sleep(0.5)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'font-family\' and @data-value=\'nanummaruburi\']')))
        font_family_btn = self.driver.find_element(By.XPATH, './/button[@data-name=\'font-family\' and @data-value=\'nanummaruburi\']')
        font_family_btn.click()
        time.sleep(0.5)

    def write_title(self, title):
        time.sleep(1)
        body_html = self.driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
        body_soup = bs(body_html, 'html.parser')
        cancel_btn = body_soup.find('button', {'class': 'se-popup-dim se-popup-dim-white'})
        if cancel_btn:
            cancel_btn = self.driver.find_elements(By.CLASS_NAME, 'se-popup-button.se-popup-button-cancel')
            if cancel_btn:
                self.click_element(cancel_btn[0])
            else:  # inserted
                cancel_text = self.driver.find_elements(By.XPATH, './/span[text()=\'취소\']')
                if cancel_text:
                    cancel_text = cancel_text[0]
                    cancel_btn = cancel_text.find_element(By.XPATH, 'parent::button[1]')
                    self.click_element(cancel_btn)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/span[contains(text(), \'제목\')]')))
        title_area = self.driver.find_element(By.XPATH, './/span[contains(text(), \'제목\')]')
        title_area.click()
        pyperclip.copy(title)
        keyboard.send_keys('^v')
        time.sleep(0.2)

    def open_target_sticker_tab(self, target_num):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'sticker\']')))
        sticker_icon = self.driver.find_element(By.XPATH, './/button[@data-name = \'sticker\']')
        sticker_icon.click()
        time.sleep(0.8)
        while True:
            selected_title = self.driver.find_element(By.XPATH, './/strong[@class=\'se-panel-title\']').text
            if selected_title.strip() == '스티커':
                break
            sticker_icon.click()
            time.sleep(0.8)
        sticker_tab_li = self.driver.find_element(By.XPATH, './/ul[@class=\'se-panel-tab-list\']')
        sticker_tab_li = sticker_tab_li.find_elements(By.TAG_NAME, 'li')
        if len(sticker_tab_li) >= target_num[0]:
            target_sticker_tab = sticker_tab_li[target_num[0]]
            WebDriverWait(target_sticker_tab, 10).until(EC.element_to_be_clickable((By.TAG_NAME, 'button')))
            target_sticker_tab = target_sticker_tab.find_element(By.TAG_NAME, 'button')
            target_sticker_tab.click()
            time.sleep(0.8)
            sticker_li = self.driver.find_elements(By.XPATH, './/li[@class=\'se-sidebar-item\']')
            target_sticker = sticker_li[target_num[1]]
            sticker_btn = target_sticker.find_element(By.TAG_NAME, 'button')
            sticker_btn.click()
            time.sleep(0.8)
            return True
        return False

    def upload_nblog_post(self, keyword, naver_id, value):
        naver_id = naver_id
        naver_pw = value['pw']
        naver_blog_id = value['blog_id']
        self.prepare_before_post(naver_id, naver_pw, naver_blog_id)
        contents = keyword.nblog_content
        if keyword.posting_title!= '':
            title = keyword.posting_title
            contents = re.sub('<b>(.*)</b>', f'<b>{title}</b>', contents)
        else:  # inserted
            title = re.findall('<title>(.*)</title>', contents)[0]
        self.write_title(title)
        keyboard.send_keys('{TAB}{ENTER}')
        time.sleep(0.2)
        contents = re.sub('<title>(.*)</title>', '', contents).strip('\n')
        contents = contents.replace('<horizontal-line>\n\n', '<horizontal-line>\n')
        contents = contents.replace(']\n\n', ']\n')
        contents = contents.replace('>\n\n', '>\n')
        if keyword.last_text:
            contents += f'\n\n{keyword.last_text}'
        self.write_body(keyword.main_keyword, keyword.photo_cnt, contents, keyword.place_keyword)
        backlink_li = self.get_random_backlink()
        if BACKLINK_YN and backlink_li:
            self.add_horizontal_line()
            pyperclip.copy('도움이 될만한 다른 정보들 👇')
            keyboard.send_keys('^v')
            keyboard.send_keys('{ENTER}')
            for backlink in backlink_li:
                self.add_link(backlink)
                time.sleep(0.5)
        self.publish(keyword)
        self.driver.switch_to.window(self.driver.window_handles[0])

    def add_map(self, place_keyword):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'map\']')))
        map_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'map\']')
        map_icon.click()
        time.sleep(2)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/div[@class=\'se-place-search-keyword\']//input')))
        title_input = self.driver.find_element(By.XPATH, './/div[@class=\'se-place-search-keyword\']//input')
        title_input.send_keys(place_keyword)
        keyboard.send_keys('{ENTER}')
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, './/ul[@class=\'se-place-map-search-result-list\']')))
        result = self.driver.find_element(By.XPATH, './/ul[@class=\'se-place-map-search-result-list\']')
        target_result = None
        if target_result is None:
            first_result = result.find_element(By.TAG_NAME, 'li')
            target_idx = 0
            first_result.click()
        else:  # inserted
            target_result.click()
        time.sleep(2)
        WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, './/button[@class=\'se-place-add-button\']')))
        add_btn = self.driver.find_elements(By.XPATH, './/button[@class=\'se-place-add-button\']')[target_idx]
        add_btn.click()
        time.sleep(2)
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-button.se-popup-button-confirm')))
        confirm_btn = self.driver.find_element(By.CLASS_NAME, 'se-popup-button.se-popup-button-confirm')
        confirm_btn.click()
        time.sleep(2)

    def add_link(self, link):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'oglink\']')))
        oglink_btn = self.driver.find_element(By.XPATH, './/button[@data-name=\'oglink\']')
        oglink_btn.click()
        time.sleep(2)
        html = self.driver.page_source
        soup = bs(html, 'html.parser')
        if not soup.find('input', {'class': 'se-popup-oglink-input'}):
            keyboard.send_keys('{TAB}')
            keyboard.send_keys('{TAB}')
            keyboard.send_keys('{ENTER}')
            time.sleep(0.2)
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-oglink-input')))
        except:
            return
        else:  # inserted
            self.driver.find_element(By.CLASS_NAME, 'se-popup-oglink-input').send_keys(link)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'se-popup-oglink-button')))
            icon_btn = self.driver.find_element(By.CLASS_NAME, 'se-popup-oglink-button')
            icon_btn.click()
            time.sleep(1)
            try:
                WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, 'se-popup-button.se-popup-button-confirm')))
                succeed = True
            except:
                succeed = False
        else:  # inserted
            if succeed:
                target_btn = self.driver.find_element(By.CLASS_NAME, 'se-popup-button.se-popup-button-confirm')
            else:  # inserted
                target_btn = self.driver.find_element(By.XPATH, './/button[@data-log=\'pog.close\']')
        self.click_element(target_btn)
        time.sleep(3)

    def publish(self, keyword):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[contains(@class, \'publish_btn\')]')))
        publish_btn = self.driver.find_element(By.XPATH, './/button[contains(@class, \'publish_btn\')]')
        self.click_element(publish_btn)
        reserved = False
        if re.findall('[\\d]{8} [012][\\d]:[012345][\\d]', keyword.reserved_time):
            if keyword.reserved_time <= datetime.now().strftime('%Y%m%d %H:%M'):
                print('지정된 예약시간이 현재 시간보다 빨라 바로 발행됩니다.\n')
            else:  # inserted
                reserved = True
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/label[@for=\'radio_time2\']')))
                reserve_radio = self.driver.find_element(By.XPATH, './/label[@for=\'radio_time2\']')
                self.click_element(reserve_radio)
                while True:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/input[contains(@class, \'input_date\')]')))
                    input_date = self.driver.find_element(By.XPATH, './/input[contains(@class, \'input_date\')]')
                    self.click_element(input_date)
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ui-datepicker-month')))
                    calendar_month = self.driver.find_element(By.CLASS_NAME, 'ui-datepicker-month').text.strip('월').zfill(2)
                    if keyword.reserved_time[4:6]!= calendar_month:
                        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@title=\'다음달\']')))
                        next_month_btn = self.driver.find_element(By.XPATH, './/button[@title=\'다음달\']')
                        self.click_element(next_month_btn)
                    else:  # inserted
                        break
                date_li = self.driver.find_elements(By.TAG_NAME, 'td')
                for date in date_li:
                    if date.text.zfill(2) == keyword.reserved_time[6:8]:
                        date_btn = date.find_element(By.TAG_NAME, 'button')
                        self.click_element(date_btn)
                        break
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/select[contains(@class, \'hour_option\')]')))
                hour_option = self.driver.find_element(By.XPATH, './/select[contains(@class, \'hour_option\')]')
                hour_select = Select(hour_option)
                hour_select.select_by_value(keyword.reserved_time[9:11])
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/select[contains(@class, \'minute_option\')]')))
                minute_option = self.driver.find_element(By.XPATH, './/select[contains(@class, \'minute_option\')]')
                minute_select = Select(minute_option)
                minute_select.select_by_value(keyword.reserved_time[12:13] + '0')
        url_before_published = self.driver.current_url
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[contains(@class, \'confirm_btn\')]')))
        confirm_btn = self.driver.find_element(By.XPATH, './/button[contains(@class, \'confirm_btn\')]')
        self.click_element(confirm_btn)
        WebDriverWait(self.driver, 20).until(EC.url_changes(url_before_published))
        keyword.nblog_uploaded_link = self.driver.current_url
        if reserved:
            print(f'👀 {keyword.reserved_time}에 포스팅 발행이 예약되었습니다.\n')
            result = '예약 발행 완료'
            keyword.result = result
        else:  # inserted
            print('👀 포스팅이 발행되었습니다.\n')
            result = '발행 완료'
            keyword.result = result

    def write_body(self, keyword, photo_cnt, contents, place_keyword):
        if ADVERTISE_ON:
            pyperclip.copy(ADVERTISEMENT_TEXT)
            keyboard.send_keys('^v')
            keyboard.send_keys('{ENTER}')
            self.add_link(ADVERTISEMENT_LINK)
            self.add_horizontal_line()
        content_li = contents.split('\n')
        for content in content_li:
            if re.findall('<b>(.*)</b>', content):
                bold_text = re.findall('<b>(.*)</b>', content)[0]
                self.add_bold_text(bold_text)
                self.set_text()
                continue
            if 'horizontal-line' in content.strip():
                self.add_horizontal_line()
                continue
            if '[썸네일]' in content.strip():
                self.add_image(f"{keyword.replace('?', '')}_썸네일.jpg")
                time.sleep(0.5)
                keyboard.send_keys('{UP}')
                time.sleep(0.5)
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-log=\'prt.center\']')))
                center_btn = self.driver.find_element(By.XPATH, './/button[@data-log=\'prt.center\']')
                self.click_element(center_btn)
                keyboard.send_keys('{DOWN}')
                time.sleep(0.5)
            else:  # inserted
                if '[스티커]' in content.strip():
                    self.add_sticker()
                else:  # inserted
                    if re.findall('<h1>(.*)</h1>', content):
                        h1_title = re.findall('<h1>(.*)</h1>', content)[0]
                        self.add_title(h1_title, 'postit')
                        self.set_text()
                    else:  # inserted
                        if re.findall('<h2>(.*)</h2>', content):
                            h2_title = re.findall('<h2>(.*)</h2>', content)[0]
                            self.add_title(h2_title, 'quotation')
                        else:  # inserted
                            if re.findall('\\[이미지(\\d)-이미지(\\d)\\]', content):
                                image_li = re.findall('\\[이미지(\\d)-이미지(\\d)\\]', content)
                                first_idx = int(image_li[0][0])
                                second_idx = int(image_li[0][1])
                                first_image = f"{keyword.replace('?', '')}_{int(image_li[0][0])}.jpg"
                                second_image = f"{keyword.replace('?', '')}_{int(image_li[0][1])}.jpg"
                                if first_idx < photo_cnt and second_idx < photo_cnt:
                                    self.add_multi_images([first_image, second_image])
                                else:  # inserted
                                    if first_idx < photo_cnt:
                                        self.add_image(first_image)
                            else:  # inserted
                                if re.findall('\\[이미지(\\d)\\]', content):
                                    image_idx = re.findall('\\[이미지(\\d)\\]', content)[0]
                                    if int(image_idx) < photo_cnt:
                                        self.add_image(f"{keyword.replace('?', '')}_{int(image_idx)}.jpg")
                                else:  # inserted
                                    if content == '':
                                        keyboard.send_keys('{ENTER}')
                                        time.sleep(0.2)
                                    else:  # inserted
                                        if re.findall('<hashtags>(.*)</hashtags>', content):
                                            hashtags = re.findall('<hashtags>(.*)</hashtags>', content)[0]
                                            pyperclip.copy(hashtags)
                                            keyboard.send_keys('^v')
                                            time.sleep(0.2)
                                            keyboard.send_keys('{ENTER}')
                                            time.sleep(0.2)
                                        else:  # inserted
                                            pyperclip.copy(content)
                                            keyboard.send_keys('^v')
                                            time.sleep(0.2)
                                            keyboard.send_keys('{ENTER}')
                                            time.sleep(0.2)
        if place_keyword:
            self.add_map(place_keyword)
        if LAST_ADD_IMG:
            for img in LAST_ADD_IMG:
                self.add_image(img, photos=False)

    def add_title(self, title, data_type):
        quotation_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'quotation\' and @aria-haspopup=\'true\']')
        quotation_icon.click()
        time.sleep(1)
        if data_type == 'quotation':
            data_value = 'quotation_underline'
        else:  # inserted
            if data_type == 'postit':
                data_value = 'quotation_postit'
        pass
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, f'.//button[@data-value=\'{data_value}\']')))
            except:
                quotation_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'quotation\' and @aria-haspopup=\'true\']')
                quotation_icon.click()
                time.sleep(1)
            else:  # inserted
                break
                quotation_btn = self.driver.find_element(By.XPATH, f'.//button[@data-value=\'{data_value}\']')
                quotation_btn.click()
                time.sleep(1)
                pyperclip.copy(title)
                keyboard.send_keys('^v')
                time.sleep(0.8)
                keyboard.send_keys('{DOWN}')
                time.sleep(0.8)
                keyboard.send_keys('{DOWN}')
                time.sleep(0.8)
                keyboard.send_keys('{ENTER}')
                time.sleep(1)

    def add_sticker(self):
        target_num = random.choice([[5, 0], [5, 2], [5, 5], [5, 11], [5, 12], [5, 19], [3, 5], [3, 9], [3, 15], [3, 3], [3, 13], [4, 1], [4, 13], [4, 14], [4, 24], [4, 25]])
        while True:
            html = self.driver.page_source
            soup = bs(html, 'html.parser')
            if soup.find('button', {'class': 'se-help-panel-close-button'}):
                close_btn = self.driver.find_element(By.XPATH, './/button[@class=\'se-help-panel-close-button\']')
                close_btn.click()
                time.sleep(0.8)
            else:  # inserted
                break
        for _ in range(10):
            if self.open_target_sticker_tab(target_num):
                break
        sticker_icon = self.driver.find_element(By.XPATH, './/button[@data-name = \'sticker\']')
        sticker_icon.click()
        time.sleep(0.8)

    def add_multi_images(self, file_name_li):
        file_path_li = [f'./photos/{file_name}0' for file_name in file_name_li]
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'image\']')))
        photo_icon = self.driver.find_element(By.XPATH, './/button[@data-name = \'image\']')
        photo_icon.click()
        for _ in range(5):
            try:
                app = Application(backend='win32').connect(title='열기', timeout=3)
                dialog = app.top_window()
                if dialog:
                    pass  # postinserted
                except:
                    pass
            else:  # inserted
                break
                time.sleep(1)
            file_path_li = ['\"' + os.getcwd() + file_path.lstrip('.').replace('/', '\\') + '\"' for file_path in file_path_li]
            pyperclip.copy(' '.join(file_path_li))
            keyboard.send_keys('^v')

    def add_image(self, file_name, photos=True):
        while True:
            html = self.driver.page_source
            if '업로드중에는일부기능을' in html.replace(' ', ''):
                time.sleep(1)
            else:  # inserted
                break
                continue
        if photos:
            file_path = f'./photos/{file_name}0'
        else:  # inserted
            file_path = f'./assets/{file_name}0'
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'image\']')))
        photo_icon = self.driver.find_element(By.XPATH, './/button[@data-name = \'image\']')
        photo_icon.click()
        for _ in range(5):
            try:
                app = Application(backend='win32').connect(title='열기', timeout=3)
                dialog = app.top_window()
                if dialog:
                    pass  # postinserted
                except:
                    pass
            else:  # inserted
                break
                time.sleep(1)
            file_path = os.getcwd() + file_path.lstrip('.').replace('/', '\\')
            pyperclip.copy(file_path)
            keyboard.send_keys('^v')
            time.sleep(0.8)
            keyboard.send_keys('{ENTER}')
            time.sleep(1)

    def add_horizontal_line(self):
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-name=\'horizontal-line\' and @aria-haspopup=\'true\']')))
        horizontal_line_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'horizontal-line\' and @aria-haspopup=\'true\']')
        horizontal_line_icon.click()
        time.sleep(0.8)
        while True:
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-value=\'line1\']')))
            except:
                horizontal_line_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'horizontal-line\' and @aria-haspopup=\'true\']')
                horizontal_line_icon.click()
                time.sleep(1)
            else:  # inserted
                break
                horizontal_line_btn = self.driver.find_element(By.XPATH, './/button[@data-value=\'line1\']')
                horizontal_line_btn.click()
                time.sleep(1)

    def add_bold_text(self, text):
        text_format_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'text-format\' and @aria-haspopup=\'true\']')
        text_format_icon.click()
        time.sleep(1)
        while True:
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, './/button[@data-value=\'sectionTitle\']')))
            except:
                text_format_icon = self.driver.find_element(By.XPATH, './/button[@data-name=\'text-format\' and @aria-haspopup=\'true\']')
                text_format_icon.click()
                time.sleep(1)
            else:  # inserted
                break
                section_title_btn = self.driver.find_element(By.XPATH, './/button[@data-value=\'sectionTitle\']')
                section_title_btn.click()
                time.sleep(1)
                pyperclip.copy(text)
                keyboard.send_keys(text.replace(' ', '{SPACE}'))
                time.sleep(0.8)
                keyboard.send_keys('{ENTER}')
                time.sleep(0.8)

    def click_element(self, element):
        self.move_to_element(element)
        try:
            self.driver.execute_script('arguments[0].click();', element)
            self.random_sleep()
        except:
            element.click()
            self.random_sleep()

    def random_sleep(self):
        sleep_time = random.uniform(1, 3)
        time.sleep(sleep_time)

    def move_to_element(self, element):
        try:
            self.actions.move_to_element(element).perform()
        except:
            return None