# -*- coding: utf-8 -*-

import pydatamodel.creditScore as creditScore
import pydatamodel.dataAnalysis as dataAnalysis
import pydatamodel.databaseModel as databaseModel
try:
    import pydatamodel.mechineLearning as mechineLearning
except ImportError:
    print('mechineLearning模块中，以下库是必须的，\
          你可能缺少了其中的一个或者多个：xlsxwriter、joblib、xgboost、openpyxl。如你不使用mechinelearning模块则无需理会本提示。')

__all__=['creditScore','dataAnalysis','databaseModel','mechineLearning']
