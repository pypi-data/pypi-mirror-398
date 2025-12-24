from pypinyin import pinyin, lazy_pinyin, Style #pip install pypinyin 
#hzList 汉字词的列表
def get_pinin( hzList):
    result = []
    for hz in hzList:
        pinyin = lazy_pinyin(hz) #pinyin(hanzi, style=Style.NORMAL)
        pinyinszm = ''
        for py in pinyin:
            pinyinszm += py[0]
        rs = {
            'hanzi':hz,  #汉字
            'pingyin':pinyin,  #拼音
            'pingyinszm':pinyinszm.upper() #拼音首字母
        }
        result.append(rs)
    return result
