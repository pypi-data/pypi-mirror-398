# 安装pdfkit
# pip install pdfkit
# pip install markdown
# 2、安装wkhtmltopdf
# 3 、pip install Pillow
# 下载地址:https://wkhtmltopdf.org/downloads.html
import os
import markdown
import pdfkit
from PIL import Image
class PDF:
    # 每个url的最大页数为50
    options = {'disable-smart-shrinking':'',
                'lowquality': '',
                'image-quality': 60,
                    'enable-local-file-access':None,   
                'page-height': str(1349.19*0.26458333),
                'page-width': '291',
                'margin-bottom': '0',
                'margin-top': '0',
                }

    @staticmethod
    def markdownToHtml(mdfile):
        filepath = os.path.dirname(mdfile) 
        filename = os.path.splitext(os.path.basename(mdfile))[0]
        filename = filename + '.html'
        htmlfilename = os.path.join(filepath, filename)
        # 读取Markdown文件
        with open(mdfile, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 将Markdown转换为HTML
        html_content = markdown.markdown(md_content)
        htmlHeader = r'<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        htmlfooter = r'</html>'
        html_content = htmlHeader + html_content + htmlfooter
        with open(htmlfilename,'w',encoding='UTF-8') as f:
            f.write(html_content)
        return html_content


    @staticmethod
    def markdownToPDF(mdfile,pdffile):
        filepath = os.path.dirname(mdfile) 
        filename = os.path.splitext(os.path.basename(mdfile))[0]
        filename = filename + '.html'
        htmlfilename = os.path.join(filepath, filename)
        try:
            htmlstring = PDF.markdownToHtml(mdfile)
            PDF.htmlToPdfFromFile(htmlfilename,pdffile)
        except Exception as e:
            print(str(e))
            


    @staticmethod
    def htmlToPdfFromFile(htmlfile,pdffile):
        pdfkit.from_file(htmlfile, pdffile, options= PDF.options)

    @staticmethod
    def htmlToPdfFromUrl(url,pdffile):
        pdfkit.from_url(url, pdffile)

    @staticmethod
    def htmlToPdfFromString(htmlstring,pdffile):
        try:
            pdfkit.from_string(htmlstring,pdffile, options= PDF.options)
        except Exception as e:
            print(str(e))
        
    
    @staticmethod
    def imageToPDF(pdfFileName,imgPath,fileList):
            namelist = fileList 
            firstimg = Image.open(os.path.join(imgPath,namelist[0]))
            firstimg = firstimg.convert('RGB')
            # firstimg.mode = 'RGB'
            imglist = []
            for imgname in namelist[1:]:
                img = Image.open(os.path.join(imgPath,imgname))
                img = img.convert("RGB")
                img.load()
                if img.mode != 'RGB':  # png图片的转为RGB mode,否则保存时会引发异常
                    img.mode = 'RGB'
                imglist.append(img)

            savepath = pdfFileName
            firstimg.save(savepath, "PDF", resolution=100.0,
                        save_all=True, append_images=imglist)