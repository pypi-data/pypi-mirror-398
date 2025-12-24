import re
import base64
import hashlib
from Crypto.Cipher import AES  # pip install pycryptodome
import itertools
from azpytools.configwrite import configparser



#基本工具函数
class Utils:
    
    @staticmethod
    def regexpFindDataInString(allString , strTemplate , data  )->list:
        # ss = strTemplate
        firstIndex = strTemplate.find(data) 
        if firstIndex == -1:
            return []
        lastIndex = firstIndex + len(data)
        if lastIndex > len(strTemplate) :
            return []
        regString = strTemplate[:firstIndex] + "(.*?)" + strTemplate[lastIndex:]
        result = re.findall(regString,allString)
        return result

    # inList:候选元素
    # resultNum：选出元素个数
    # calType：排列还是组合，C-组合，P-排列
    @staticmethod
    def getPLZH(inList:list,resultNum = 1,calType = 'C' ):
        sourceData = [i for i in inList]
        retNum = resultNum
        if len(sourceData) == 0 or resultNum == 0:
            return None
        if len(sourceData) < resultNum:
            retNum = len(sourceData)
        resultLists=[]
        counter = 0
        if calType == 'P':
        # 排列
            for p in itertools.permutations(sourceData,retNum):
                if not p is None: 
                    resultLists.append(p)
        else:
        # 组合 
            for c in itertools.combinations(sourceData,retNum): #打乱不重复组合
                if not c is None: 
                    resultLists.append(c)
        return resultLists	
    
    # 根据关键字，返回另一个字段值
    @staticmethod
    def getValueFromListByKey(dataList:list,keyFiled , keyValue,returnField ):
        lst = dataList
        returnValue = None
        try:
            if keyValue  in [dict.get(keyFiled) for dict in lst ]:
                dict = sorted(lst,key = lambda dicts:dicts[keyFiled] != keyValue)[0]
                returnValue = dict.get(returnField)
            else:
                returnValue = None 
        except:
            returnValue = None 
        return  returnValue  
    # 根据关键字，返回另一个字段值
    @staticmethod
    def getDictFromListByKey(dataList:list,keyFiled,keyValue ):
        lst = dataList
        returnValue = None
        try:
            if keyValue  in [dict.get(keyFiled) for dict in lst ]:
                dict = sorted(lst,key = lambda dicts:dicts[keyFiled] != keyValue)[0]
                returnValue = dict
            else:
                returnValue = None 
        except:
            returnValue = None 
        return  returnValue  
    
class Encrypt:
    
    @staticmethod
    def encryptBase64(_string):
        # return base64.b64encode(_string.eccode('utf-8'))
        return base64.b64encode(_string.encode('utf-8')).decode()
    
    @staticmethod
    def decryptBase64(_string):
        return base64.b64decode(_string).decode()
    
    # MD5加密(不可逆)
    """
MD5 Message-Digest Algorithm，一种被广泛使用的密码散列函数，可以产生出一个128位(16字节)的散列值(hash value)，
用于确保信息传输完整一致。MD5是最常见的摘要算法，速度很快，生成结果是固定的128 bit字节，通常用一个32位的16进制字符串表示。
update() 方法内传参为二进制数据  所以需要将字符串数据 encode()
作用：加密用户密码；保证数据唯一性（MD5可以保证唯一性）;比较文件是否被篡改等
"""
    @staticmethod
    def getMD5(string):
        hashMd5 = hashlib.md5()
        hashMd5.update(string.encode("utf-8"))
        return hashMd5.hexdigest()

#  SHA1加密（不可逆）
# """
# SHA1的全称是Secure Hash Algorithm(安全哈希算法) 。SHA1基于MD5，加密后的数据长度更长，
# 它对长度小于264的输入，产生长度为160bit的散列值。比MD5多32位,因此，比MD5更加安全，但SHA1的运算速度就比MD5要慢
# """
    @staticmethod
    def getSHA1(string):
        hashSha1 = hashlib.sha1()
        hashSha1.update(string.encode("utf-8"))
        return hashSha1.hexdigest()
  
    @staticmethod
    def encryptAES(_string,_password):
        BLOCK_SIZE = 16  # Bytes
        pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
        if len(_password) % 16:
            add = 16 - (len(_password) % 16)
        else:
            add = 0
        passKey = _password + "_" * add
        passKey = passKey.encode('utf8')
    # 字符串补位
        data = pad(_string)
        cipher = AES.new(passKey, AES.MODE_ECB)
    # 加密后得到的是bytes类型的数据，使用Base64进行编码,返回byte字符串
        result = cipher.encrypt(data.encode())
        encodestrs = base64.b64encode(result)
        enctext = encodestrs.decode('utf8')
        return enctext

    @staticmethod
    def decryptAES(_string,_password):
        unpad = lambda s: s[:-ord(s[len(s) - 1:])]
        if len(_password) % 16:
            add = 16 - (len(_password) % 16)
        else:
            add = 0
        passKey = _password + "_" * add
        passKey = passKey.encode('utf8')
        data = base64.b64decode(_string)
        cipher = AES.new(passKey, AES.MODE_ECB)
    # 去补位
        text_decrypted = unpad(cipher.decrypt(data))
        text_decrypted = text_decrypted.decode('utf8')
        return text_decrypted
    

import tkinter
from tkinter import ttk
class TkinderUtils:
    # font =tkFont.Font(family='宋体',size=10)
    #  widget.bind(sequence,func,add='')
    # 其中，widget 代表控件的控件对象，之后，采用 bind() 方法进行事件绑定，该函数的参数：
    # command 定义方法： 参考：eventTemplate
    # Active	当组件的状态从“未激活”变为“激活”的时候触发该事件
    # Button	<Button-1>鼠标左键，<Button-2>鼠标中键（滚轮点击），<Button-3>鼠标右键，<Button-4>滚轮上滚（
    # Linux），<Button-5>滚轮下滚（Linux）
    # ButtonRelease：当用户释放鼠标按键的时候触发该事件 在大多数情况下，比Button要更好使用，因为如果当用户不小心按下鼠标键，
    #               用户可以将鼠标移出组件再释放鼠标，从而避免不小心触发事件
    # Deactivate	 当组件的状态从“激活”变为“未激活”的时候触发该事件
    # Destroy当组件被销毁时触发该事件
    # Enter	 当鼠标指针进入组件的时候触发该事件 注意：不是用户按下回车键（回车键是Return<Key-Return>）
    # FocusIn	 当组件获得焦点的时候触发该事件 用户可以用Tab键将焦点转移到该组件上（需要该组件的takefocus选项为True）
    #         你也可以调用focus_set()方法使该组件获得焦点
    # FocusOut	当组件失去焦点的时候触发该事件
    # KeyPress	 当用户按下键盘按键的时候触发该事件
    #  detail可以指定具体的按键，例如<KeyPress-H>表示当大写字母H被按下的时候触发该事件
    #  KeyPress可以缩写为Key
    # KeyRelease	当用户释放键盘按键的时候触发该事件
    # Leave	当鼠标指针离开组件的时候触发该事件

    def __init__(self) -> None:
        pass
   
    # 事件模版 func
    def eventTemplate(event,add=''):
        pass
        # event.keycode
        # Return向高级别进行了“传递",调用顺序为instance/class/toplevel/all


    @classmethod
    def createTextEditwithLabel(cls,_parent,_lbText = 'Label',_textVar=None,_lblLen =10,_varLen = 20,_EnterEvent = None,_LeaveEvent=None )->ttk.Frame:
        width = ( _lblLen + _varLen + 1) * 8 
        txtFrame = ttk.Frame(_parent,height=200,width= width)  #height=600,width= 500,
        lbl = cls.createLabelFixText(txtFrame,_lbText,_width = _lblLen)
        lbl.pack(side=tkinter.LEFT,anchor=tkinter.CENTER)
        
        # lbl.grid(row=0,column =0,sticky=tkinter.NW) #. #.place(x=0,y=1)
        txtEdit= cls.createEntry(txtFrame,_textVar =_textVar,_width = _varLen ,_EnterEvent = _EnterEvent,_LeaveEvent=_LeaveEvent)
        txtEdit.pack(side=tkinter.RIGHT,anchor=tkinter.CENTER,padx=5)
        # txtEdit.grid(row=0,column =1,sticky=tkinter.NW) #.pack(side=tkinter.RIGHT)
        return txtFrame

    @classmethod
    def createComboboxWithLabel(cls,_parent,_textVar,_valueList:list,_lbText = 'Label',_labelLen =10,_comboLen = 20,_command=None ,_status = "readonly")->ttk.Frame:
        width = ( _labelLen + _comboLen + 1) * 8 
        txtFrame = ttk.Frame(_parent,height=200,width= width)  #height=600,width= 500,
        lbl = cls.createLabelFixText(txtFrame,_lbText,_width = _labelLen)
        lbl.pack(side=tkinter.LEFT,anchor=tkinter.CENTER)
        
        cbox = cls.createCombobox(txtFrame,_textVar = _textVar,_valueList=_valueList,_status=_status,_width=_comboLen,_command=_command)
        cbox.pack(side=tkinter.RIGHT,anchor=tkinter.CENTER,padx=5)
        return txtFrame
        
    @classmethod
    def createLabelFixText(cls,_parent,_text='',_width = 10  )->tkinter.Label:
        lblObj = tkinter.Label(_parent,text = _text,width=_width,fg="red",anchor='w',justify=tkinter.LEFT )
        # lblObj["font"] = self.font
        return lblObj
    
    @classmethod    
    def createLabelVarText(self,_parent:ttk.Frame,textVar ,_width = 10 ):
        # textVar = StringVar()
        # textVar.set('Labeltext')
        lblObj = tkinter.Label(_parent,textvariable = textVar,width=_width,fg="red",anchor=tkinter.W,justify=tkinter.LEFT )
        # lblObj["font"] = self.font
        return lblObj
    
    @classmethod
    def createCheckBox(self,_parent,_checkVar,_text = 'Checked',_command = None):
        # <Button-1>	鼠标左键单击
        # <Button-2>	鼠标中键单击
        # <Button-3>	鼠标右键单击
        # <Button-4>	鼠标滑轮向上滚动(Linux)
        # <Button-5>	鼠标滑轮向下滚动(Linux)
        # <B1-Motion>	鼠标左键拖动
        # <B2-Motion>	鼠标中键拖动
        # <B3-Motion>	鼠标右键拖动
        # <ButtonRelease-1>	鼠标左键释放
        # <ButtonRelease-2>	鼠标中键释放
        # <ButtonRelease-3>	鼠标右键释放
        # <Double-Button-1>	鼠标左键双击
        # <Double-Button-2>	鼠标中键双击
        # _checkVar = BooleanVar()
        chk = tkinter.Checkbutton(_parent)
        # chk["font"] = self.font
        chk["text"] = _text
        chk["offvalue"] = False
        chk["onvalue"] =  True
        chk["variable"] =  _checkVar
        if _command:
            chk.bind("<Button-1>", _command)
        return chk
    
    # textVar :一下几种类型对象 tkinter.StringVar() ，tkinter.IntVar(),tkinter.DoubleVar()，tkinter.BooleanVar()
    @classmethod
    def createEntry(cls,_parent,_dataType = 'STR',_width=10,_textVar = None,justify = 'left',_EnterEvent = None,_LeaveEvent=None):
        if _textVar:
            entryObj = tkinter.Entry(_parent,textvariable=_textVar,width=_width)
        elif _dataType == 'INT':
            entryObj = tkinter.Entry(_parent,textvariable=tkinter.IntVar(),width=_width)
        elif _dataType == 'QTY':
            entryObj = tkinter.Entry(_parent,textvariable=tkinter.DoubleVar(),width=_width)
        elif _dataType == 'BOOL':
            entryObj = tkinter.Entry(_parent,textvariable=tkinter.BooleanVar(),width=_width)
        else:
            entryObj = tkinter.Entry(_parent,textvariable=tkinter.StringVar(),width=_width)
        entryObj['justify'] = justify
        if _EnterEvent:
            # print(_EnterEvent)
            entryObj.bind('<Return>',_EnterEvent)
        if _LeaveEvent:
            # entryObj.bind('<Leave>',_LeaveEvent)
            entryObj.bind('<FocusOut>',_LeaveEvent)
        return entryObj
    
    @classmethod
    def createCombobox(cls,_parent,_textVar,_valueList:list,_status = "readonly",_width = 10,_command=None ):
        cbox = ttk.Combobox(_parent,width=_width,textvariable=_textVar,state=_status)
        cbox["values"] = [i for i in _valueList]
        if _command:
            cbox.bind("<<ComboboxSelected>>", _command)
        return cbox
        
    @classmethod
    def createButton(cls,_parent,text,command,width = 8,height=1):
        return tkinter.Button(_parent,text=text,command=command,width=width,height=height,justify='center')

    @classmethod
    def createTreeView(cls,_parent,treeviewColumns:list=None,data:list=None,hight = 20 ,widthOpt = True ):
        # 样例        
        tableColumns = [] # ["id","tokenId","5万"]
        ColumnsWidth = [] #[55,55,25]
        if treeviewColumns:
            for col in treeviewColumns:
                tableColumns.append(col.get('name'))
                ColumnsWidth.append(col.get('width'))

        treeview =ttk.Treeview(_parent,columns=tableColumns,
                        show='headings', #show=’tree’ 当然默认的是显示所有列，参数: show=’tree headings’显示列表栏，参数: show=’headings’
                        height=hight,
                        padding=(5,5,5,5))
        for i in range(len(tableColumns)):
            treeview.heading(column=tableColumns[i], text=tableColumns[i],  command=lambda _col =tableColumns[i] : cls.treeViewSortColumn(treeview,_col,True)) # 定义表头anchor=CENTER,
            treeview.column(tableColumns[i], minwidth=5,width=ColumnsWidth[i] ,stretch=True)
        
        # print(treeview["columns"])   
        xscroll = tkinter.Scrollbar(_parent, orient=tkinter.HORIZONTAL)
        yscroll = tkinter.Scrollbar(_parent, orient=tkinter.VERTICAL)
        xscroll.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        yscroll.pack(side=tkinter.RIGHT,fill = tkinter.Y)
        treeview.config(yscrollcommand=yscroll.set)
        treeview.config(xscrollcommand=xscroll.set)
        xscroll.config(command=treeview.xview)
        yscroll.config(command=treeview.yview)
        treeview.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
        cls.treeViewRefresh(treeView=treeview,dataList= data,widthOpt=widthOpt)

    @classmethod
    def  treeViewSortColumn(cls,treeView:ttk.Treeview,col,reverse):       #Treeview、列名、排列方式
        l = [(treeView.set(k,col),k) for k in treeView.get_children('')]
        l.sort(reverse=reverse)    # 排序方式
        for index,(val,k) in enumerate(l):  # 根据排序后索引移动
            treeView.move(k, '', index)
        treeView.heading(col,command=lambda:cls.treeViewSortColumn(treeView,col,not reverse))

    @staticmethod
    def treeViewDeleteSelection(treeView:ttk.Treeview):
        treeView.selection_set("ALL")
        selected_items = treeView.selection()
        for item in selected_items:
            treeView.delete(item)

    @staticmethod
    def treeViewDeleteAll(treeView:ttk.Treeview):
        all_items = treeView.get_children()
        for item in all_items:
            treeView.delete(item)

    @classmethod
    def treeViewRefresh(cls,treeView:ttk.Treeview,dataList:list,widthOpt=True):
        cls.treeViewDeleteAll(treeView)
        if dataList:
            for row in dataList:
                rdata = []
                for colname in treeView['columns']:
                    rdata.append(row.get(colname) if row.get(colname) else '' )
                    if widthOpt and  treeView.column(colname)['width'] < len(str(row.get(colname))*8) :
                        treeView.column(colname,width=len(str(row.get(colname)))*8)
        #     # insert()方法插入数据
                treeView.insert('', 'end',  value=rdata)
        treeView.update()

    # 获取选择行
    @classmethod    
    def treeViewGetSelection(cls,treeView:ttk.Treeview):
        selected = []
        for item in treeView.selection():
            item_text = treeView.item(item,"values")
            selected.append(item_text)
            # print(item_text[0])#输出所选行的第一列的值
        return selected
    