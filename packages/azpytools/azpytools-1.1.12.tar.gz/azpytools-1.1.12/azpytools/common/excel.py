
import pandas as pd

class excel:
    # df['销售额'] = df['访客数'] * df['转化率'] * df['客单价']
    def __init__(self) -> None:
        pass

    @staticmethod
    def record_count(file_in,file_result,fields):
        # 统计重复项
        # 调用方法
        # 统计 date1 ，uname 记录数
        # excel.record_count(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_count.xlsx',fields = ['date1','uname'])

        df1 = pd.read_excel(file_in)
        df1.dropna() # 删除所有包含空值的⾏
        # df_result = df1[fields].duplicated()
        df_result = df1.groupby(fields)[fields[0]].count().reset_index(name="count_1")
        # df_result['销售额'] = df_result['count_1'] * 10
        # df_result = df1.groupby(fields).count.reset_index(name=field_sum).sort_values(field_sum,ascending=False)
        # df_result = df1[df1[fields].duplicated()].count()
        df_result.to_excel(file_result,index=False)

    @staticmethod
    def record_duplicates(file_in,file_result,fields):
        # 去重
        # excel.record_duplicates(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_duplicates.xlsx',fields = ['date1','uname'])
        # df['city'].drop_duplicates()#将city列中的重复值删除，默认保留第一个出现的
        # df['city'].drop_duplicates(keep='last')#将city列中的重复值删除，默认保留最后一个
        df1 = pd.read_excel(file_in)
        df_result = df1.drop_duplicates(subset = fields,keep='first')
        df_result.to_excel(file_result,index=False)

    @staticmethod
    def record_sort(file_in,file_result,fields,ascendings):
        # 排序
        # excel.record_sort(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_sort.xlsx',fields = ['date1','uname'],ascendings=[False,True] )
        df1 = pd.read_excel(file_in)
        # df.sort_values([col1,col2],ascending=[True,False]) # 先按列col1升序排列，后按col2降序排列数据
        df_result = df1.sort_values(fields,ascending=ascendings)
        df_result.to_excel(file_result,index=False)

    @staticmethod
    def record_replace(file_in,file_result,values_old,values_new):
        #单元格数值替换 values_old,values_new
        # excel.record_replace(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_replace.xlsx',values_old= [r'.',150],values_new= ["",680])
        df1 = pd.read_excel(file_in)
        # replace([1,3],['one','three']) # ⽤'one'代替1，⽤'three'代替3
        # for field in fields:
        #      for i in range(len(values_old)):
        #         #   print(f'{field},{values_old[i]},{values_new[i]} ')
        #             df_result = df1[field].replace(values_old[i],values_new[i],True)
        df_result = df1.replace(values_old,values_new)
        df_result.to_excel(file_result,index=False)

    @staticmethod
    def cell_replace_char(file_in,file_result,fields,values_old,values_new):
        #单元格中字符替换 values_old,values_new
        # excel.cell_replace_char(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_replace_char.xlsx',fields = ['date1','uname'],values_old= r'.',values_new="")
        df1 = pd.read_excel(file_in)
        for index,row in df1.iterrows():
            for field in fields:
                df1.loc[index:index,(field)] = row.get(field).replace(values_old,values_new)
        df1.to_excel(file_result,index=False)

    @staticmethod
    def cell_sign_left(file_in,file_result,fields):
        # 负号提前
        # excel.cell_sign_left(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_sign_left.xlsx',fields = ['QTY'])
        df1 = pd.read_excel(file_in)
        for index,row in df1.iterrows():
            for field in fields:
                cellvalue = row.get(field)
                # print(type(cellvalue))
                if type(cellvalue) == str:
                    # print(type(-13.33))
                    # print(cellvalue[-1:])
                    # print('-' + cellvalue[:-1])
                    df1.loc[index:index,(field)] = float(cellvalue if cellvalue[-1:] != '-' else '-' + cellvalue[:-1])
        df1.to_excel(file_result,index=False)


    @staticmethod
    def record__group(file_in,file_result,fields,field_sum):
        # 分组,汇总
        # excel.record__group(file_in = r'E:\data\data1.xlsx',file_result=r'E:\data\tresult_group.xlsx',fields = ['date1','uname'],field_sum = 'QTY')
        new_sum_field_name = field_sum + "_SUM"
        df1 = pd.read_excel(file_in)
        # df1.append(df2) # 将df2中的⾏添加到df1的尾部
        # groupby('品牌')['销售额'].sum().reset_index().sort_values('销售额', ascending=False)
        df_result = df1.groupby(fields)[field_sum].sum().reset_index(name=new_sum_field_name).sort_values(new_sum_field_name,ascending=False)  # 返回⼀个按多列进⾏分组的Groupby对象
        # df.groupby(col1)[col2].agg(mean) # 返回按列col1进⾏分组后，列col2的均值,agg可以接受列表参数，agg([len,np.mean])
        df_result.to_excel(file_result,index=False)

    @staticmethod
    def vlook(dat_left,dat_right,dat_result,left_fields,right_fields):
        # 连接
        # dat_left 与dat_right 通过 dat_left.left_fields = dat_right.right_fields 关联
        # 结果放在dat_result中
        # left_fields : 表1 关联字段名称: ['matnr','mat1']
        # right_field: 表2 关联字段名称: ['mat','mat_1']
        # dat_left 与dat_right 通过 dat_left.left_fields = dat_right.right_fields 关联
        # 结果放在dat_result中
        # excel.vlook(dat_left=r'E:\data\data1.xlsx',dat_right=r'E:\data\data2.xlsx',dat_result=r'E:\data\tresult_vlook.xlsx',left_fields=['matnr','mat1'],right_fields=["mat","mat_1"] )


        # 读入表1
        df1 = pd.read_excel(dat_left)
        # 读入表2
        df2 = pd.read_excel(dat_right)
        # 关联数据
        #  how 参数： left ,right,inner
        data = df1.merge(df2, left_on=left_fields,right_on=right_fields,how = "left",left_index=False, right_index=False, sort=False)
        data.to_excel(dat_result,index=False)

        # 单个字段关联
        # df_meg = pd.merge(left= df1,right=df2,left_on = "matnr",right_on="mat")
        # data = df1.merge(df2, left_on=['matnr','mat1'],right_on=["mat","mat_1"],how = "left",left_index=False, right_index=False, sort=False)
        # data1 = df1.merge(df2, left_on='matnr',right_on="mat",how = "inner",left_index=False, right_index=False, sort=False)

