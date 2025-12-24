import requests
from lxml import etree
import json
import re
import datetime

class spider:
    '''cls_scrapy = spider(url_str,headers)
    htmls = cls_scrapy.html_xpath()
    newlists = htmls.xpath("//span[@class='c-34304b']/div")
    for newlist in newlists:
            data = {}
            str = etree.tostring(newlist,encoding ='utf-8').decode('utf-8')
            data['title'] = re.findall(r"<strong>(.*?)</strong>",str)[0] if re.findall(r"<strong>(.*?)</strong>",str) else None 
    ''' 
    def __init__(self,url,headers) -> None:
        self.session = requests.Session()
        self.__url = url
        self.__headers = headers
        self.response = self.__url_parse()
        self.__html_str = ""
        if self.response.status_code == 200:
            self.__html_str = self.response.content.decode(encoding= 'utf8')
        else:
            self.__html_str = None 
        self.html_list = []
        
    def __url_parse(self) :
        response =  self.session.get(self.__url, headers=self.__headers)
        # response =  requests.get(self.__url, headers=self.__headers)
        return response

    @property 
    def html_str(self):
        return self.__html_str

    def html_xpath(self):
        return etree.HTML(self.__html_str)

    def get_html_json(self):
        data_list = self.html_list
        jsons = json.dumps(data_list,ensure_ascii=False)
        return jsons



class clsSpider():
        url_str = 'https://www.cls.cn/telegraph'
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
               }
               
        def __init__(self,maxpage = 0):
            self.curpage = 0
            self.html_list = []
            self.maxpages = maxpage
            self.get_html_list(datetime.datetime.timestamp(datetime.datetime.now()))
            
        def get_html_list(self,intimestamp):
            self.curpage += 1
            url = "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&category=&lastTime={}".format(intimestamp)
            data_list =[]
            lasttime = 0
            if intimestamp == 0:
                return
            cls_scrapy = spider(url,self.headers)
            htmls = json.loads(cls_scrapy.html_str)['data']['roll_data']
            for newlist in htmls:
                data = {}
                data['from'] = 'CLS.CN'
                data['timestamp'] = newlist['ctime']
                data['date'] = datetime.datetime.strftime( datetime.datetime.fromtimestamp(data['timestamp']),'%Y-%m-%d %H:%M:%S') 
                data['title'] = newlist['title']
                data['text'] = newlist['content'].replace('\n','<br>')
                data['brief'] = newlist['brief']
                if not data['title']:
                    data['title'] = data['brief']
                data_list.append(data)
            if data_list:    
                self.html_list.extend(data_list)
                lasttime = data_list[-1]['timestamp']
            
            if self.curpage <= self.maxpages:
                self.get_html_list(lasttime)
                
class JinseSpider(spider):
        # maxpages = 1
        url_str = 'https://api.jinse.cn/noah/v2/lives?limit=20'
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
               }
               
        def __init__(self,maxpage):
            self.curpage = 0
            self.html_list = []
            self.maxpages = maxpage
            self.get_html_list(0)


            
        def get_html_list(self,id=0):
            url_next = "https://api.jinse.cn/noah/v2/lives?reading=false&sort=&flag=down&id={}&limit=20&_source=m".format(id)
            if id >0 :
                jinse = spider(url_next,self.headers)
            else:
                jinse = spider(self.url_str,self.headers)
            data_list =[]
            self.curpage += 1 
            htmls = jinse.html_str
            newlists = json.loads(htmls)["list"][0]["lives"]
            data_list = [{"from":"JINSE.CN",
                          "title": news["content_prefix"], 
                          "text":news["content"].replace('\n','<br>'),
                          "date":datetime.datetime.strftime(datetime.datetime.fromtimestamp(news["created_at"]),'%Y-%m-%d %H:%M:%S') ,
                          'id':news['id']} for news in newlists]
            self.html_list.extend(data_list) 
            newid = data_list[-1]['id']
            
            if self.curpage <= self.maxpages and newid:
                self.get_html_list(newid)  


class weiboSpider():
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
                }          
        def __init__(self,uuid,cookie):
            self.html_list = []
            self.headers["cookie"] = cookie
            for i in range(2):
                url_str = 'https://weibo.com/ajax/statuses/mymblog?uid={}&page={}&feature=0'.format(uuid,i+1)
                self.html_list.extend(self.get_html_list(url_str))
            
        def get_html_list(self,url_str):
            weibo_scrapy = spider(url_str,self.headers)
            htmls = weibo_scrapy.html_str
            newlists = json.loads(htmls)["data"]["list"]
            data_list = []
            data_list =[{'name':lst['user']['screen_name'], 
                          'title':lst['created_at'],
                          'mblogid':lst['mblogid'], 
                          'date':datetime.datetime.strftime(datetime.datetime.strptime(lst['created_at'],"%a %b %d %H:%M:%S %z %Y"),'%Y-%m-%d %H:%M:%S')  ,
                          'longtext':self.get_longtext(lst['mblogid']) if bool(lst['isLongText'])  else  lst['text'],
                          'text': lst['text_raw']} for lst in newlists ]
            del data_list[0]
            return data_list
            
        
        def get_longtext(self,mblogid):
            longtext = ''
            url_string = "https://weibo.com/ajax/statuses/longtext?id={}".format(mblogid)
            weibo_longtext_scrapy = spider(url_string,self.headers)
        
            htmls = weibo_longtext_scrapy.html_str
            if htmls != None:
                ljson_data = json.loads(htmls).get("data",None)
                if ljson_data != None:
                    longtext = ljson_data.get("longTextContent")
            # longtext = json.loads(htmls)["data"]["longTextContent"]
            return longtext
        
 
class weiboHotSpider():
        url_str = 'https://weibo.com/ajax/statuses/hot_band'
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
                  "x-requested-with":"XMLHttpRequest",
               }          
        def __init__(self,cookie):
            self.headers["cookie"] = cookie
            self.html_list = []
            self.html_list.extend(self.get_html_list())
            
        def get_html_list(self):
            weibo_scrapy = spider(self.url_str,self.headers)
            htmls = weibo_scrapy.html_str
            # print(htmls)
            newlists = json.loads(htmls)["data"]["band_list"]
            # print(newlists)
            data_list = []
            for lst in newlists:
                dats = {}
                # Not AD
                if lst.get("is_ad",None) == None:
                    dats['name'] = 'HOT'
                    dats['title'] = lst['note']
                    dats['hotnum'] = lst['num']  
                    dats['date'] = datetime.datetime.strftime(datetime.datetime.fromtimestamp(lst.get('onboard_time'),None),'%Y-%m-%d %H:%M:%S') 
                    lmblog = lst.get('mblog',None)
                    if lmblog != None:
                        dats['text'] = lmblog.get('text','')  # lst['mblog']['text'] 
                    data_list.append(dats)                          
            return data_list
                
