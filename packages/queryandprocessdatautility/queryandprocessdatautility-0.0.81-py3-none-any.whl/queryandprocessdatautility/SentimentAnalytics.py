import os
import json
import pickle
import datetime
import traceback
import pandas as pd 
from tensorflow import keras
import commonutility as common
import loggerutility as logger
from tensorflow.keras.models import Model
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.initializers import Constant
from tensorflow.keras.layers import Embedding, serialize
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences 
from tensorflow.keras.layers import Dense, Input, GlobalMaxPooling1D
from tensorflow.keras.layers import LSTM,Dense, Dropout, SpatialDropout1D
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Embedding, Flatten

class SentimentAnalytics:

    modelScope = 'G'
    
    def trainData(self, jsonData):
        try:
            flag = ""
            modelType = ""
            input_column_name = ""
            train_column_name = ""
            logger.log(f"inside SentimentAnalytics() class","0")
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
            
            if modelType == 'sentiment_analytics':
                logger.log(f"Inside sentimentTraining model","0")      
                review_df = df[colNamesLst]
                logger.log(f'\nreview_df.shape : {review_df.shape}',"0")
                review_df = review_df[review_df[colNamesLst[1]] != "neutral"]  
                review_df[colNamesLst[1]].value_counts()
                sentiment_label=review_df[colNamesLst[1]].factorize()  
                tweet = review_df[colNamesLst[0]].values
                tokenizer = Tokenizer(num_words=5000)
                tokenizer.fit_on_texts(tweet)
                encoded_docs = tokenizer.texts_to_sequences(tweet)     
                vocab_size = len(tokenizer.word_index) + 1
                padded_sequence = pad_sequences(encoded_docs, maxlen=200)
                embedding_vector_length = 32
                model = Sequential()
                model.add(Embedding(vocab_size, embedding_vector_length, input_length=200))
                model.add(SpatialDropout1D(0.25))
                model.add(LSTM(50, dropout=0.5, recurrent_dropout=0.5))
                model.add(Dropout(0.2))
                model.add(Dense(1, activation='sigmoid'))
                model.compile(loss='binary_crossentropy',optimizer='adam', metrics=['accuracy'])
                model.fit(padded_sequence,sentiment_label[0], epochs=3, validation_split=0.2, batch_size=32)

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
            modelFilePath = modelPath + ".keras"  # change code for migration for python3.11 version (18-June-2024)
            tokenizerDictionaryPath = modelPath + '/tokenizer.dictionary'  
            logger.log(f"modelPath::{modelFilePath}", "0")
            model.save(modelFilePath)
            with open(tokenizerDictionaryPath, 'wb') as tokenizer_dictionary_file:
                pickle.dump(tokenizer, tokenizer_dictionary_file)
                flag = "SUCCESSFUL"
                logger.log("Sentiment Model has been trained and saved successfully.", "0")

            result= common.createModelScope(self.modelScope, modelType, modelName, enterprise)
            logger.log(f"ModelScope result::{result}","0")
            
        return flag
    
    def prediction(self, textColumn, modelName,  modelType, modelScope, enterprise ):
        logger.log(f'\n Inside SentimentAnalytics class prediction() ', "0")
        logger.log(f'\n LOCALS():::\t{locals()}\n', "0")
        predicted_Sentiment=None
        predicted_label_lst=[]
        
        try: 
            modelPath = common.getTraineModelPath(modelType, modelName, modelScope, enterprise) 
            modelFilePath = modelPath + ".keras"
            logger.log(f"modelFilePath: {modelFilePath}")
            tokenizerDictionaryPath = modelPath + '/tokenizer.dictionary'
            logger.log(f"modelPath:::{modelPath} {type(modelPath)}","0")
            
            if modelType == 'sentiment_analytics':
                with open(tokenizerDictionaryPath, 'rb') as config_dictionary_file:
                    tokenizer = pickle.load(config_dictionary_file)
                    logger.log(f"tokenizer:::{tokenizer} {type(tokenizer)}","0")
                    logger.log(f'\nSentiment prediction start time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    loaded_Model = keras.models.load_model(modelFilePath) 
                    for i,j in textColumn.iteritems():
                        tw = tokenizer.texts_to_sequences([j])
                        tw = pad_sequences(tw, maxlen=200)
                        prediction = int(loaded_Model.predict(tw).round().item())
                        predicted_label = "Positive" if prediction==0 else "Negative" 
                        predicted_label_lst.append(predicted_label)
            
           
            logger.log(f'\nSentiment prediction end time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
            predicted_Sentiment = pd.DataFrame(predicted_label_lst, columns=['predicted_sentiment'])
            logger.log(f"predicted_Sentiment:::{predicted_Sentiment} {type(predicted_Sentiment)}","0")

        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)

        return predicted_Sentiment


