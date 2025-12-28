# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from .Tool import predict_proba
from . import lan

def syn_reject_dat(clf,dat_X,dat_y,rej_X,rej_X_to_predict=None,dat_fitW=None,dat_meaW=None,rej_fitW=None,rej_meaW=None,y_label=None):
    if y_label is None:
        y_label={'event':1,'unevent':0}
    
    if dat_fitW is None:
        dat_fitW = pd.Series(1,index=dat_y.index)
    if rej_fitW is None:
        rej_fitW = pd.Series(1,index=rej_X.index)
        
    if dat_fitW.name is None and rej_fitW.name is None:
        dat_fitW.name='__fitW'
        rej_fitW.name='__fitW'
    elif dat_fitW.name is not None and rej_fitW.name is None:
        rej_fitW.name = dat_fitW.name
    elif rej_fitW is not None and dat_fitW.name is None:
        dat_fitW.name = rej_fitW.name
    elif rej_fitW is not None and dat_fitW.name is not None:
        if dat_fitW.name!=rej_fitW.name:
            raise ValueError(lan['1169'])

    
    if dat_meaW is not None and rej_meaW is None:
        rej_meaW = pd.Series(1,index=rej_X.index)
    elif dat_meaW is None and rej_meaW is not None:
        dat_meaW = pd.Series(1,index=dat_y.index)
           
    if not (dat_meaW is None and rej_meaW is None):
        if dat_meaW.name is None and rej_meaW.name is None:
            dat_meaW.name='__meaW'
            rej_meaW.name='__meaW'
        elif dat_meaW.name is not None and rej_meaW.name is None:
            rej_meaW.name = dat_meaW.name
        elif rej_meaW is not None and dat_meaW.name is None:
            dat_meaW.name = rej_meaW.name
        elif rej_meaW is not None and dat_meaW.name is not None:
            if dat_meaW.name!=rej_meaW.name:
                raise ValueError(lan['1170'])
            
    
    if rej_X_to_predict is None:    
        rej_X_to_predict = rej_X
    rej_hat = predict_proba(clf,rej_X_to_predict.loc[rej_X.index])
    
    rej_X1 = rej_X.copy()
    rej_y1 = pd.Series(y_label['event'],index=rej_X1.index,name=dat_y.name)

    rej_fitW1 = rej_fitW * rej_hat
    rej_fitW1.name = rej_fitW.name
    
    if rej_meaW is not None:
        rej_meaW1 = rej_meaW * rej_hat
        rej_meaW1.name = rej_meaW.name
    
    
    rej_y0 = pd.Series(y_label['unevent'],index=rej_X.index,name=dat_y.name)
    rej_fitW0 = rej_fitW * (1-rej_hat)
    rej_fitW0.name = rej_fitW.name
    if rej_meaW is not None:
        rej_meaW0 = rej_meaW * (1-rej_hat)
        rej_meaW0.name = rej_meaW.name
    
    syn_X = pd.concat([dat_X,rej_X,rej_X1],ignore_index=True)
    syn_y = pd.concat([dat_y,rej_y0,rej_y1],ignore_index=True)
    syn_y.name = dat_y.name
    syn_fitW = pd.concat([dat_fitW,rej_fitW0,rej_fitW1],ignore_index=True)
    syn_fitW.name = dat_fitW.name
    tmps = [syn_X,syn_y,syn_fitW]
    if rej_meaW is not None:
        syn_meaW = pd.concat([dat_meaW,rej_meaW0,rej_meaW1],ignore_index=True)
        syn_meaW.name = dat_meaW.name
        tmps.append(syn_meaW)
    syn_dat = pd.concat(tmps,axis=1).sample(frac=1)
    
    if rej_meaW is None:
        return syn_dat[syn_X.columns],syn_dat[syn_y.name],syn_dat[syn_fitW.name],None
    else:
        return syn_dat[syn_X.columns],syn_dat[syn_y.name],syn_dat[syn_fitW.name],syn_dat[syn_meaW.name]


def diff(base_clf,clf,X,X2=None):
    if X2 is None:
        X2 = X
    hat0 = predict_proba(base_clf,X)
    hat = predict_proba(clf,X2)
    diff = np.abs(hat0 - hat).mean()
    return diff