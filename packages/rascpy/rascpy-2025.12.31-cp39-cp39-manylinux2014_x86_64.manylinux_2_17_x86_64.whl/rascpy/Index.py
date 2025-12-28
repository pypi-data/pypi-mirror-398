# -*- coding: utf-8 -*-
from sklearn.metrics import explained_variance_score
from sklearn.metrics import r2_score
from sklearn.metrics import max_error
from sklearn.metrics import accuracy_score
from sklearn.metrics import roc_auc_score
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import average_precision_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
import numpy as np
import pandas as pd
from .Cutter import cut_array,sort_label
from .Tool import trans_y,value_counts_weight
from . import lan

def KS(target,score,sample_weight=None,y_label=None):
    
    '''
    计算KS指标
    支持权重
    支持target取值自定义
    
    Parameters
    ----------
    target : array like
        实际的target。
    
    score : array like
        预测值
        
    sample_weight : array like
        样本的权重
        None：所有权重都是1
        默认:None.
        
    y_label : dict
        将target中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y取值填写
        默认:None
        None的含义与{'unevent':0,'event':1}相同
        
    Returns
    -------
    float
        预测KS值
    
    '''
    
    if not isinstance(target,pd.Series):
        target=pd.Series(target)
        
    if y_label is not None and not (y_label['unevent']==0 and y_label['event']==1):
        target = target.apply(trans_y, y_label=y_label)
    
    if sample_weight is None:
        sample_weight=pd.Series(np.ones_like(target),index=target.index)
    else:
        sample_weight = sample_weight.loc[target.index]
        
    if not isinstance(score,pd.Series):
        score = pd.Series(score,index=target.index)
    else:
        score = score.loc[target.index]
        
    sample_weight.name='weight'
    target.name='y'
    score.name='score'
    df = pd.concat([score,target,sample_weight],axis=1)
    df['y_mutli_w']=df['y']*df['weight']
    total = df.groupby(['score'])['weight'].sum()
    event = df.groupby(['score'])['y_mutli_w'].sum()
    all_df = pd.DataFrame({'total':total, 'event':event})
    all_df['unevent'] = all_df['total'] - all_df['event']
    all_df.reset_index(inplace=True)
    all_df = all_df.sort_values(by='score',ascending=False)
    all_df['eventCumRate'] = all_df['event'].cumsum() / all_df['event'].sum()
    all_df['uneventCumRate'] = all_df['unevent'].cumsum() / all_df['unevent'].sum()
    ks = all_df.apply(lambda x: x.uneventCumRate - x.eventCumRate, axis=1)
    return np.around(np.abs(ks).max(),4)

SCORERS = dict(
    r2=r2_score,
    explained_variance_score=explained_variance_score,
    max_error = max_error,
    roc_auc=roc_auc_score,
    average_precision=average_precision_score,
    ks=KS)
    
def VIF(df):
    '''
    计算变量的VIF

    Parameters
    ----------
    df : DataFrame
        多列变量

    Returns
    -------
    Series
        每个变量的VIF值.

    '''
    vif = pd.DataFrame()
    vif[lan['Vars']] = df.columns
    if df.shape[1]>1:
        vif['VIF Factor'] = [variance_inflation_factor(df.values, i) for i in range(df.shape[1])]
    else:
        vif['VIF Factor']=0
    vif = vif.sort_values('VIF Factor',ascending=False)
    vif.set_index(lan['Vars'],inplace=True)
    vif['VIF Factor'] = vif['VIF Factor'].apply(np.around,decimals=4)
    return vif

def AUC(target,score,sample_weight=None,y_label=None):
    '''
    计算AUC指标
    支持权重
    支持target取值自定义
    
    Parameters
    ----------
    target : array like
        实际的target。
    
    score : array like
        预测值
        
    sample_weight : array like
        样本的权重
        None：所有权重都是1
        默认:None.
        
    y_label : dict
        将target中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y取值填写
        默认:None
        None的含义与{'unevent':0,'event':1}相同
        
        
    Returns
    -------
    float
        预测AUC值
    
    '''
    if not isinstance(target,pd.Series):
        target=pd.Series(target)
    if y_label is not None and not (y_label['unevent']==0 and y_label['event']==1):
        target = target.apply(trans_y, y_label=y_label)
    
    if sample_weight is None:
        sample_weight=pd.Series(np.ones_like(target),index=target.index)
    else:
        sample_weight = sample_weight.loc[target.index]
    if not isinstance(score,pd.Series):
        score = pd.Series(score,index=target.index)
    else:
        score = score.loc[target.index]
        
    return np.around(roc_auc_score(target.copy(), score.loc[target.index],sample_weight=sample_weight),4)


def LIFTn(target,pred,n=10,weight=None,score_reverse=True,y_label=None):
    '''
    计算LIFT指标
    支持权重
    支持target取值自定义
    
    Parameters
    ----------
    target : array like
        实际的target。
    
    pred : array like
        预测值
        
    n : int
        指定LIFT的百分位
        
    weight : array like
        样本的权重
        None：所有权重都是1
        默认:None.
        
   score_reverse : bool
       True : pred越大，事件发生率越低
       False : pred越小，事件发生率越低
        
   y_label : dict
        将target中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y取值填写
        默认:None
        None的含义与{'unevent':0,'event':1}相同
        
    Returns
    -------
    float
        LIFTn的值
    
    '''
    from .Performance import gen_perf_table_by_pred
    perf,_ = gen_perf_table_by_pred(target,pred,0.01,y_label,weight,score_reverse)
    diff = np.abs(perf['%s_%s'%(lan['Total amount'],lan['Cumulative distribution'])] - n/100) 
    return perf.iloc[diff.argmin()][lan['Lift']]

def PSI_by_dist(Ddist,spec_value=[],min_spec_dist=0.005):
    '''
    给定每个单列数据集的分布，计算数据集两两之间的PSI
    
    示例：
    from rascpy.Index import PSI_by_dist
    import pandas as pd
    label = ['[0.0,2.0)','[2.0,3.0)','[3.0,4.0)',['[4.0,22.0]','{-9993,-9994}'], '{-9996,-9997,-9998,-9999}']
    d1 = pd.Series(index=label,data=[0.6497,0.0943,0.0422,0.0346,0.1792])
    d2 = pd.Series(index=label,data=[0.6286,0.0960,0.0428,0.0410,0.1916])
    d3 = pd.Series(index=label,data=[0.6417,0.0844,0.0478,0.0445,0.1816])
    dists = {'d1':d1,'d2':d2,'d3':d3}
    psi_max,psi_df,dist_df,psi_values = PSI_by_dist(dists)
    
    psi_max:0.0044
    
    psi_df:
                                         d1      d2       PSI   SUM_PSI     d1      d3       PSI     SUM_PSI    d2      d3       PSI     SUM_PSI
        [0.0,2.0)                     0.6497  0.6286  0.000697  0.002651   0.6497  0.6417  0.000099  0.004418  0.6286  0.6417  0.000270  0.003139
        [2.0,3.0)                     0.0943  0.0960  0.000030  0.002651   0.0943  0.0844  0.001098  0.004418  0.0960  0.0844  0.001494  0.003139
        [3.0,4.0)                     0.0422  0.0428  0.000008  0.002651   0.0422  0.0478  0.000698  0.004418  0.0428  0.0478  0.000552  0.003139 
        [[4.0,22.0],{-9993,-9994}]    0.0346  0.0410  0.001086  0.002651   0.0346  0.0445  0.002491  0.004418  0.0410  0.0445  0.000287  0.003139
        {-9996,-9997,-9998,-9999}     0.1792  0.1916  0.000830  0.002651   0.1792  0.1816  0.000032  0.004418  0.1916  0.1816  0.000536  0.003139 

    dist_df:
                                       d1      d2      d3     PSI_MAX   MAX_LOC
        [0.0,2.0)                     0.6497  0.6286  0.6417   0.0044   d1 , d3
        [2.0,3.0)                     0.0943  0.0960  0.0844   0.0044   d1 , d3
        [3.0,4.0)                     0.0422  0.0428  0.0478   0.0044   d1 , d3
        [[4.0,22.0],{-9993,-9994}]    0.0346  0.0410  0.0445   0.0044   d1 , d3
        {-9996,-9997,-9998,-9999}     0.1792  0.1916  0.1816   0.0044   d1 , d3

    psi_values:
              data_name_1 data_name_2       PSI
        0          d1          d2        0.002651
        1          d1          d3        0.004418
        2          d2          d3        0.003139
    
    Parameters
    ----------
    Ddist : dict<str,Series>
        单列数据集的分布信息。多个数据集之间的分布节点需要保持一致
         
    spec_value : list
        特殊值的取值范围
        例. ["{-9997}","{-9999,-9998}"]
        
    min_spec_dist : float
        如果每个数据集的特殊值的占比都小于min_spec_dist,则特殊值不参与PSI的计算.
        默认:0

    Returns
    -------
    float:
        数据集之间两两计算中最大的PSI
        
    DataFrame:
        两两数据集计算PSI的中间数据
        
    DataFrame:
        结果的汇总信息。包括最大PSI产生在哪两个数据集之间
        
    DataFrame:
        两两数据集之间的PSI。

    '''
    def _f1(x):
        def _f2():
            if spec_value is None:
                return False
            for i in spec_value:
                if str(i) == x.name:
                    return True
            return False
        
        if (_f2() or x.name=='{None}') and ((x < min_spec_dist).all() or (x.isna()).all()):
            return np.nan
        tmp = x.fillna(0.0001).replace(0,0.0001)
        col1 = tmp.iloc[0]
        col2 = tmp.iloc[1]
        return np.log(col1 / col2) * (col1 - col2)
            
    psi_max = 0
    max_loc=''
    psi_dfs = []
    psi_values = pd.DataFrame(columns=['data_name_1','data_name_2','PSI'])
    for i,name1 in enumerate(Ddist.keys()):
        for j,name2 in enumerate(Ddist.keys()):
            if i<j:
                psi_df = pd.concat([Ddist[name1],Ddist[name2]],axis=1)
                psi_df.columns = [name1,name2]
                psi_df['PSI'] = psi_df.apply(_f1,axis=1)
                sum_psi = psi_df['PSI'].sum()
                psi_values.loc[psi_values.shape[0]] = pd.Series({'data_name_1':name1,'data_name_2':name2,'PSI':sum_psi})
                psi_df['SUM_PSI']=sum_psi
                psi_dfs.append(psi_df)
                if sum_psi > psi_max:
                    psi_max = sum_psi
                    max_loc = '%s , %s'%(name1,name2)
    psi_max =   np.around(psi_max,4)       
    dist_df = pd.concat(Ddist,axis=1)
    dist_df.columns = dist_df.columns.to_series().apply(lambda c:c[0])
    # dist_df = dist_df.loc[sorted(dist_df.index,key=sort_label)].sort_index(1)
    dist_df['PSI_MAX'] = psi_max
    dist_df['MAX_LOC'] = max_loc
    return psi_max,pd.concat(psi_dfs,axis=1),dist_df,psi_values

# cutby可以是数据集的名称,也可以是bins
def PSI_by_dat(Ddat,threshold_distr=0.05,min_distr=0.02,cutby=0,Dweight=None,spec_value=[],min_spec_dist=0.005):
    '''
    计算多个单列数据集之间的PSI，先按照指定数据集进行分箱节点计算。然后按照该节点对所有数据集进行分割，并计算分布。最后调用PSI_by_dist方法，得到两两数据集的PSI值与相关其他信息。

    Parameters
    ----------
    Ddat : dict<str,Series>
        多个单列数据集
        
    threshold_distr : int or float
        大于1：分成几份
        小于1：每份的占比是多少
        默认: 0.05
        
    min_distr : float
        所能接受的最小的占比。因为数据倾斜，并不能保证所有分箱都能满足threshold_distr。有的分箱会高于threshold_distr，有的会低于threshold_distr。但是最低不会低于min_distr。
        
    cutby : int ,str, list
        int:如果datas是ndarray like，则cutby是以第几个数列为基准来进行分组
        str:如果datas是dict或者DataFrame，则按照cutby对应基准数列来进行分组
        list:cutby是bins，所有数列按照cutby来进行分组
        默认:0.
        
    Dweight : dict<str,Series>
        每个数列的权重
        None：每个数据点的权重都为1
        默认:None
        
    spec_value : list
        特殊值的取值范围
        例. ["{-9997}","{-9999,-9998}"]
        默认:[].
        
    min_spec_dist : float
        如果每个数据集的特殊值的占比都小于min_spec_dist,则特殊值不参与PSI的计算.
        默认:0

    Returns
    -------
    float:
        数据集之间两两计算中最大的PSI
        
    DataFrame:
        两两数据集计算PSI的中间数据
        
    DataFrame:
        结果的汇总信息。包括最大PSI产生在哪两个数据集之间
        
    DataFrame:
        两两数据集之间的PSI。

    '''
    if Dweight is None or isinstance(cutby,list):
        cut_weight = None
    else:
        cut_weight = Dweight[cutby]
    
    labels,_ = cut_array(Ddat,threshold_distr,min_distr,cutby,cut_weight,spec_value)
    Ddists = {}
    for i,label in labels.items():
        if Dweight is None:
            tmp_weight = None
        else:
            tmp_weight = Dweight[i]
        _,dist = value_counts_weight(label,tmp_weight)
        Ddists[i] = dist
    return PSI_by_dist(Ddists,spec_value,min_spec_dist)


# import math

# def aic(y_true, y_pred, n_params):

#     # 计算残差平方和
#     residuals = [y_true[i] - y_pred[i] for i in range(len(y_true))]
#     residuals_sum = sum(residuals)**2

#     # 计算对数似然值
#     log_likelihood = math.log(residuals_sum) * -2

#     # 计算AIC
#     aic = -2 * log_likelihood + 2 * n_params

#     return aic

# BIC=k×ln(n)−2×ln(L)，其中，k为模型参数个数，n为样本数量，L为模型的最大似然估计值。