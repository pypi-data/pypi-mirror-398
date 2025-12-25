# -*- coding: utf-8 -*-
#===========评分卡建模函数================
#用于评分卡建模的函数
#许冠明
#20180801
#=======================================
import sys
import numpy as np
import pandas as pd

import matplotlib as mpl
mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['font.serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题,或者转换负号为字符串

import matplotlib.pyplot as plt
import os
import statsmodels.api as sm
from sklearn.tree import DecisionTreeClassifier
from statsmodels.stats.outliers_influence import variance_inflation_factor#方差膨胀因子
from sklearn.cluster import KMeans


#from interval import Interval

#判断是否有包含特殊字符的字段，如果有，提示出来
def varSpecialCharCheck(inds=None,specialChar=','):
    #xuguanming 20190524
    #判断数据集中的字符型字段中，是否包含特殊字符
    varDtypes=inds.dtypes
    varObject=list(varDtypes[varDtypes==object].index)
    #i="result_YQ_LJCS"
    varTe=[]
    for i in varObject:
       #dd= pd.value_counts(inds[i],dropna=False).sort_index()
       varObjectChar=list(set(inds[i]))
       k=0
       for j in varObjectChar:           
           if(j.find(specialChar)>=0):
               k=k+1
       if k>0:
           varTe.append(i)
           print(i+" 包含特殊字符'"+specialChar+"'，请预先处理！")
    return varTe 
#对包含特殊字符的字段，用普通字符替换特殊字符    
def varSpecialCharReplace(inds=None,replaceVars=[],oldChar=",",newChar="_"):
    #xuguanming 20190524
    #将数据集中的特定字符型替换为指定字符
    outds=inds.copy()
    def f(x):
        y=x.replace(oldChar,newChar) 
        return y
    for i in replaceVars:
        a=outds[i].apply(f)
        outds[i]  =   a
        print(i+" 特殊字符已处理！")
    return outds

def objVars2NumVars(inds=None,toDoVar=None,notDoVar=None,naStr=['-','--',''],block=0):
    #对dataframe数据集中非数值变量转换为数值变量
    #xuguanming 20200406 20211130增加naStr参数
    #toDoVar:要处理的变量
    #notDoVar：不要处理的变量
    #block：当字符变量取值naStr中包含的字符时,转为什么数字，可以转为0、np.nan等
    #naStr:表示当取值为特定字符时，取值为block
    #inds=dat1
    #toDoVar=['low_最低价']
    #notDoVar=['code_证券代码','date_交易所行情日期']
    
    #block=0
    baostockHisMonth1=inds.copy()
    columns_0=list(baostockHisMonth1.columns) 
    if toDoVar is not None:
        columns_1=toDoVar
    elif notDoVar is not None:
        columns_1=[y for y in columns_0 if y not in notDoVar ]
    else:
        columns_1=columns_0
    
    #baostockHisMonth1_columns=list(baostockHisMonth1.columns  ) 
    #baostockHisMonth1.index=list(range(0,baostockHisMonth1.shape[0]))
    for j in columns_1:
        #j=columns_1[1]
        #print(j)
        if baostockHisMonth1.loc[:,j].dtypes=="object":
            #baostockHisMonth1[j][baostockHisMonth1[j]=='']=str(block)
            for k in naStr:
                baostockHisMonth1.loc[baostockHisMonth1[j] == k,j]=str(block)
            baostockHisMonth1.loc[:,j] = baostockHisMonth1.loc[:,j].astype(float)
    return baostockHisMonth1


def DataCheck(CheckData=None,specialchar=[',','"',"'"],newchar=['_','_','_']):
	#xuguanming 202101
    #判断字符型变量中，是否包含特殊字符(不可包含引物逗号、引号)
    CheckData0=CheckData.copy()
    CheckData1=CheckData0.dropna()
    if(CheckData1.shape[0]< CheckData0.shape[0]):
        print("警告：数据集存在缺失值，请填充缺失值。如未填充，将删除缺失值所在行！")
    if specialchar is not None:
        for i in range(len(specialchar)):
            varCheck1=varSpecialCharCheck(inds=CheckData1,specialChar=specialchar[i])
            if len(varCheck1)>0:
        #将包含特殊字符的变量，其中的特殊字符替换为指定字符
                CheckData1=varSpecialCharReplace(inds=CheckData1,replaceVars=varCheck1,oldChar=specialchar[i],newChar=newchar[i])#训练集    
    return CheckData1



def Var_Baifenwei(inds, var, pct=10):
    # 许冠明 20180801
    # inds：输入数据框。
    # var：需要GROUP的VARIABLE名，
    # pct: 百分位数组
    # 输出：
    # outds-原始数据集+BFW+GROUP
    # Freq-BFW分布，以及对应的GROUP
    # Cut-POINT
    if isinstance(pct,np.ndarray):
        pct = pct.tolist()
    if pct is None:
        pct = 10
    data0 =inds[var]#包含缺失值
    data = inds[var].dropna()#不包含缺失值
    if len(data0)==len(data):#是否包含缺失值
        isNA=0
    else:
        isNA=1
        
    length = len(np.unique(data))
    # 如果pct为整数，则转化为等分百分数数组
    # 如果pct为list，则直接转化为百分数数组
    # 如果分组大于数据种类个数，将原始分组数改为数据种类个数（对应分类变量）
    if isinstance(pct, int):
        if pct > length:
            pct = length
        pct = ((np.arange(pct) + 1) / pct).tolist()
    BFW = np.array(pct) * 100

    # 如果数据类型不是数值型
    if data.dtypes == object:

        table = pd.value_counts(data0,dropna=False).sort_index()
        out = data0
        Cut = np.unique(data).tolist()
        if isNA==1:
            Cut.append(np.nan)
        Freq = pd.DataFrame({'GROUP': Cut, 'COUNT': table.tolist(),
                             'RATE': (table / sum(table)).tolist()})
        Freq_tot=pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
                                         'RATE': [sum(Freq['RATE'])]})
        Freq=pd.concat([Freq,Freq_tot],axis=0)
        #Freq = Freq.append(pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
        #                                 'RATE': [sum(Freq['RATE'])]}), ignore_index=True)
        outds = inds.copy()
        outds['GROUP'] = out

    else:
        # 找到各分位数对应的数据点
        # cut_points去重后得到cut_points_unique
        cut_points = np.percentile(data, BFW)
        cut_points_unique, idx = np.unique(cut_points, return_index=True)

        # 为了统一word表中所给格式，将左右起点改为正负无穷大
        # Cut数组存储区间端点
        inf = float('inf')
        Cut = np.hstack((np.array([-inf]), cut_points_unique))
        Cut[-1] = inf

        # 找到数据对应的区间
        intervals = pd.cut(data0, Cut, right=True, include_lowest=True)

        outds = inds.copy()
        outds['GROUP'] = intervals

        # count表存储区间及其个数
        count = intervals.value_counts(dropna=False).sort_index()
        # rate表存储区间个数的占比
        rate = count / data.size
        BFWv=[int(item * 100) / 100 for item in BFW[idx]]
        Cut=Cut.tolist()
        cut_points_unique=cut_points_unique.tolist()
        if isNA==1:
            BFWv.insert(0,np.nan)
            Cut.insert(0,np.nan)
            cut_points_unique.insert(0,np.nan)
        Freq0 = pd.DataFrame({'BFW': BFWv,
                             'COUNT': count.tolist(),
                             'RATE': rate.tolist(),
                             'POINT': cut_points_unique,
                             'LOW': Cut[:-1],
                             'UP': Cut[1:],
                             'GROUP': count.index})
        
        Freq_tot=pd.DataFrame({'BFW': [9999],
                                         'COUNT': [sum(Freq0['COUNT'])],
                                         'RATE': [sum(Freq0['RATE'])],
                                         'POINT': np.nan,
                                         'LOW': np.nan,
                                         'UP': np.nan,
                                         'GROUP': 'TOTAL'})
        Freq=pd.concat([Freq0,Freq_tot],axis=0)
        '''
        Freq = Freq0.append(pd.DataFrame({'BFW': [9999],
                                         'COUNT': [sum(Freq0['COUNT'])],
                                         'RATE': [sum(Freq0['RATE'])],
                                         'POINT': np.nan,
                                         'LOW': np.nan,
                                         'UP': np.nan,
                                         'GROUP': 'TOTAL'}),
                           # 'GROUP':pd.Interval(left=-inf, right=inf)}),\
                           ignore_index=True)
        '''

        #Freq0["GROUP1"]=list(Freq0["GROUP"])
        #outds.loc[:,"GROUP1"]=outds.loc[:,"GROUP"].astype(object)
        #outds=pd.merge(outds,Freq0[["BFW","GROUP1"]],how='left',on='GROUP1')

    # print ('done!')
    if isNA==1:
        del Cut[0]
    return outds, Freq, Cut




def Var_Groupcut_Tot(inds, idvar="ID", ignore_index=False):
    dds = pd.DataFrame()
    for i, string in enumerate(inds.drop(idvar, axis=1).columns):
        Freq = Var_Baifenwei(inds, string)[1]
        Freq['VARIABLE'] = [string] * Freq.shape[0]
        dds = dds.append(Freq.rename(columns={'GROUP': 'GROUP'})[['GROUP', 'COUNT', 'RATE', 'VARIABLE']],
                         ignore_index=ignore_index)

    return dds


def Var_Groupcut(inds, var, groupcut=None, groupn=10):
    # inds：输入数据框。
    # var：需要GROUP的VARIABLE名，
    #     如果var是字符型变量，那么按字符取值分布就行了，groupcut和groupn无效。
    # groupcut：划分的POINT
    # groupn:等分的份数
    # 输出：
    # $outds---原始数据集+GROUP变量
    # $Freq---GROUP分布，以及对应的GROUP,
    # $Cut-POINT

    def Var_Groupcut_catagory(data):

        # table表存储data中的种类和个数
        table = pd.value_counts(data,dropna=False).sort_index()
        out = data
        Cut = np.unique(data.dropna())
        Freq = pd.DataFrame({'GROUP': Cut, 'COUNT': table.tolist(),
                             'RATE': (table / sum(table)).tolist()})
        #Freq = Freq.append(pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
        #                                 'RATE': [sum(Freq['RATE'])]}), ignore_index=True)
        
        Freq_tot=pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
                                         'RATE': [sum(Freq['RATE'])]})
        Freq=pd.concat([Freq,Freq_tot],axis=0)
        
        return out, Freq, Cut

    def Var_Groupcut_group(data, group):
        # print (group)
        #group=groupcut
        # table表用来存储所有单分类及其个数
        table = pd.value_counts(data,dropna=False).sort_index()
        # count数组用来存储各个分类的个数COUNT
        count = np.array([0] * (len(group) + 1))
        # ss数组用来存储在group中的catagories
        ss = []
        for (i, s) in enumerate(group):
            s = s.split(',')
            for item in s:
                count[i] += table[item] if item in table.index else 0
                ss.append(item)
        # left数组用来存储不在group中的catagories
        left = []
        for s in table.index:
            if s not in ss:
                left.append(s)
        for item in left:
            count[-1] += table[item]
        # out数组用来存储各个元素所在的group区间
        out = data
        # Cut即为cut points
        Cut = (group + [','.join(left)]) if left != [] else group

        # unique之后空串一定在第一个元素

        # 构造函数f(x）来判断应该在哪一个分类组中
        def f(x):
            for i, j in enumerate(Cut):
                if x in j.split(','):
                    return j

        out = data.apply(f)

        # 将left数组变成一个字符串用来表示余下的所有catagories构成的cut point
        left = [','.join(left)]
        if left == [','.join([])]:
            count = count[:-1]
        Freq = pd.DataFrame({'GROUP': Cut, 'COUNT': count,
                             'RATE': (count / sum(count))})
        #Freq = Freq.append(pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
        #                                 'RATE': [sum(Freq['RATE'])]}), ignore_index=True)

        Freq_tot=pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
                                         'RATE': [sum(Freq['RATE'])]})
        Freq=pd.concat([Freq,Freq_tot],axis=0)
        return out, Freq, Cut

    def Var_Groupcut_groupcut(data, groupcut):
        out = pd.cut(data, groupcut, right=True, include_lowest=True)
        count = out.value_counts(dropna=False).sort_index()
        Freq = pd.DataFrame({'GROUP': count.index, 'COUNT': count.values, 'RATE': (count / sum(count))})
        #Freq = Freq.append(pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
        #                                 'RATE': [sum(Freq['RATE'])]}), ignore_index=True)
        
        Freq_tot=pd.DataFrame({'GROUP': 'TOTAL', 'COUNT': [sum(Freq['COUNT'])],
                                         'RATE': [sum(Freq['RATE'])]})
        Freq=pd.concat([Freq,Freq_tot],axis=0)
        return out, Freq, groupcut

    data = inds[var]

    # if type(groupcut) == type(np.array([])):
    if isinstance(groupcut, np.ndarray):
        groupcut = groupcut.tolist()

    if (data.dtypes == object) and (groupcut is None):
        # print ('using Var_Groupcut_catagory')
        out, Freq, Cut = Var_Groupcut_catagory(data)
        outds = inds.copy()
        outds['GROUP'] = out
        del out
    elif (data.dtypes == object) and (groupcut is not None):
        if isinstance(groupcut, int):
            # print ('using Var_Groupcut_catagory')
            out, Freq, Cut = Var_Groupcut_catagory(data)
        elif isinstance(groupcut, list):
            # print ('using Var_Groupcut_group')
            out, Freq, Cut = Var_Groupcut_group(data, groupcut)
        else:
            raise ('groupcut must be a int or list or a numpy.ndarray!')
        outds = inds.copy()
        outds['GROUP'] = out
        del out
    elif groupcut is None:
        # print ('using Var_Baifenwei')
        outds, freq, Cut = Var_Baifenwei(inds, var, groupn)
        Freq = freq[['GROUP', 'COUNT', 'RATE']].rename(columns={'GROUP': 'GROUP'})
    else:
        # print ('using Var_Groupcut_groupcut')
        out, Freq, Cut = Var_Groupcut_groupcut(data, groupcut)
        outds = inds.copy()
        outds['GROUP'] = out
        del out
        
    #处理一下两头为0的情况 --为了画图好看   
    groupCutResTab=Freq.copy()
    groupCutResTab1=groupCutResTab[(groupCutResTab['GROUP']!="TOTAL") & (groupCutResTab['GROUP'].notnull())].copy()
    groupCutResTab1['rank']=range(groupCutResTab1.shape[0])
    
    groupCutResTab1=groupCutResTab1.sort_values(by='rank',ascending=True)
    groupCutResTab1.index=range(groupCutResTab1.shape[0])
    #第一个不等于0所在的行
    firsti=0
    lasti=groupCutResTab1.shape[0]
    for i in range(groupCutResTab1.shape[0]):
        if groupCutResTab1.loc[i,"COUNT"]>0:
            firsti=groupCutResTab1['rank'][i]
            break
        
    groupCutResTab1=groupCutResTab1.sort_values(by='rank',ascending=False)
    groupCutResTab1.index=range(groupCutResTab1.shape[0])
    #第一个不等于0所在的行
    for i in range(groupCutResTab1.shape[0]):
        if groupCutResTab1.loc[i,"COUNT"]>0:
            lasti=groupCutResTab1['rank'][i]
            break
    groupCutResTab2=groupCutResTab1[(groupCutResTab1['rank']>=firsti) & (groupCutResTab1['rank']<=lasti)]    
    groupCutResTab2=groupCutResTab2.sort_values(by='rank') [['GROUP','COUNT','RATE']]   
    groupCutResTab2.index= range(groupCutResTab2.shape[0]) 
    groupCutResTab3=pd.concat([groupCutResTab[groupCutResTab['GROUP'].isnull()],groupCutResTab2,groupCutResTab[groupCutResTab['GROUP']=="TOTAL"]],axis=0)    
 
    return outds, Freq, Cut,groupCutResTab3


def Var_Multi_Groupby(inds=None,groupby=['adm_pre_result','adm_result'],target='CreditAmt'):
    # 多维变量汇总
    # xuguanming 20240530
    # inds：输入数据框。
    # groupby：需要GROUP的VARIABLE名。
    #target:被统计变量，必须数值型，None则表示计数
    #fun:被统计变量的统计函数:avg/mean-求均值,sum,max,min
    if (target != None) &(target !='*') :
        groupby0=groupby.copy()
        groupby0.append(target)
        
        groupby1=groupby.copy()
        groupby1.append('_t_flag__')
        tmpdata=inds[groupby0]
        #tmpdata.loc[:,'_t_flag__']=1
        tmpdata['_t_flag__']=1
        
        tmptab1=tmpdata[groupby0].groupby(groupby).sum()
        tmptab2=tmpdata[groupby0].groupby(groupby).mean()
        tmptab3=tmpdata[groupby0].groupby(groupby).max()
        tmptab4=tmpdata[groupby0].groupby(groupby).min()
        tmptab4_1=tmpdata[groupby0].groupby(groupby).median()
        
        tmptab0=tmpdata[groupby1].groupby(groupby).sum()
        
        tmptab5=pd.concat([tmptab0,tmptab1,tmptab2,tmptab4_1,tmptab3,tmptab4],axis=1)
        tmptab5.columns=['Count','Sum','Mean','Median','Max','Min']
        tl=list(tmptab5.index)
        tl2=pd.DataFrame(tl)
        tl2.columns=groupby
        tl2['Count']=list(tmptab5['Count'])
        tl2['Sum']=list(tmptab5['Sum'])
        tl2['Mean']=list(tmptab5['Mean'])
        tl2['Median']=list(tmptab5['Median'])
        tl2['Max']=list(tmptab5['Max'])
        tl2['Min']=list(tmptab5['Min'])
        
        tl2_tot=pd.DataFrame({groupby[0]:'合计','Count':sum(tmptab0['_t_flag__']),'Sum':sum(tmpdata[target]),'Mean':np.mean(tmpdata[target]),'Median':np.median(tmpdata[target]),'Max':max(tmpdata[target]),'Min':min(tmpdata[target])},index=[0])  
        tmptab99=pd.concat([tl2,tl2_tot],axis=0)
        tmptab99.index=range(tmptab99.shape[0])

    else:
        tmpdata=inds[groupby]
        #tmpdata.loc[:,'_t_flag__']=1
        tmpdata['_t_flag__']=1
        target = '_t_flag__'

        tmptab5=tmpdata.groupby(groupby).sum()

        tl=list(tmptab5.index)
        tl2=pd.DataFrame(tl)
        tl2.columns=groupby
        tl2['Count']=list(tmptab5[target])
        tl2_tot=pd.DataFrame({groupby[0]:'合计','Count':sum(tl2['Count'])},index=[0])    
    
        tmptab99=pd.concat([tl2,tl2_tot],axis=0)
        tmptab99['Rate']=tmptab99['Count']/tl2_tot['Count'][0]
        tmptab99.index=range(tmptab99.shape[0])
        
    return tmptab99


def Treebinning(x: pd.Series, y: pd.Series, max_leaf_nodes=8,nan: float = -999.):

    boundary = []  # 待return的分箱边界值列表
    x = x.fillna(nan).values  # 填充缺失值
    y = y.values
    clf = DecisionTreeClassifier(criterion='gini',    #“基尼系数”最小化准则划分
                                 max_leaf_nodes=max_leaf_nodes,       # 最大叶子节点数
                                 min_samples_leaf=0.05)  # 叶子节点样本数量最小占比

    clf.fit(x.reshape(-1, 1), y)  # 训练决策树
    n_nodes = clf.tree_.node_count
    children_left = clf.tree_.children_left
    children_right = clf.tree_.children_right
    threshold = clf.tree_.threshold

    for i in range(n_nodes):
        if children_left[i] != children_right[i]:  # 获得决策树节点上的划分边界值
            boundary.append(threshold[i])

    boundary.sort()
    min_x = x.min()
    max_x = x.max() + 0.1  # +0.1是为了考虑后续groupby操作时，能包含特征最大值的样本
    boundary = [min_x] + boundary + [max_x]
    return boundary

def IV_Compute_Single(inds, var, target, pct=None, groupcut=None):
    #xuguanming 20180930 20190521
    #计算IV值
    '''
    inds=S1_train
    var="pay_1"
    target="gbie"
    pct=None
    groupcut=[-inf,-1,5,10,20,30,40,50,inf]
    '''
    inf = float('inf')
    varDtype=inds[[var]].dtypes[0]
    if varDtype==object:
        sc="character"
    else:
        sc="numeric"
    if groupcut is None:
        
        if sc=="numeric":
            boundary = Treebinning(inds[var], inds[target],max_leaf_nodes=10)
            boundary[0]=-inf
            boundary[len(boundary)-1]=inf
            a0, b, c ,d= Var_Groupcut(inds, var, groupcut=boundary,groupn=None)
        else:
            a0, b, c = Var_Baifenwei(inds, var)
            b=b.rename(columns={'GROUP': 'GROUP'})
    else:
        a0, b, c ,d= Var_Groupcut(inds, var, groupcut=groupcut,groupn=None)
        #dd=Var_Groupcut(inds, var, groupcut=[float("-inf"),10,20,30,40,41,41.1,50,60,float("inf")],groupn=None)

    
    a = pd.DataFrame({target: a0[target], 'GROUP': a0.iloc[:, -1]}).groupby('GROUP').sum()
    a["GROUP"]=list(a.index)
    a.index=range(a.shape[0])
    iv_table0=pd.merge(b[b.GROUP!="TOTAL"],a,how="left",on="GROUP")
    iv_table = pd.DataFrame({'n_0': iv_table0['COUNT'] - iv_table0[target],
                             'n_1': iv_table0[target],
                             'count': iv_table0['COUNT']})
    adj = pd.Series([0] * iv_table.shape[0])
    adj = adj.mask(iv_table['n_0'] == 0, 0.5)
    adj = adj.mask(iv_table['n_1'] == 0, 0.5)
    iv_table['adj'] = adj
    iv_table['rate'] = iv_table['n_1'] / iv_table['count']
    iv_table['p_0'] = (iv_table['n_0'] + iv_table['adj']) / sum(iv_table['n_0'])
    iv_table['p_1'] = (iv_table['n_1'] + iv_table['adj']) / sum(iv_table['n_1'])
    iv_table['p_01'] = (iv_table['n_0'] +iv_table['n_1']+ iv_table['adj']) / sum(iv_table['n_0']+iv_table['n_1'])
    iv_table['WOE'] = np.log(iv_table['p_0'] / iv_table['p_1'])
    iv_table['iv_att'] = (iv_table['p_0'] - iv_table['p_1']) * iv_table['WOE']
    iv_table['iv'] = sum(iv_table['iv_att'])
    iv_table['group'] = iv_table0.GROUP
    iv_table['vname'] = var
    iv_table['vdtype']=sc
    iv_table['grp']=range(0,iv_table.shape[0])
    iv_table.index=range(0,iv_table.shape[0])
    for i in range(iv_table.shape[0]):
        iv_table.loc[i,'ks'] = 100*(abs(sum(iv_table.loc[list(range(i+1)),'n_1']) / sum(iv_table['n_1'])-sum(iv_table.loc[list(range(i+1)),'n_0']) / sum(iv_table['n_0'])))
    iv_table['KS']=max(iv_table['ks'])
    return iv_table, c

def IVtable2WoeRule(iv_table=None,outpath=None):
    #xuguanming
    #20190522 20190622
    iv_table_tmp=iv_table.copy()
    iv_table_tmp.index=range(iv_table_tmp.shape[0])
    iv_table_tmp['UP']=None
    iv_table_tmp['LOW']=None
    iv_table_tmp['RULE']=None
    var=str(iv_table_tmp['vname'][0])
    var_dtype=str(iv_table_tmp['vdtype'][0])

    
    #python格式规则代码
    file = open(outpath+"\\"+var+".py",'w')
    #i=1
    if (var_dtype !="character"):#如果是数值型变量
        for i in range(iv_table_tmp.shape[0]):
  
            #iv_table_tmp.loc[i,"group"].left
            if i==0:
                iv_table_tmp.loc[i,'RULE']="\tinds.loc[inds['"+var+"']<="+str(iv_table_tmp.loc[i,"group"].right)+",'WOE_"+var+"']="+str(iv_table_tmp.loc[i,"WOE"])
            elif i !=(iv_table_tmp.shape[0]-1):
                 iv_table_tmp.loc[i,'RULE']="\tinds.loc[ (inds['"+var+"']>"+str(iv_table_tmp.loc[i,"group"].left)+") & (inds['"+var+"']<="+str(iv_table_tmp.loc[i,"group"].right)+"),'WOE_"+var+"']="+str(iv_table_tmp.loc[i,"WOE"])
            else:
                iv_table_tmp.loc[i,'RULE']="\tinds.loc[inds['"+var+"']>"+str(iv_table_tmp.loc[i,"group"].left)+",'WOE_"+var+"']="+str(iv_table_tmp.loc[i,"WOE"])
            file.write(iv_table_tmp.loc[i,'RULE'])
            file.write("\n")
    else:
        for i in range(iv_table_tmp.shape[0]):
            s=iv_table_tmp.loc[i,"group"].split(",")
            file.write("\n\tinds.loc[")
            for j in range(len(s)):
                file.write("\n\t\t("+"inds['"+var+"']=='"+s[j]+"')")
                if j<(len(s)-1):
                    file.write("\n\t\t| ")
                elif j==(len(s)-1):
                    file.write("\n\t\t,'WOE_"+var+"']="+str(iv_table_tmp.loc[i,"WOE"])+"\n")
    file.close()
    
    #SAS格式规则代码
    file = open(outpath+"\\"+var+".sas",'w')
    #i=0
    if (var_dtype !="character"):#如果是数值型变量
        file.write("Length LBL_"+var+" $60;\n")
        for i in range(iv_table_tmp.shape[0]):
            LOW=str(iv_table_tmp.loc[i,"group"].left)
            UP=str(iv_table_tmp.loc[i,"group"].right)
            if LOW=="-inf":
                LOW="low"
            if UP=="inf":
                UP="high"
            if i!=0:
                file.write("else\n")
            if i!=(iv_table_tmp.shape[0]-1):
                file.write("if "+var+" LE "+UP+" then do;\n")
            else:
                file.write("do;\n")
            file.write("WOE_"+var+" = "+str(iv_table_tmp.loc[i,"WOE"])+";\n")
            file.write("GRP_"+var+" = "+str(iv_table_tmp.loc[i,"grp"]+1)+";\n")
            file.write("LBL_"+var+" = '"+LOW+"<"+var+"<="+UP+"';\n")
            file.write("end;\n")

    else:
        file.write("Length LBL_"+var+" $200;\n")
        file.write("length _FORMAT $ 200;\n")
        file.write("drop _FORMAT;\n")
        file.write("_FORMAT = strip(put( "+var+" ,$200.));\n")

        for i in range(iv_table_tmp.shape[0]):
            if i!=0:
                file.write("else\n")
            file.write("if _FORMAT in(\n")
            file.write("/*,*/'"+iv_table_tmp.loc[i,"group"].replace(",","','")+"'\n")
            file.write(") then do;\n")
            file.write("WOE_"+var+" = "+str(iv_table_tmp.loc[i,"WOE"])+";\n")
            file.write("GRP_"+var+" = "+str(iv_table_tmp.loc[i,"grp"]+1)+";\n")
            file.write("LBL_"+var+" = '"+iv_table_tmp.loc[i,"group"]+"';\n")
            file.write("end;\n")
            
    file.close()    
    #return iv_table_tmp['RULE']

#IVtable2WoeRule(iv_table=ivSingle[0],outfile=r'C:\Xuguanming\原先的文件夹\python\Python评分卡建模\tmp\woerule.txt')

def Var_Binning_Single(trainds=None,testds=None,var="sy_cert_age",target="gbie",
	pct=None,groupcut=None,autoCombin=True,labelds=None,plotShow=True,plotSave=True,naValue=-1,
	outpath=r"C:\Xuguanming\原先的文件夹\python\tmp"):
    #开发者：许冠明
    #开发日期：20190608
    
    inf=float("inf")
    if labelds is not None:
        #labelds.columns=["vname","label"]
        pass
    else:
        labelds=pd.DataFrame({"vname":list(trainds.columns),"label":list(trainds.columns)})

    if trainds[var].dtypes == object:#如果是字符型变量    
        ivtrainRes=IV_Compute_Single(inds=trainds, var=var, target=target, pct=pct, groupcut=groupcut)
        ivValidateRes=IV_Compute_Single(inds=testds, var=var, target=target, pct=None, groupcut=ivtrainRes[1])
    else:#如果是数值型变量
        if naValue !=None:#  假设设定了-1为缺失值
            tmpdata=trainds.loc[trainds[var]>naValue,[var,target]]
            if tmpdata.shape[0] <trainds.shape[0]:#存在缺失值的情况               
                ivtrainRes=IV_Compute_Single(inds=tmpdata, var=var, target=target, pct=pct, groupcut=groupcut)
                cuttmp0=ivtrainRes[1].copy()
                cuttmp=[-inf]
                for k in cuttmp0:
                    if k>naValue:
                        cuttmp.append(k)
                cuttmp.insert(1,naValue)

                if autoCombin:#
                    ivtrainRes=autoGrpCombine(inds=trainds,var=var,target=target,pct=None,groupcut=cuttmp,firstSegIsNa=True)
                    ivValidateRes=autoGrpCombine(inds=testds,var=var,target=target,pct=None,groupcut=ivtrainRes[1],firstSegIsNa=True)
                    ivtrainRes=IV_Compute_Single(inds=trainds,var=var,target=target,pct=None,groupcut=ivValidateRes[1])
                else:
                    ivtrainRes=IV_Compute_Single(inds=trainds, var=var, target=target, pct=None, groupcut=cuttmp)
                    ivValidateRes=IV_Compute_Single(inds=testds, var=var, target=target, pct=None, groupcut=cuttmp)
            else:
                if autoCombin:
                    ivtrainRes=autoGrpCombine(inds=trainds,var=var,target=target,pct=pct,groupcut=groupcut,firstSegIsNa=False)
                    ivValidateRes=autoGrpCombine(inds=testds,var=var,target=target,pct=None,groupcut=ivtrainRes[1],firstSegIsNa=False) 
                    ivtrainRes=IV_Compute_Single(inds=trainds,var=var,target=target,pct=None,groupcut=ivValidateRes[1])
                else:
                    ivtrainRes=IV_Compute_Single(inds=trainds, var=var, target=target, pct=pct, groupcut=groupcut)
                    ivValidateRes=IV_Compute_Single(inds=testds, var=var, target=target, pct=None, groupcut=ivtrainRes[1])
        else:
            if autoCombin:
                ivtrainRes=autoGrpCombine(inds=trainds,var=var,target=target,pct=pct,groupcut=groupcut,firstSegIsNa=False)
                ivValidateRes=autoGrpCombine(inds=testds,var=var,target=target,pct=None,groupcut=ivtrainRes[1],firstSegIsNa=False) 
                ivtrainRes=IV_Compute_Single(inds=trainds,var=var,target=target,pct=None,groupcut=ivValidateRes[1])
            else:#
                ivtrainRes=IV_Compute_Single(inds=trainds, var=var, target=target, pct=pct, groupcut=groupcut)
                ivValidateRes=IV_Compute_Single(inds=testds, var=var, target=target, pct=None, groupcut=ivtrainRes[1])
   
    ivres=pd.merge(ivtrainRes[0],ivValidateRes[0].drop(columns=["vname","vdtype"]),how="left",on="group")
       
    ivres['grp']=range(ivres.shape[0])
    ivres.rename(columns={'WOE_x':'WOE'}, inplace=True)#修改woe列名，为后面规则做准备 
   
    #对于数值型，group要从interval类型转为字符串
    if ivres.loc[0,"vdtype"]=="numeric":
        for i in range(ivres.shape[0]):
            ivres.loc[i,"groupC"]=str('[{}, {}]'.format(ivres.loc[i,"group"].left, ivres.loc[i,"group"].right))
    else:
        ivres.loc[:,"groupC"]=ivres.loc[:,"group"]
    ivres["WoeCorr"]=ivres[["WOE","WOE_y"]].corr().loc["WOE","WOE_y"]   

    #计算PSI
    diff = (ivres.loc[:, "p_01_y"] - ivres.loc[:, "p_01_x"])
    log = np.log((ivres.loc[:, "p_01_y"] )/(ivres.loc[:, "p_01_x"] ))
    ivres['psitmp'] = diff * log
    ivres["PSI"]=sum(ivres['psitmp'])
    ivres["label"]=labelds["label"][labelds["vname"]==var].values[0]

    if plotShow or plotSave:
	
        plt.figure(1,figsize=(10, 7))#创建图表1
        plt.figure(2,figsize=(10, 7))#创建图表2
        plt.figure(3,figsize=(10, 7))#创建图表2
        plt.figure(4,figsize=(10, 7))#创建图表2
        ax1=plt.subplot(221)#在图表2中创建子图1
        ax2=plt.subplot(222)#在图表2中创建子图2
        ax3=plt.subplot(223)#在图表2中创建子图2
        ax4=plt.subplot(224)#在图表2中创建子图2
        plt.suptitle(var+"\n"+labelds[labelds["vname"]==var]["label"].values[0])
        plt.sca(ax1)
        plt.title('Train(IV='+str(round(max(ivres["iv_x"]),2))+")")
        plt.bar(x=list(ivres["groupC"]),height=ivres["p_01_x"])
    
        plt.sca(ax2)
        plt.title('Validate(IV='+str(round(max(ivres["iv_y"]),2))+",PSI="+str(round(max(ivres["PSI"]),3))+")")
        plt.bar(x=ivres["groupC"],height=ivres["p_01_y"])
       
        plt.sca(ax3)
        plt.title('The badrate of train and validate')
        plt.plot(ivres["grp"], ivres["rate_x"], color='green', label='train',marker="o")
        plt.plot(ivres["grp"], ivres["rate_y"], color='red', label='validate',marker="o")
        plt.legend() # 显示图例
        plt.sca(ax4)
       
        plt.title('WOE(Corr='+str(round(max(ivres["WoeCorr"]),2))+")")
        plt.plot(ivres["grp"], ivres["WOE"], color='green', label='train',marker="o")
        plt.plot(ivres["grp"], ivres["WOE_y"], color='red', label='validate',marker="o")
        plt.legend() # 显示图例 
    
    
    if outpath !=None:
            #plt.close()
        if plotSave:
            plt.savefig(outpath+"\\"+var+".png",dpi=50)
        if plotShow:           
            plt.show()
            #plt.close()
        #生成规则
        IVtable2WoeRule(iv_table=ivres,outpath=outpath)#生成py和sas的WOE规则代码
        ivres.to_csv(outpath+"\\"+var+".csv",encoding="ansi")
    else:
        if plotShow:
            plt.show()
            #plt.close()
        else:
            pass
    if plotShow:
        print(ivtrainRes[0][["grp","group","count","p_01","n_1","rate"]])
        print(ivtrainRes[1])
    if plotShow or plotSave:
        plt.close()
    return ivres


def autoGrpCombine(inds=None,var="x1",target="gbie",pct=None,groupcut=None,firstSegIsNa=False):
#20190607 20190910
    ivtrainRes=IV_Compute_Single(inds=inds, var=var, target=target, pct=pct, groupcut=groupcut)
    
    ivres1=ivtrainRes[0].copy()
    cut=ivtrainRes[1].copy()
    NaFlag=0
    if firstSegIsNa:
        ivres1=ivres1.loc[range(1,ivres1.shape[0]),:]
        ivres1.index=range(ivres1.shape[0])
        NaFlag=1

    w=1
    c=1
    w=1
    while (w!=999) and (ivres1.shape[0]>2) :
   
        def f(x):
            x_pf=x*x
            return x_pf
        ivres1["grp_pf"]=ivres1["grp"].apply(f)    
     
        from sklearn.linear_model import LinearRegression
        lrModel = LinearRegression()
        lrModel.fit(ivres1[["grp","grp_pf"]],ivres1[["WOE"]])

        pred=lrModel.predict(ivres1[["grp","grp_pf"]])
      

        xl=[]
        for i in range(1,ivres1.shape[0]):
            tmp=ivres1["WOE"][i]-ivres1["WOE"][i-1]
            xl.append(tmp)
        
        
        xlpred=[]
        for i in range(1,ivres1.shape[0]):
            tmp=pred[i][0]-pred[i-1][0]
            xlpred.append(tmp)
        

        xl_z=np.array(xl)*np.array(xlpred)
        hebing=-1
        for i in range(0,len(xl_z)):
            if (xl_z[i]<=0) and (i <(len(xl_z)-1)):
                if abs(xl[i])<=abs(xl[i+1]):
                    hebing=i+1+NaFlag
                    w=1
                    break
                if abs(xl[i])>abs(xl[i+1]):
                    hebing=i+2+NaFlag
                    w=1
                    break
            elif (xl_z[i]<=0) and (i ==(len(xl_z)-1)):
                hebing=i+1+NaFlag
                w=1
                break
            else:
                w=999 
                

        if w!=999:        
            cut.pop(hebing)    
            ivtrainRes=IV_Compute_Single(inds=inds, var=var, target=target, pct=None, groupcut=cut)
            ivres1=ivtrainRes[0].copy()
            cut=ivtrainRes[1].copy()
                        
            if firstSegIsNa:
                ivres1=ivres1.loc[range(1,ivres1.shape[0]),:]
                ivres1.index=range(ivres1.shape[0])
                NaFlag=1

    return  ivtrainRes       
#res= autoGrpCombine(inds=trainds,var="TJXX_60d_reglasttime_nonbank",target="gbie",pct=None,groupcut=None,firstSegIsNa=False)



def IV_Compute_Total(inds, target, cal_vars=None, del_vars=None):
    # cal_var 和del_var 是 list或者单个字符变量

    if (cal_vars is None) and (del_vars is None):
        cal_vars = inds.columns.drop(target).tolist()
        # del_vars = []
    elif (cal_vars is None) and (del_vars == []):
        cal_vars = inds.columns.drop(target).tolist()
    elif (cal_vars is None):
        cal_vars = inds.columns.drop(del_vars).drop(target).tolist()
    else:
        cal_vars = [cal_vars] if isinstance(cal_vars, str) else cal_vars
    iv_values = []
    # woe_values = []
    table_base=pd.DataFrame()
    for var in cal_vars:
        table = IV_Compute_Single(inds, var, target)[0]
        iv_values.append(table['iv'][0])
        table['vname']=var
        table_base=pd.concat([table_base,table],axis=0)
        del table
    return pd.DataFrame({'vname': cal_vars, 'iv': iv_values},
                        index=inds.columns.get_indexer(cal_vars)),table_base


def SingleWoeRule2TotalWoeRule(inpath=None,outpath=None):
    #注意：inpath 和 outPath 不可相同，且最后一位无'\'
    #许冠明
    #20190622
    
    filePath=inpath
    fileList=pd.DataFrame(os.listdir(filePath))
    fileList=fileList.rename(columns={0:"filename"})
    def f(x):
        y=x.split('.')[1]
        return y
    def m(x):
        y="WOE_"+x.split('.')[0]
        return y
    fileList["filenameEnd"]=fileList["filename"].apply(f)
    fileList["valiables"]=fileList["filename"].apply(m)
    fileListValiables=fileList.loc[fileList["filenameEnd"]=="py","valiables"]
    fileListPy=fileList.loc[fileList["filenameEnd"]=="py","filename"]
    basePycode=[]
    for i in list(fileListPy):
        data = []
        for line in open(filePath +"\\"+i,"r"): #设置文件对象并读取每一行文件
            data.append(line)               #将每一行文件加入到list中
        basePycode.append(data)
    
    fileListSAS=fileList.loc[fileList["filenameEnd"]=="sas","filename"]
    baseSAScode=[]
    for i in list(fileListSAS):
        data = []
        for line in open(filePath +"\\"+i,"r"): #设置文件对象并读取每一行文件
            data.append(line)               #将每一行文件加入到list中
        baseSAScode.append(data)
        
  
    file = open(outpath+"\\"+"WoeRule"+".py",'w')  
    file.write("def WoeTransforms(ds=None,ID=None,target=None,dropVar=None):\n")
    file.write("\tinds=ds.copy()\n")
    file.write("\tIDs=ID.copy()\n")
    for i in basePycode:
        for j in i:
            file.write(j)  
    file.write("\tif target is not None:\n")
    file.write("\t\tIDs.append(target)\n")
    file.write("\t\tkeepvar=IDs\n")
    file.write("\telse:\n")
    file.write("\t\tkeepvar=IDs\n")
    file.write("\tfileListValiables="+str(list(fileListValiables))+"\n")
    file.write("\tkeepvar.extend(fileListValiables)\n")
    file.write("\tinds=inds[keepvar]\n")
    file.write("\t#inds=inds.drop(dropVar,axis=1)\n")
    file.write("\treturn inds\n")
    file.close()    
    
    file = open(outpath+"\\"+"WoeRule"+".sas",'w')  
    for i in baseSAScode:
        for j in i:
            file.write(j)  
    file.close()  


def VariableBinningInteractiveResult(inpath=None):
    #把分箱后的IV、PSI、corr等指标更新汇总
    #许冠明 20190802
    filePath=inpath
    fileList=pd.DataFrame(os.listdir(filePath))
    fileList=fileList.rename(columns={0:"filename"})
    def f(x):
        y=x.split('.')[1]
        return y
    fileList["filenameEnd"]=fileList["filename"].apply(f)
    
    fileListPy=fileList.loc[fileList["filenameEnd"]=="csv","filename"]
    basePycode=pd.DataFrame()
    for i in list(fileListPy):
        data = pd.read_csv(filePath+"\\"+i,engine='python',encoding='ansi')
        data=data.drop('Unnamed: 0',axis=1)
        basePycode=basePycode.append(data)
    #basePycode=pd.merge(basePycode,label,how='left',on=['vname'])    
    basePycodeTot=basePycode.drop_duplicates(
        subset=['vname'], # 去重列，按这些列进行去重
        keep='last' # 保存最后一条重复数据
        )
    basePycodeTot=basePycodeTot[['vname','grp','iv_x','iv_y','KS_x','KS_y','WoeCorr','PSI','label']] 
    basePycodeTot.index=range(basePycodeTot.shape[0])
    basePycode.index=range(basePycode.shape[0])
    for i in range(basePycode.shape[0]):
        basePycode.loc[i,'woe_vname']='WOE_'+basePycode.loc[i,'vname']
    for i in range(basePycodeTot.shape[0]):
        basePycodeTot.loc[i,'woe_vname']='WOE_'+basePycodeTot.loc[i,'vname']
    return  basePycode, basePycodeTot
    

def Data2WoeData(ds=None,ID=None,target=None,mypath=None):
    #xuguanming
    #20201224
    makeNewDir(mypath+"\\bins")
    makeNewDir(mypath+"\\rules")
    SingleWoeRule2TotalWoeRule(inpath=mypath+"\\bins",outpath=mypath+"\\rules")
    sys.path.append(mypath+"\\rules")
    import WoeRule as WoeRule    
    S4_WoeDataTrain=WoeRule.WoeTransforms(ds=ds,ID=ID,target=target)
    return S4_WoeDataTrain

def PSI_Compute_Single(trainds, testds, var, pct=None, groupcut=None, groupn=10,plotShow=False,
	label1="Train",label2="Validate",graphSaveFile=None):
    '''
    trainds=train_predprob1
    testds=test_predprob1
    var='score'
    pct=None
    groupcut=list(range(minscore,maxscore,scoreGroupcut))
    groupn=None
    graphSaveFile=r"C:\Xuguanming\原先的文件夹\python\tmp\tmp.png"
    '''
    for item in [pct, groupcut, groupn]:
        if isinstance(item, np.ndarray):
            item = item.tolist()
    if pct is not None:
        cut = pct
        freq_train = Var_Baifenwei(inds=trainds, var=var, pct=cut)
    elif groupcut is not None:
        if isinstance(groupcut, np.ndarray):
            groupcut = groupcut.tolist()
        groupcut.insert(0, float('-inf'))
        groupcut.insert(0, float('inf'))
        groupcut = np.unique(groupcut).tolist()
        cut = groupcut
        freq_train = Var_Groupcut(inds=trainds, var=var, groupcut=cut)
    else:

        cut = groupn
        freq_train = Var_Groupcut(inds=trainds, var=var, groupn=cut)
    Cut = freq_train[2]
    # if not isinstance(Cut, list):
    #     Cut = Cut.tolist()

    freq_train = freq_train[1][['GROUP', 'COUNT', 'RATE']]
    freq_test = Var_Groupcut(inds=testds, var=var, groupcut=Cut)[1][['GROUP', 'COUNT', 'RATE']]\
        .rename(columns={'COUNT': 'COUNT_test', 'RATE': 'RATE_test'})

    psi_table = pd.merge(freq_train, freq_test, on='GROUP').sort_index()
    # exclude_value = freq_train.iloc[-1, 0]
    # exclude_value_row = psi_table[psi_table['GROUP'] == exclude_value]
    # psi_table = psi_table[psi_table['GROUP'] != exclude_value]
    adj = pd.Series([0] * psi_table.shape[0])
    adj = adj.mask(psi_table['RATE'] == 0, 0.5)
    adj = adj.mask(psi_table['RATE_test'] == 0, 0.5)
    psi_table['adj'] = adj
    diff = (psi_table.iloc[:, 4] - psi_table.iloc[:, 2])
    log = np.log((psi_table.iloc[:, 4] + psi_table['adj'])/(psi_table.iloc[:, 2] + psi_table['adj']))
    psi_table['psitmp'] = diff * log
    psi_table['psi'] = [np.sum(psi_table['psitmp'])] * psi_table.shape[0]
    # exclude_value_row['psitmp'] = 0
    # exclude_value_row['psi'] = np.sum(psi_table['psitmp'])
    # psi_table = psi_table.append(exclude_value_row)
    
    tmp=psi_table.loc[psi_table["GROUP"]!='TOTAL',]
    plt.figure(figsize=(8,4))
    plt.title(label1+' Vs '+label2+' PSI='+str(round(min(tmp['psi']),3)))
    plt.plot(tmp["GROUP"].astype('str'), tmp["RATE"], color='green', label=label1,marker="o")
    plt.plot(tmp["GROUP"].astype('str'), tmp["RATE_test"], color='red', label=label2,marker="o")
    plt.xticks(rotation=90)
    plt.legend() # 显示图例
    if graphSaveFile is not None:
        plt.savefig(graphSaveFile, dpi=250,bbox_inches='tight')
    if plotShow:
        plt.show()
    plt.close()
    
    return psi_table

def PSI_Compute_Table(tab_train, tab_test):
    '''
    xuguanming 20240530
    '''  

    freq_train = tab_train[['GROUP', 'COUNT', 'RATE']]
    freq_test = tab_test[['GROUP', 'COUNT', 'RATE']]
    
    freq_test=freq_test.rename(columns={'COUNT': 'COUNT_test', 'RATE': 'RATE_test'})

    psi_table = pd.merge(freq_train, freq_test, on='GROUP').sort_index()
    # exclude_value = freq_train.iloc[-1, 0]
    # exclude_value_row = psi_table[psi_table['GROUP'] == exclude_value]
    # psi_table = psi_table[psi_table['GROUP'] != exclude_value]
    adj = pd.Series([0] * psi_table.shape[0])
    adj = adj.mask(psi_table['RATE'] == 0, 0.5)
    adj = adj.mask(psi_table['RATE_test'] == 0, 0.5)
    psi_table['adj'] = adj
    diff = (psi_table.iloc[:, 4] - psi_table.iloc[:, 2])
    log = np.log((psi_table.iloc[:, 4] + psi_table['adj'])/(psi_table.iloc[:, 2] + psi_table['adj']))
    psi_table['psitmp'] = diff * log
    psi_table['psi'] = [np.sum(psi_table['psitmp'])] * psi_table.shape[0]
    # exclude_value_row['psitmp'] = 0
    # exclude_value_row['psi'] = np.sum(psi_table['psitmp'])
    # psi_table = psi_table.append(exclude_value_row)
    
    tmp=psi_table.loc[psi_table["GROUP"]!='TOTAL',]
    psi_value=psi_table['psi'][0]
    return psi_table,psi_value


def PSI_Compute_Total(trainds, testds, cal_vars=None, del_vars=None):
    if (cal_vars is None) and (del_vars is None):
        cal_vars = trainds.columns.tolist()
        del_vars = []
    elif (cal_vars is None) and (del_vars == []):
        cal_vars = trainds.columns.tolist()
    elif cal_vars is None:
        cal_vars = trainds.columns.drop(del_vars).tolist()
    else:
        cal_vars = [cal_vars] if isinstance(cal_vars, str) else cal_vars
    psi_table_single = pd.DataFrame()
    psi_value = []
    for var in cal_vars:
        table = PSI_Compute_Single(trainds, testds, var)#.iloc[:-1,:]
        table.insert(table.shape[1], 'vname', [var]*table.shape[0])
        psi_value.append(table['psi'][0])
        psi_table_single = psi_table_single.append(table)
    return psi_table_single, pd.DataFrame({'vname': cal_vars, 'psi': psi_value},
                                          index=trainds.columns.get_indexer(cal_vars))

#KSres=KS(inds=score.copy(), target='gbie0', rankvar='Score_sys', pct=np.arange(.05, 1.05, 0.05), groupcut=None, groupn=None, descending=False, graph=False)

def KS(inds, target, rankvar, pct=np.arange(.05, 1.05, 0.05), groupcut=None, groupn=None, descending=False, graph=True,graphShow=False,graphSaveFile=None,title=""):
    # 许冠明 20180801
    def make_ks_table(function, data, target, rankvar, group, descending):
        #function=Var_Baifenwei
        #data=data
        #target=target
        #group=pct
        ks_table = function(data, rankvar, group)[0]
        groupby = ks_table.columns[-1]
        ks_table = ks_table.drop(rankvar, axis=1).groupby(groupby).agg(['sum', 'count'])
        ks_table.columns=['N_Bad','N_Total']    
        if descending is True:
            ks_table = ks_table.iloc[::-1]
            # ks_table = ks_table.sort_index(ascending=False)
        ks_table['N_Good'] = ks_table['N_Total'] - ks_table['N_Bad']
        ks_table = ks_table[['N_Good', 'N_Bad', 'N_Total']]
        # ks_table,insert(0, 'N_Good', ks_table['N_Total'] - ks_table['N_Bad'])
        ks_table[['C_Good', 'C_Bad', 'C_Total']] = np.cumsum(ks_table[['N_Good', 'N_Bad', 'N_Total']])
        ks_table['C_P_Good'] = (ks_table['C_Good'] / ks_table['C_Good'].tolist()[-1]) * 100
        ks_table['C_P_Bad'] = (ks_table['C_Bad'] / ks_table['C_Bad'].tolist()[-1]) * 100
        ks_table['C_P_Total'] = (ks_table['C_Total'] / ks_table['C_Total'].tolist()[-1]) * 100
        ks_table['CN_P_Bad'] = (ks_table['C_Bad'] / ks_table['C_Total']) * 100
        ks_table['KS'] = np.abs(ks_table['C_P_Good'] - ks_table['C_P_Bad'])
        ks_table['Lift'] = (ks_table['C_P_Bad'] / ks_table['C_P_Total'])
        return ks_table, groupby

    data = inds[[target, rankvar]]

    for item in [pct, groupcut, groupn]:
        if isinstance(item, np.ndarray):
            item = item.tolist()

    if (groupcut is None) and (groupn is None):

        ks_table, groupby = make_ks_table(Var_Baifenwei, data, target, rankvar, pct, descending)

    elif (groupcut is None) and (groupn is not None):

        percent = (np.arange(0, 100, groupn) + 100 / groupn) / 100
        ks_table, groupby = make_ks_table(Var_Baifenwei, data, target, rankvar, percent, descending)

    else:
        if isinstance(groupcut, np.ndarray):
            groupcut = groupcut.tolist()
        groupcut.insert(0, float('-inf'))
        groupcut.insert(0, float('inf'))
        groupcut = np.unique(groupcut).tolist()

        ks_table, groupby = make_ks_table(Var_Groupcut, data, target, rankvar, groupcut, descending)

    if graph is True:
        #import matplotlib.pyplot as plt
        plt.figure(figsize=(8,4))
        imax = 0
        for i, loc in enumerate(ks_table['KS']):
            if loc == max(ks_table['KS']):
                imax = (i + 1) * 100 / ks_table.shape[0]

        m = ks_table[ks_table['KS'] == max(ks_table['KS'])]

        x = (np.arange(ks_table.shape[0] + 1)) * 100 / ks_table.shape[0]
        y_good = ks_table['C_P_Good'].tolist()
        y_good.insert(0, 0)
        y_bad = ks_table['C_P_Bad'].tolist()
        y_bad.insert(0, 0)
        plt.plot(x, y_good, 'b.-',#blue
                 x, y_bad, 'r.-',#red
                 [imax] * len(np.linspace(0, 100)), np.linspace(0, 100), '--',
                 np.linspace(0, 100), [m['C_P_Good']] * len(np.linspace(0, 100)), 'b--',
                 np.linspace(0, 100), [m['C_P_Bad']] * len(np.linspace(0, 100)), 'r--')
        plt.legend(['Good', 'Bad'])
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        rotation = 90 if (groupby == 'GROUP' and ks_table.shape[0] >= 5) or groupcut is not None else 0
        plt.xticks((np.arange(0, ks_table.shape[0]) + 1) * 100 / ks_table.shape[0], ks_table.index, rotation=rotation)
        plt.grid()
        plt.title(title+' Kolmogorov-Smirnoff(max= '+  str(round(max(ks_table['KS']),2))+')' , fontsize=15)
        
        if graphSaveFile is not None:
            plt.savefig(graphSaveFile, dpi=250,bbox_inches='tight')
        if graphShow:
            plt.show()
        plt.close()

    return ks_table

#KS的另一个函数
def PlotKS(preds, labels, n, asc):

    # preds is score: asc=1
    # preds is prob: asc=0

    pred = preds  # 预测值
    bad = labels  # 取1为bad, 0为good
    ksds = pd.DataFrame({'bad': bad, 'pred': pred})
    ksds['good'] = 1 - ksds.bad

    if asc == 1:
        ksds1 = ksds.sort_values(by=['pred', 'bad'], ascending=[True, True])
    elif asc == 0:
        ksds1 = ksds.sort_values(by=['pred', 'bad'], ascending=[False, True])
    ksds1.index = range(len(ksds1.pred))
    ksds1['cumsum_good1'] = 1.0*ksds1.good.cumsum()/sum(ksds1.good)
    ksds1['cumsum_bad1'] = 1.0*ksds1.bad.cumsum()/sum(ksds1.bad)

    if asc == 1:
        ksds2 = ksds.sort_values(by=['pred', 'bad'], ascending=[True, False])
    elif asc == 0:
        ksds2 = ksds.sort_values(by=['pred', 'bad'], ascending=[False, False])
    ksds2.index = range(len(ksds2.pred))
    ksds2['cumsum_good2'] = 1.0*ksds2.good.cumsum()/sum(ksds2.good)
    ksds2['cumsum_bad2'] = 1.0*ksds2.bad.cumsum()/sum(ksds2.bad)

    # ksds1 ksds2 -> average
    ksds = ksds1[['cumsum_good1', 'cumsum_bad1']]
    ksds['cumsum_good2'] = ksds2['cumsum_good2']
    ksds['cumsum_bad2'] = ksds2['cumsum_bad2']
    ksds['cumsum_good'] = (ksds['cumsum_good1'] + ksds['cumsum_good2'])/2
    ksds['cumsum_bad'] = (ksds['cumsum_bad1'] + ksds['cumsum_bad2'])/2

    # ks
    ksds['ks'] = ksds['cumsum_bad'] - ksds['cumsum_good']
    ksds['tile0'] = range(1, len(ksds.ks) + 1)
    ksds['tile'] = 1.0*ksds['tile0']/len(ksds['tile0'])

    qe = list(np.arange(0, 1, 1.0/n))
    qe.append(1)
    qe = qe[1:]

    ks_index = pd.Series(ksds.index)
    ks_index = ks_index.quantile(q = qe)
    ks_index = np.ceil(ks_index).astype(int)
    ks_index = list(ks_index)

    ksds = ksds.loc[ks_index]
    ksds = ksds[['tile', 'cumsum_good', 'cumsum_bad', 'ks']]
    ksds0 = np.array([[0, 0, 0, 0]])
    ksds = np.concatenate([ksds0, ksds], axis=0)
    ksds = pd.DataFrame(ksds, columns=['tile', 'cumsum_good', 'cumsum_bad', 'ks'])

    ks_value = ksds.ks.max()
    ks_pop = ksds.tile[ksds.ks.astype(float).idxmax()]
    print ('ks_value is ' + str(np.round(ks_value, 4)) + ' at pop = ' + str(np.round(ks_pop, 4)))

    # chart
    plt.plot(ksds.tile, ksds.cumsum_good, label='cum_good',
                         color='blue', linestyle='-', linewidth=2)

    plt.plot(ksds.tile, ksds.cumsum_bad, label='cum_bad',
                        color='red', linestyle='-', linewidth=2)

    plt.plot(ksds.tile, ksds.ks, label='ks',
                   color='green', linestyle='-', linewidth=2)

    plt.axvline(ks_pop, color='gray', linestyle='--')
    plt.axhline(ks_value, color='green', linestyle='--')
    plt.axhline(ksds.loc[ksds.ks.astype(float).idxmax(), 'cumsum_good'], color='blue', linestyle='--')
    plt.axhline(ksds.loc[ksds.ks.astype(float).idxmax(),'cumsum_bad'], color='red', linestyle='--')
    plt.title('KS=%s ' %np.round(ks_value, 4) +  
                'at Pop=%s' %np.round(ks_pop, 4), fontsize=15)

    return ksds

#逐步回归
def LogitStepwiseSelection(X, y,
                       initial_list=[],
                       threshold_in=0.01,
                       threshold_out = 0.05,
                       verbose = True):
    """ Perform a forward-backward feature selection
    based on p-value from statsmodels.api.OLS
    Arguments:
        X - pandas.DataFrame with candidate features
        y - list-like with the target
        initial_list - list of features to start with (column names of X)
        threshold_in - include a feature if its p-value < threshold_in
        threshold_out - exclude a feature if its p-value > threshold_out
        verbose - whether to print the sequence of inclusions and exclusions
    Returns: list of selected features
    Always set threshold_in < threshold_out to avoid infinite looping.
    See https://en.wikipedia.org/wiki/Stepwise_regression for the details
    Also see https://blog.csdn.net/qwertyuiop5rghar/article/details/85000847
    y=Y
    """
    included = list(initial_list)
    #sk=1
    while True:
        #print("step="+str(sk))
        #print(included)
        changed=False
        # forward step
        excluded = list(set(X.columns)-set(included))
        new_pval = pd.Series(index=excluded)
        for new_column in excluded:
            model = sm.Logit(y, sm.add_constant(pd.DataFrame(X[included+[new_column]]))).fit()
            new_pval[new_column] = model.pvalues[new_column]
        best_pval = new_pval.min()
        #print("best_pval="+str(best_pval))
        #print(threshold_in)
        if best_pval < threshold_in:
            best_feature = new_pval.idxmin()
            included.append(best_feature)
            changed=True
            if verbose:
                print('Add  {:30} with p-value {:.6}'.format(best_feature, best_pval))
        #print("zheli???D")
        # backward step
        model = sm.Logit(y, sm.add_constant(pd.DataFrame(X[included])),disp=False).fit()
        # use all coefs except intercept
        pvalues = model.pvalues.iloc[1:]
        worst_pval = pvalues.max() # null if pvalues is empty
        if worst_pval > threshold_out:
            changed=True
            worst_feature = pvalues.idxmax()
            included.remove(worst_feature)
            if verbose:
                print('Drop {:30} with p-value {:.6}'.format(worst_feature, worst_pval))
        if not changed:
            break
        #sk=sk+1
    return model,included

def Modeling_old(X,y,label=None):
    #xuguanming
    #202012
    x=X.copy()
    x["intercept"] = 1.0
    #拟合参数
    S6_LogitFit = sm.Logit(y,x).fit()
    print(S6_LogitFit.summary())#模型统计参数
    
    S6_LogitResult=pd.DataFrame({'woe_vname': S6_LogitFit.params.index.tolist(), 
                                 'coef': S6_LogitFit.params.tolist(),
                                 'tvalues':S6_LogitFit.tvalues.tolist(),
                                 'tvaluesabs':np.abs(S6_LogitFit.tvalues.tolist()),
                                 'pvalues':S6_LogitFit.pvalues.tolist()                             
                                 },
                                 index=range(len(S6_LogitFit.params.index.tolist())))
    if label is not None:
        S6_LogitResult=pd.merge(S6_LogitResult,label,how="left",on='woe_vname').sort_values(by='tvaluesabs',ascending=False)
    #入选的WOE变量
    S6_LogitResultWoeVname=S6_LogitResult['woe_vname'][S6_LogitResult['woe_vname']!='intercept'].tolist()
    S6_LogitResultWoeVnameVif = [round(variance_inflation_factor(X[S6_LogitResultWoeVname].values, i),2) for i in range(X[S6_LogitResultWoeVname].shape[1])] # 方差膨胀因子
    S6_LogitResultWoeVnameVif=pd.DataFrame({'woe_vname':S6_LogitResultWoeVname,'VIF':S6_LogitResultWoeVnameVif})
    #入选变量匹配VIF值
    S6_LogitResult=pd.merge(S6_LogitResult,S6_LogitResultWoeVnameVif,how="left",on='woe_vname').sort_values(by='tvaluesabs',ascending=False)

    print("输出3个结果：[0]为逻辑回归拟合对象，[1]为入选变量及其参数情况，[2]为入选的woe变量列表")
    return S6_LogitFit,S6_LogitResult.drop('tvaluesabs',axis=1),S6_LogitResult['woe_vname'][S6_LogitResult['woe_vname']!='intercept']


def Modeling(ds=None,expvar=None,delvar=None,target=None,selection='stepwise',label=None,
                       threshold_in=0.01,
                       threshold_out = 0.05,
                       verbose = True):
    #xuguanming
    #202012 20210109
    '''
    ds=S4_WoeDataTrain.copy()
    validateds=S4_WoeDataValidate.copy()
    expvar=None
    delvar=IDTarget
    target=Target
    threshold_in=0.01
    threshold_out = 0.05
    verbose = True
    '''
    if expvar is not None:
        X=ds[expvar].copy()
    elif delvar is None:
        X=ds[list(set(ds.columns)-set([target]))].copy()
    else:
        X=ds[list(set(ds.columns)-set([target])-set(delvar))].copy()
    y=ds[target]
        
    if selection=='stepwise':
        S6_StepwiseLogitResult=LogitStepwiseSelection(X, y,
                       initial_list=[],
                       threshold_in=threshold_in,
                       threshold_out = threshold_out,
                       verbose = verbose)
        #print(S6_StepwiseLogitResult[0].summary())
        S6_LogitFit=S6_StepwiseLogitResult[0]
        print(S6_LogitFit.summary())
        
    elif selection==None:
        #x=X.copy()
        X["intercept"] = 1.0
        #拟合参数
        S6_LogitFit = sm.Logit(y,X).fit()
        print(S6_LogitFit.summary())#模型统计参数
        
    S6_LogitResult=pd.DataFrame({'woe_vname': S6_LogitFit.params.index.tolist(), 
                                     'coef': S6_LogitFit.params.tolist(),
                                     'tvalues':S6_LogitFit.tvalues.tolist(),
                                     'tvaluesabs':np.abs(S6_LogitFit.tvalues.tolist()),
                                     'pvalues':S6_LogitFit.pvalues.tolist()                             
                                     },
                                     index=range(len(S6_LogitFit.params.index.tolist())))
    S6_LogitResult.loc[S6_LogitResult['woe_vname']=='const','woe_vname']='intercept'
    if label is not None:
        label0=label.copy()
        def f(x):
            x_pf="WOE_"+x
            return x_pf
        label0["woe_vname"]=label0["vname"].apply(f)    
        S6_LogitResult=pd.merge(S6_LogitResult,label0,how="left",on='woe_vname').sort_values(by='tvaluesabs',ascending=False)
    #入选的WOE变量
    S6_LogitResultWoeVname=S6_LogitResult['woe_vname'][S6_LogitResult['woe_vname']!='intercept'].tolist()
    S6_LogitResultWoeVnameVif = [round(variance_inflation_factor(X[S6_LogitResultWoeVname].values, i),2) for i in range(X[S6_LogitResultWoeVname].shape[1])] # 方差膨胀因子
    S6_LogitResultWoeVnameVif=pd.DataFrame({'woe_vname':S6_LogitResultWoeVname,'VIF':S6_LogitResultWoeVnameVif})
    #入选变量匹配VIF值
    S6_LogitResult=pd.merge(S6_LogitResult,S6_LogitResultWoeVnameVif,how="left",on='woe_vname').sort_values(by='tvaluesabs',ascending=False)

    print("输出3个结果：[0]为逻辑回归拟合对象，[1]为入选变量及其参数情况，[2]为入选的woe变量列表")
    return S6_LogitFit,S6_LogitResult.drop('tvaluesabs',axis=1),S6_LogitResult['woe_vname'][S6_LogitResult['woe_vname']!='intercept']




def CorrelationAnalysis(ds=None,threshold=0.5,according=None):
    #xuguanming
    #20201219
    #according:包含两列，一列为woe变量名，一列为改变量对应的iv值
    '''
    ds=S5_WoeDataTrainOfX
    according=S4_BinRes[['woe_vname','iv_x']]
    '''
    according.columns=['woe_vname','iv_x']
    S5_corrX = ds.corr()  # 相关系数矩阵
    colnames = S5_corrX.columns
    S5_ColnamesDrop = list()  # 用于存储要剔除的变量名
    S5_ColnamesDropDetail=list()
    thred_corr = threshold # 相关系数阈值,即两个自变量相关系数大于0.5就只保留一个
    for i in range(S5_corrX.shape[0]):  # 删除相关系数大于0.5的变量
        #print("i====="+str(i))
        for j in range(i+1,S5_corrX.shape[1]):
            #print("j====="+str(j))
            #print(list(S5_corrX.index)[i]+list(S5_corrX.index)[j]+" rho:="+str(round(S5_corrX.iloc[i, j],2)))
            if (abs(S5_corrX.iloc[i, j]) >= thred_corr) and (i !=j):
                k1=according.loc[according['woe_vname']==list(S5_corrX.index)[i],'iv_x'].values[0]
                k2=according.loc[according['woe_vname']==list(S5_corrX.index)[j],'iv_x'].values[0]
                #print(list(S5_corrX.index)[i]+" K1="+str(round(k1,2)))
                #print(list(S5_corrX.index)[j]+" K2="+str(round(k2,2)))
                if k2>=k1:
                    # 保留IV较大的那一个
                    #print("剔除："+list(S5_corrX.index)[i])
                    S5_ColnamesDrop.append(list(S5_corrX.index)[i])
                    S5_ColnamesDropDetail.append("剔除原因：与 "+list(S5_corrX.index)[j]+" 相关性过大")
                    break
    S5_ColnamesKeep =list( colnames.drop(list(set(S5_ColnamesDrop)))  )
    S5_DropReason=pd.DataFrame({'ColnamesDrop':S5_ColnamesDrop,'DropReason':S5_ColnamesDropDetail})
    print(S5_DropReason)
    print('三个输出：[0]为相关系数矩阵，[1]为筛选后保留的变量列表，[2]为剔除掉的变量列表及其原因')
    return S5_corrX,S5_ColnamesKeep,S5_DropReason
def KMeansAnalysis(ds=None,n_clusters=8, random_state=10,according=None):
    #xuguanming
    #20201219
    #according:包含两列，一列为woe变量名，一列为改变量对应的iv值
    according.columns=['vname','woe_vname','iv_x']
    S5_2_WoeDataTrain_t=ds.T
    S5_kmeans = KMeans(n_clusters=n_clusters, random_state=random_state).fit(S5_2_WoeDataTrain_t)
    S5_clustersResult=pd.DataFrame({'woe_vname': list(S5_2_WoeDataTrain_t.index), 'clusters': S5_kmeans.labels_},
                                              index=range(len(S5_kmeans.labels_)))
    for i in range(S5_clustersResult.shape[0]):
        S5_clustersResult.loc[i,"vname"]=S5_clustersResult.loc[i,"woe_vname"][4:]
    S5_clustersResult=pd.merge(S5_clustersResult,according,how="left",on="vname")
    
    S5_clustersResult0=S5_clustersResult.sort_values(by=['clusters','iv_x'])
    S5_clustersResult=S5_clustersResult0.drop_duplicates(
        subset=['clusters'], # 去重列，按这些列进行去重
        keep='last' # 保存最后一条重复数据
        )
    S5_clustersResult=S5_clustersResult.drop(['woe_vname_y'], axis=1)
    S5_clustersResult=S5_clustersResult.rename(columns={'woe_vname_x':'woe_vname'})
    S5_clustersResult.index=range(S5_clustersResult.shape[0])
    return S5_clustersResult


def ScoreCard2Rules(ScoreCard=None,Base=500,PDO=20,outpath=None):
    #xuguanming
    #20201219 	20210109
    #iv_table_tmp=S7_Score.copy()
    #outpath=mypath+"\\rules"
    intercept_score=ScoreCard.loc[ScoreCard['vname']=='intercept','score'].values[0]
    iv_table_tmp=ScoreCard.loc[ScoreCard['vname']!='intercept',]
    iv_table_tmp.index=range(iv_table_tmp.shape[0])
    #iv_table_tmp['UP']=None
    #iv_table_tmp['LOW']=None
    #iv_table_tmp['RULE']=None
    
    #python格式规则代码
    file = open(outpath+"\\"+'ScoreCardRules'+".py",'w')
    file.write("def ScoreCardRules(ds=None):\n")
    file.write("#Base="+str(Base)+"\n")
    file.write("#PDO="+str(PDO)+"\n")
    file.write("\tinds=ds.copy()\n")
    #i=1
    for i in range(iv_table_tmp.shape[0]):
        #print(i)
        #print(iv_table_tmp['vdtype'][i])
        #print(str(iv_table_tmp['vname'][i]))
        var=str(iv_table_tmp['vname'][i])
        if (iv_table_tmp['vdtype'][i] !="character"):
            
            #iv_table_tmp.loc[i,"group"].left
            if str(iv_table_tmp.loc[i,"group"].split(',')[0].replace('(',''))=='-inf':
                iv_table_tmp.loc[i,'RULE']="\tinds.loc[inds['"+var+"']<="+str(iv_table_tmp.loc[i,"group"].split(',')[1].replace(']',''))+",'SCR_"+var+"']="+str(iv_table_tmp.loc[i,"score"])
            elif str(iv_table_tmp.loc[i,"group"].split(',')[1].replace(']',''))==' inf':
                iv_table_tmp.loc[i,'RULE']="\tinds.loc[inds['"+var+"']>"+str(iv_table_tmp.loc[i,"group"].split(',')[0].replace('(',''))+",'SCR_"+var+"']="+str(iv_table_tmp.loc[i,"score"])
            else:
                 iv_table_tmp.loc[i,'RULE']="\tinds.loc[ (inds['"+var+"']>"+str(iv_table_tmp.loc[i,"group"].split(',')[0].replace('(',''))+") & (inds['"+var+"']<="+str(iv_table_tmp.loc[i,"group"].split(',')[1].replace(']',''))+"),'SCR_"+var+"']="+str(iv_table_tmp.loc[i,"score"])
            file.write(iv_table_tmp.loc[i,'RULE'])
            file.write("\n")
        else:
            s=iv_table_tmp.loc[i,"group"].split(",")
            file.write("\n\tinds.loc[")
            for j in range(len(s)):
                file.write("\n\t\t("+"inds['"+var+"']=='"+s[j]+"')")
                if j<(len(s)-1):
                    file.write("\n\t\t| ")
                elif j==(len(s)-1):
                    file.write("\n\t\t,'SCR_"+var+"']="+str(iv_table_tmp.loc[i,"score"])+"\n")
    varlist=list(set(iv_table_tmp['vname']))
    varlist_scr=[]
    scoresumL=''
    for i in varlist:
        varlist_scr.append("SCR_"+i)
        scoresum="inds['SCR_"+i+"']"
        if scoresumL =='':
            scoresumL=scoresum
        else:
            scoresumL=scoresumL+"+"+scoresum
    scoresumL="inds['Score_sys'] = "+scoresumL+"+"+str(intercept_score)
    file.write("\tinds['Intercept_Score']="+str(intercept_score)+"\n")
    file.write("\t"+scoresumL+'\n')
    file.write("\tinds.loc[(inds['Score_sys']<100),'Score_sys']=100\n")
    file.write("\tinds.loc[(inds['Score_sys']>999),'Score_sys']=999\n")
    #file.write("    #评分需要向下取整\n")
    file.write("\tinds['Score_sys'] = inds['Score_sys'].astype(int)\n")
    file.write("\tinds['Score_sys_Prob']=1/(pow(2,((inds['Score_sys']-"+ str(Base) +")/"+ str(PDO) +"))+1)\n")
    #varlist.extend(varlist_scr)
    varlist_scr.extend(['Intercept_Score','Score_sys','Score_sys_Prob'])
    #file.write("\treturn inds["+str(varlist_scr)+"]")
    file.write("\treturn inds")
    file.close()
    
    #SAS格式规则代码
    file = open(outpath+"\\"+'ScoreCardRules'+".sas",'w')
    file.write("/*Base="+str(Base)+"*/\n")
    file.write("/*PDO="+str(PDO)+"*/\n")
    
    file.write('SCR_Intercept = '+ str(intercept_score)+";\n")

    for i in range(iv_table_tmp.shape[0]):
        #print(i)
        #print(iv_table_tmp['vdtype'][i])
        #print(str(iv_table_tmp['vname'][i]))
        var=str(iv_table_tmp['vname'][i])
        if (iv_table_tmp['vdtype'][i] !="character"):
            #iv_table_tmp.loc[i,"group"].left
            if str(iv_table_tmp.loc[i,"group"].split(',')[0].replace('(',''))=='-inf':
                iv_table_tmp.loc[i,'RULESAS']="IF "+var+" <="+str(iv_table_tmp.loc[i,"group"].split(',')[1].replace(']',''))+" THEN "+"SCR_"+var+" = "+str(iv_table_tmp.loc[i,"score"])+";"
            elif str(iv_table_tmp.loc[i,"group"].split(',')[1].replace(']',''))==' inf':
                iv_table_tmp.loc[i,'RULESAS']="ELSE IF "+var+" > "+str(iv_table_tmp.loc[i,"group"].split(',')[0].replace('(',''))+" THEN "+"SCR_"+var+" = "+str(iv_table_tmp.loc[i,"score"])+";"
            else:
                iv_table_tmp.loc[i,'RULESAS']="ELSE IF "+var+" <="+str(iv_table_tmp.loc[i,"group"].split(',')[1].replace(']',''))+" THEN "+"SCR_"+var+" = "+str(iv_table_tmp.loc[i,"score"])+";"

            file.write(iv_table_tmp.loc[i,'RULESAS'])
            file.write("\n")
        else:
            s="('"+iv_table_tmp.loc[i,"group"].replace(",","','")+"')"
            if iv_table_tmp.loc[i,"grp"]==0:
                file.write("IF "+ var + " in "+ s +" THEN " + "SCR_"+var+" = "+ str(iv_table_tmp.loc[i,"score"])+";\n")
            else:
                file.write("ELSE IF "+ var + " in "+ s +" THEN " + "SCR_"+var+" = "+ str(iv_table_tmp.loc[i,"score"])+";\n")
    varlist=list(set(iv_table_tmp['vname']))
    varlist_scr=[]
    scoresumL=''
    for i in varlist:
        varlist_scr.append("SCR_"+i)
        scoresum="SCR_"+i+""
        if scoresumL =='':
            scoresumL=scoresum
        else:
            scoresumL=scoresumL+"+"+scoresum
    scoresumL="Score_sys = "+scoresumL+"+"+"SCR_Intercept"

    file.write(scoresumL+"\n")
    file.write("IF Score_sys <100 THEN Score_sys=100\n")
    file.write("IF Score_sys >999 THEN Score_sys=999\n")
    #file.write("    #评分需要向下取整\n")
    file.write("Score_sys=int(Score_sys)\n")
    file.write("Score_sys_Prob=1/((2**(( Score_sys -"+ str(Base)+")/"+str(PDO)+"))+1;\n")
    file.close()    

def ScoreCard(LogitResult=None,BinResult=None,Base=600,PDO=20,Odds=1/60,RulesPath=None):
	#许冠明 20210109
    '''
    LogitResult=S6_LogitResult[1]
    BinResult=S4_BinResDetail
    RulesPath=mypath+"\\rules"
    Odds=1/60
    Base=600
    PDO=20
    '''
    B=PDO/np.log(2)
    A=Base+B*np.log(Odds)
    #print(A)
    #print(B)
    
    S7_BinResCoef=pd.merge(BinResult[['woe_vname','vname','label','group','vdtype','grp','WOE']],
                           LogitResult[['woe_vname','coef','tvalues']],how='right',on='woe_vname')
    S7_BinResCoef['tvaluesabs']=np.abs(S7_BinResCoef['tvalues'])
    S7_BinResCoef=S7_BinResCoef.sort_values(by=['tvaluesabs','vname','grp'],ascending=[False,True,True])
    S7_BinResCoef.index=range(S7_BinResCoef.shape[0])
    S7_BinResCoef.loc[S7_BinResCoef['vname'].isnull(),'vname']='intercept'
    S7_BinResCoef['score']=0
    for i in range(S7_BinResCoef.shape[0]):
        if S7_BinResCoef.loc[i,'vname'] != 'intercept':
            S7_BinResCoef.loc[i,'score']=-1*B*S7_BinResCoef.loc[i,'coef'] * S7_BinResCoef.loc[i,'WOE'] 
        else:
            S7_BinResCoef.loc[i,'score']= A-B*S7_BinResCoef.loc[i,'coef']
    
    #生成评分规则表
    S7_Score=S7_BinResCoef[['vname','label','group','vdtype','grp','score']]
    #生产规则代码
    ScoreCard2Rules(ScoreCard=S7_Score,Base=Base,PDO=PDO,outpath=RulesPath)
    print("规则代码已保存在:"+RulesPath)
    return S7_Score

def makeNewDir(path):
    # 引入模块
    # 去除首位空格
    path=path.strip()
    # 去除尾部 \ 符号
    path=path.rstrip("\\")
    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists=os.path.exists(path)
     # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)  
        print(path+' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        #print(path+' 目录已存在')
        return False
    
    
def Score(ds=None,RulesPath=None):
	#许冠明 20210109
    #基于评分规则表生成跑分代码
    #RulesPath=mypath+"\\rules"
    sys.path.append(RulesPath)
    import ScoreCardRules as ScoreCardRules    
    S7_train_score=ScoreCardRules.ScoreCardRules(ds=ds)
    return S7_train_score

