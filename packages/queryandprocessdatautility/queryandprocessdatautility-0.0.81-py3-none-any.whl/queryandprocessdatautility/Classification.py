import os
import json
import pickle
import joblib
import traceback
import pandas as pd 
import commonutility as common
import loggerutility as logger
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

class Classification:

    modelScope = 'G'
    
    def trainData(self, jsonData):
        
        try:
            flag =""
            modelType = ""
            input_column_name = ""
            train_column_name = ""
            logger.log(f"inside Classification class ","0")
            logger.log(f"jsonData: {jsonData}{type(jsonData)}","0")
            modelType = jsonData['modelType'].lower().replace(" ","_")    # Added by SwapnilB for replacing folder name with "space" to "_"   
            jsonToDf = jsonData['modelJsonData']
            parsed_json = (json.loads(jsonToDf))
            df = pd.DataFrame(parsed_json[1:])
            
            modelParameter =json.loads(jsonData['modelParameter'])
            if "input_column_name" in modelParameter and modelParameter["input_column_name"] != None:
                input_column_name = modelParameter['input_column_name']

            if "train_column_name" in modelParameter and modelParameter["train_column_name"] != None: 
                train_column_name = modelParameter['train_column_name']
            
            logger.log(f"\n\ninput_column_name:::{input_column_name}\ttrain_column_name:::{train_column_name}\n\n","0")    
            colNamesLst=[input_column_name, train_column_name]
            if 'model_name' not in modelParameter.keys() or modelParameter["model_name"] == None:
                modelName = modelType +"_training_model"  
            else:
                modelName = modelParameter['model_name'].lower().replace(" ","_")
                
            self.modelScope = "global" if jsonData['modelScope'] == "G" else "enterprise"   
            enterprise = jsonData['enterprise'].lower()     

            review_df = df[colNamesLst]
            train_column_name=review_df[colNamesLst[1]]
            input_column_name = review_df[colNamesLst[0]]
            X_train, X_test, y_train, y_test = train_test_split(input_column_name, train_column_name, test_size=10,
                                                random_state=10)
            svm = Pipeline([
                ('vect', CountVectorizer()),
                ('tfidf', TfidfTransformer()),
                ('clf', LinearSVC()),
            ])
            svm.fit(X_train, y_train)
            logger.log(f'Model Created',"0")

        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)


        else:
            # will execute only if there is no exception
            result=""
            modelPath = common.getTraineModelPath(modelType, modelName, self.modelScope, enterprise)
            joblib.dump(svm, modelPath +'/' + modelName +'.pkl')
            flag = "SUCCESSFUL"
            logger.log("Classification Model has been trained and saved successfully.","0")

            result= common.createModelScope(self.modelScope, modelType, modelName, enterprise)
            logger.log(f"ModelScope result::{result}","0")

        return flag    
    
    def prediction(self, textColumn, modelName,  modelType, modelScope, enterprise):
        try:

            modelPath = common.getTraineModelPath(modelType, modelName, modelScope, enterprise)

            if modelType == "classification":
                iterater = []
                predictmodel = joblib.load(modelPath +"/" +modelName+".pkl")
                logger.log(f"predictmodel : {predictmodel} {str(type(predictmodel))}","0")
                return predictmodel.predict(textColumn)
        
        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)
