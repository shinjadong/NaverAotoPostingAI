# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: imagehelper.py
# Bytecode version: 3.12.0rc2 (3531)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from settings import *
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from openai import OpenAI
import urllib

class ImageHelper:

    def __init__(self):
        self.image_client = OpenAI(api_key=OPENAI_API_KEY)

    def create_image(self, keyword, sumnail_template, text_color):
        subject = keyword.main_keyword
        cnt = keyword.photo_cnt
        response = self.image_client.images.generate(model='dall-e-3', prompt=f"A realistic, clean, and visually appealing sumnail image illustrating the concept of '{keyword}'. The image should be simple and focus on the essence of the keyword, suitable for use in a blog post, but without no words or text. Natural lighting, a balanced composition, and a neutral or lightly textured background. If applicable, include a person or objects that directly relate to the concept, ensuring a professional and polished look. DON'T INCLUDE TEXT", size='1024x1024', quality='standard', n=1)
        image_url = response.data[0].url
        urllib.request.urlretrieve(image_url, f"./photos/{subject.replace('?', '')}_썸네일.jpg")
        self.resize_image(f"./photos/{subject.replace('?', '')}_썸네일.jpg")
        self.create_sumnail_image(subject, f"./photos/{subject.replace('?', '')}_썸네일.jpg", sumnail_template, text_color)
        for idx in range(cnt):
            response = self.image_client.images.generate(model='dall-e-3', prompt=f"A realistic, clean, and visually appealing image illustrating the concept of '{keyword}'. The image should be simple and focus on the essence of the keyword, suitable for use in a blog post, but without no words or text. Natural lighting, a balanced composition, and a neutral or lightly textured background. If applicable, include a Korean person or objects that directly relate to the concept, ensuring a professional and polished look. DON'T INCLUDE TEXT", size='1024x1024', quality='standard', n=1)
            image_url = response.data[0].url
            urllib.request.urlretrieve(image_url, f"./photos/{subject.replace('?', '')}_{idx}.jpg")
            if IMAGE_CHANGE:
                self.transform_image(f"./photos/{subject.replace('?', '')}_{idx}.jpg")

    def create_sumnail_image(self, title, created_image, sumnail_template, text_color):
        sumnail_image = created_image
        if not text_color:
            text_color = '#000'
        img = Image.open(sumnail_image)
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(0.5)
        if sumnail_template:
            template = Image.open(f'./assets/{sumnail_template}0')
            img.paste(template, (0, 0), template)
        if LOGO_FILE_NAME != '':
            logo = Image.open(f'./assets/{LOGO_FILE_NAME}0')
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            logo = logo.resize((int(img.width * 0.1), int(img.width * 0.1 * logo.height / logo.width)), Image.Resampling.LANCZOS)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.paste(logo, (img.width - logo.width - 15, img.height - int(logo.height) - 15), logo)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(created_image, 'JPEG', quality=95)
        self.add_centered_text_with_border(title, text_color, sumnail_image)
    pass
    pass
    pass
    pass

    def add_centered_text_with_border(self, title, text_color, sumnail_file, font_path='./assets/Recipekorea.ttf', font_size=60, border_color='white', border_width=0):
        if len(title) >= 5:
            if ' ' in title:
                title_splited_li = title.split(' ')
                title_splited_li_len = len(title_splited_li)
                title_splited = ' '.join(title_splited_li[:title_splited_li_len // 2]) + '\n' + ' '.join(title_splited_li[title_splited_li_len // 2:])
            else:
                title_splited = title[:len(title) // 2].strip() + '\n' + title[len(title) // 2:].strip()
        else:
            title_splited = title
        try:
            img = Image.open(sumnail_file)
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(font_path, font_size)
            image_width, image_height = img.size
            bbox = draw.textbbox((0, 0), title_splited, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (image_width - text_width) // 2
            text_y = (image_height - text_height) // 2
            for dx in range(-border_width, border_width + 1):
                for dy in range(-border_width, border_width + 1):
                    if dx != 0 or dy != 0:
                        draw.multiline_text((text_x + dx, text_y + dy), title_splited, font=font, fill=border_color, align='center', spacing=20)
            draw.multiline_text((text_x, text_y), title_splited, font=font, fill=text_color, align='center', spacing=20)
            img.save(sumnail_file)
        except UnicodeDecodeError as e:
            print(f'UnicodeDecodeError: {e}')
        except FileNotFoundError as e:
            print(f'FileNotFoundError: {e}')
        except Exception as e:
            print(f'An error occurred: {e}0')
    pass
    pass
    pass
    pass
    pass
    pass

    def add_text_with_border(self, img, title, text_color='white', font_path='./assets/Recipekorea.ttf', font_size=25, border_color='black', border_width=2, margin_ratio=0.04):
        try:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(font_path, font_size)
            image_width, image_height = img.size
            text_x = image_width * margin_ratio
            text_y = image_height * margin_ratio
            for dx in range(-border_width, border_width + 1):
                for dy in range(-border_width, border_width + 1):
                    if dx != 0 or dy != 0:
                        draw.multiline_text((text_x + dx, text_y + dy), title, font=font, fill=border_color, anchor='la', align='left')
            draw.multiline_text((text_x, text_y), title, font=font, fill=text_color, anchor='la', align='left')
            return img
        except UnicodeDecodeError as e:
            print(f'UnicodeDecodeError: {e}')
        except FileNotFoundError as e:
            print(f'FileNotFoundError: {e}')
        except Exception as e:
            print(f'An error occurred: {e}0')

    def resize_image(self, image_path):
        img = Image.open(image_path)
        img = img.resize((600, 600))
        file_extension = image_path.lower().split('.')[-1]
        if file_extension == 'png':
            img.save(image_path, 'PNG')
            return img
        img = img.convert('RGB')
        img.save(image_path, 'JPEG', quality=95)
        return img

    def transform_image(self, image_path):
        """
        size : 600x600
        색처리 : 밝기 -30 / 대비 -15 / 채도 +10

        """
        img = self.resize_image(image_path)
        if LOGO_FILE_NAME != '':
            logo = Image.open(f'./assets/{LOGO_FILE_NAME}0')
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            logo = logo.resize((int(img.width * 0.1), int(img.width * 0.1 * logo.height / logo.width)), Image.Resampling.LANCZOS)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.paste(logo, (img.width - logo.width - 15, img.height - int(logo.height) - 15), logo)
        file_extension = image_path.lower().split('.')[-1]
        if file_extension == 'png':
            img.save(image_path, 'PNG')
        else:
            img = img.convert('RGB')
            img.save(image_path, 'JPEG', quality=95)