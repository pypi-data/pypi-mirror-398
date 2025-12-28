# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 11:47:59 2024

@author: wangwenhao
"""
import os
import numpy as np
from .Bins import OptBin,OptBin_mp
from .Tool import region_attr,is_spec_value
class BCSpecValImpute():
    def __init__(self,spec_value={},default_spec_value=[],order_cate_vars={},unorder_cate_vars={},impute_None=True,cores=None):
        '''
        常见的填失方法只能处理缺失值，但是无法处理特殊值，尤其是数据中即包含缺失值同时又包含特殊值的场景。特殊值不能简单的等同于缺失值，如果不分业务场景就简单的把特殊值当成缺失值处理会导致信息损失。特殊值会使得数值型数据变成一种类别型与数值型混合在一起的复杂数据类型，目前没有模型能够直接处理这种数据（尽管有一些模型能够跑出结果，但是不够准确，也没有实际意义）。通过使用RASC提供的Impute包可以解决这一问题，通过它变换后的数据，可以直接送入任何模型，并符合实际业务意义。
        BCSpecValImpute可以用来处理二分类问题的数据中的特殊值和缺失值。
        它可以处理连续型，无序类别型和有序类别型变量的特殊值和缺失值.
        BCSpecialsImpute不只是填充空值，还会对模型无法处理的特殊值进行转换
        它利用rascpy中Bins模块（一种最优分箱算法，它用数学来保证其IV是最高的）的特殊值合并方法，将特殊值与正常值合并，然后将特殊值设置成与其合并的分箱内所有正常数值的均值（对于连续型变量）或随机挑选一个类别（对于类别型变量。因分箱内的所有类别都被视为同一个类别，所以可以随机挑选）
        
        Parameters
        ----------

        spec_value : dict
            每个变量的特殊值的取值范围
            ex. {"x1":["{-9997}","{-9999,-9998}"],"x2":["{None}"]}
            "{... , ...}"不会被解析成set，会按照字符串处理，{}在特殊值里表达的是离散型的取值空间符号
            举例讲解下表达式的含义：
            "{-9997}"：当变量取值为-9997时发生了特殊的含义。例如法院执行次数，-9997可能是指这个身份证没有在公民信息库里，而不是被执行了-9997次。通过这个例子，使用者能明显感觉到 -9997与0,1,2这些取值在含义上的不同。
            "{-9998,-9999}"：当变量取值为-9998或者是-9999时，发生了特殊的含义，虽然这两种含义不同，不过对于此次建模的业务来说，这两种含义可以视为同一种含义，并按照相同的业务逻辑来处理。例如在采集数据时，因为甲方的原因没有采集到的数据被标记为-9998，因为乙方的原因没有采集到的数据被标记为-9999，但是对于业务来说，这两种取值都意味着数据随机缺失，所以把他们都按照随机缺失的逻辑来处理。这样即可以保留原始数据的取值约定，以便回溯，又可以免去使用者处理数据带来的额外编写代码的工作。
            "{None}"是空特殊值或缺失值，两者的区别请参看关于异常值、缺失值、特殊值。之所以用{None}，而没用{miss}等字眼来表示，是因为有时空值的产生机制与缺失值产生的机制并不一样。缺失值代表抽样过程中某些人为无法控制的原因导致没有采集到样本点，导致数据信息缺失，如数据传递过程中断网，设备故障导致的数据没有被采集，这是一种随机缺失。而空值产生的原因除了随机缺失，还可能是因为非信息缺失造成，如没有贷款记录，因健康不需要做某项检查，温度太低设备采集不到等，空值本身就是信息。不要将带有信息的空值和随机缺失空值混合成一个特殊值。
            ex. {"x1":"{None,-9997}"} 其含义是经过对业务的分析，空值和-9997对于此次建模可以采用相同的处理方法
            如果某个变量没有配置空特殊值，但该变量里包含空值，那么会自动生成一个{None}组来包含该变量的空值。
            默认:{}.
            
        default_spec_value : list
            如果变量没有被配置在spec_value中，其默认的特殊值
            通常在数据有全局公共特殊值时，这个配置很方便
            ex. ["{-9997}","{None}","{-9998,-9996}"]。
            默认:[].
            
        order_cate_vars : dict
            将有序类别变量列举在此处，并给出变量中每个类别的顺序，如果取值顺序设置为None时则使用字符的字典序作为顺序
            对于有序变量,相邻的名义顺序只能出现在同一分箱内或者相邻分箱的首尾邻接点
            如果名义顺序与事件发生率顺序不一致，可根据业务情况自己判断是否将该变量配置成有序变量
            Bins对有序变量支持全局最优分箱
            例如： {"x1":("v1","v2"),"x2":("v3","**","v4"),"x3":None}
            所有未在配置中出现的类别（不包含特殊值），统称为通配类别，用**来表示。字典序作为顺序时，没有通配类别
            None或{}：变量中没有有序类别的变量.
            默认:{}.
            
        unorder_cate_vars : dict
            将无序类别变量列举在此处，无序类别会依据事件发生率作为类别的顺序。
            每个变量配置一个阈值,将分布占比小于该阈值的类别并入通配类别。如果某个变量的阈值为None，则对该变量频数过小的类别不做通配处理
            ex1. {'x1':0.01,'x2':None}
            Bins对无序变量支持全局最优分箱
            在其他数据集有可能见到训练集上未覆盖的值，这些类别也放入通配类别。
            None或{}:变量中没有无序类别变量。
            默认:{}.
            
        impute_None : boolean
            对空值是否进行填充，因为有的模型能够自动处理空值，如后续要使用此类模型，填充时可以不去处理空值。
            如果数据中的空并非随机缺失，而是业务缺失，代表着一种状态且后续使用的模型能够自动处理空值，则建议将该参数设置成False
            True: 填充空值
            False：不填充空值，交由后续模型处理（如果模型能够处理空值）
            默认: True
            
        cores : int
            使用CPU的核数。
            None：使用全部核数
            小于0时，为保留cpu核数，即os.cpu_count() - cores
            默认:None.

        Returns
        -------
        None.

        '''
        self.default_distr_min = 0.2
        self.spec_value = spec_value
        self.default_spec_value = default_spec_value
        self.order_cate_vars = order_cate_vars
        self.unorder_cate_vars = unorder_cate_vars
        self.impute_None = impute_None
        
        if cores is None:
            self.no_cores = os.cpu_count()
        elif cores < 0:
            self.no_cores = os.cpu_count() - cores
        else:
            self.no_cores = cores
            
    def _get_cols_with_spec(self,X):
        tmp_cols = X.apply(lambda s:s.apply(lambda x:is_spec_value(x,self.spec_value.get(s.name,self.default_spec_value),self.impute_None)).any())
        self.spec_cols = list(tmp_cols[tmp_cols].index)
            
    def fit(self,X,y,weight=None,y_label=None):
        '''
        训练每个变量的每个缺失值的填充方法（如果impute_None=True）和每个特殊值的转换方法
        
        Parameters
        ----------
        X : DataFrame
            需要被转换的数据
            如果某个变量没有配置特殊值，或者是不包含所配置的特殊值，则该变量会被自动忽略
            
        y : Series
            target
            
        weight : Series, optional
            权重 
            默认： None.
        y_label : dict,optional
             将target中的哪个取值定义为事件发生，哪个取值定义为事件未发生。
             keys的取值只能是unevent或event
             values的取值要根据y取值填写
             默认:None
             None的含义与{'unevent':0,'event':1}相同
        
        Returns
        -------
        None.

        '''
        self._get_cols_with_spec(X)
        self.impute_values={}
        if len(self.spec_cols)==0:
            return
        if self.no_cores == 1:
            optbins = OptBin(X_dats=X[self.spec_cols],y_dats=y,y_label=y_label,weight_dats=weight,train_name=None,
                             mono={},default_mono='N',sgst_monos={},
                             distr_min={},default_distr_min=self.default_distr_min,
                             rate_gain_min={},default_rate_gain_min=None,
                             bin_cnt_max={},default_bin_cnt_max=None,
                             spec_value=self.spec_value,default_spec_value=self.default_spec_value,
                             spec_distr_min={},default_spec_distr_min=1,
                             spec_comb_policy={},default_spec_comb_policy='a',
                             order_cate_vars=self.order_cate_vars,unorder_cate_vars=self.unorder_cate_vars
                             ,no_wild_treat={},default_no_wild_treat=None)
        else:
            optbins = OptBin_mp(X_dats=X[self.spec_cols],y_dats=y,y_label=y_label,weight_dats=weight,train_name=None,
                              mono={},default_mono='N',sgst_monos={},
                              distr_min={},default_distr_min=self.default_distr_min,
                              rate_gain_min={},default_rate_gain_min=None,
                              bin_cnt_max={},default_bin_cnt_max=None,
                              spec_value=self.spec_value,default_spec_value=self.default_spec_value,
                              spec_distr_min={},default_spec_distr_min=1,
                              spec_comb_policy={},default_spec_comb_policy='a',
                              order_cate_vars=self.order_cate_vars,unorder_cate_vars=self.unorder_cate_vars
                              ,no_wild_treat={},default_no_wild_treat=None,
                              cores=self.no_cores)
        
        for k,v in optbins.items():
            self.impute_values[k]={}
            for i in v:
                if isinstance(i,list):
                    for ii in i:
                        if  ii.startswith('[') or ii.startswith('('):
                            v1,v2,decimals,asc,left_close,right_close = region_attr(ii)
                            tmp = X[k]
                            p1 = '>=' if left_close else '>'
                            p2 = v1 if asc else v2
                            p3 = '<=' if right_close else '<'
                            p4 = v2 if asc else v1
                            cond = '(tmp %s %s) & (tmp %s %s)'%(p1,p2,p3,p4)
                            tmp = tmp[eval(cond)]
                            inp_value = np.around(tmp.mean(),decimals)
                        elif ii.startswith('<'):
                            inp_value = ii[1:-1].split(',')[0]
                            
                    for ii in i:
                        if ii.startswith('{'):
                            specs = eval(ii)
                            for spec in specs:
                                self.impute_values[k][spec] = inp_value#包含None
                                if spec is None:
                                    self.impute_values[k][np.nan] = inp_value
      
    def transform(self,X):
        '''
        填充缺失值和转换特殊值。需要在调用fit后。
        
        Parameters
        ----------
        X : DataFrame
            需要被填充和转换的数据
        
        Returns
        -------
        DataFrame
            填充和转换后的数据.

        '''
        return X.apply(lambda x:x.replace(self.impute_values[x.name]) if x.name in self.spec_cols else x)
    
    def fit_transform(self,X,y,weight=None,y_label=None):
        '''
        先调用fit训练，再调用transform转换

        参看fit,transform

        '''
        self.fit(X,y,weight,y_label)
        return self.transform(X)