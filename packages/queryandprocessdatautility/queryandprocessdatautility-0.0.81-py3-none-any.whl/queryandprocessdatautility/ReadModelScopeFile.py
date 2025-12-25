import os
import json
import pickle
import datetime
import traceback
import pandas as pd 
from flask import request
import commonutility as common
import loggerutility as logger

class ReadModelScopeFile:

    def getModelScopeList(self):
        try:
            enterprise=""
            listreturn = {}
            modelScopeList=[]
            descr=""
            filePath="/proteus-sense/trained_model/modelScope.json"
            jsonData = (request.get_data('jsonData', None)).decode("utf-8")[9:]
            logger.log(f"jsonData::{jsonData}{type(jsonData)}","0")
            jsonData = json.loads(jsonData)
            modelType = jsonData["function_name"].lower().replace(" ","_")
            modelScope = "global" if jsonData["model_scope"]=="G" else "enterprise"
            
            if 'enterprise' in jsonData.keys():
                if jsonData['enterprise'] != None and jsonData['enterprise'] != "":
                    enterprise = jsonData['enterprise'].lower()
                    logger.log(f"enterprise::{enterprise}{type(enterprise)}","0")

            if os.path.exists(filePath) and len(open(filePath).read())!=0 :
                with open(filePath, "r") as file:
                    fileData = json.loads(file.read())
                    if modelType in fileData.keys():
                        if modelScope == "global":
                            if modelScope in fileData[modelType]:
                                modelScopeList = fileData[modelType][modelScope]
                            else:
                                descr = f'''For the model scope {modelScope.title()} and model type {modelType.title().replace("_"," ")} there is no trained model found.'''
                        else:
                            if modelScope in fileData[modelType]:
                                if enterprise in fileData[modelType][modelScope]:
                                    modelScopeList = fileData[modelType][modelScope][enterprise]
                                else:
                                    descr = f'''For the model scope {modelScope.title()} and  and model type {modelType.title().replace("_"," ")} there is no trained model found.'''
                            else:
                                descr = f'''For the model scope {modelScope.title()} and model type {modelType.title().replace("_"," ")} there is no trained model found.'''
                    else:
                        descr = f'''For the model scope {modelScope.title()} and model type {modelType.title().replace("_"," ")} there is no trained model found.'''
                        
                    logger.log(f"\nmodelScopeList::{modelScopeList}{type(modelScopeList)}","0")
                    listreturn['modelname'] = modelScopeList
                    logger.log(f"\nlistreturn::{listreturn}{type(listreturn)}","0")
            else:
                descr = f'''For the model scope {modelScope.title()} and model type {modelType.title().replace("_"," ")} there is no trained model found.'''    
            if descr != "":
                returnErr = common.getErrorXml(descr, "ERROR")
                return returnErr 
            else:
                return json.dumps(listreturn)
                
        except Exception as e:
            logger.log(f"Exception in getModelScopeAPI:: {e}","0")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside getModelScopeList : {returnErr}', "0")
            return str(returnErr)
