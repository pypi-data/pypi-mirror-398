# 需要安装pytesseract和PIL两个库，然后还要安装tesseract-ocr识别引擎
# pip isntall pytesseract 
# pip isntall pillow 
# pip isntall pillow-pil 
# 以下是关于Tesseract的常用网址
# 下载地址：https://digi.bib.uni-mannheim.de/tesseract/
# 官方网站：https://github.com/tesseract-ocr/tesseract
# 官方文档：https://github.com/tesseract-ocr/tessdoc
# 语言包地址：https://github.com/tesseract-ocr/tessdata

import pytesseract
from PIL import Image

class OCR:
    @staticmethod
    def getText(imgFile,Language='chi_sim'):
        # 打开要识别的图片
        image = Image.open(imgFile)
        # 使用pytesseract调用image_to_string方法进行识别，传入要识别的图片，lang='chi_sim'是设置为中文识别，
        text = pytesseract.image_to_string(image, lang=Language)
        # 输入所识别的文字
        return text

