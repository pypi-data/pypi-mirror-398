#-*- coding: utf-8 -*-
#===========数据分析函数============
#数据分析、统计、报表等相关功能
#许冠明
#20221217
#=======================================

import pandas as pd
import calendar
import datetime
def is_float(num):
    """
    判断用户输入的是否为小数或整数
    :param num: str
    :return: bool
    """
    if (num.startswith("-") and num[1:].isdigit()) or num.isdigit():
        return True
    elif num.count(".") == 1 and not num.startswith(".") and not num.endswith("."):
        li = num.split(".")
        if li[0].startswith("-"):
            if li[0][1:].isdigit() and li[1].isdigit():
                return True
            else:
                return False
        else:
            if li[0].isdigit() and li[1].isdigit():
                return True
            else:
                return False
    else:
        return False

def dataCompare(baseData,compareData,IDcol,baseTag='base',compareTag='compare',isDetail=True):
    # 许冠明 20210801
    '''
    baseData=old
    compareData=new
    IDcol=['PROJ_ID']
    baseTag='old'
    compareTag='new'
    isDetail=True
    '''
    base=baseData.copy()
    compare=compareData.copy()
    IDcol=IDcol.copy()
    tag1=baseTag
    tag2=compareTag
    columnsTotal=list(base.columns)
    columnsCompare=columnsTotal.copy()
    for i in IDcol:
        columnsCompare.remove(i)
    
    compareC=list(compare.columns)#对比数据的列名
    
    base['_ID']=base[IDcol[0]]
    compare['_ID']=compare[IDcol[0]]
    if len(IDcol)>1:
        
        for i in range(1,len(IDcol)):
            base['_ID']=base['_ID']+' '+base[IDcol[i]]
            compare['_ID']=compare['_ID']+' '+compare[IDcol[i]]

    baseCompareResult=pd.DataFrame(columns=columnsTotal) 
    baseCompareResult['_ID']=base['_ID']
    
    k=0
    for j0 in range(len(columnsCompare)):#j0=1
        print(str(j0)+"/"+str(len(columnsCompare)-1))
        j=columnsCompare[j0]
        if j in compareC:#j=
            
            
            base1=base[['_ID',j]]
            base1.columns=['_ID','b_var']
            base1['flagb']=1
            compare1=compare[['_ID',j]]
            compare1.columns=['_ID','c_var']
            compare1['flagc']=1
            
            # 添加一个辅助列保存 base1 的原始顺序
            base1 = base1.reset_index().rename(columns={'index': 'original_order'})
            
            ress1=pd.merge(base1,compare1,how='left',on='_ID', sort=False)
            # 按照原始顺序排序
            ress1 = ress1.sort_values(by='original_order').drop(columns=['original_order']).reset_index(drop=True)
            
            if k==0:
                baseCompareResult.loc[ress1['flagc'] !=1 ,'是否有此ID']='不一致！：'+compareTag+'无此ID'
                baseCompareResult.loc[ress1['flagc'] ==1 ,'是否有此ID']=baseTag+'和'+compareTag+'都有此ID'

            if isDetail:#如果需要详细
                if base[j].dtypes=='O' or compare[j].dtypes=='O' :#其中之一是字符型
                    baseCompareResult[j]=ress1.apply(lambda x: "不一致！"+baseTag+":" + str(x['b_var'])+","+compareTag+":"+str(x['c_var']) if (str(x['b_var']) != str(x['c_var'])) else '一致',axis=1)
                else:
                    baseCompareResult[j]=ress1.apply(lambda x: "不一致！"+baseTag+":" + str(x['b_var'])+","+compareTag+":"+str(x['c_var']) if (abs(x['b_var']-x['c_var'])>0.2) else '一致',axis=1)
            else:
                if base[j].dtypes=='O' or compare[j].dtypes=='O' :#其中之一是字符型
                    baseCompareResult[j]=ress1.apply(lambda x: "不一致！" if (str(x['b_var']) != str(x['c_var'])) else '一致',axis=1)
                else:
                    baseCompareResult[j]=ress1.apply(lambda x: "不一致！" if (abs(x['b_var']-x['c_var'])>0.2) else '一致',axis=1)
 
            
            baseCompareResult.loc[ress1['flagc'] !=1 ,j]=None
            
        else:
                #baseCompareResult[j]='Compare没有此列'  
                print('没有此列')
                print(j+'('+compareTag+'没有此列)')
                baseCompareResult[j]=base[j]
                baseCompareResult=baseCompareResult.rename(columns={j:j+'('+compareTag+'没有此列)'})
                #baseCompareResult.loc[pd.isnull(baseCompareResult[j]),j]=''
        for m in IDcol:
            baseCompareResult[m]=base[m]
        k=k+1
        
    #对于在compare数据中，但是不在base中的数据，在id列展示出来
    inCompareNotinBase= pd.DataFrame({'_ID':list(set(compare['_ID']).difference(set(base['_ID']))),'是否有此ID':baseTag+'没有此ID，但'+compareTag+'有此ID'})
    print(1111)
    #baseCompareResult=baseCompareResult.append(inCompareNotinBase)
    baseCompareResult=pd.concat([baseCompareResult, inCompareNotinBase], ignore_index=True)
    print(2222)
  
    return baseCompareResult  

    """
    print('start')
    res=dataCompare(baseData=baseData,compareData=compareData,IDcol=['old_sys_seq'],baseTag='old',compareTag='new')
    print('done!')
    """  


def calenderHandle(start_date='2006-01-01',end_date='2023-07-31',outtype='-'):
    #输出startdate和enddate之间的所有日期
    #20230501 20240125
    mindate=int(start_date.replace('-', ''))
    maxdate=int(end_date.replace('-', ''))
    minyear=int(start_date[:4])
    maxyear=int(end_date[:4])
    minyearmonth=int(start_date[:7].replace('-', ''))
    maxyearmonth=int(end_date[:7].replace('-', ''))
    
    #print(minyearmonth)
    #print(maxyearmonth)
    #y=2023
    #m=10
    
    yearmonthlist=[]
    yearmonthstartlist=[]
    yearmonthendlist=[]
    yearlist=[]
    yearmonthdaylist=[]
    for y in list(range(minyear,maxyear+1)):
        yearlist.append(y)
        for m in list(range(1,12+1)):
            
            ym=y*100+m
            #print(ym)
            if ym> maxyearmonth:
                #print(1)
                pass
            elif ym < minyearmonth:
                #print(2)
                pass
            else:
                #print(3)
                #print(ym)
                ym_char=str(ym)[:4]+"-"+str(ym)[4:6]
                
                ym_start = ym_char + '-01'
                obj_date=datetime.datetime.strptime(ym_start,'%Y-%m-%d')
                last_day = calendar.monthrange(obj_date.year,obj_date.month)
                ym_end = str(datetime.datetime(obj_date.year,obj_date.month,last_day[1]))[0:10]
                
                if outtype=='-':
                    yearmonthlist.append(ym_char)
                    yearmonthstartlist.append(ym_start)
                    yearmonthendlist.append(ym_end)
                else:
                    yearmonthlist.append(ym)
                    yearmonthstartlist.append(int(ym_start.replace('-','')))
                    yearmonthendlist.append(int(ym_end.replace('-','')))
                for d in list(range(1,calendar.monthrange(y, m)[1]+1)):
                    ymd=ym*100+d
                    if ymd>maxdate:
                        #print(4)
                        pass
                    elif ymd<mindate:
                        #print(5)
                        pass
                    else:
                        ymd_cha=ym_char+'-'+str(ymd)[6:9]
                        if outtype=='-':
                            yearmonthdaylist.append(ymd_cha)
                        else:
                            yearmonthdaylist.append(ymd)
                        
                
    return   yearlist,yearmonthlist,yearmonthstartlist,yearmonthendlist, yearmonthdaylist     
    

#dd=calenderHandle(start_date='2006-01-01',end_date='2023-07-31')
def num2date(num=20230101):
    #num可以是数字，也可以是字符
    #
    numc=str(num)
    res=numc[:4]+"-"+numc[4:6]+'-'+numc[6:8]
    return res

def date2num(date='2023-01-01'):
    #num可以是数字，也可以是字符
    res=date.replace('-', '')
    return res  

def get_date_of_previous_month(date='2023-01-15',m=6):
    # 获取指定日期的前几个月
    date_sp=date.split('-')
    date=datetime.date(int(date_sp[0]), int(date_sp[1]), int(date_sp[2]))
    previous_month = pd.to_datetime(date) - pd.DateOffset(months=m)
    return previous_month.strftime("%Y-%m-%d")

