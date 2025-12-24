import tushare as ts
import pandas as pd
import akshare as ak
import re

 
class stockAPIAkShare:
    COLUMN_MAP= {'日期':'date', 
                 '股票代码':'code', 
                 '名称':'name', 
                 '板块名称':'name', 
                 '板块代码':'code', 
                #  '最新价':'close', 
                 '代码':'code', 
                  '开盘':'open', 
                  '收盘':'close',
                  '最新价':'close',
                  '市盈率-动态':'pe', 
                  '市净率':'pb', 
                  '最高':'high', 
                  '最低':'low', 
                  '成交量':'volume', 
                  '成交额':'amount', 
                  '振幅':'amplitude', 
                  '涨跌幅':'change_pct', 
                  '涨跌额':'change_amt', 
                  '换手率':'turnover_rate',
                  '总市值':'total_share',
                  '流通市值':'float_share',}
    
    def __init__(self):
        pass
    # 板块
    def get_board_list(self):
        """_获取板块概念列表
        排名	int64	-
        板块名称	object	-
        板块代码	object	-
        最新价	float64	-
        涨跌额	float64	-
        涨跌幅	float64	注意单位：%
        总市值	int64	-
        换手率	float64	注意单位：%
        上涨家数	int64	-
        下跌家数	int64	-
        领涨股票	object	-
        领涨股票-涨跌幅	float64	注意单位：%
        """
        stock_board_concept = ak.stock_board_concept_name_em()
        stock_board_industry = ak.stock_board_industry_name_em()
        retdata = pd.concat([stock_board_concept, stock_board_industry], axis=0)
        retdata.rename(columns=self.COLUMN_MAP, inplace=True)
        return retdata  
    
    def get_board_pe_ratio(self,board_name,date ):
        """_行业市盈率
        变动日期          行业分类  行业层级  ... 静态市盈率-加权平均 静态市盈率-中位数  静态市盈率-算术平均
        """
        return  ak.stock_industry_pe_ratio_cninfo(symbol= board_name, date=date)
    
    def get_board_contain_stock(self,board_name):
        """_获取板块成分股列表
        名称	类型	描述
        序号	int64	-
        代码	object	-
        名称	object	-
        最新价	float64	-
        涨跌幅	float64	注意单位: %
        涨跌额	float64	-
        成交量	float64	注意单位: 手
        成交额	float64	-
        振幅	float64	注意单位: %
        最高	float64	-
        最低	float64	-
        今开	float64	-
        昨收	float64	-
        换手率	float64	注意单位: %
        市盈率-动态	float64	-
        市净率	float64	-
      """
    # 板块成分
        stock_board_concept  = ak.stock_board_concept_cons_em(symbol=board_name)
        if stock_board_concept is None:
            # return stock_board_concept
            stock_board_concept  = ak.stock_board_industry_cons_em(symbol=board_name)
        stock_board_concept.rename(columns=self.COLUMN_MAP, inplace=True)
        return stock_board_concept
        # return stock_board_industry
    
    def get_ticket(self,ts_code):
    # 盘口
        stock_bid = ak.stock_bid_ask_em(symbol=ts_code)
        return stock_bid
    
    def get_minute_history(self,ts_code,start_date,end_date,period='1'):
        # 分时数据
        # period='1'; 获取 1, 5, 15, 30, 60 分钟的数据频率
        # "2024-03-20 09:30:00"
        stock_zh_a_hist_min = ak.stock_zh_a_hist_min_em(symbol=ts_code, start_date=start_date, end_date=end_date, period="1", adjust="qfq")
        return stock_zh_a_hist_min

    # 分时数据-新浪
    # period='1'; 获取 1, 5, 15, 30, 60 分钟的数据频率
    # stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol='sh600751', period='1', adjust="qfq")
    # 分时数据-东财
    # 注意：该接口返回的数据只有最近一个交易日的有开盘价，其他日期开盘价为 0
    def get_minute(self,ts_code,period='1'):
    # 日内分时数据-东财
        stock_intraday = ak.stock_intraday_em(symbol=ts_code)
        return stock_intraday
    
    def get_today_list(self):
        stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
        stock_zh_a_spot_em_df.rename(columns=self.COLUMN_MAP, inplace=True)
        return stock_zh_a_spot_em_df
    
    def get_daily_by_code_list(self,ts_codes,start_date='', end_date=''):
        """根据股票代码清单，获取日线数据

        Args:
            ts_codes (_type_): 多个股票代码，逗号分开，如：'600004,600005'
            start_date (str, optional): 开始日期，如：'20200101'
            end_date (str, optional): 结束日期，如：'20200102' .

        Returns:
            _type_: _description_
        """
        retdata =None
        #根据回车或换行符切割
        codelist = re.split(',|;',ts_codes)
        for code in codelist:
            if code.strip():
                data = self.get_daily_by_code(code.strip(),start_date, end_date)
                if data is not None:
                    if retdata is None:
                        retdata = data
                    else:
                        retdata =pd.concat([retdata,data],axis=0)
        return retdata
 
        
    def get_daily_by_code(self,ts_code,start_date='', end_date=''):
        """根据单个股票代码，获取日线数据

        Args:
            ts_codes (_type_): 股票代码 ，如：'600004'
            start_date (str, optional): 开始日期，如：'20200101'
            end_date (str, optional): 结束日期，如：'20200102' .
"""
        columns = { '日期':'date',
                    '股票代码':'code',
                    '开盘':'open',
                    '收盘':'close',
                    '最高':'high',
                    '最低':'low',
                    '成交量':'volume',
                    '成交额':'amount',
                    # '振幅':'pct_chg',
                    # '涨跌幅',
                    # '涨跌额',
                    # '换手率'
                    }
        # period='daily'; choice of {'daily', 'weekly', 'monthly'}
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=ts_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        stock_zh_a_hist_df.rename(columns=self.COLUMN_MAP, inplace=True)
        return stock_zh_a_hist_df

    def get_code_list(self):
        """_获取股票列表

        Returns:
            code	object	-
         name	object
        """
        stock_info = ak.stock_info_a_code_name()
        return stock_info
    
    def get_basic_data(self,tscode):
        """_获取股票基本信息
        Returns:
            code	object	-
         name	object
        """
        stock_a_indicator = ak.stock_a_indicator_lg(symbol=tscode)
        # stock_a_indicator = ak.stock_value_em(symbol=tscode)
        return stock_a_indicator
    
    
    def get_basic_gdhs_by_date(self,date):
        """股东户数，按日期"""
        try:
            stock_zh_a_gdhs_df = ak.stock_zh_a_gdhs(symbol=date) #每个季度末最后一天
            return stock_zh_a_gdhs_df
        except Exception as e:
            str(e)
            return pd.DataFrame()
        
        
        
    def get_basic_gdhs_by_code(self,tscode):
        """股东户数，按股票代码,包含历史数据"""
        stock_zh_a_gdhs_detail_em_df = ak.stock_zh_a_gdhs_detail_em(symbol=tscode)
        return stock_zh_a_gdhs_detail_em_df
    
    def get_basic_holders_top10_free_by_date(self,date):

        #     名称	类型	描述
        # 序号	int64	-
        # 股东名称	object	-
        # 股东类型	object	-
        # 股票代码	object	-
        # 股票简称	object	-
        # 报告期	object	-
        # 期末持股-数量	float64	注意单位: 股
        # 期末持股-数量变化	float64	注意单位: 股
        # 期末持股-数量变化比例	float64	注意单位: %
        # 期末持股-持股变动	float64	-
        # 期末持股-流通市值	float64	注意单位: 元
        # 公告日	object	-   
        """股东持股分析-十大股东"""
        try:
                    # 股东持股明细-十大流通股东
        #  stock_gdfx_free_holding_detail_em 
        #     股东持股分析-十大流通股东
        # 接口: stock_gdfx_free_holding_analyse_em
            stock_gdfx_holding_analyse_em_df = ak.stock_gdfx_free_holding_analyse_em(date=date)
            return stock_gdfx_holding_analyse_em_df
        except Exception as e:
            str(e)
            return pd.DataFrame()

    def get_basic_holders_top10_by_date(self,date):
        """股东持股分析-十大股东"""
        try:
            # 接口: stock_gdfx_holding_detail_em
            stock_gdfx_holding_analyse_em_df = ak.stock_gdfx_holding_analyse_em(date=date)
            return stock_gdfx_holding_analyse_em_df
        except Exception as e:
            str(e)
            return pd.DataFrame()
    
    def get_basic_holders_top10_by_code(self,tscodde,date):
        """十大股东(个股)"""
        stock_gdfx_top_10_em_df = ak.stock_gdfx_top_10_em(symbol=tscodde, date=date)
        return stock_gdfx_top_10_em_df
    
      
    # 财务指标
#     stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol="600004", start_year="2020")
    def get_basic_institute_hold_list(self,quarter):
        """_获取机构持股列表
        Args:
            quarter (str): 季度如：20201 年+季度
        Returns:
        证券代码  证券简称 机构数  机构数变化   持股比例  持股比例增幅  占流通股比例  占流通股比例增幅
            _type_: _description_dataframe
        """
        stock_institute_hold_df = ak.stock_institute_hold(symbol=quarter)
        return stock_institute_hold_df
    def get_basic_institute_hold_detail_by_stock(self,stock,quarter):
        """_获取机构持股详情
        Args:
            stock (str): 股票代码如：300033
            quarter (str): 季度如：20201 年+季度
        Returns:
        持股机构类型  持股机构代码      持股机构简称  ... 最新占流通股比例  持股比例增幅  占流通股比例增幅
            _type_: _description_dataframe
        """
        stock_institute_hold_detail_df = ak.stock_institute_hold_detail(stock=stock, quarter=quarter)
        return stock_institute_hold_detail_df
    

    def get_daily_list(self,start_date='', end_date=''):
        """_获取日期列表
        Args:
        """
        retdata =None
        #根据回车或换行符切割
        codelist=self.get_code_list()
        for code in codelist:
            if code.get('code'):
                data = self.get_daily_by_code(code.get('code'),start_date, end_date)
                if data is not None:
                    if retdata is None:
                        retdata = data
                    else:
                        retdata =pd.concat([retdata,data],axis=0)
        return retdata
    
    def get_index_daily_by_code(self,tscode,start_date='', end_date='' ,period='daily'):
        '''
            历史行情数据-通用
            输入参数
        名称	类型	描述
        symbol	str	symbol="399282"; 指数代码，此处不用市场标识
        period	str	period="daily"; choice of {'daily', 'weekly', 'monthly'}
        start_date	str	start_date="19700101"; 开始日期
        end_date	str	end_date="22220101"; 结束时间
        '''
        index_zh_a_hist_df = ak.index_zh_a_hist(symbol=tscode, period=period, start_date=start_date, end_date=end_date)
        index_zh_a_hist_df.rename(columns=self.COLUMN_MAP, inplace=True)
        return index_zh_a_hist_df 
    
    def get_index_list(self,symbol='沪深重要指数'):  
        '''
        symbol="上证系列指数"；choice of {"沪深重要指数", "上证系列指数", "深证系列指数", "指数成份", "中证系列指数"}
        '''
        stock_zh_index_spot_em_df = ak.stock_zh_index_spot_em(symbol=symbol)
        return stock_zh_index_spot_em_df

    def get_index_minute_by_code(self,tscode,start_date='', end_date='' ,period='1'):
        '''
        历史分钟数据-通用
        # 名称	类型	描述
        # symbol	str	symbol="399006"; 指数代码，此处不用市场标识
        # period	str	period="1"; choice of {'1', '5', '15', '30', '60'}, 其中 1 分钟数据只能返回当前的, 其余只能返回近期的数据
        # start_date	str	start_date="1979-09-01 09:32:00"; 开始日期时间
        # end_date	str	end_date="2222-01-01 09:32:00"; 结束时间时间
        '''
        index_zh_a_hist_min_em_df = ak.index_zh_a_hist_min_em(symbol=tscode, period=period, start_date=start_date, end_date=end_date)
        return index_zh_a_hist_min_em_df 
                
        
class stockAPITuShare:
    COLUMN_MAP= {'trade_date':'date', 
                 'ts_code':'code', 
                 'con_code':'code', 
                 '名称':'name', 
                 '板块名称':'name', 
                 '板块代码':'code', 
                #  '最新价':'close', 
                 '代码':'code', 
                  '开盘':'open', 
                  '收盘':'close',
                  '最新价':'close',
                  '市盈率-动态':'pe', 
                  '市净率':'pb', 
                  '最高':'high', 
                  '最低':'low', 
                  'vol':'volume', 
                  '成交额':'amount', 
                  '振幅':'amplitude', 
                  'pct_chg':'change_pct', 
                  'change':'change_amt', 
                  '换手率':'turnover_rate',
                  'open_qfq':'open',
                  'high_qfq':'high',
                  'low_qfq':'low',
                  'close_qfq':'close',
                    }
    
    
    def __init__(self,apitoken):
        self.API = ts.pro_api(apitoken)
        
    def get_trade_date(self,exchange = 'SSE', start_date='', end_date=''):
        """_summary_

        Args:
            exchange	str	Y	交易所 SSE上交所 SZSE深交所
            cal_date	str	Y	日历日期
            is_open	str	Y	是否交易 0休市 1交易
            pretrade_date	str	Y	上一个交易日
        """
        df = self.API.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
        return df
        
        
    def get_kdata(self,ts_code,start_date='', end_date='',freq = 'D'):
        """获取股票K线数据
        Args:
            ts_code (_type_): 股票代码如：300033.SZ '688362.SH,600203.SH,300223.SZ,300346.SZ'
            start_date (str, optional): 开始日期：'20200102'.
            end_date (str, optional):  开始日期：'20200202'.
            freq：频率：D=日线 W=周 M=月
        Returns:
            _type_  : _description_dataframe:
            code ：代码
            date  ：交易日期 
            open   ：开盘价
            high   ：最高价 
            low    ：最低价 
            close  ：收盘价 
            pre_close ：昨收价【除权价，前复权】
            previous_close ：前收价
            change  ：涨跌额 
            pct_chg ：涨跌幅 
            volume: 成交量 
            amount ：成交额 
        """
        if freq == 'D':
            # df =  self.API.daily(ts_code=ts_code , start_date=start_date, end_date=end_date)
            df =  self.API.query('daily', ts_code=ts_code,start_date=start_date, end_date=end_date)
        elif freq == 'W':
            # df = self.API.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            df =  self.API.query('weekly', ts_code=ts_code,start_date=start_date, end_date=end_date)
        elif freq == 'M':
            # 获取月线行情
            # df=pro.stk_week_month_adj(ts_code='000001.SZ',freq='week')
            df = self.API.monthly(ts_code=ts_code, start_date=start_date, end_date=end_date) #, fields='ts_code,trade_date,open,high,low,close,vol,amount')
        else:
            return pd.DataFrame()
          
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        df['amount'] = df['amount'] * 1000
        return df
    
    def get_kdata_index(self,ts_code,start_date='', end_date='',freq = 'D'):
        """获取指数K线数据
        Args:
            ts_code (_type_): 股票代码如：300033.SZ '688362.SH,600203.SH,300223.SZ,300346.SZ'
            start_date (str, optional): 开始日期：'20200102'.
            end_date (str, optional):  开始日期：'20200202'.
            freq：频率：D=日线 W=周 M=月
        Returns:
            _type_  : _description_dataframe:
            code ：代码
            date  ：交易日期 
            open   ：开盘价
            high   ：最高价 
            low    ：最低价 
            close  ：收盘价 
            pre_close ：昨收价【除权价，前复权】
            previous_close ：前收价
            change  ：涨跌额 
            pct_chg ：涨跌幅 
            volume: 成交量 
            amount ：成交额 
        """
        if freq == 'D':
            df =  self.API.index_daily(ts_code=ts_code , start_date=start_date, end_date=end_date)
        elif freq == 'W':
            df = self.API.index_weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
        elif freq == 'M':
            # 获取月线行情
            df = self.API.index_monthly(ts_code=ts_code, start_date=start_date, end_date=end_date) #, fields='ts_code,trade_date,open,high,low,close,vol,amount')
        else:
            return pd.DataFrame()  
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        df['amount'] = df['amount'] * 1000
        return df
   
    def get_kdata_etf(self,ts_code,start_date='', end_date='',freq = 'D'):
        '''
        获取ETFK线数据
        Args:
            ts_code (_type_): 股票代码如：300033.SZ '688362.SH,600203.SH,300223.SZ,300346.SZ'
            start_date (str, optional): 开始日期：'20200102'.
            end_date (str, optional):  开始日期：'20200202'.
            freq：频率：D=日线 W=周 M=月
        Returns:
            _type_  : _description_dataframe:
            code ：代码
            date  ：交易日期 
            open   ：开盘价
            high   ：最高价 
            low    ：最低价 
            close  ：收盘价 
            pre_close ：昨收价【除权价，前复权】
            previous_close ：前收价
            change  ：涨跌额 
            pct_chg ：涨跌幅 
            volume: 成交量 
            amount ：成交额 
        '''
            # # adj
        # df = pro.fund_adj(ts_code='513100.SH', start_date='20190101', end_date='20190926')
    
        if freq == 'D':
            df =  self.API.fund_daily(ts_code=ts_code , start_date=start_date, end_date=end_date)
        # elif freq == 'W':
        #     df = self.API.fund_weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
        # elif freq == 'M':
        #     # 获取月线行情
        #     df = self.API.fund_monthly(ts_code=ts_code, start_date=start_date, end_date=end_date) #, fields='ts_code,trade_date,open,high,low,close,vol,amount')
        else:
            return pd.DataFrame()  
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        df['amount'] = df['amount'] * 1000
        return df
    
   
    def get_basic(self):
        """_获取股票列表
        Returns:
            _type_: _description_dataframe
        """
        df = self.API.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df
    
    def get_basic_etf(self):            
        # #获取当前所有上市的ETF列表
        df = self.API.etf_basic(list_status='L', fields='ts_code,extname,index_code,index_name,exchange,mgr_name')
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df
    
    def get_basic_index(self,market='SSE'):
        """获取指定市场指数列表 
            MSCI	MSCI指数
            CSI	中证指数
            SSE	上交所指数
            SZSE	深交所指数
            CICC	中金指数
            SW	申万指数
            OTH	其他指数
        """    
        df = self.API.index_basic(market=market)
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df
    
    def get_basic_concept(self):
        """获取概念列表 
        """    
        # df = pro.concept_detail(id='TS2', fields='ts_code,name')
        # #或者查询某个股票的概念
        # df = pro.concept_detail(ts_code = '600848.SH')
        df = self.API.concept()
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df
    
    def get_basic_index_content(self,index_code, start_date='', end_date=''):
        """获取指数成份股
        Args:
            index_code (str): 指数代码如：399300.SZ
            start_date和end_date分别输入当月第一天和最后一天的日期
            Returns:
            _type_: _description_dataframe
        """
        #提取沪深300指数2018年9月成分和权重 index_code='399300.SZ'
        df = self.API.index_weight(index_code=index_code, start_date=start_date, end_date=end_date)
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df

    def get_weekly_montly(self,ts_code,start_date='', end_date='',freq = 'W'):
        """获取周线月线行情
        Args:
            ts_code (str): 股票代码如：300033.SZ
            start_date和end_date分别输入当月第一天和最后一天的日期
            freq：频率：D=日线 W=周 M=月
        Returns:
            _type_: _description_dataframe
        """
        if freq == 'W':
            df = self.API.stk_week_month_adj(ts_code=ts_code, start_date=start_date, end_date=end_date,freq='week')
        elif freq == 'M':
            df = self.API.stk_week_month_adj(ts_code=ts_code, start_date=start_date, end_date=end_date,freq='month')
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        df['amount'] = df['amount'] * 1000
        return df
    
    # df=pro.stk_week_month_adj(ts_code='000001.SZ',freq='week')
    def get_daily_list(self,trade_date=''):
        '''根据指定日期获取当日股票行情列表 
        '''
        # data = pd.DataFrame()
        df = self.API.daily(trade_date=trade_date)
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        df['amount'] = df['amount'] * 1000
        return df
    
    def get_daliy_basic_by_code(self,ts_code,start_date='', end_date=''):
        '''获取每日指标
        '''
        df = self.API.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date) #, fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df
    
    def get_daliy_basic(self,trade_date):
        '''获取每日指标
        '''
        df = self.API.daily_basic(ts_code='', trade_date=trade_date) #, fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb')
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df
    
    def get_daliy_adj(self,ts_code='',trade_date=''):
        '''
        获取股票复权因子
        '''
        # 类型	算法	参数标识
        # 不复权	无	空或None
        # 前复权	当日收盘价 × 当日复权因子 / 最新复权因子	qfq
        # 后复权	当日收盘价 × 当日复权因子	hfq
        
        if ts_code == '':
            #提取开始日期所有股票复权因子
            df = self.API.adj_factor(ts_code='', trade_date=trade_date)
        else:
            #提取股票所有复权因子
            df = self.API.adj_factor(ts_code=ts_code, trade_date='')
        df.rename(columns=self.COLUMN_MAP, inplace=True)
        return df

    def get_stock_top10_holders(self,ts_code,start_date='', end_date=''):
        '''
        获取股票前十大股东
        '''
        df = self.API.top10_holders(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
        
        
    def get_stock_top10_floatholders(self,ts_code,start_date='', end_date=''):
        '''
        获取股票前十大流通股东
        '''
        df = self.API.top10_floatholders(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
    
    def get_stock_holdernumber(self,ts_code,start_date='', end_date=''):
        '''
        获取股票股东人数
        '''
        df = self.API.stk_holdernumber(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
                 
 
if __name__ == '__main__':
    apitoken = 'APIKEY'
    stock = stockAPITuShare(apitoken)
    
    # data = stock.get_daily_by_code('600203.SH,300223.SZ',start_date='20250612', end_date='20250612')
    
    # data = stock.get_basic_data()
    data = stock.get_daily_list(trade_date='20250715')
    print(data.head())
    
    # stockak = stockAPIAkShare()
    # data = stockak.get_daily_by_code('000001',start_date='20250612', end_date='20250712')
    # data = stockak.get_board_list()
    # data=stockak.get_board_contain_stock('融资融券')
    # data=stockak.get_ticket('000001')
    # data = stockak.get_minute('000001',period='5')
    # data = stockak.get_minute_history('000001',period='1' ,start_date='20250710 08:30:00', end_date='20250712 13')
    # data = stockak.get_daily_by_code_list('000001,300222',start_date='20250612', end_date='20250712')
    # data = stockak.get_daily_by_code_list('600203,000001', '20250101', '20250704')
    # data = stockak.get_basic_data('000001')
    # data= stockak.get_institute_hold_list('20251')
    # data = stockak.get_institute_hold_detail_by_stock('000001', '20244')
    # data = stockak.get_daily_list()
    # data = stockak.get_today_list()
    # data = stockak.get_basic_gdhs_by_date('20250331')
    # print(data.head())
    
    