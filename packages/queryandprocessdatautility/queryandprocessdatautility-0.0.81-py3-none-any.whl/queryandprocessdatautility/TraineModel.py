import json
import traceback
from flask import request
import loggerutility as logger
import commonutility as common
from .Classification import Classification
from .SentimentAnalytics import SentimentAnalytics
from .IntentClassification import IntentClassification
from openAIInsight import  OpenAI_PineConeVector
from .ProductIdentification import ProductIdentification
from openAIInsight import Weaviate

class TraineModel:

    def trainemodel(self):
        returnJson      = {}
        returnJsonStr   = ""
        try:
            result = ""
            logger.log(f"inside trainemodel()","0")
            jsonData = request.get_data('jsonData', None)
            jsonData = json.loads(jsonData[9:])
            logger.log(f"jsonData: {jsonData}{type(jsonData)}","0")
            modelType = jsonData['modelType'].lower().replace(" ","_")    
            
            if modelType == 'sentiment_analytics':
                sentimentAnalytics = SentimentAnalytics()
                result = sentimentAnalytics.trainData(jsonData)

            elif modelType == 'classification':
                classification = Classification()
                result = classification.trainData(jsonData)
            
            elif modelType == "intent_classification":
                intentClassifier = IntentClassification()
                result = intentClassifier.trainData(jsonData)

            elif modelType == "product_identification":
                productIdentification = ProductIdentification()
                result = productIdentification.trainData(jsonData)
            
            elif modelType == "pinecone_vector":
                pineConeVector = OpenAI_PineConeVector()
                result = pineConeVector.trainData(jsonData)

            elif modelType == "weaviatevector":
                weaviatetrain = Weaviate()
                result = weaviatetrain.traindata(jsonData)
                
            else:
                logger.log(f'Invalid Model Type',"0")
                raise Exception(f"Ivalid Model Type:{modelType}")

        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)
            
        if "SUCCESSFUL" in result :
            returnJson["status"]    =  "SUCCESS"
            returnJson["message"]   =  modelType.upper() + " Model has been trained and saved successfully." 
        else:
            returnJson["status"]    =  "FAILURE"
            returnJson["message"]   =  modelType.upper() + " Model has failed to train."

        returnJsonStr = str(returnJson)
        logger.log(f'\n FINAL returnJsonStr : {returnJsonStr}\n', "0")
        
        return str(returnJsonStr)
            
