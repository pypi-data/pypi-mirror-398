# -*- coding: utf-8 -*-

import pickle
import os

def get_data(data_name):
    with open('%s/Dats.pkl'%(os.path.dirname(__file__)),'rb') as f:
        dats = pickle.load(f)
    return dats[data_name]