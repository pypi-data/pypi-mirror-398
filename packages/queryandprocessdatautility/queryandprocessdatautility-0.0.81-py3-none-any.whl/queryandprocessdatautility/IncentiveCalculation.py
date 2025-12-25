import pandas as pd 
import os
import json
from pandas import to_datetime
from flask import request, make_response, Flask 
import urllib.parse
import datetime
from pandarallel import pandarallel
import numpy as np
from functools import partial
import traceback
import loggerutility as logger
import re
import sys
import matplotlib
from prophet import Prophet
from DatabaseConnectionUtility import Oracle, SAPHANA, InMemory, Dremio, MySql, ExcelFile, Postgress, MSSQLServer, Tally, ProteusVision, SnowFlake, FileURL, RestAPI
import requests
import pickle
import joblib
from rasamodelandtrain import Rasa
from .TimeSeriesForecasting import timeseriesforecasting
from .Classification import Classification
from .SentimentAnalytics import SentimentAnalytics
from .IntentClassification import IntentClassification
from .Outlier import outlierClass
import mtranslate as mt

class IncentiveCalculation:

    pandarallel.initialize()
    
    df = None
    detSql = None
    sqlQuery = None
    lookupTableMap = {}
    queryStringMap = {}
    currentDetData = None
    CPU_COUNT = os.cpu_count()
    errorId = ""
    dbDetails = None
    calculationData=""
    val="" 
    group_style =""
    outputType="JSON"
    group=""
    colum=""
    pool = None
    isPool  = 'false'
    minPool = 2
    maxPool = 100
    timeout = 180
    editorId=""
    userId=""
    visualId=""
    tableHeading =""
    argumentList = None
    advancedFormatting=None 
    isColumnChange= 'true'   
    isSqlChange= 'true'      
    transpose="false"
    dataSourceType="S"
    fileName=""
    transId=""
    auth_key=""
    serverUrl=""
    userName=""
    password= "" 
    jsonDataResponse=""
    dataSourceColumlist  = []
    client_DBDetails     = ""
    client_connectionObj = ""
    
    def getConnection(self, dbDetails):
       
        if dbDetails != None:
                # Added by SwapnilB for dynamically creating instance of DB class on [ 10-AUG-22 ] [ START ] 
                klass = globals()[dbDetails['DB_VENDORE']]
                dbObject = klass()
                self.pool = dbObject.getConnection(dbDetails)
                # Added by SwapnilB for dynamically creating instance of DB class on [ 10-AUG-22 ]  [ END ] 
                
        return self.pool

    def getQueryData(self, jsonData=None, isWebsocet=None):
        try:
            con = None
            logger.log(f'\n This code is From queryandprocessdata Package', "0")
            logger.log(f'\n Print time on start : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
            
            if isWebsocet == "true":
                print("jsonData in getQueryData:", jsonData, type(jsonData))
                domData = jsonData
            else:
                domData = request.get_data('jsonData', None)
                domData = domData[9:]
            self.calculationData = json.loads(domData)
            logger.log(f'\n Inside getQueryData jsonData : {self.calculationData}', "0")

            if 'isSqlChange' in self.calculationData.keys():
                if self.calculationData.get('isSqlChange') != None:
                    self.isSqlChange = self.calculationData['isSqlChange']

            if 'isColumnChanges' in self.calculationData.keys():
                if self.calculationData.get('isColumnChanges') != None:
                    self.isColumnChange = self.calculationData['isColumnChanges']   

            if 'editorId' in self.calculationData.keys():
                if self.calculationData.get('editorId') != None:
                    self.editorId = self.calculationData['editorId']   

            if 'userId' in self.calculationData.keys():
                if self.calculationData.get('userId') != None:
                    self.userId = self.calculationData['userId']   
            
            if 'visualId' in self.calculationData.keys():
                if self.calculationData.get('visualId') != None:
                    self.editorId = self.calculationData['visualId']   

            if 'tableHeading' in self.calculationData.keys():
                if self.calculationData.get('tableHeading') != None:
                    self.tableHeading = self.calculationData['tableHeading']        
        
            if 'argumentList' in self.calculationData.keys():
                if self.calculationData.get('argumentList') != None:
                    argumentList_withOperator = self.calculationData['argumentList']   
                    if len(argumentList_withOperator) > 0 and argumentList_withOperator != 'undefined':   # Added for handling pineCone Vector model training json-decoder exception
                        argumentList_withOperator = json.loads(argumentList_withOperator)
                    logger.log(f"argumentList_withOperator::: {argumentList_withOperator}","0" )
                    if bool(argumentList_withOperator) and argumentList_withOperator != 'undefined':      # Added for handling pineCone Vector model training json-decoder exception
                        logger.log(f"inside argumentList not empty condition  ::: ","0" )
                        self.argumentList = self.removeOperator(argumentList_withOperator)
                    else:
                        logger.log(f"self.argumentList is empty:: {self.argumentList}","0")
                    logger.log(f"self.argumentList ::: {self.argumentList}","0" )
        
            if 'advancedFormatting' in self.calculationData.keys():
                if self.calculationData.get('advancedFormatting') != None:
                    self.advancedFormatting = self.calculationData['advancedFormatting']

            if 'dbDetails' in self.calculationData.keys() and self.calculationData.get('dbDetails') != None:
                if 'DATA_SOURCE_TYPE' in self.calculationData['dbDetails'] and self.calculationData.get('dbDetails')['DATA_SOURCE_TYPE'] != None:
                    self.dataSourceType = self.calculationData['dbDetails']['DATA_SOURCE_TYPE']
                    logger.log(f'\n self.dataSourceType : {self.dataSourceType}', "0")
            
            if 'client_DBDetails' in self.calculationData.keys():
                if self.calculationData.get('client_DBDetails') != None:
                    self.client_DBDetails = self.calculationData['client_DBDetails']
                logger.log(f'\n self.client_DBDetails ::: {self.client_DBDetails} Type ::: {type(self.client_DBDetails)}', "0")


            sql = self.calculationData['source_sql']
            self.dbDetails = self.calculationData['dbDetails']
            
            if self.dataSourceType == "S":
                self.pool = self.getConnection(self.dbDetails)

            if self.dbDetails != None:
                if self.dbDetails['DB_VENDORE'] == 'Oracle':
                    if self.isPool == 'true':
                        con = self.pool.acquire()
                    else:
                        con = self.pool
                else:
                    con = self.pool

            if ' update ' in sql or ' delete ' in sql:
                return self.getErrorXml("Invalid SQL" , "Update and Delete operations are not allowed in Visual.")
            else:
                if self.isSqlChange == 'true':
                    logger.log(f'\n Print time for before executing source_sql : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                    
                    if self.dataSourceType == "F":          
                        klass = globals()[self.dbDetails['DB_VENDORE']]
                        fileObject = klass()
                        self.df = fileObject.getData(self.calculationData)
                        logger.log(f"fileURL self.df shape:: {self.df.shape}","0")

                    elif self.dataSourceType == "R":
                        klass = globals()[self.dbDetails['DB_VENDORE']]
                        APIObject = klass()
                        self.df = APIObject.getData(self.calculationData)
                        logger.log(f"\nRestAPI self.df:: {self.df}\n {type(self.df)}\n","0")
                        if type(self.df)== str :
                            if "Errors" in self.df:
                                return str(self.df)
                        elif type(self.df)== dict :
                            if "Errors" in self.df["Root"]:
                                return str(self.df)
                        else:
                            logger.log(f"'Errors' key not found :: {self.df}","0")
                        logger.log(f"RestAPI self.df shape:: {self.df.shape}","0")
                    
                    elif self.dataSourceType == "S":
                        self.df = pd.read_sql(sql, con)
                        logger.log(f"self.df type-S read_sql :::::{self.df}{type(self.df)}","0")
                        
                    else:
                        logger.log(f"Invalid dataSourceType:::::{self.dataSourceType}","0")

                    logger.log(f'\n Print time for after executing source_sql : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                    self.storePickleFile(self.df, self.userId, self.editorId, self.visualId, 'sourceSql')
                else:
                    self.df = self.readPickleFile(self.userId, self.editorId, self.visualId, 'sourceSql')

            self.df.columns = self.df.columns.str.strip().str.lower()
            
            if con:
                if self.dbDetails != None:
                    if self.dbDetails['DB_VENDORE'] == 'Oracle':
                        if self.isPool == 'true' :
                            self.pool.release(con)

            udf_divide = partial(self.udf_divide)
            udf_round = partial(self.udf_round)
            contribution = partial(self.contribution)               # Added by AniketG on [16-Aug-2022] for calculating percentage
            predict = partial(self.predict)
            translate = partial(self.translate)
            
            #logger.log(f'\n Print sourcesql result ::: \n {self.df}', "0")

            self.client_connectionObj = self.getConnection(self.client_DBDetails)
            logger.log(f"Client Database Connection Object ::: {self.client_connectionObj} ")

            if not self.df.empty:
                
                if self.isColumnChange == 'true':
      
                    for key in self.calculationData:

                        if key == 'column':
                            detailArr = self.calculationData[key]
                            
                            for detail in detailArr:
                                self.currentDetData = detail

                                if "line_no" in detail:
                                    self.errorId = 'errDetailRow_' + str(detail['line_no'])
                                
                                if detail['calc_type'] == 'S':
                                    logger.log(f'\n Inside getQueryData calc_expression for type SQL : {detail["calc_expression"]}', "0")
                                    self.detSql = detail['calc_expression']
                                    logger.log(f'\n Print time for type SQL before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        self.df[detail['col_name'].lower().strip()] = self.df.apply(lambda row : self.getSqlResult(row, self.pool, detail), axis=1)
                                    else:
                                        self.df[detail['col_name'].lower().strip()] = self.df.parallel_apply(lambda x : None, axis=1)

                                    logger.log(f'\n Print time for type SQL after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")

                                elif detail['calc_type'] == 'F':
                                    logger.log(f'\n Inside getQueryData calc_expression for type Forecast : {detail["calc_expression"]}', "0")
                                    expr = detail['col_name'].lower().strip() + '=' + detail['calc_expression'].lower().strip()
                                    logger.log(f'\n Print time for type Forecast before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        forecastingmethods = timeseriesforecasting()
                                        self.df = forecastingmethods.forecast(self.calculationData,self.df)
                                        
                                    else:
                                        self.df = self.df.eval(detail['col_name'].lower().strip() + '=' + None, engine='python' )

                                    logger.log(f'\n Print time for type Forecast after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")

                                elif detail['calc_type'] == 'E':
                                    logger.log(f'\n Inside getQueryData calc_expression for type EXPRESSION : {detail["calc_expression"]}', "0")
                                    expr = detail['col_name'].lower().strip() + '=' + detail['calc_expression'].lower().strip()
                                    logger.log(f'\n Print time for type EXPRESSION before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        self.df = self.df.eval(expr, engine='python')
                                    else:
                                        self.df = self.df.eval(detail['col_name'].lower().strip() + '=' + None, engine='python')

                                    logger.log(f'\n Print time for type EXPRESSION after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")

                                elif detail['calc_type'] == 'L':
                                    logger.log(f'\n Inside getQueryData calc_expression for type LOOKUP : {detail["calc_expression"]}', "0")
                                    self.detSql = detail['calc_expression']
                                    
                                    logger.log(f'\n Print time for type LOOKUP before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        self.df[detail['col_name'].lower().strip()] = self.df.apply(lambda row : self.getLookUpValue(row, self.client_connectionObj), axis=1)
                                    else:
                                        self.df[detail['col_name'].lower().strip()] = self.df.apply(lambda row : self.getLookUpValue(row, self.client_connectionObj), axis=1)

                                    logger.log(f'\n Print time for type LOOKUP after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")

                                elif detail['calc_type'] == 'C':
                                    logger.log(f'\n Inside getQueryData calc_expression for type CONDITIONAL EXPRESSION : {detail["calc_expression"]}', "0")
                                    logger.log(f'\n Print time for type CONDITIONAL EXPRESSION before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        exprArr = detail['calc_expression'].split(':')
                                        condition = exprArr[0]
                                        trueExpr = None
                                        falseExpr = None
                                        if exprArr[1] != None:
                                            trueExpr = exprArr[1]
                                        if exprArr[2] != None:
                                            falseExpr = exprArr[2]
                                        
                                        logger.log(f"condition ::: {condition}")
                                        logger.log(f"trueExpr ::: {trueExpr}")
                                        logger.log(f"falseExpr ::: {falseExpr}")

                                        self.df[detail['col_name'].lower().strip()] = self.udf_if(self.df, condition, trueExpr, falseExpr)
                                    else:
                                        self.df = self.df.eval(detail['col_name'].lower().strip() + ' = ' + None, engine='python')

                                    logger.log(f'\n Print time for type CONDITIONAL EXPRESSION after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                elif detail['calc_type'] == 'U':
                                    logger.log(f'\n Inside getQueryData calc_expression for type Cumulative Sum : {detail["calc_expression"]}', "0")
                                    logger.log(f'\n Print time for type Cumulative Sum before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        columnArrList = detail['calc_expression'].lower().split(',')
                                        cumsumColumn = columnArrList[0]
                                        if len(columnArrList) == 1:
                                            self.df[detail['col_name'].lower().strip()] = self.df[cumsumColumn].cumsum()
                                        else:
                                            del columnArrList[0]
                                            self.df[detail['col_name'].lower().strip()] = self.df.groupby(columnArrList)[cumsumColumn].cumsum()
                                    else:
                                        self.df[detail['col_name'].lower().strip()] = self.df.parallel_apply(lambda x : None, axis=1)

                                elif detail['calc_type'] == 'N':
                                    logger.log(f'\n Inside getQueryData UserDefine for type EXPRESSION : {detail["calc_expression"]}', "0")
                                    expr = detail['col_name'].lower().strip() + '=' + detail['calc_expression'].lower().strip()
                                    logger.log(f'\n Print time for type EXPRESSION before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        self.df = self.df.eval(expr, engine='python')
                                    else:
                                        self.df = self.df.eval(detail['col_name'].lower().strip() + '=' + None, engine='python')

                                    logger.log(f'\n Print time for type EXPRESSION after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")

                                elif detail['calc_type'] == 'O':
                                    logger.log(f'\n Inside getQueryData calc_expression for type Outlier : {detail["calc_expression"]}', "0")
                                    expr = detail['col_name'].lower().strip() + '=' + detail['calc_expression'].lower().strip()
                                    logger.log(f'\n Print time for type Outlier before performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                                    
                                    if detail['calc_expression'] != None:
                                        outliermethods = outlierClass()
                                        self.df = outliermethods.outlierMainFunction(self.calculationData,self.df)
                                    else:
                                        self.df = self.df.eval(detail['col_name'].lower().strip() + '=' + None, engine='python')

                                    logger.log(f'\n Print time for type Outlier after performing applyFunction : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")

                    self.storePickleFile(self.df, self.userId, self.editorId, self.visualId, 'final')               
                else:
                    self.df = self.readPickleFile(self.userId, self.editorId, self.visualId, 'final')        
            else:
                returnErr = self.getErrorXml("No records found against the source sql", "")
                logger.log(f'\n Print exception returnSring inside getQueryData : {returnErr}', "0")
                return str(returnErr)
            
            #logger.log(f'\n End of query datatypes:::\n {self.df.dtypes}', "0")
            self.df.columns = self.df.columns.str.strip().str.lower()
            
            if self.calculationData.get('sorting_col_name'):
                sortingColName = self.calculationData['sorting_col_name']
                if sortingColName != "":
                    sortingColName = sortingColName.lower().strip()
                    self.df.sort_values(by=[sortingColName], inplace=True, ascending=True)
            
            dbDataTypes = self.df.dtypes.to_json()
            #self.df = self.df.to_json(orient='records')
            #logger.log(f'\n End of query data:::\n {self.df}', "0")
            
            if 'visualJson' in self.calculationData.keys():
                if self.calculationData.get('visualJson') != None:
                    visualJson = self.calculationData['visualJson']

            if 'OutputType' in self.calculationData.keys():
                if self.calculationData.get('OutputType') != None:
                    self.outputType = self.calculationData['OutputType']      
            
            if 'columnHeading' in self.calculationData.keys():
                if self.calculationData.get('columnHeading') != None:
                    columnHeading = self.calculationData['columnHeading']        
            
            if 'oldColumnHeading' in self.calculationData.keys():
                if self.calculationData.get('oldColumnHeading') != None:
                    oldColumnHeading = self.calculationData['oldColumnHeading']        

            if self.outputType == 'HTML':
                #logger.log(f'\n Print dataframe at end::: \n {self.df}', "0")
                visualJson1 = json.loads(visualJson)
                columnHeading = columnHeading.split(",")
                self.df.rename(columns=dict(zip(self.df.columns, columnHeading)), inplace=True)
                oldColumnHeading = oldColumnHeading.split(",")
            
                if 'groups' in visualJson1.keys():
                    if len(visualJson1.get('groups')) != 0:    
                        self.group = visualJson1['groups']

                if 'rows' in visualJson1.keys():
                    if len(visualJson1.get('rows')) != 0: 
                        row = visualJson1["rows"]
                
                if 'columns' in visualJson1.keys():
                    if len(visualJson1.get('columns')) != 0:
                        self.colum = visualJson1["columns"]
                
                if 'values' in visualJson1.keys():
                    if len(visualJson1.get('values')) != 0:
                        self.val = visualJson1["values"]
                        
                if len(self.group) != 0:
                    lst=[]
                    for label, df_obj in (self.df).groupby(self.group):
                        sum = df_obj[self.val].sum()
                        df_obj.loc[' '] = sum   
                        lst.append(df_obj)

                    final_df = pd.concat(lst)
                    final_df.loc[final_df[row[0]].isnull(), self.group[0]] = "Total "  
                    final_df.loc[''] = self.df[self.val].sum()
                    final_df.fillna('', inplace=True)
                    final_df.iloc[-1, final_df.columns.get_loc(self.group[0])] = 'Grand Total '
                    self.group_style = True
                    html_str = self.getTableHTML(final_df)
                    logger.log(f'\n Print time on end : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                    return html_str
                    
                elif len(self.colum) == 0:
                    html_str = self.getTableHTML(self.df)
                    logger.log(f'\n Print time on end : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                    return html_str
                    
                else:
                    final_pivot = pd.pivot_table(self.df, index=row, columns=self.colum, values=self.val)
                    html_str = self.getTableHTML(final_pivot)
                    logger.log(f'\n Print time on end : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                    return html_str
                    
            elif self.outputType == "JSON":
                self.df = self.df.to_json(orient='records', date_format='iso')
                #logger.log(f'\n Print dataframe at end::: \n {self.df}', "0")
                data_set = {"dbDataTypesDetails": dbDataTypes, "allData":  self.df }
                logger.log(f'\n Print time on end : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                #return self.df
                #return data_set 
                return json.dumps(data_set)
            
            elif self.outputType == "XML":               
                xml_Str = self.to_xml(self.df)
                xmlStr = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n' + xml_Str + '\n</root>'
                logger.log(f'\n Print time on end : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                return xmlStr

            else:
                pass
                
        except Exception as e:
            logger.log(f'\n In getQueryData exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            if "Invalid column name" in descr :
                trace = "Column is not present in selected criteria, so please select specific column in criteria and then use in your calculation."
                returnErr = self.getErrorXml(descr, trace)
                logger.log(f'\n Print SQLResult exception  getQueryData : {returnErr}', "0")
                return str(returnErr)
            else:    
                returnErr = self.getErrorXml(descr, trace)
                logger.log(f'\n Print exception returnSring inside getQueryData : {returnErr}', "0")
                return str(returnErr)
        finally:
            try:
                if self.pool:
                    if self.dbDetails != None:
                        if self.dbDetails['DB_VENDORE'] == 'Oracle':
                            if self.isPool == 'true' :
                                self.pool.close()
                            else:
                                if con:
                                    con.close()
                        else:
                            if con:
                                con.close()
                if self.client_connectionObj:
                    self.client_connectionObj.close()
            except Exception as e: 
                logger.log(f'\n In getQueryData exception stacktrace : ', "1")
                trace = traceback.format_exc()
                descr = str(e)
                returnErr = self.getErrorXml(descr, trace)
                logger.log(f'\n Print exception returnSring inside getQueryData : {returnErr}', "0")
                return str(returnErr)

    def getLookUpValue(self, row, client_DBConnection):
        try:
            expr = self.detSql.split(',')
            lookUpTable = str(expr[0].strip())
            lookUpCol = expr[1].strip().lower()
            validateLookup = "false"
            isLookUpDateColValBlank = "false"
            lookupExpLen = len(expr)
            
            if lookupExpLen == 3:
                lookUpDateCol = expr[2].strip().lower()
                lookUpDateColVal = row[lookUpDateCol]
                validateLookup = "true"
                if str(lookUpDateColVal) == None or str(lookUpDateColVal) == '' or str(lookUpDateColVal) == 'NaT':
                    lookUpDateColVal = str('')
                    isLookUpDateColValBlank = "true"

            if lookUpTable != None and lookUpTable.startswith('\''):
                length = len(lookUpTable)
                lookUpTable = lookUpTable[1:length-1]
            else:
                lookUpTable = lookUpTable.lower()
                if  lookUpTable in row:
                    rowVal = row[lookUpTable]
                    lookUpTable = str(rowVal)
                else:
                    lookUpTable = ""
            
            rowVal = row[lookUpCol]

            isLookUpColValBlank = "false"
            if str(rowVal) == None or str(rowVal) == '' or str(rowVal) == 'NaT':
                rowVal = str('')
                isLookUpColValBlank = "true"

            if self.lookupTableMap == None or not ""+str(lookUpTable) in self.lookupTableMap:
                self.setLookUpData( lookUpTable, validateLookup, client_DBConnection)

            if validateLookup == 'true':
                lookUpTable = lookUpTable + '_validate'

            dfLookUpDet = None
            resDataType = str('')
            isdfLookUpDet = "false"
            if self.lookupTableMap != None and ""+str(lookUpTable) in self.lookupTableMap:
                lookUpHeadDetMap = self.lookupTableMap[""+str(lookUpTable)]

                dfLookUpDet = lookUpHeadDetMap["lookUpDet"]

                resDataType = lookUpHeadDetMap["resDataType"]

                keyDataType = lookUpHeadDetMap["keyDataType"]
                if keyDataType == 'N':
                    rowVal = pd.to_numeric(rowVal)

                query = lookUpHeadDetMap["queryString"]
                if isLookUpDateColValBlank == "false" and isLookUpColValBlank == "false":
                    dfLookUpDet = dfLookUpDet.query( query )
                    isdfLookUpDet = "true"
                else:
                    isdfLookUpDet = "false"
            else:
                isdfLookUpDet = "false"

            if  isdfLookUpDet == "false" or dfLookUpDet.empty:
                if resDataType == 'N':
                    dfLookUpDet = 0
                    dfLookUpDet = pd.to_numeric(dfLookUpDet)
                elif resDataType == 'D':
                    dfLookUpDet = str('')
                    dfLookUpDet = pd.to_datetime(dfLookUpDet)
                elif resDataType == 'S':
                    dfLookUpDet = str('')
                else:
                    dfLookUpDet = str('')

            else:
                dfLookUpDet = dfLookUpDet.iloc[0:1,0:1]
                dfLookUpDet = dfLookUpDet.iat[0,0]

                if resDataType == 'N':
                    dfLookUpDet = pd.to_numeric(dfLookUpDet)
                elif resDataType == 'D':
                    dfLookUpDet = pd.to_datetime(dfLookUpDet)
                logger.log(f"Lookup Value:: {dfLookUpDet}")
            return dfLookUpDet
        except Exception as e:
            logger.log(f'\n In getLookUpValue exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = self.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside getLookUpValue : {returnErr}', "0")
            raise str(returnErr)
            
    def getSqlResult(self, row, pool, detail):
        try:
            if self.dbDetails != None:
                if self.dbDetails['DATABASETYPE'] == '1':
                    if self.isPool == 'true':
                        con = self.pool.acquire()
                    else:
                        con = self.pool
                elif self.dbDetails['DATABASETYPE'] == '2' or self.dbDetails['DATABASETYPE'] == '3' :
                    con = self.pool

            colDbType = detail['col_datatype']
            self.sqlQuery = self.detSql
            splitColValue = None
            dfSqlResult = None
            newSql = None

            if self.sqlQuery.find("?") != -1:
                newSql = self.sqlQuery.split(':')
                self.sqlQuery = newSql[0]
                sqlInput = newSql[1].lower()
                columns = sqlInput.split(',')
                self.buildSqlQuery(self.sqlQuery, columns, row)

            if ' update ' in self.sqlQuery or ' delete ' in self.sqlQuery:
                return self.getErrorXml("Invalid SQL" , "Update and Delete operations are not allowed in Visual.")
            else:
                logger.log(f"self.sqlQuery:: {self.sqlQuery}","0")
                dfSqlResult = pd.read_sql(
                    self.sqlQuery, con
                )

            if not dfSqlResult.empty:
                dfSqlResult = dfSqlResult.iloc[0:1,0:1]
                dfSqlResult = dfSqlResult.iat[0,0]
            else:
                if colDbType == 'N':
                    dfSqlResult = 0
                    dfSqlResult = pd.to_numeric(dfSqlResult)
                elif colDbType == 'D':
                    dfSqlResult = str('')
                    dfSqlResult = pd.to_datetime(dfSqlResult)
                else:
                    dfSqlResult = str('')
                    
            return dfSqlResult
        except Exception as e:
            logger.log(f'\n In getSqlResult exception stacktrace : ', "1")
            descr = str(e)
            raise Exception(f"{descr}") 

        finally:
            try:
                if con:
                    if self.dbDetails != None:
                        if self.dbDetails['DATABASETYPE'] == '1':
                            if self.isPool == 'true' :
                                self.pool.release(con)
                        
            except Exception as e :
                logger.log(f'\n In getSqlResult exception stacktrace : ', "1")
                trace = traceback.format_exc()
                descr = str(e)
                returnErr = self.getErrorXml(descr, trace)
                logger.log(f'\n Print exception returnSring inside getSqlResult : {returnErr}', "0")
                return str(returnErr)

    def buildSqlQuery(self, sql, columns, row):
        ctr = 0
        rowVal = ""
        logger.log(f"\nsql:::{sql}  /ncolumns:::{columns}  /nrow:::{row} ","0")
        if sql.find('?') != -1 and len(columns) > 0:
            indexPos = sql.find('?')
            
            if columns[ctr].lower().startswith("criteria"):
                logger.log("inside criteria","0")
                criteriaColName = columns[ctr][columns[ctr].find('.')+1:]  # slice
                logger.log(f"criteriaColName:::{criteriaColName}","0")
                criteriaColName = criteriaColName.upper()
                logger.log(f"criteriaColName upper():::{criteriaColName}","0")
                logger.log(f"self.argumentList:::{self.argumentList}","0")
                
                if criteriaColName in self.argumentList.keys():
                    if self.argumentList.get(criteriaColName) != None:
                        rowVal = self.argumentList[criteriaColName]   
                else:
                    logger.log(f"inside buildSqlQuery else column not found ","0")
                    descr = "Invalid column name : " + criteriaColName
                    raise Exception(descr)
                    
                logger.log(f"rowVal:::{rowVal}","0")

            else:
                rowVal = str(row[columns[ctr].strip()])
                
            if str(rowVal) == None or str(rowVal) == 'None':
                rowVal = str('')
                
            if len(sql) - 1 != indexPos:
                sql = sql[:indexPos] + "'" + rowVal + "'" + sql[indexPos+1:]
                
            else:
                sql = sql[:-1] + "'" + rowVal + "'"
                
            columns.pop(ctr)
            self.sqlQuery = str(sql)
            if(sql.find('?') != -1):
                self.buildSqlQuery(sql, columns, row)

    def getErrorXml(self, descr, trace, message=""):

        if  self.currentDetData:
            colName = self.currentDetData['col_name']
            calcType = self.currentDetData['calc_type']
            
            errorXml = '''<Root>
                            <Header>
                                <editFlag>null</editFlag>
                            </Header>
                            <Errors>
                                <error column_name="'''+colName+'''" type="E" column_value="'''+calcType+'''">
                                    <message><![CDATA[Error occurred in calculation of '''+colName+''' column for column type '''+calcType+''']]></message>
                                    <description><![CDATA['''+descr+''']]></description>
                                    <trace><![CDATA['''+trace+''']]></trace>
                                    <type>E</type>
                                    <errorId>'''+self.errorId+'''</errorId>
                                </error>
                            </Errors>
                        </Root>'''

            return errorXml
        else:
            errorXml = '''<Root>
                            <Header>
                                <editFlag>null</editFlag>
                            </Header>
                            <Errors>
                                <error type="E">
                                    <message><![CDATA['''+message+''']]></message>
                                    <description><![CDATA['''+descr+''']]></description>
                                    <trace><![CDATA['''+trace+''']]></trace>
                                    <type>E</type>
                                </error>
                            </Errors>
                        </Root>'''

            return errorXml

    def udf_divide(self, x, y):
        return x/y

    def udf_round(self, value, decimal):
        return round(value, decimal)

    def udf_if(self, df,condition,true_exp, false_exp):
        udf_divide = partial(self.udf_divide)
        udf_round = partial(self.udf_round)
        return np.where(df.eval(condition),df.eval(true_exp),df.eval(false_exp))

    def firstRowColVal(self, df):
        df = df.iloc[0:1,0:1]
        df = df.iat[0,0]
        return df
        
    def setLookUpData(self,lookUpTable,validateLookup, con): #pool):
        try:
            # Commented by SwapnilB to handle the case - Add provision for calculation type Lookup to connect to separate client specific database on [ 18-Sept-24 ] [START]

            #con = ""
            # if self.dbDetails != None:
            #     if self.dbDetails['DATABASETYPE'] == '1':
            #         if self.isPool == 'true':
            #             con = self.pool.acquire()
            #         else:
            #             con = self.pool
            #     elif self.dbDetails['DATABASETYPE'] == '2' or self.dbDetails['DATABASETYPE'] == '3' :
            #         con = self.pool
            #     else :
            #         con = self.pool
            
            # Commented by SwapnilB to handle the case - Add provision for calculation type Lookup to connect to separate client specific database on [ 18-Sept-24 ] [END]

            logger.log(f"\n\n Lookup Connection ::: {con} ") 
            dfLookUpHead = None
            dfLookUpDet = None
            queryString = ''

            lookUpSql = "SELECT LOOKUP_TYPE, KEY_DATA_TYPE, RESULT_DATA_TYPE FROM GENLOOKUP WHERE LOOKUP_TABLE = '" + lookUpTable + "'"
            logger.log(f" LookUp Sql ::: {lookUpSql} ") 
            dfLookUpHead = pd.read_sql ( lookUpSql, con )

            lookUpDetSql = "SELECT RESULT_VALUE, MIN_KEY_VALUE, MAX_KEY_VALUE, EFF_FROM, VALID_UPTO FROM GENLOOKUP_TABLE WHERE LOOKUP_TABLE = '" + lookUpTable + "'"    
            logger.log(f" LookUp Data Sql ::: {lookUpDetSql} \n\n ") 
            dfLookUpDet = pd.read_sql( lookUpDetSql, con )

            rowVal = ''
            rowVal = str(rowVal)

            lookUpDateColVal = ''
            lookUpDateColVal = str(lookUpDateColVal)

            if not dfLookUpHead.empty and not dfLookUpDet.empty:
                # ADDED by YASH S. to do all columns of df in uppercase for postgres condition [START]
                dfLookUpHead.columns = dfLookUpHead.columns.str.upper()
                dfLookUpDet.columns = dfLookUpDet.columns.str.upper()
                # ADDED by YASH S. to do all columns of df in uppercase for postgres condition [END]

                resDataType = dfLookUpHead['RESULT_DATA_TYPE'].iloc[0]
                lookUpType = dfLookUpHead['LOOKUP_TYPE'].iloc[0]
                keyDataType = dfLookUpHead['KEY_DATA_TYPE'].iloc[0]

                if lookUpType == 'F':
                    if keyDataType == 'N':
                        dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]] = dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]].apply(pd.to_numeric)
                        rowVal = pd.to_numeric(rowVal)

                    elif keyDataType == 'D':
                        dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]] = dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]].apply(pd.to_datetime)
                        rowVal = pd.to_datetime(rowVal)

                    queryString = '@rowVal == MIN_KEY_VALUE'
                elif lookUpType == 'S':
                    if keyDataType == 'N':
                        dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]] = dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]].apply(pd.to_numeric)
                        rowVal = pd.to_numeric(rowVal)

                    elif keyDataType == 'D':
                        dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]] = dfLookUpDet[["MIN_KEY_VALUE", "MAX_KEY_VALUE"]].apply(pd.to_datetime)
                        rowVal = pd.to_datetime(rowVal)

                if validateLookup == 'true':
                    dfLookUpDet[["EFF_FROM", "VALID_UPTO"]] = dfLookUpDet[["EFF_FROM", "VALID_UPTO"]].apply(pd.to_datetime)
                    lookUpDateColVal = pd.to_datetime(lookUpDateColVal)
                    if lookUpType == 'S':
                        queryString = '(@rowVal >= MIN_KEY_VALUE & @rowVal <= MAX_KEY_VALUE) & (@lookUpDateColVal >= EFF_FROM & @lookUpDateColVal <= VALID_UPTO)'
                    else:
                        queryString = '(@rowVal == MIN_KEY_VALUE) & (@lookUpDateColVal >= EFF_FROM & @lookUpDateColVal <= VALID_UPTO)'
                    lookUpTable = lookUpTable + '_validate'
                else:
                    if lookUpType == 'S':
                        queryString = '@rowVal >= MIN_KEY_VALUE & @rowVal <= MAX_KEY_VALUE'
                    else:
                        queryString = '@rowVal == MIN_KEY_VALUE'

                lookUpHeadDetMap = {}
                lookUpHeadDetMap["lookUpDet"] = dfLookUpDet
                lookUpHeadDetMap["resDataType"] = resDataType
                lookUpHeadDetMap["keyDataType"] = keyDataType
                lookUpHeadDetMap["queryString"] = queryString
                self.lookupTableMap[lookUpTable] = lookUpHeadDetMap
                logger.log(f" lookupTableMap ::: {self.lookupTableMap} \n")
        except Exception as e:
            logger.log(f'\n In setLookUpData exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = self.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside setLookUpData : {returnErr}', "0")
            raise str(returnErr)

    def is_json(self,a):                                               
        try:
            json.loads(a)
        except Exception as e:
            return False
        return True

    def to_xml(self, dt_frame):
        def row_xml(row):
            xml = ['<Detail>']
            for i, col_name in enumerate(row.index):
                xml.append('  <{0}>{1}</{0}>'.format(col_name, row.iloc[i]))
            xml.append('</Detail>')
            return '\n'.join(xml)
        res = '\n'.join(dt_frame.apply(row_xml, axis=1))
        return(res)

    def format_num(self, str):
        return "text-align:right !important"

    def getTableHTML(self,pivot):
        if self.group_style :
            pivot_style = (pivot).reset_index(drop=True).style.applymap(self.format_num, subset=self.val).format('{:.3f}', na_rep='', subset=self.val)
            
        else:
            pivot_style = (pivot).style.applymap(self.format_num, subset=self.val).format('{:.3f}', na_rep='', subset=self.val)
        
        pivot_style = (pivot_style).set_table_attributes('class= "insight_html_table"')
        html = pivot_style.render()
        # logger.log(f'\n html inside method pivotstyle  : {type(html), html}', "0")                      

        col_dtype = dict(zip((self.calculationData['columnHeading']).split(','), json.loads(self.calculationData['columndataTypes']).values()))
        
        if self.advancedFormatting:
            for i in self.advancedFormatting.keys():
                if col_dtype[i] == 'string' :
                    pivot_style = pivot_style.set_properties(**{'background-color': self.advancedFormatting[i]}, subset=[i])
                else:
                    pivot_style = pivot_style.background_gradient(cmap=self.advancedFormatting[i], subset=[i])
                    
        html = "<h3 class='tableHeading'>"+ self.updateTableHeading(self.tableHeading, self.argumentList)+"</h3>" +  pivot_style.render()
        return html
    
    def storePickleFile(self, df, userId, editorId, visualId, transpose):
        dir = 'Pickle_files'
        if not os.path.exists(dir):
            os.makedirs(dir)
        
        filename= str(userId) +'_' + str(editorId) + '_' + str(visualId) + '_' + transpose
        df.to_pickle(dir + '/' + filename + '.pkl')
        if os.path.isfile(dir +'/' + filename + '.pkl'):
            logger.log('\n' + transpose + ' Pickle file created','0')   
        else:
            logger.log('\n' + transpose + ' Pickle file created','0')
        return dir +'/' + filename + '.pkl'
    
    def readPickleFile(self, userId, editorId, visualId, transpose):
        dir = 'Pickle_files'
        if os.path.exists(dir):
            filename= str(userId) +'_' + str(editorId) + '_' + str(visualId) + '_' + transpose
            if os.path.isfile(dir +'/' + filename + '.pkl'):
                df_obj = pd.read_pickle(dir +'/' + filename + '.pkl')
                return df_obj
        else:
            return self.getErrorXml( dir + "directory does not exist","Pickle file directory not found" )  
    
    def replace(self, tableHeading, argumentList):
        left, right = tableHeading[:tableHeading.find("@")], tableHeading[tableHeading.find("@"):]
        key = right[:right.find(" ")]
        
        for i in argumentList.keys():
            if (key[1:]) in i:
                tableHeading = re.sub(key, argumentList[i], tableHeading) 
                break
        if "@" in tableHeading:
            tableHeading = self.replace(tableHeading, argumentList)
        
        return tableHeading

    def updateTableHeading(self, tableHeading, argumentList):    
        if "@" in tableHeading:
            tableHeading = self.replace(tableHeading, argumentList)
        else:
            return tableHeading

        return tableHeading

    def contribution(self, x):
        return (x / x.sum()) * 100
            
    def predict(self, textColumn, modelName,  modelType, modelScope):
        logger.log(f"inside predict_sentiment","0")
        modelType = modelType.lower().replace(" ","_")
        if 'enterprise' in self.calculationData.keys():
            if self.calculationData.get('enterprise') != None:
                enterprise = self.calculationData['enterprise']

        if modelType == "sentiment_analytics":
            sentimentAnalytics = SentimentAnalytics()
            result = sentimentAnalytics.prediction(textColumn, modelName, modelType, modelScope, enterprise)
            
        elif modelType == "classification":
            classification = Classification()
            result = classification.prediction(textColumn, modelName, modelType, modelScope, enterprise)
            
        elif modelType == "intent_classification":
            intentClassifier = IntentClassification()
            result = intentClassifier.prediction(textColumn, modelName, modelType, modelScope, enterprise)
            
        else:
            raise Exception(f"Invalid model name : '{modelType}'")
        
        return result 

    def translate(self,colname_value,translate_to=None):
        logger.log(f'\n Print time for before executing Translate function : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
        ls=[]
        for i in colname_value:
            if i != None:
                logger.log(f'\n Print time for before executing Translate OPERATION : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")
                ls.append(mt.translate(i, to_language=translate_to))
                logger.log(f'\n Print time for after executing Translate OPERATION : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")          
            else:
                ls.append("")
        logger.log(f'\n translate() final list :::{ls}')                  
        logger.log(f'\n Print time for after executing Translate function : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "0")          
        return ls

    def removeOperator(self, argumentList):
        with_OperatorLst=[]
        without_OperatorLst=[]
        without_Operator = ""
        
        with_OperatorLst = [key[:(key.rfind("_")+1)] for key in argumentList.keys()]
        logger.log(f"with_OperatorLst:: {with_OperatorLst}", "0")
        for i in range(len(with_OperatorLst)):
            if "_like_" in with_OperatorLst[i]:
                logger.log(f"inside _like_ :: {with_OperatorLst[i]}", "0")
                without_Operator = with_OperatorLst[i].replace("_like_","")
            
            elif "_between_" in with_OperatorLst[i]:
                logger.log(f"inside _between_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace("_between_","")
            
            elif "_in_" in with_OperatorLst[i]:
                logger.log(f"inside _in_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace("_in_","")
            
            elif "!=_" in with_OperatorLst[i]:
                logger.log(f"inside !=_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace("!=_","")
            
            elif ">_" in with_OperatorLst[i]:
                logger.log(f"inside >_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace(">_","")
            
            elif ">=_" in with_OperatorLst[i]:
                logger.log(f"inside >=_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace(">=_","")
            
            elif "<_" in with_OperatorLst[i]:
                logger.log(f"inside >=_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace("<_","")
            
            elif "<=_" in with_OperatorLst[i]:
                logger.log(f"inside >=_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace("<=_","")
            
            elif "=_" in with_OperatorLst[i]:
                logger.log(f"inside >=_ :: {with_OperatorLst[i]}","0")
                without_Operator = with_OperatorLst[i].replace("=_","")
            
            without_OperatorLst.append(without_Operator)
        
        logger.log(f"without_OperatorLst:: {without_OperatorLst}","0")
        
        final_argumentList = dict(zip(without_OperatorLst, list(argumentList.values())))
        logger.log(f"\nargumentList:: {argumentList} \n\nfinal_argumentList:: {final_argumentList}","0")
        return final_argumentList       
    
