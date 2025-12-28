# -*- coding: utf-8 -*-
"""
Created on Mon May  8 16:52:46 2015

@author: rascpy
"""
import numpy as np
import pandas as pd
from . import lan
from .Tool import parse_x_group

class Filters():
    def __init__(self,sc,fore = False,is_rej=False):
        self.filters = sc.fore_filters if fore else sc.filters
        self.filter_data_names = sc.filter_data_names
        self.bins_stat = sc.freqbins_stat if fore else sc.optbins_stat
        self.bins_stat_flat = {}
        for k1,v1 in self.bins_stat.items():
            for k2,v2 in v1.items():
                self.bins_stat_flat[k2]=v2
        
        self.datas_flat = {}
        
        for use,d in sc.datas.items():
            for name,dat in d.items():
                self.datas_flat[name]=dat
                
        self.sc = sc
        self.col_indices={}
        self.filtered_cols={}
        self.filters_middle_data={}
        
        self.is_rej = is_rej
        
        for name,thv in self.filters.items():
            values,locs,middle_data = eval('self._%s(thv)'%name)

            if middle_data is not None:
                self.filters_middle_data.update(middle_data)
            
            if name.startswith('big'):
                index_name = name[4:]
                sign = '>'
            elif name.startswith('small'):
                index_name = name[6:]                
                sign = '<'
                
            if values is not None:
                self.col_indices[index_name] = values
    
                for col in list(values[eval('values %s thv'%sign)].index):
                    if col in sc.user_save or col in sc.user_set:
                        continue
                    s = '%s %s %s'%(index_name,sign,thv)
                    
                    if locs is not None:
                        s = '%s [%s]'%(s,locs[col])
                    if fore==True:
                        s = '[fore]%s'%s
                    if col not in self.filtered_cols:
                        self.filtered_cols[col] = s
                    else:
                        self.filtered_cols[col] = '\n'.join([self.filtered_cols[col],s])
                        
    def _big_miss(self,thv=None):
        tmps = []
        for filter_data_name in self.filter_data_names['big_miss']:
            try:
                data = self.datas_flat[filter_data_name]
                X = data.loc[:,~data.columns.isin(self.sc.not_X_cols)]
                tmp = X.apply(lambda m:m.isna().sum()/m.shape[0]).apply(np.around,decimals=2)
                tmps.append(tmp)
            except Exception as e:
                # 'rascpy:执行big_miss过滤器时，在%s数据集上发生错误'
                e.add_note(lan['1056']%filter_data_name)
                raise e
        return pd.concat(tmps,axis=1).max(axis=1),pd.concat(tmps,axis=1).idxmax(axis=1).apply(lambda x:self.filter_data_names['big_miss'][x]),None
    
    def _big_homogeneity(self,thv=None):
        tmps = []
        for filter_data_name in self.filter_data_names['big_homogeneity']:
            try:
                k=None
                tmp = pd.Series()
                for k,v in self.bins_stat_flat[filter_data_name].items():
                    tmp[k] = v[lan['Distribution']].max()
                tmps.append(tmp)
            except Exception as e:
                if k is not None:
                    #'rascpy:执行big_homogeneity过滤器时，在%s数据集上的%s列发生错误'
                    msg = lan['1057']%(filter_data_name,k)
                else:
                    # 'rascpy:执行big_homogeneity过滤器时，在%s数据集上发生错误'
                    msg = lan['1058']%filter_data_name
                e.add_note(msg)
                raise e
        return pd.concat(tmps,axis=1).max(axis=1),pd.concat(tmps,axis=1).idxmax(axis=1).apply(lambda x:self.filter_data_names['big_homogeneity'][x]),None
    
    def _big_psi(self,thv=None):
        from .Index import PSI_by_dist
        Ddists={}
        from .ScoreCard import PSI_DATA
        if 'big_psi' not in self.filter_data_names and PSI_DATA not in self.sc.datas:
            # 'rascpy:您已经指定了big_psi过滤器，要么在filter_data_names中提供big_psi的数据集，要么设置psi_data_file_path，现在两者均没有配置'
            raise ValueError(lan['1120'])
            
        tmp = self.filter_data_names.get('big_psi',None)
        if tmp is None:
            tmp = list(self.sc.datas[PSI_DATA].keys())
        #big_psi 和 PSI_DATA必有一个不为空
        for filter_data_name in tmp:
            try:
                col_name = None
                for col_name,dist in self.bins_stat_flat[filter_data_name].items():
                    tmp = Ddists.get(col_name,{})
                    tmp[filter_data_name]=dist[[lan['Bins'],lan['Distribution']]].set_index(lan['Bins'])
                    tmp[filter_data_name].index = tmp[filter_data_name].index.to_series().apply(str)
                    Ddists[col_name]=tmp
            except Exception as e:
                if col_name is not None:
                    # 'rascpy:执行big_psi过滤器时，在计算%s数据集的%s列的分布时发生错误'
                    msg = lan['1059']%(filter_data_name,col_name)
                else:
                    # 'rascpy:执行big_psi过滤器时，在计算%s数据集的分布时发生错误'
                    msg = lan['1060']%filter_data_name
                e.add_note(msg)
                raise e

        psis = pd.Series()
        locs = pd.Series()
        psi_dfs = {}
        for col_name,Ddist in Ddists.items():
            try:
                max_psi,_,dist_df,_ = PSI_by_dist(Ddist,self.sc.spec_value.get(col_name,self.sc.default_spec_value),0.01)
                psis[col_name] = max_psi
                locs[col_name] = dist_df['MAX_LOC'].iloc[0]
                psi_dfs[col_name] = dist_df
                
            except Exception as e:
                # 'rascpy:执行big_psi过滤器时，在计算%s列的psi和psi中间表时发生错误'
                e.add_note(lan['1061']%col_name)
                raise e
        #'psi中间表'
        mid = pd.concat(psi_dfs)
        mid.index.names=(lan['Vars'],lan['Bins'])
        return psis,locs,{lan['0062']:mid}

    def _small_iv(self,thv=None):
        tmps = []
        for filter_data_name in self.filter_data_names['small_iv']:
            try:
                k=None
                tmp = pd.Series()
                for k,v in self.bins_stat_flat[filter_data_name].items():
                    tmp[k] = v['IV'].iloc[0]
                tmps.append(tmp)
            except Exception as e:
                if k is not None:
                    # 'rascpy:执行small_iv过滤器时，在%s数据集上的%s列发生错误'
                    msg = lan['1063']%(filter_data_name,k)
                else:
                    msg = lan['1064']%filter_data_name
                e.add_note(msg)
                raise e
        return pd.concat(tmps,axis=1).min(axis=1).apply(np.around,decimals=4),pd.concat(tmps,axis=1).idxmin(axis=1).apply(lambda x:self.filter_data_names['small_iv'][x]),None

    def _big_ivCoV(self,thv=None):
        ivs = {}
        for filter_data_name in self.filter_data_names['big_ivCoV']: 
            try:
                col = None
                for col,stat in self.bins_stat_flat[filter_data_name].items():
                    tmp = ivs.get(col,[])
                    tmp.append(stat.IV.iloc[0])
                    ivs[col] = tmp  
            except Exception as e:
                if col is not None:
                    # 'rascpy:执行big_ivCoV过滤器时，在%s数据集上的%s列发生错误'
                    msg = lan['1065']%(filter_data_name,col)
                else:
                    # 'rascpy:执行big_ivCoV过滤器时，在%s数据集上发生错误'
                    msg = lan['1066']%filter_data_name
                e.add_note(msg)
                raise e
                 
        from scipy.stats import variation 
        ivCovs = pd.Series(name='ivCoV')
        for k,v in ivs.items():
            ivCovs[k] = np.around(variation(v),2)
        
        tmp1 = pd.DataFrame(ivs).T
        tmp1.columns =  self.filter_data_names['big_ivCoV']  
        tmp1 = tmp1.merge(ivCovs,right_index=True,left_index=True)
        # 'ivCoV中间表'
        tmp1.index.name=lan['Vars']
        return ivCovs,None,{lan['0067']:tmp1}
    
    # 1.不能为了用户删除字段，删除与其相关性高的变量。
    # 2.不能为了别的变量而删除用户保留的变量，只能删除与用户保留变量相关性高的变量，无论IV哪个更高
    def _big_corr(self,thv):
        from .ScoreCard import MODEL_DATA
        from .ScoreCardRej import REJ_DATA,SYN_DATA_NAME
        tmp_data_use = MODEL_DATA if self.is_rej==False else REJ_DATA
        tmp_data_name = self.sc.train_data_name if self.is_rej==False else SYN_DATA_NAME
        df_IVs = []
        for k,d in self.bins_stat[tmp_data_use].items():
            if self.is_rej == True and k!=SYN_DATA_NAME:
                continue
            IVs = pd.Series()
            for k,v in d.items():
                IVs[k]=v.IV.iloc[0]
            df_IVs.append(IVs)
        df_IVs = pd.concat(df_IVs,axis=1)
        IVs = df_IVs.mean(axis=1)
        IVs.sort_values(ascending=False,inplace=True)
        woe = self.sc.woes[tmp_data_use][tmp_data_name] 
        try:
            df_corr = woe[IVs.index].corr()
            df_corr = df_corr.apply(lambda x:np.around(x,2))
            while df_corr.shape[0]>0:
                corrs = df_corr.iloc[0]
                if corrs.name not in self.sc.user_del:
                    cols = df_corr.columns[np.abs(corrs) > thv]
                    cols = cols[cols.to_series().apply(lambda m:m not in self.sc.user_save)]   
                    cols = list(cols)
                    for col in cols:
                        if col == corrs.name:
                            continue
                        s = 'corr = %s > %s [%s]'%(corrs[col],thv,corrs.name)
                        if col not in self.filtered_cols:
                            self.filtered_cols[col] = s
                        else:
                            self.filtered_cols[col] = '\n'.join([self.filtered_cols[col],s])
                    cols.append(corrs.name)
                else:
                    cols=[corrs.name]
                df_corr = df_corr.loc[~df_corr.index.isin(cols),~df_corr.columns.isin(cols)]
        except Exception as e:
            # 'rascpy:执行big_corr过滤器时，发生错误'
            msg = lan['1068']
            e.add_note(msg)
            raise e
        return None,None,None

def user_del(sc):
    if sc.user_del is None or len(sc.user_del)==0:
        return
    for col in sc.user_del:
        # '用户删除'
        s = lan['0069']
        if col not in sc.filtered_cols:
            sc.filtered_cols[col] = s
        else:
            sc.filtered_cols[col] = '\n'.join([sc.filtered_cols[col],s])
            
def user_del_groups(sc,is_rej=False):
    if sc.X_group_format is None or sc.user_del_groups is None or len(sc.user_del_groups)==0:
        return
    
    from .ScoreCard import MODEL_DATA
    from .ScoreCardRej import REJ_DATA,SYN_DATA_NAME
    tmp_data_use = MODEL_DATA if is_rej==False else REJ_DATA
    tmp_data_name = sc.train_data_name if is_rej==False else SYN_DATA_NAME
    X = sc.woes[tmp_data_use][tmp_data_name]
    X_groups = X.columns.to_series().apply(parse_x_group,fmt=sc.X_group_format)
    X_groups = X_groups.apply(lambda x:x in sc.user_del_groups)
    del_cols = X.columns[X_groups]

    for col in del_cols:
        # '该变量所在组被用户删除'
        s = lan['0173']
        if col not in sc.filtered_cols:
            sc.filtered_cols[col] = s
        else:
            sc.filtered_cols[col] = '\n'.join([sc.filtered_cols[col],s])
            
def user_save(sc):
    if sc.user_save is None or len(sc.user_save)==0:
        return
    for col in sc.user_save:
        # 'Y [用户保留变量]'
        sc.used_cols[col] = lan['0070']
        if col in sc.filtered_cols:
            del sc.filtered_cols[col]
            
            
def user_save_groups(sc,is_rej=False):
    if sc.X_group_format is None or sc.user_save_groups is None or len(sc.user_save_groups)==0:
        return
    
    from .ScoreCard import MODEL_DATA
    from .ScoreCardRej import REJ_DATA,SYN_DATA_NAME
    tmp_data_use = MODEL_DATA if is_rej==False else REJ_DATA
    tmp_data_name = sc.train_data_name if is_rej==False else SYN_DATA_NAME
    X = sc.woes[tmp_data_use][tmp_data_name]
    X_groups = X.columns.to_series().apply(parse_x_group,fmt=sc.X_group_format)
    X_groups = X_groups.apply(lambda x:x not in sc.user_save_groups)
    del_cols = X.columns[X_groups]

    for col in del_cols:
        # '该变量不在用户指定的变量组中'
        s = lan['0174']
        if col not in sc.filtered_cols:
            sc.filtered_cols[col] = s
        else:
            sc.filtered_cols[col] = '\n'.join([sc.filtered_cols[col],s])

def user_set(sc,is_rej=False):
    if sc.user_set is None or len(sc.user_set)==0:
         return 
     
    from .ScoreCard import MODEL_DATA
    from .ScoreCardRej import REJ_DATA,SYN_DATA_NAME
    tmp_data_use = MODEL_DATA if is_rej==False else REJ_DATA
    tmp_data_name = sc.train_data_name if is_rej==False else SYN_DATA_NAME
    
    for col in sc.user_set:
        #'Y [用户设定变量]'
        sc.used_cols[col] = lan['0071']
        if col in sc.filtered_cols:
            del sc.filtered_cols[col]
    X = sc.woes[tmp_data_use][tmp_data_name]
    for i in X.columns:
        if i not in sc.user_set:
            # '不在用户设定变量之内'
            s = lan['0072']
            if i not in sc.filtered_cols:
                sc.filtered_cols[i] = s
            else:
                sc.filtered_cols[i] = '\n'.join([sc.filtered_cols[i],s])