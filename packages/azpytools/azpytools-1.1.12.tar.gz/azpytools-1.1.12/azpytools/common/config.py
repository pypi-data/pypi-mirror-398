import configparser
import json
import os

class Config(object):
    def __init__(self, config_file='config.ini',rawFlg = True):
        self._path = os.path.join(os.getcwd(), config_file)
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"No such file: {self._path}")
        if rawFlg:
            self._config = configparser.RawConfigParser()
        else:
            self._config = configparser.ConfigParser()
        self._config.read(self._path, encoding='utf-8-sig')
        # self._configRaw = configparser.RawConfigParser()
        # self._configRaw.read(self._path, encoding='utf-8-sig') 
        
    #获取Sections 清单
    def getSections(self):
        return self._config.sections
    
    #获取Item 清单
    def getItems(self,_SectionName):
        if self._config.has_section(_SectionName):
           return self._config.items(_SectionName)
        else:
            return None
    
    #获取单个Item
    def getItem(self,_SectionName,_ItemName):
        if self._config.has_option(_SectionName,_ItemName):
            return self._config.get(_SectionName,_ItemName)
        else:
            return None
    
    def dataToObject(self,_Item):
        if _Item == None:
            return None
        else:
            return json.loads(_Item)
    
    def objectToData(self,Obj):
        return json.dumps(Obj)
    
class ConfigWrite(Config):

    def __init__(self, config_file='config.ini'):
        super().__init__(config_file,True)
        
    #添加section    
    def addSection(self,_SectionName):
        if not self._config.has_section(_SectionName):
            self._config.add_section(_SectionName)
    
    #删除section    
    def delSection(self,_SectionName):
        if self._config.has_section(_SectionName):
            self._config.remove_section(_SectionName)

    #设置配置项    
    def setItem(self,_SectionName,_ItemName,_ItemValue):
        self._config.set(_SectionName,_ItemName,_ItemValue)

    #删除配置项    
    def delItem(self,_SectionName,_ItemName,_ItemValue):
        if self._config.has_option(_SectionName,_ItemName):
            self._config.remove_option(_SectionName,_ItemName,_ItemValue)
        
    def saveConfig(self):
        with open(self._path,'w') as f:
            self._config.write(f)            
    
