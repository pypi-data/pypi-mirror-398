import json
import traceback
import pandas as pd
import loggerutility as logger
import commonutility as common
from rasamodelandtrain import Rasa

class ProductIdentification:

    def trainData(self, jsonData):

        try:
            flag =""
            modelType = ""
            input_column_name = ""
            train_column_name = ""
            logger.log(f"inside SentimentAnalytics() class","0")
            logger.log(f"jsonData: {jsonData}{type(jsonData)}","0")
            modelType = jsonData['modelType'].lower().replace(" ","_")    
            jsonToDf  = jsonData['modelJsonData']
            parsed_json = (json.loads(jsonToDf))
            df = pd.DataFrame(parsed_json[1:])
            
            modelParameter =json.loads(jsonData['modelParameter'])
            if "input_column_name" in modelParameter and modelParameter["input_column_name"] != None:
                input_column_name = modelParameter['input_column_name']

            if "train_column_name" in modelParameter and modelParameter["train_column_name"] != None: 
                train_column_name = modelParameter['train_column_name']
            
            logger.log(f"\n\ninput_column_name:::{input_column_name}\ttrain_column_name:::{train_column_name}\n\n","0")    
            if 'model_name' not in modelParameter.keys() or modelParameter["model_name"] == None:
                modelName = modelType +"_training_model"  
            else:
                modelName = modelParameter['model_name'].lower().replace(" ","_")
                
            self.modelScope = "global" if jsonData['modelScope'] == "G" else "enterprise"   
            enterprise = jsonData['enterprise'].lower()     
            
            if "training_mode" in modelParameter or modelParameter["training_mode"] == None:
                mode=modelParameter["training_mode"] 
                parsed_json=parsed_json[1:]  
                logger.log(f"parsed_json from index 1: {parsed_json}{type(parsed_json)}","0")
                modelType=modelType.lower()
                rasa = Rasa()
                result = rasa.create_model(enterprise, mode, parsed_json, self.modelScope, modelName, modelType, modelParameter)
                logger.log(f"rasa result : {result}","0")
        
        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)

        else:
            result=""
            
            flag="SUCCESSFUL"
            result= common.createModelScope(self.modelScope, modelType, modelName, enterprise)
            logger.log(f"ModelScope result::{result}","0")

        return flag
