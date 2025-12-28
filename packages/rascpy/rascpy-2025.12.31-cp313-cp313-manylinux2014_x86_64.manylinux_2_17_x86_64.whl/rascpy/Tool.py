# -*- coding: utf-8 -*-
import numpy as np
import logging
import pandas as pd
import os
import pickle
import json
from . import lan

def value_counts_weight(data,weight=None):
    '''
    功能与pandas.Series.value_counts()相同，但value_counts_weight支持权重

    Parameters
    ----------
    data : array like
        需要被统计的序列.
        
    weight : array like
        数据点的权重
        None:每个数据点的权重都是1
        默认:None.

    Returns
    -------
    Series
        每个数据点的数量(带权重)
    Series
        每个数据点的占比(带权重)

    '''
    if not isinstance(data,pd.core.series.Series):
        data = pd.Series(data)
    data.name = 'data'
        
    if weight is None:
        weight=pd.Series(np.ones_like(data),index=data.index)
    elif not isinstance(weight,pd.core.series.Series):
        weight = pd.Series(weight,index=data.index)
    
    weight = weight.loc[data.index]
    weight.name = '__weight'
    df = pd.concat([data,weight],axis=1)
    cnt = df.groupby('data',dropna=False)['__weight'].sum()
    distr = cnt / cnt.sum()
    return cnt,distr

# dat ,y,weight都是数列，不是列名
def value_counts_weight_y(dat,y,y_label=None,weight=None):
    '''
    统计每个取值的事件发生与事件未发生的情况

    Parameters
    ----------
    dat : array like
        一列数列
        
    y : array like
        数列的target（不是列名）.
        
    y_label : dict
        将y中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y取值填写
        默认:None.
        None的含义与{'unevent':0,'event':1}相同
        
    weight : Series
        数据点的权重列（不是列名）
        None：所有权重都是1
        默认:None.

    Returns
    -------
    DataFrame
        columns = ['每个取值的数量'，'占比'，'事件发生的数量'，'事件未发生的数量'，'事件发生率']
        
    '''
    dat = to_series(dat,'__dat',None)
    y = to_series(y,'__y',dat.index)
    w = to_series(weight,'__w',dat.index)
    
    # 还权后的事件发生的数量
    df = pd.DataFrame(columns=[lan['Event'],lan['Total amount'],lan['Event rate']])
    def _f1(y):
        tmp_w = w.loc[y.index]
        tmp_y = y.copy()
        if y_label is None:
            y_event = tmp_y.loc[tmp_y == 1]
        else:
            y_event = tmp_y.loc[tmp_y == y_label['event']]
        w_event = tmp_w.loc[y_event.index]
        total = int(np.around(tmp_w.sum(),0))
        event = int(np.around(w_event.sum(),0))
        eventProb = np.around(event/total,4)
        df.loc[y.name] = pd.Series({lan['Event']:event,lan['Total amount']:total,lan['Event rate']:eventProb})
 
    y.groupby(dat,dropna=False).apply(_f1)
    df[lan['Distribution']] = np.around(df[lan['Total amount']]/df[lan['Total amount']].sum(),4)
    df[lan['Unevent']] = df[lan['Total amount']] - df[lan['Event']]
    return df[[lan['Total amount'],lan['Distribution'],lan['Event'],lan['Unevent'],lan['Event rate']]]


def profit(y,pred,weight=None
           ,score_reverse=True,fea_count=None,avg_fea_cost=None
           ,avg_quota=10000,day_call=10000
           ,pass_rate=0.4,use_rate=0.7
           ,avg_profit_rate=0.2,avg_loss_rate=0.8,y_label=None):
    '''
    依据真实的表现和模型给出的预测值，给出一个大致盈利的测算

    Parameters
    ----------
    y : Series
        真实的表现
        
    pred : Series
        预测值
        
    weight : Series, optional
        样本权重
        默认： None
        
    score_reverse : boolean, optional
        pred与事件发生率的关系
        True:反向关系。pred值越高，事件发生率越低
        False:正向关系。pred值越高，事件发生率越高
        默认： True
        
    fea_count : int
        模型包含变量的特征个数
        
    avg_fea_cost : float
        特征的平均单价
    
    avg_quota : float, optional
        样本额度（平均）
        默认： 10000
        
    day_call : int, optional
        模型日均调用次数
        默认： 10000
        
    pass_rate : float, optional
        模型通过率
        默认： 0.4
        
    use_rate : float, optional
        用户提现率 
        默认：  0.7
        
    avg_gain_rate : float, optional
        正常客户每笔平均收益
        默认：  0.2
        
    avg_loss_rate : float, optional
        违约客户每笔平均损失
        默认：  0.8
        
    y_label : dict, optional
        将y的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y的取值填写
        默认:None
        None的含义与{'unevent':0,'event':1}相同

    Returns
    -------
    dict
        day_bad：按照提供的y和pred，换算成day_call访问量下，每日产生的违约样本
        day_good：按照提供的y和pred，换算成day_call访问量下，每日产生的正常样本
        bad_rate：按照提供的y和pred和pass_rate计算的违约率
        day_total：day_bad + day_good
        year_gain：年收入（亿元）
        year_loss: 年坏账金额（亿元）,
        year_fea_cost: 年征信成本（亿元）,
        year_profit:年盈利（亿元），year_gain - year_loss - year_fea_cost

    ''' 
    if y_label is not None and not (y_label['unevent']==0 and y_label['event']==1):
        y = y.apply(trans_y, y_label=y_label)
    tmp = value_counts_weight_y(dat = pred,y=y,weight=weight).sort_index(ascending=not score_reverse)
    tmp['tmp1'] = tmp[lan['Total amount']].cumsum() - tmp[lan['Total amount']].sum()*pass_rate
    tmp['tmp1'] = tmp['tmp1'].apply(np.abs)
    cutoff = tmp.iloc[tmp['tmp1'].argmin()].name
    tmp = tmp.loc[tmp.index>=cutoff]
    bad = tmp[lan['Event']].sum()
    good = tmp[lan['Unevent']].sum()
    bad_rate = bad/(good+bad)
    
    day_bad = np.around(day_call * pass_rate * use_rate * bad_rate,decimals=0)
    day_good = np.around(day_call * pass_rate * use_rate * (1-bad_rate),decimals=0)
    day_total = day_bad + day_good
    
    year_gain = day_good *  avg_quota * avg_profit_rate * 365 / 10**8
    year_loss = day_bad * avg_quota * avg_loss_rate * 365 / 10**8
    year_fea_cost = fea_count * avg_fea_cost * day_call * 365 / 10**8
    
    year_profit = year_gain - year_loss - year_fea_cost
    # year_invest_amt = day_total * avg_quota * 365 / 10**8
    return {'day_bad':int(day_bad),
            'day_good':int(day_good),
            'bad_rate':float(bad_rate),
            'day_total':float(day_total),
            'year_gain':float(year_gain),
            'year_loss':float(year_loss),
            'year_fea_cost':float(year_fea_cost),
            'year_profit':float(year_profit)
            # ,'year_invest_amt':float(year_invest_amt)
            }


class _Bin_Path():
    def __init__(self,path,sum_iv=0,last_y_mean=None):
        self.path=path
        self.sum_iv = sum_iv
        self.last_y_mean = last_y_mean

def prob2score(p,base_points=500,base_event_rate=0.05,pdo=50):
    '''
    将一个概率转换成整数分数

    Parameters
    ----------
    p : float
        将被转换的概率
        
    base_points : float, optional
        基准分数
        默认 500.
        
    base_event_rate:float, optional
        基准分数对应的概率（注意：不是比率）
        默认 0.05.
        
    pdo : float, optional
        pdo
        默认 50.

    Returns
    ----------
    int
        返回的分数值.

    '''
    if p==0:
        p=0.0001
    elif p==1:
        p=0.9999
    B=pdo/np.log(2)
    odds=p/(1-p)
    base_odds = base_event_rate/(1-base_event_rate)
    A = base_points + B*np.log(base_odds)
    return int(np.around(A-B*np.log(odds)))
            
def trans_y(y,y_label):
    # if y_label is None:
    #     return y
    if y == y_label['unevent']:
        return 0
    elif y == y_label['event']:
        return 1

def make_logger(logger_name,logger_file):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logger_file,mode='w')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(name)s]-[%(filename)s-%(lineno)d]-[%(levelname)s]: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger,fh    

def to_series(s,default_name,index=None):
    if s is None:
        return pd.Series(1,index=index)
    if not isinstance(s,pd.core.series.Series):
        s = pd.Series(s)
    else:
        s = s.copy()  
        
    if s.name is None:
        s.name = default_name
    
    if index is not None:
        s.index = index
    return s

def load_all_files(path):
    '''
    读取path下的所有数据，但不支持文件夹嵌套
    支持的数据格式有csv,excel,pkl，对应的后缀必须是csv,xlsx,pkl

    Parameters
    ----------
    path : str
        文件夹地址

    Returns
    -------
    datas : dict{str,dataframe}
        文件夹下所有数据集
        key是文件的名称去掉后缀作为数据集的名称

    '''
    tmps={}
    for f in os.listdir(path):
        ind = f.rfind('.')
        suf = f[ind+1:]
        name = f[:ind]
        file = '%s/%s'%(path,f)
        if suf=='xlsx':
            try:
                tmps[name] = pd.read_excel(file,index_col=0)
            except UnicodeDecodeError:
                tmps[name] = pd.read_excel(file,index_col=0,encoding='gbk')
        elif suf=='csv':
            try:
                tmps[name] = pd.read_csv(file,index_col=0)
            except UnicodeDecodeError:
                tmps[name] = pd.read_csv(file,index_col=0,encoding='gbk')
        elif suf=='pkl':
            with open(file,'rb') as f:
                tmps[name] = pickle.load(f)
    return tmps

def get_decimals(i):
    '''
    得到一个数字的小数位数
    支持科学计数法
    1.0,2.00,...这样的数字被认为没有小数位数

    Parameters
    ----------
    i : numeric
        任意数值

    Returns
    -------
    int
        小数位数.

    '''
    if int(i) == i:
        return 0
    s = str(float(i)).strip()
    
    if 'e' in s:
        tmp1 = float(s.split('e')[0])
        tmp1 = get_decimals(tmp1)
        tmp2 = float(s.split('e')[1])
        return tmp1-tmp2

    # if '.' not in s:
    #     return int(s.split('e-')[1])     
    return len(s)-1-s.index('.')

def region_attr(region):
    region = region.strip()
    left_close = False
    right_close = False
    
    if region[0]=='[':
        left_close = True
    if region[-1]==']':
        right_close = True
        
    region = region[1:-1]
    vs = region.split(',')
    v1 = float(vs[0])
    v2 = float(vs[1])
    asc = v1 < v2 
    decimals = max(get_decimals(v1),get_decimals(v2))            
    return v1,v2,decimals,asc,left_close,right_close

def parse_dict_col(s):
    if isinstance(s,dict):
        return pd.Series(s)
    return pd.Series(json.loads(s))
            
# d = pd.Series([1,2,3,4])
#如果设定的空值不包括'None',但是数据中含有空值，则自动向spec_value中追加一个'{None}'
def _spec_None(data,spec_value):
    '''
    如果设定的空值不包括'None',但是数据中含有空值，则自动向spec_value中追加一个'{None}'

    Parameters
    ----------
    data : array like
        原始数据
        
    spec_value : list
        特殊值

    Returns
    -------
    new_spec_value : list
        加入'{None}'后的特殊值，如果原始spec_value中还有'None'，则不会被添加
        例如原始spec_value=['{-1,-2}','{None}']或者spec_value=['{-1,-2}','{-997,None}']或者spec_value=['{-1,-2}',['{-997,None}','{-998}']]则不会改变原始的spec_value

    '''
    if data.notna().all():
        return spec_value
    for i in spec_value:
        if isinstance(i,list):
            for ii in i:
                if 'None' in ii:
                    return spec_value
        else:
            if 'None' in i:
                return spec_value
    spec_value.append('{None}')
    return spec_value

#删除数据中的特殊值，只有没有特殊值的数据，才能够进行切割
#加入了字符特殊值和数字特殊值自适应
def _spec_del(data,spec_value):
    '''
    删除数列中的特殊值

    Parameters
    ----------
    data : array like
        一列数列.
    spec_value : list
        特殊值的取值.
        如果某个特殊值不在数列中，则该特殊值会被自动忽略
        例. ["{-9997}","{-9999,-9998}"]

    Returns
    -------
    array like 与data类型相同
        删除特殊值后的新数列.

    '''
    data = data.loc[data.notna()]
    if spec_value is None:
        return data
    
    def _f1(m):
        if m is not None and m==m:
            return str(m)
        return m

    def _f2(m):
        if m is not None and m==m:
            try:
                m = float(m)
            except:
                return m
        return m
  
    for i in spec_value:
        if isinstance(i, list):
            for ii in i:
                ii = ii.strip()
                tmp_str = set(map(_f1,eval('{%s}'%(ii[1:-1]))))
                data = data.loc[~data.isin(tmp_str)]
                
                tmp_float = set(map(_f2,eval('{%s}'%(ii[1:-1]))))
                data = data.loc[~data.isin(tmp_float)]
        else:
            i = i.strip()
            tmp_str = set(map(_f1,eval('{%s}'%(i[1:-1]))))
            data = data.loc[~data.isin(tmp_str)]
            
            tmp_float = set(map(_f2,eval('{%s}'%(i[1:-1]))))
            data = data.loc[~data.isin(tmp_float)]
    return data

def is_spec_value(value,spec_value,None_is_spec=True):
    '''
    判断数值是否为特殊值
    Parameters
    ----------
    value : float or str
        待判断的值
        
    spec_value : list
        特殊值.例：['{-999,-888}','{-1000}']
        
    None_is_spec : bool
        如果 'None'不在spec_value中，那么None值是否会被当成特殊值
        True:会被当成特殊值
        False:不会被当成特殊值

    Returns
    -------
    bool
        该值是否是特殊值.

    '''
    if value is None or value!=value or pd.isna(value) or 'None' == str(value):
        if None_is_spec == True:
            return True
        for i in spec_value:
            if isinstance(i, list):
                for ii in i:
                    ii = ii.strip()
                    if 'None' in ii:
                        return True
            else:
                i = i.strip()
                if 'None' in i:
                    return True  
        
    if spec_value is None:
        return False
    
    def _f1(m):
        if m is not None and m==m:
            return str(m)
        return m

    def _f2(m):
        if m is not None and m==m:
            try:
                m = float(m)
            except:
                return m
        return m    
    
    for i in spec_value:
        if isinstance(i, list):
            for ii in i:
                ii = ii.strip()
                if value in set(map(_f1,eval('{%s}'%(ii[1:-1])))) or value in set(map(_f2,eval('{%s}'%(ii[1:-1])))):
                    return True
        else:
            i = i.strip()
            if value in set(map(_f1,eval('{%s}'%(i[1:-1])))) or value in set(map(_f2,eval('{%s}'%(i[1:-1])))):
                return True            
    return False

def predict_proba(clf,X,decimals=4):
    '''
计算模型的预测概率。他提供了如下方便的功能：
1.如果clf是statsmodels.generalized_linear_model或statsmodels.discrete.discrete_model则会自动加入常数项，即自动调用sm.add_constant。
2.如果clf中含有feature_importances_==0的列（不是实际需要），而X中不存在这些列，则能保证模型继续运行，不会报错，也不会产生不一致的结果。
3.如果X中存在但在clf中不需要的列，则能保证模型继续运行，不会报错，也不会产生不一致的结果。
4.会直接返回事件发生的概率，而不会向其他predict_proba方法返回事件未发生和事件发生两个概率所组成的二维数组（二分类时）。

Parameters
----------
clf : TYPE
    模型.
    
X : DataFrame
    数据
    
decimals : int, optional
    概率保留的小数点位数
    默认：4.

Raises
------
Exception
    clf实际需要的列，但是X中没有这些列，则抛出异常

Returns
-------
pd.Series
    事件发生的概率

    '''
    from statsmodels.genmod.generalized_linear_model import GLMResultsWrapper
    from statsmodels.discrete.discrete_model import BinaryResultsWrapper
    from .StepwiseRegressionSKLearn import LogisticReg
    if isinstance(clf,GLMResultsWrapper) or isinstance(clf,BinaryResultsWrapper):
        import statsmodels.api as sm 
        from .StepwiseRegressionSKLearn import _estimator_cols
        proba_hat = pd.Series(clf.predict(sm.add_constant(X[_estimator_cols(clf)])),index = X.index)
    elif isinstance(clf,LogisticReg):
        import statsmodels.api as sm 
        from .StepwiseRegressionSKLearn import _estimator_cols
        proba_hat = pd.Series(clf.estimator_.predict(sm.add_constant(X[_estimator_cols(clf)])),index = X.index)
    else:
        impt = getattr(clf, 'feature_importances_', None)
        cols = getattr(clf, 'feature_names_in_', None)
        
        if impt is None or cols is None:
            proba_hat = pd.Series(clf.predict_proba(X)[:,1],index = X.index)
        else:
            cols_impt = pd.Series(impt,index=cols)
            X = X.copy()
            miss_cols=[]
            for i in cols_impt.index:
                if i not in X:
                    if cols_impt[i] > 0:
                        miss_cols.append(i)
                    else:
                        X[i] = np.nan
            if len(miss_cols)>0:
                raise Exception(lan['1171']%','.join(miss_cols))
            proba_hat = pd.Series(clf.predict_proba(X[cols])[:,1],index = X.index)                 
    return proba_hat.apply(np.around,decimals=decimals)

def mean_weight(dat,weight=None,decimals=4):
    '''
    
    功能与pandas.Series.mean()相同，但mean_weight支持权重
    
    Parameters
    ----------
    dat : pandas.Series
        数列.
        
    weight : pandas.Series, optional
        样本权重。None：每个样本权重一样
        默认：None.
    
    decimals: int
        保留的小数位数
        默认：4
        
    Returns
    -------
    float
        加权均值.

    '''
    if weight is not None:
        return np.around((dat * weight).sum() / weight.sum(),decimals)
    else:
        return np.around(dat.mean(),decimals)
    
def parse_x_group(var_name,gsplit=None,gindex=None,fmt=None):
    if fmt is None and gsplit is None and gindex is None:
        # fmt,gsplit,gindex不能都为None
        raise ValueError(lan['1175'])
    
    if fmt is None and (gsplit is None or gindex is None):
        # fmt为None时，gsplit和gindex不能为None
        raise ValueError(lan['1176'])
    
    if gsplit is None or gindex is None:
        gsplit,gindex  = get_gsplit_gindex(fmt)
        
    if gsplit not in var_name:
        return None
    return var_name.split(gsplit)[gindex]

def get_gsplit_gindex(fmt):
    if fmt is None:
        # fmt不能是None
        raise ValueError(lan['1177'])
  
    gsplit = fmt.replace('g','')
    if fmt.startswith('g'):
        gindex = 0
    elif fmt.endswith('g'):
        gindex = -1
    return gsplit,gindex  