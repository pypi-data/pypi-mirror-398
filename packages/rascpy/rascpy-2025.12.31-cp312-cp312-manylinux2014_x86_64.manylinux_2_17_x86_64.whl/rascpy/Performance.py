# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from .Cutter import freq_cut,cut_by_bins,cut_array,sort_label,freq_cut_data
from .Tool import trans_y
from . import lan

#datas:{data_name:(target,pred,weight)}
#wide 粗分组宽度
#thin 细分组宽度
#thin_head
def perf_summary(datas,y_label=None,cut_data_name=None,wide=0.05,thin=None,thin_head=10,lift=None,score_reverse=True):
    '''
    对模型性能进行计算并汇总。包括：
    1.对模型的输出进行等频划分，观察每个区间段的数量，分布，比例，累计数量，累积分布，累积比例，ODDS，Lift等信息进行汇总
    2.lift，ks，auc
    
    Parameters
    ----------
    datas : dict{str,tuple(y_true,y_hat,weight)}
        所有需要汇总模型性能的数据集.
        key是数据集的名称，value是一个tuple结构，里面存储的是y_true,y_hat,weight
        
    y_label : dict, optional
        将target中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y取值填写
        默认:None.
        None的含义与{'unevent':0,'event':1}相同
        
    cut_data_name : str, optional
        按照哪个数据集对模型的输出进行等频划分. 
        None：按照每个数据集自己的分布进行等频划分
        究竟是选择用同一数据集还是用各自数据集计算等频分割结点取决于使用者的关注点和自身业务。使用同一数据集（通常是train），除了反映模型效能，还能反映模型输出的稳定性和模型在不同数据集上打分的差异。如果使用各自的数据集计算等频分割结点，则能反映模型在每份数据上更真实的效能（通常会比使用同一数据集的效能要高）。
        举一个例子：假设模型用于排序业务（如：将得分排序后按照一定比例通过某项申请），如果使用者对所有业务申请使用同一个阈值，则考虑使用同一数据集计算分割结点。如果使用者对不同业务申请定制不同的阈值，则考虑使用各自的数据集计算分割结点。
        使用相同或不同数据集来计算分割结点需要使用者结合自身的业务应用场景来综合判断。
        默认：None.
        
    wide : float, optional
        对模型的输出进行等频分组，该参数是用户期望的每组占比。依赖于Cutter模块的强大功能，即使打分分布偏斜，也能给出最接近wide的分组。
        默认： 0.05.
        
    thin : float, optional
        与wide含义相同，但是比wide分的更细。有的业务可能不只是需要关注整体情况，还需要关注事件发生率最高（或最低）的那一小部分的识别效率（如召回率，召准率等），则可以通过配置thin来实现。如果thin不为None，则函数会返回两个等频分组的模型指标统计表，一个更宽的wide模型指标统计表，和一个更窄的thin模型指标统计表。
        默认： None.
        
    thin_head : int, optional
        thin越小则等频分组数越多，更窄的thin模型指标统计表就会越长，看起来不是很方便，通常使用thin的目的只是为了关注头部的数据，所以通过thin_head可控制thin模型指标统计表的长度，只保留前thin_head个组
        如果thin为None，则会自动忽略thin_head
        如果thin_head为None，则会将所有thin的分组全部保留
        默认： 10.
        
    lift : tuple(int,...), optional
        计算对应的lift值
        例：(1,5,10,20)，代表计算模型的lift1,lift5,lift10,lift20
        None：不计算模型的lift
        默认： None.
        
    score_reverse : boolean, optional
        告知打分分值与事件发生率的关系，以便该函数给出人性化的展示
        True：事件发生概率越高，得分越低
        False: 事件发生概率越高，得分越高
        默认:True

    Returns
    -------
    wide_perfs : dict<str,pd.DataFrame>
        返回每个数据集按照wide对模型输出进行等频分组后的每个区间段的数量，分布，比例，累计数量，累积分布，累积比例，ODDS，Lift等信息进行汇总
        
    thin_perfs : dict<str,pd.DataFrame>
        返回每个数据集按照thin对模型输出进行等频分组后的每个区间段的数量，分布，比例，累计数量，累积分布，累积比例，ODDS，Lift等信息进行汇总
        
    lifts : dict<str,list>
        返回各个数据集用户指定的lift
        如果用户指定的lift为None，则该值也返回None
        
    ks : dict<str,float>
        返回各个数据集的ks
        
    auc : dict<str,float>
        返回各个数据集的auc

    '''
    if cut_data_name is None:
        wide_labs = {k:freq_cut_data(v[1],wide,wide*0.7,v[2],ascending=score_reverse)[0] for k,v in datas.items()}
        if thin is not None:
            thin_labs = {k:freq_cut_data(v[1],thin,thin*0.7,v[2],ascending=score_reverse)[0] for k,v in datas.items()}
    else:    
        wide_labs,_ = cut_array({k:v[1] for k,v in datas.items()},wide,wide*0.7,cutby=cut_data_name,weight=datas[cut_data_name][2],ascending=score_reverse)
        if thin is not None:
            thin_labs,_ = cut_array({k:v[1] for k,v in datas.items()},thin,thin*0.7,cutby=cut_data_name,weight=datas[cut_data_name][2],ascending=score_reverse)
    
    
    wide_perfs = {k:gen_perf_table_by_label(v[0],wide_labs[k],y_label,v[2],score_reverse) for k,v in datas.items()}
    if thin is not None:
        thin_perfs = {k:gen_perf_table_by_label(v[0],thin_labs[k],y_label,v[2],score_reverse)[0:thin_head] for k,v in datas.items()}
    else:
        thin_perfs = None
    
    from .Index import LIFTn,KS,AUC
    if lift is not None:
        lifts = {k:[LIFTn(v[0],v[1],i,v[2],score_reverse = score_reverse,y_label=y_label) for i in lift] for k,v in datas.items()}
    else:
        lifts = None
    
    if lift is not None and len(lift)>0:
        print('    lift: ',lifts)
        print('    ','.'*80)
    ks = {k:KS(v[0],v[1],v[2],y_label=y_label) for k,v in datas.items()}
    print('    ks: ',ks)
    print('    ','.'*80)
    if score_reverse:
        auc = {k:1-AUC(v[0],v[1],v[2],y_label=y_label) for k,v in datas.items()} 
    else:
        auc = {k:AUC(v[0],v[1],v[2],y_label=y_label) for k,v in datas.items()}
    print('    auc: ',auc)
    print('    ','.'*80)
    return wide_perfs,thin_perfs,lifts,ks,auc

def gen_perf_table_by_pred(target,pred,pect,y_label=None,weight=None,score_reverse=True):
    '''
    根据用户给定的y_target，y_hat，权重和指定的每个等频分组的占比来观察模型输出的每个区间段的数量，分布，比例，累计数量，累积分布，累积比例，ODDS，Lift等信息进行汇总

    Parameters
    ----------
    target : pd.Series
        y_target
        
    pred : pd.Series
        y_true
        
    pect : float
        每个分组的期望占比，依赖于Cutter模块的强大功能，即使打分分布偏斜，也能给出最接近pect的分组。
        
    y_label : dict, optional
        将target中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y取值填写
        默认:None
        None的含义等同于{'unevent':0,'event':1}
        
    weight : pd.Series
        每个样本的权重
        None：所有样本的权重相同
        默认： None.
        
    score_reverse : boolean, optional
        告知打分分值与事件发生率的关系，以便该函数给出人性化的展示
        True：事件发生概率越高，得分越低
        False: 事件发生概率越高，得分越高
        默认:True

    Returns
    -------
    perf : pd.DataFrame
        返回对模型输出进行等频分组后的每个区间段的数量，分布，比例，累计数量，累积分布，累积比例，ODDS，Lift等信息进行汇总
        
    label_bins : list
        返回模型输出的分组

    '''
    label_bins = freq_cut(pred,pect,pect*0.7,weight,ascending=score_reverse)
    label,_,_ = cut_by_bins(pred,label_bins)
    perf = gen_perf_table_by_label(target,label,y_label,weight,score_reverse)
    return perf,label_bins
        
def gen_perf_table_by_label(target,label,y_label=None,weight=None,score_reverse=True):
    df = pd.DataFrame({'target':list(target),lan['Label']:list(label)})
    
    if y_label is not None and not (y_label['unevent']==0 and y_label['event']==1):
        df['target'] = df['target'].apply(trans_y, y_label=y_label)
        
    if weight is None:
        df['weight'] = 1
    else:
        df['weight'] = list(weight)
        
    df[lan['Label']] = df[lan['Label']].apply(str)
    
    df['mutli_w'] = df['target'] * df['weight']
    
    perf= df.groupby(lan['Label'])[['weight','mutli_w']].sum()
    
    perf = perf.loc[sorted(perf.index,key=sort_label,reverse= not score_reverse)]
    
    perf.columns = [lan['Total amount'],lan['Event']]
    perf[lan['Total amount']] = perf[lan['Total amount']].apply(lambda x:int(np.around(x,0)))
    perf[lan['Event']] = perf[lan['Event']].apply(lambda x:int(np.around(x,0)))
    perf[lan['Unevent']] = perf[lan['Total amount']] - perf[lan['Event']]
    
    jd = 3
    
    for i in [lan['Total amount'],lan['Event'],lan['Unevent']]:
        perf['%s_%s'%(i,lan['Cumulative'])] = perf[i].cumsum().apply(lambda x:int(np.around(x,0)))   
        
    for i in [lan['Total amount'],lan['Event'],lan['Unevent']]: 
        perf['%s_%s'%(i,lan['Distribution'])] = np.around(perf[i] / perf[i].sum(),jd)
        
    for i in [lan['Total amount'],lan['Event'],lan['Unevent']]:
        perf['%s_%s'%(i,lan['Cumulative distribution'])] = np.around(perf['%s_%s'%(i,lan['Cumulative'])] / perf[i].sum(),jd)   
        
    perf[lan['Event rate']] = np.around(perf[lan['Event']] / perf[lan['Total amount']],jd)
    
    # perf[lan['EVENT_RATE_CUM']] = np.around(perf['EVENT_CUM'] / perf['TOTAL_CUM'],jd) 
    perf[lan['Cumulative EVENT rate']] = np.around(perf['%s_%s'%(lan['Event'],lan['Cumulative'])] / perf['%s_%s'%(lan['Total amount'],lan['Cumulative'])],jd) 
    
    perf['ODDS ratio'] = np.around((1-perf[lan['Event rate']])/perf[lan['Event rate']],jd)
    
    perf['Cumulative ODDS ratio'] = np.around((1-perf[lan['Cumulative EVENT rate']])/perf[lan['Cumulative EVENT rate']],jd) 
    
    perf[lan['Lift']] = np.around(perf[lan['Cumulative EVENT rate']] / perf[lan['Cumulative EVENT rate']].iloc[-1],jd)
    return perf