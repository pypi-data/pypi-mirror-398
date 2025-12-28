# -*- coding: utf-8 -*-

from .Tree import auto_xgb
import pandas as pd
from .RejInfer import syn_reject_dat,diff
import numpy as np
from . import lan
from .Tool import trans_y

def auto_rej_xgb(train_X,train_y,val_X,val_y,rej_train_X,rej_val_X,train_w=None,val_w=None,rej_train_w=None,rej_val_w=None,metric='auc',iter_cost_time=60*5,y_label=None):
    '''
    xgb拒绝推断模型
    
    Parameters
    ----------
    train_X : DataFrame
        训练集
        
    train_y : Series
        训练target
        
    val_X : DataFrame
        验证集
         
    val_y : Series
        验证target
        
    rej_train_X : DataFrame
        拒绝推断训练集
        
    rej_val_X : DataFrame
        拒绝推断验证集
        
    train_w : Series, optional
        训练集权重
        默认：None.
        
    val_w : Series, optional
        验证集权重
        默认：None.
        
    rej_train_w : Series, optional
        拒绝推断训练集权重
        默认：None.
        
    rej_val_w : Series, optional
        拒绝推断验证集权重
        默认：None.
        
    metric : TYPE, optional
        模型评价指标 ，目前支持'ks' 或 'auc'
        默认：'auc'
        
    iter_cost_time : int, optional
        每轮迭代所耗费时长
        默认：60*5.
        
    y_label : dict, optional
        将y中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
        keys的取值只能是unevent或event
        values的取值要根据y的取值填写
        默认:None.
        None的含义与{'unevent':0,'event':1}相同
    
    Returns
    -------
    not_rej_clf : xgboost
        非拒绝推断的xgb模型
        
    rej_clf : xgboost
        拒绝推断的xgb模型
        
    syn_train : DataFrame
        用于训练最后一轮拒绝推断模型的合成数据
        
    syn_val : DataFrame
        用于验证最后一轮拒绝推断模型的合成数据

    '''
    if y_label is not None and not (y_label['unevent']==0 and y_label['event']==1):
        train_y = train_y.apply(trans_y, y_label=y_label) 
        val_y = val_y.apply(trans_y, y_label=y_label) 
    perf_cands,params_cands,clf_cands,vars_cands = auto_xgb(train_X,train_y,val_X,val_y,train_w,val_w,metric=metric,cost_time=60*5,cands_num=1)
    not_rej_clf = clf_cands[0]
    if train_w is None:
        train_w = pd.Series(1,index = train_y.index)
        
    if rej_train_w is None:
        rej_train_w = pd.Series(1,index = rej_train_X.index)
    
    d = np.inf
    last_clf = not_rej_clf
    rej_clf = not_rej_clf#最终的clf
    ite = 0
    X_for_diff = pd.concat([val_X,rej_val_X])
    while(True):
        ite+=1
        syn_train_X,syn_train_y,syn_train_w,_ = syn_reject_dat(last_clf,train_X,train_y,rej_train_X,None,train_w,None,rej_train_w,None)
        
        syn_val_X , syn_val_y , syn_val_w , _ = syn_reject_dat(last_clf,val_X,val_y,rej_val_X,None,val_w,None,rej_val_w,None)
        
        _,_,tmp_clf_cands,_ = auto_xgb(syn_train_X,syn_train_y,syn_val_X,syn_val_y,syn_train_w,syn_val_w,metric=metric,cost_time=iter_cost_time,cands_num=1)
        
        clf = tmp_clf_cands[0]
        tmp_d = np.around(diff(rej_clf,clf,X_for_diff),4)
        print(lan['0172']%ite)
        if tmp_d < d:
            d = tmp_d
            rej_clf = clf
            c=1
            syn_train = (syn_train_X,syn_train_y,syn_train_w)
            syn_val = (syn_val_X , syn_val_y , syn_val_w)
        else:
            c+=1
            if c>2:
                break
        last_clf = clf
    return not_rej_clf,rej_clf,syn_train,syn_val