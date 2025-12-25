# -*- coding: utf-8 -*-
#===========机器学习建模函数============
#机器学习，自动生产excel模型文档
#许冠明
#20200101
#=======================================
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
from xgboost import XGBClassifier
import openpyxl
import os
import xlsxwriter
import joblib

import riskscore.creditscore as cs

def mechineLearning(train=None,validate=None,
                            test=None,
                            IDcol=None,
                            predictVar=None,
                            target=None,
                            labelds=None,
                              max_depth=2,
                              n_estimators=20, 
                              learning_rate=0.1, 
                              subsample=0.5,
                              colsample_bytree=0.5,
                              #objective= 'binary:logistic', 
                              min_child_weight=None,
                              #eval_metric='auc',
                              seed=999,
                              reg_alpha=0,
                              reg_lambda=1,
                              lmd=1,
                              PDO=45,
                              Base=500,
                              modelFile="XgboostModel",
                              outpath="C:",
                              scoreGroupcut=10,
                              tag="",
                              outXlsxNew=True,
                              gbieCount=None,#样本整体数据分布，可为None
                              IVCount=None,#IV值，可为None
                              IVCountDetail=None,#IV详细，可为NOne
                              IVpicpath=None):
    '''
    outXlsxNew:生产一个新的excel结果文档，而不是在原有文档上添加
    predictVar=["AGE","pay_1"]
    
    train=trainds
    validate=validateds
    test=testds
    IDcol=delcols
    predictVar=None
    target=target
    labelds=inputLabel
    max_depth=max_depth
    n_estimators=n_estimators 
    learning_rate=learning_rate
    subsample=subsample
    colsample_bytree=colsample_bytree
    #objective= 'binary:logistic'
    min_child_weight=min_child_weight
    #eval_metric='auc'
    seed=seed
    reg_alpha=reg_alpha
    reg_lambda=reg_lambda
    lmd=1
    PDO=20
    Base=500
    modelFile="XGBOOST_MODEL"
    outpath=appFilesPath+"\\"+runRequest[0][0]+"\\output\\"+target+"\\附件3：机器学习模型文档"+"\\"+target+"_"+productClassV+"_"+varClassV
    scoreGroupcut=10
    tag=target+"_"+productClassV+"_"+varClassV+"_"
    outXlsxNew=False
    gbieCount=Tot_gbie_count.copy()#样本整体数据分布，可为None
    IVCount=S4_BinRes.copy()#IV值，可为None
    IVCountDetail=S4_BinResDetail.copy()#IV详细，可为NOne
    IVpicpath=tmpfsave
    
    '''
    if validate is None:
        validate=train
    if test is None:
        test=validate
    
    if labelds is not None:
        labelds0=labelds.copy()
        labelds0=labelds0.iloc[:,[0,1]]
        labelds0.columns=["vname","label"]
        pass
    else:
        labelds0=pd.DataFrame({"vname":list(train.columns),"label":list(train.columns)})

    if IDcol is None:
        IDcol=[]
    if predictVar is None:
        delcol=IDcol.copy()
        delcol.append(target)
    
        
        train_data=train.drop(columns=delcol)
            #要把字符型的变量先删掉
        cldtype=train_data.dtypes
        cl=list(train_data.columns)
        cldf=pd.DataFrame({"vname":cl,'dtyp':list(cldtype)})
        clObj=list(cldf.loc[cldf['dtyp']=='object','vname'])
        
        #delcol=delcol+clObj
        train_data=train_data.drop(columns=clObj)
    else:
        train_data=train[predictVar]
            #要把字符型的变量先删掉
        cldtype=train_data.dtypes
        cl=list(train_data.columns)
        cldf=pd.DataFrame({"vname":cl,'dtyp':list(cldtype)})
        clObj=list(cldf.loc[cldf['dtyp']=='object','vname'])
        
        #delcol=delcol+clObj
        train_data=train_data.drop(columns=clObj)
    
    predictors = [x for x in train_data.columns ]
    
    predictorsOut0=pd.DataFrame({"vname":predictors})
    predictorsOut=pd.merge(predictorsOut0,labelds0,on='vname',how='left')
    #predictors = ["AGE" ]
    
    
    #看下目标的分布情况
    gbieTrain=pd.value_counts(train[target])
    gbieTest=pd.value_counts(validate[target])
    print("训练集好坏分布：")
    print(gbieTrain)
    print(gbieTrain/sum(gbieTrain))
    print("验证集好坏分布：")
    print(gbieTest)
    print(gbieTest/sum(gbieTest))
    
    
    
    x_train=train[predictors]#训练集的预测变量
    y_train=train[target]#训练集的目标
    x_test=validate[predictors]#验证集的预测变量
    y_test=validate[target]#验证集的目标
    if min_child_weight==None:
        min_child_weight=round(max(gbieTrain/min(gbieTrain)),0)
    
    xgbclassifier = XGBClassifier(max_depth=max_depth,
                                  n_estimators=n_estimators, 
                                  learning_rate=learning_rate, 
                                  subsample=subsample,
                                  colsample_bytree=colsample_bytree,
                                  objective= 'binary:logistic', 
                                  min_child_weight=min_child_weight,
                                  eval_metric='auc',
                                  seed=seed,
                                  reg_alpha=reg_alpha, 
                                  reg_lambda=reg_lambda)
    
    
    #把auc数据保存到一个文件中
    savedStdout = sys.stdout  #保存标准输出流
    with open(outpath+"\\evaluation_log.txt", 'wt') as file:
        sys.stdout = file  #标准输出重定向至文件
        xgbclassifier.fit(x_train, y_train, eval_set=[(x_train, y_train), (x_test, y_test)], early_stopping_rounds=10)
    sys.stdout = savedStdout  #恢复标准输出流
    evaluation_log=pd.read_csv(outpath+"\\evaluation_log.txt",delimiter="\t",header=None,engine='python')
    
    if os.path.exists(outpath+"\\evaluation_log.txt"):
        os.remove(outpath+"\\evaluation_log.txt")  
        
    for i in range(evaluation_log.shape[0]):
        evaluation_log.loc[i,"del"]=0
        if evaluation_log.loc[i,0].find("[")<0 :
            evaluation_log.loc[i,"del"]=1
        elif i>0:
            if evaluation_log.loc[i-1,0].find("Stopping.")>=0 :
                evaluation_log.loc[i,"del"]=2
        else:
            pass
    evaluation_log1=evaluation_log[evaluation_log['del'] < 1 ]
    evaluation_log1.index=range(evaluation_log1.shape[0])
    evaluation_log2=evaluation_log1.copy()
    for i in range(evaluation_log1.shape[0]):
        evaluation_log2.loc[i,"train_auc"]=float(evaluation_log1.iloc[i,1].split(":")[1])
        evaluation_log2.loc[i,"eval_auc"]=float(evaluation_log1.iloc[i,2].split(":")[1])
    #画图，对比训练和验证plt.figure(figsize=(10,5))
    fig  = plt.figure(figsize=(8,4))
    ax = fig.add_subplot(1,1,1)
    ax.plot(evaluation_log2['train_auc'])
    ax.plot(evaluation_log2['eval_auc'])
    ax.set_title("auc of train vs eval")
    ax.set_xlabel("num_round")
    ax.set_ylabel("auc")
    ax.legend(('train', 'eval')) 
    ax.grid(True)
    plt.savefig(outpath+"\\"+tag+"迭代表现.png", dpi=150)
    #plt.show()
    plt.close()
    if evaluation_log[evaluation_log['del'] ==2].shape[0]>0: 
        print("Stopping. Best iteration:"+ \
              list(evaluation_log[0][evaluation_log['del'] ==2])[0]+" "+\
              list(evaluation_log[1][evaluation_log['del'] ==2])[0]+" "+\
              list(evaluation_log[2][evaluation_log['del'] ==2])[0])
    
    
    
    
    feat_imp = pd.Series(xgbclassifier.get_booster().get_fscore()).sort_values(ascending=False)
    feat_imp.plot(kind='bar', title='Feature Importances',figsize=(16,5))
    plt.ylabel('Feature Importance Score')
    #plt.show()
    plt.close()
    feat_imp1=pd.DataFrame({"vname":list(feat_imp.index),"FeatureImportance":feat_imp})
    feat_imp1=pd.merge(feat_imp1,labelds0[["vname","label"]],on='vname',how='left')
    #准确性
    #y_pred = xgbclassifier.predict(x_test)
    #print("准确率：")
    #print(accuracy_score(y_pred, y_test))
    #1/((1/I230-1)*K$228+1)
    #
    
    
    
    train_predprob = xgbclassifier.predict_proba(train[predictors])[:,1]
    train_predprob_aln=1/((1/train_predprob-1)*lmd+1)
    train_predprob1=pd.DataFrame({"prob":train_predprob,"prob_aln":train_predprob_aln,"target":train[target]})
    train_predprob1['score'] = (np.log((1-train_predprob1['prob_aln'])/train_predprob1['prob_aln'])*PDO/np.log(2) + Base).astype(int);
    train_predprob1['flag']="1_Train"
    test_predprob = xgbclassifier.predict_proba(validate[predictors])[:,1]
    test_predprob_aln=1/((1/test_predprob-1)*lmd+1)
    test_predprob1=pd.DataFrame({"prob":test_predprob,"prob_aln":test_predprob_aln,"target":validate[target]})
    test_predprob1['score'] = (np.log((1-test_predprob1['prob_aln'])/test_predprob1['prob_aln'])*PDO/np.log(2) + Base).astype(int);
    test_predprob1['flag']="2_Validate"
#测试集
    testt_predprob = xgbclassifier.predict_proba(test[predictors])[:,1]
    testt_predprob_aln=1/((1/testt_predprob-1)*lmd+1)
    testt_predprob1=pd.DataFrame({"prob":testt_predprob,"prob_aln":testt_predprob_aln,"target":test[target]})
    testt_predprob1['score'] = (np.log((1-testt_predprob1['prob_aln'])/testt_predprob1['prob_aln'])*PDO/np.log(2) + Base).astype(int);
  
    total_predprob1=pd.concat([train_predprob1,test_predprob1],axis=0)
    
    
    
    trainKsres=cs.KS(inds=train_predprob1, target="target", rankvar='score', pct=np.arange(.05, 1.05, 0.05), 
                  groupcut=None, groupn=None, descending=False, graph=True,title="Train",
                  graphSaveFile=outpath+"\\"+tag+"训练KS.png")
    testKsres=cs.KS(inds=test_predprob1, target="target", rankvar='score', pct=np.arange(.05, 1.05, 0.05), 
                 groupcut=None, groupn=None, descending=False, graph=True,title="validate",
                  graphSaveFile=outpath+"\\"+tag+"验证KS.png")
    totalKsres=cs.KS(inds=total_predprob1, target="target", rankvar='score', pct=np.arange(.05, 1.05, 0.05),
                  groupcut=None, groupn=None, descending=False, graph=True,title="Total",
                  graphSaveFile=outpath+"\\"+tag+"整体KS.png")
    
    testtKsres=cs.KS(inds=testt_predprob1, target="target", rankvar='score', pct=np.arange(.05, 1.05, 0.05), 
                 groupcut=None, groupn=None, descending=False, graph=True,title="Test",
                  graphSaveFile=outpath+"\\"+tag+"测试KS.png")

    trainKsres["flag"]="1_Train"
    testKsres["flag"]="2_Validate"
    totalKsres["flag"]="3_Total"
    testtKsres["flag"]="4_Test"
    trainKsres["group"]=trainKsres.index
    testKsres["group"]=testKsres.index
    totalKsres["group"]=totalKsres.index
    testtKsres["group"]=testtKsres.index
    trainKsres.index=range(trainKsres.shape[0])
    testKsres.index=range(testKsres.shape[0])
    totalKsres.index=range(totalKsres.shape[0])
    testtKsres.index=range(testtKsres.shape[0])
    KSresult = pd.concat([trainKsres,testKsres,totalKsres,testtKsres])
    #KSresult.index=list(range(KSresult.shape[0]))
    KSresult['group_c']=KSresult.group.astype('str')
    KSresult=KSresult.drop(columns=['group'])
    
    minscore=min(min(total_predprob1['score']),min(testt_predprob1['score']))
    maxscore=max(max(total_predprob1['score']),max(testt_predprob1['score']))
    #按分段
    trainKsresCut=cs.KS(inds=train_predprob1, target="target", rankvar='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None, descending=False, graph=True,title="Train"
                     ,graphSaveFile=outpath+"\\"+tag+"训练KS_Cut.png")
    testKsresCut=cs.KS(inds=test_predprob1, target="target", rankvar='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None, descending=False, graph=True,title="validate"
                    ,graphSaveFile=outpath+"\\"+tag+"验证KS_Cut.png")
    totalKsresCut=cs.KS(inds=total_predprob1, target="target", rankvar='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None, descending=False, graph=True,title="Total"
                     ,graphSaveFile=outpath+"\\"+tag+"整体KS_Cut.png")
    testtKsresCut=cs.KS(inds=testt_predprob1, target="target", rankvar='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None, descending=False, graph=True,title="Test"
                     ,graphSaveFile=outpath+"\\"+tag+"测试KS_Cut.png")
    

    trainKsresCut["flag"]="1_Train"
    testKsresCut["flag"]="2_Validate"
    totalKsresCut["flag"]="3_Total"
    testtKsresCut["flag"]="4_Test"
    trainKsresCut["group"]=trainKsresCut.index
    testKsresCut["group"]=testKsresCut.index
    totalKsresCut["group"]=totalKsresCut.index
    testtKsresCut["group"]=testtKsresCut.index
    trainKsresCut.index=range(trainKsresCut.shape[0])
    testKsresCut.index=range(testKsresCut.shape[0])
    totalKsresCut.index=range(totalKsresCut.shape[0])
    testtKsresCut.index=range(testtKsresCut.shape[0])
    KSresultCut = pd.concat([trainKsresCut,testKsresCut,totalKsresCut,testtKsresCut])
    #KSresultCut.index=list(range(KSresultCut.shape[0]))
    KSresultCut['group_c']=KSresultCut.group.astype('str')
    KSresultCut=KSresultCut.drop(columns=['group'])
    #PSI
    PSI_TrainVsValidate=cs.PSI_Compute_Single(train_predprob1, test_predprob1, var='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None,
                                           label1='Train',label2='Validate',plotShow=False,graphSaveFile=outpath+"\\"+tag+"训练VS验证PSI.png")
    PSI_TrainVsTest=cs.PSI_Compute_Single(train_predprob1, testt_predprob1, var='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None,
                                           label1='Train',label2='Test',plotShow=False,graphSaveFile=outpath+"\\"+tag+"训练VS测试PSI.png")
    PSI_ValidateVsTest=cs.PSI_Compute_Single(test_predprob1, testt_predprob1, var='score', pct=None, groupcut=list(range(minscore,maxscore,scoreGroupcut)), groupn=None,
                                           label1='Validate',label2='Test',plotShow=False,graphSaveFile=outpath+"\\"+tag+"验证VS测试PSI.png")
    PSI_TrainVsValidate['flag']="1_Train_Vs_Validate" 
    PSI_TrainVsTest['flag']="2_Train_Vs_Test"     
    PSI_ValidateVsTest['flag']="1_Validate_Vs_Test"          
    PSIresultCut = pd.concat([PSI_TrainVsValidate,PSI_TrainVsTest,PSI_ValidateVsTest])
    #PSIresultCut.index=list(range(PSIresultCut.shape[0]))
    PSIresultCut['GROUP_C']=PSIresultCut.GROUP.astype('str')
    PSIresultCut=PSIresultCut.drop(columns=['GROUP'])   
    
    #模型准确性
    accTrain=cs.Var_Groupcut(inds=train_predprob1, var="score", groupcut=None, groupn=20)
    accTrain_t0=accTrain[0][["target","GROUP"]].groupby('GROUP').count()
    accTrain_t1=accTrain[0][["target","GROUP"]].groupby('GROUP').sum()
    accTrain_t2=accTrain[0][["target","prob","prob_aln","GROUP"]].groupby('GROUP').mean()
    accTrain_t3=pd.concat([accTrain_t0,accTrain_t1,accTrain_t2],axis=1)
    accTrain_t3["flag"]="1_Train"
    accTrain_t3["GROUP"]=list(accTrain_t3.index)
    accTrain_t3.index=range(accTrain_t3.shape[0])
    accTrain_t3.columns=["TOTOL","BAD",'prob_sample',"prob",'prob_aln','flag','GROUP']
   
    accValidate=cs.Var_Groupcut(inds=test_predprob1, var="score", groupcut=None, groupn=20)
    accValidate_t0=accValidate[0][["target","GROUP"]].groupby('GROUP').count()
    accValidate_t1=accValidate[0][["target","GROUP"]].groupby('GROUP').sum()
    accValidate_t2=accValidate[0][["target","prob","prob_aln","GROUP"]].groupby('GROUP').mean()
    accValidate_t3=pd.concat([accValidate_t0,accValidate_t1,accValidate_t2],axis=1)
    accValidate_t3["flag"]="1_Validate"
    accValidate_t3["GROUP"]=list(accValidate_t3.index)
    accValidate_t3.index=range(accValidate_t3.shape[0])
    accValidate_t3.columns=["TOTOL","BAD",'prob_sample',"prob",'prob_aln','flag','GROUP']
    
    accTest=cs.Var_Groupcut(inds=testt_predprob1, var="score", groupcut=None, groupn=20)
    accTest_t0=accTest[0][["target","GROUP"]].groupby('GROUP').count()
    accTest_t1=accTest[0][["target","GROUP"]].groupby('GROUP').sum()
    accTest_t2=accTest[0][["target","prob","prob_aln","GROUP"]].groupby('GROUP').mean()
    accTest_t3=pd.concat([accTest_t0,accTest_t1,accTest_t2],axis=1)
    accTest_t3["flag"]="1_Test"
    accTest_t3["GROUP"]=list(accTest_t3.index)
    accTest_t3.index=range(accTest_t3.shape[0])
    accTest_t3.columns=["TOTOL","BAD",'prob_sample',"prob",'prob_aln','flag','GROUP']
    
    plt.figure(figsize=(8,4))
    plt.title('The accurary of Train')
    plt.plot(accTrain_t3["GROUP"].astype('str'), accTrain_t3["prob_sample"], color='red', label='prob_sample',marker="o")
    plt.plot(accTrain_t3["GROUP"].astype('str'), accTrain_t3["prob"], color='green', label='prob',marker="o")
    plt.plot(accTrain_t3["GROUP"].astype('str'), accTrain_t3["prob_aln"], color='blue', label='prob_aln',marker="o")
    plt.xticks(rotation=90)
    plt.savefig(outpath+"\\"+tag+"准确性Train.png", dpi=150,bbox_inches='tight')
    plt.legend() # 显示图例
    plt.close()
    plt.figure(figsize=(8,4))
    plt.title('The accurary of Validate')
    plt.plot(accValidate_t3["GROUP"].astype('str'), accValidate_t3["prob_sample"], color='red', label='prob_sample',marker="o")
    plt.plot(accValidate_t3["GROUP"].astype('str'), accValidate_t3["prob"], color='green', label='prob',marker="o")
    plt.plot(accValidate_t3["GROUP"].astype('str'), accValidate_t3["prob_aln"], color='blue', label='prob_aln',marker="o")
    plt.xticks(rotation=90)
    plt.savefig(outpath+"\\"+tag+"准确性Validate.png", dpi=150,bbox_inches='tight')
    plt.legend() # 显示图例
    plt.close()
    plt.figure(figsize=(8,4))
    plt.title('The accurary of Test')
    plt.plot(accTest_t3["GROUP"].astype('str'), accTest_t3["prob_sample"], color='red', label='prob_sample',marker="o")
    plt.plot(accTest_t3["GROUP"].astype('str'), accTest_t3["prob"], color='green', label='prob',marker="o")
    plt.plot(accTest_t3["GROUP"].astype('str'), accTest_t3["prob_aln"], color='blue', label='prob_aln',marker="o")
    plt.xticks(rotation=90)
    plt.savefig(outpath+"\\"+tag+"准确性Test.png", dpi=150,bbox_inches='tight')
    plt.legend() # 显示图例
    plt.close()
    
    accResult=pd.concat([accTrain_t3,accValidate_t3,accTest_t3],axis=0)
    accResult.columns=["TOTOL","BAD",'prob_sample',"prob",'prob_aln','flag','GROUP']
    #accResult.index=list(range(accResult.shape[0]))
    accResult['GROUP_C']=accResult.GROUP.astype('str')
    accResult=accResult.drop(columns=['GROUP'])   
    
    #模型参数
    if len(evaluation_log[0][evaluation_log['del'] ==2])==0:
        bi=evaluation_log2.shape[0]
    else:
        bi=int(list(evaluation_log[0][evaluation_log['del'] ==2])[0][1:(len(list(evaluation_log[0][evaluation_log['del'] ==2])[0])-1)])+1
    
    
    xcs=pd.DataFrame({"Base":Base,"PDO":PDO,"lmd":lmd,"params":[str(xgbclassifier  ) ] ,"Best iteration":bi,"Target Variable":target,"tag":tag} ) 
    #xcs=pd.DataFrame({"params":[""] ,"Best iteration":list(evaluation_log[0][evaluation_log['del'] ==2])[0]} ) 
    
    #案例
    #v=IDcol.copy()
    #v.extend(feat_imp.index)
    case=pd.concat([train[predictors].head(50),train_predprob1.head(50)],axis=1)
    
    
    #输出pmml文件，上线部署
    if outpath !=None:
        #pipeline = sklearn2pmml.PMMLPipeline([('classifier',xgbclassifier)])
        #pipeline.fit(train[predictors],train[target])
        #sklearn2pmml.sklearn2pmml(pipeline, outpath+"\\"+tag+modelFile+".pmml",with_repr = True)
        #print("模型的pmml文件已成功保存在："+outpath+"\\"+pmmlFile)
        joblib.dump(xgbclassifier, outpath+"\\"+tag+modelFile+'.model')
        #xgbclassifier.get_booster().save_model(outpath+"\\"+tag+modelFile+'.model') 
        #xgbclassifier.save_model(outpath+"\\"+tag+modelFile+'.model') 
        try:
            clf = joblib.load(outpath+"\\"+tag+modelFile+'.model')
            predRes=list(clf.predict_proba(train[predictors].head(50))[:,1]) #此处test_X为特征集
            case["modelFilePred_导入模型正确性验证"]=predRes
        except:     
            print("model文件导入失败")

        if  outXlsxNew:      
            workbook = xlsxwriter.Workbook(outpath+"\\"+tag+"机器学习模型文档.xlsx")     #新建excel表
            if gbieCount is not None:
                addWorksheet(workbookObj=workbook,inds=gbieCount,sheet_name="数据分布",
                    picOrder=None,
                     picfile=None,
                     picinch=None)  
                print("数据分布")
            if IVCount is not None:
                addWorksheet(workbookObj=workbook,inds=IVCount[['vname','grp','iv_x','iv_y','WoeCorr','PSI','label','custType','varType']],sheet_name="全部变量IV及PSI",
                    picOrder=None,
                    picfile=None,
                    picinch=None) 
                print("全部变量IV及PSI")
            addWorksheet(workbookObj=workbook,inds=predictorsOut,sheet_name="候选变量",
                picOrder=None,
                 picfile=None,
                 picinch=None)
            print("候选变量")
            addWorksheet(workbookObj=workbook,inds=feat_imp1,sheet_name="入选变量",
                picOrder=None,
                 picfile=None,
                 picinch=None) 
            print("入选变量")
            if IVCountDetail is not None:
                IVCount1=pd.merge(left=IVCount,right=feat_imp1[['vname','FeatureImportance']],on='vname',how='right')
                IVCount1=IVCount1.loc[IVCount1['grp']>0,]
                IVCount1.sort_values( by= ['FeatureImportance','vname'],ascending=[False,True],inplace=True)
                IVCount1.index=list(range(IVCount1.shape[0]))
                IVCountDetail1=pd.merge(left=IVCountDetail,right=feat_imp1,on='vname',how='inner')
                IVCountDetail1=IVCountDetail1[['vname','groupC','n_0_x','n_1_x','count_x','rate_x','p_01_x','WOE','iv_x',\
				'grp_x','n_0_y','n_1_y','count_y','rate_y','p_01_y','WOE_y','PSI','FeatureImportance','label_x']]

				
                grpCum=1
                picinch=[[0.2,0.2]]
                IVCountDetail1.sort_values(by=['FeatureImportance','vname','grp_x'],ascending=[False,True,True],inplace=True,na_position='last')
                IVCountDetail1.index=list(range(IVCountDetail1.shape[0]))
				#IVCountDetail1.index=range(IVCountDetail1.shape[0])
				
                for ip in range(IVCount1.shape[0]):  
                    IVCount1.loc[ip,'grpCum']=grpCum+IVCount1.loc[ip,'grp']+1
                    grpCum=grpCum+IVCount1.loc[ip,'grp']+1
                    if ip==0:
                        IVCount1.loc[ip,'picOrder']="T"+str(1)
                    else:
                        if ip%2 ==0:
                            IVCount1.loc[ip,'picOrder']="T"+str(int(IVCount1.loc[ip-1,'grpCum']))
                        else:
                            IVCount1.loc[ip,'picOrder']="W"+str(int(IVCount1.loc[ip-1,'grpCum']))
                        picinch.append([0.2,0.2])
                    IVCount1.loc[ip,'picfile']=IVpicpath+"\\"+IVCount1.loc[ip,'vname']+".png"
                    #IVCount1.loc[ip,'picinch']=(1,1)
				
                addWorksheet(workbookObj=workbook,inds=IVCountDetail1,sheet_name="入选变量分箱",
                    picOrder=list(IVCount1['picOrder']),
                    picfile=list(IVCount1['picfile']),
                    picinch=picinch) 
                print("入选变量分箱")
            
            addWorksheet(workbookObj=workbook,inds=xcs,sheet_name="模型参数",
                picOrder=None,
                 picfile=None,
                 picinch=None)
            print("模型参数")
            addWorksheet(workbookObj=workbook,inds=evaluation_log2,sheet_name="迭代表现",
                picOrder=['G1'],
                 picfile=[outpath+"\\"+tag+"迭代表现.png"],
                 picinch=[[1,1]]) 
            print("迭代表现")
            addWorksheet(workbookObj=workbook,inds=KSresult,sheet_name="KS按百分位",
                picOrder=['P1','P23','P46','P69'],
                 picfile=[outpath+"\\"+tag+"训练KS.png",outpath+"\\"+tag+"验证KS.png",outpath+"\\"+tag+"整体KS.png",outpath+"\\"+tag+"测试KS.png"],
                 picinch=[[1,1],[1,1],[1,1],[1,1]]) 
            print("KS按百分位")
            addWorksheet(workbookObj=workbook,inds=KSresultCut,sheet_name="KS按分数段",
                picOrder=['P1','P23','P46','P69'],
                 picfile=[outpath+"\\"+tag+"训练KS_Cut.png",outpath+"\\"+tag+"验证KS_Cut.png",outpath+"\\"+tag+"整体KS_Cut.png",outpath+"\\"+tag+"测试KS_Cut.png"],
                 picinch=[[1,1],[1,1],[1,1],[1,1]]) 
            print("KS按分数段")
            addWorksheet(workbookObj=workbook,inds=PSIresultCut,sheet_name="模型稳定性",
                picOrder=['K1','K23','K46'],
                 picfile=[outpath+"\\"+tag+"训练VS验证PSI.png",outpath+"\\"+tag+"训练VS测试PSI.png",outpath+"\\"+tag+"验证VS测试PSI.png"],
                 picinch=[[1,1],[1,1],[1,1]])  
            print("模型稳定性")
            addWorksheet(workbookObj=workbook,inds=accResult,sheet_name="模型准确性",
                picOrder=['I1','I23','I46'],
                 picfile=[outpath+"\\"+tag+"准确性Train.png",outpath+"\\"+tag+"准确性Validate.png",outpath+"\\"+tag+"准确性Test.png"],
                 picinch=[[1,1],[1,1],[1,1]]) 
            print("模型准确性")
            workbook.close()          #将excel文件保存关闭，如果没有这一行运行代码会报错
            #删除那些png图片
            files=os.listdir(outpath)
            #pngfile=[]
            for iq in range(len(files)):
                ed=files[iq][(len(files[iq])-4):len(files[iq])]
                if ed=='.png':
                    #pngfile.append(outpath+"\\"+files[iq])
                    os.remove(outpath+"\\"+files[iq])
            case.to_csv(outpath+"\\"+tag+"模型核对案例.csv",encoding='ansi')
     
        print("模型结果保存在："+outpath)
    print("return: [0]分类器,[1]备选预测变量,[2]入选变量重要性,[3][0]按百分位KS,[3][1]按等分段KS,[4]训练和验证的预测概率和评分")
    if IVCountDetail is not None:
        return xgbclassifier,predictors,feat_imp,[KSresult,KSresultCut],total_predprob1,IVCountDetail1
    else:
        return xgbclassifier,predictors,feat_imp,[KSresult,KSresultCut],total_predprob1
    
def addWorksheet(workbookObj=None,inds=None,sheet_name=None,picOrder=['A1','A10'],
                 picfile=[r'\pic\jxl_searched_cnt_01_L90D.jpg',r'\pic\jxl_searched_cnt_01_L90D.jpg'],
                 picinch=[[1,2],[0.5,0.6]]):
    worksheetObj= workbookObj.add_worksheet(sheet_name) 
    worksheetObj.write_row('A1',list(inds.columns))
    if inds.shape[0]>=1:
        coldtypes= inds.dtypes
        for pr in list(inds.columns):
            if coldtypes[pr]=='object':
                inds.loc[inds[pr].isnull(),pr]='-99'
            else:
                inds.loc[inds[pr].isnull(),pr]=-99
        for i in range(inds.shape[0]):
            worksheetObj.write_row('A'+str(i+2),inds.iloc[i,])
    if picfile is not None:
        for j in range(len(picfile)):
            if(os.path.exists(picfile[j])):
                worksheetObj.insert_image(picOrder[j], picfile[j],{'x_scale': picinch[j][0], 'y_scale': picinch[j][1]})
                #os.remove(picfile[j])
    #import pandas as pd
     
 
def add_sheet(data, excel_writer, sheet_name):
    """
    不改变原有Excel的数据，新增sheet。
    注：
        使用openpyxl操作Excel时Excel必需存在，因此要新建空sheet
        无论如何sheet页都会被新建，只是当sheet_name已经存在时会新建一个以1结尾的sheet，如：test已经存在时，新建sheet为test1，以此类推
    :param data: DataFrame数据
    :param excel_writer: 文件路径
    :param sheet_name: 新增的sheet名称
    :return:
    """
    book = openpyxl.load_workbook(excel_writer.path)
    excel_writer.book = book
    data.to_excel(excel_writer=excel_writer, sheet_name=sheet_name, index=True, header=True)
 
    excel_writer.close()
 
 
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
        print(path+' 目录已存在')
        return False
 
# 定义要创建的目录
#mkpath="d:\\qttc\\web\\"
# 调用函数
#mkdir(mkpath)



