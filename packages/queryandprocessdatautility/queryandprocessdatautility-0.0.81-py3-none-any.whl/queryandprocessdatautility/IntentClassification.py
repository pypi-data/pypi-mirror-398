import os
import json
import pickle
import traceback
import pandas as pd 
import numpy as np
from tensorflow import keras
import loggerutility as logger
import commonutility as common
from tensorflow.keras.models import Model
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.initializers import Constant
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences 
from tensorflow.keras.layers import Dense, Input, GlobalMaxPooling1D
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Embedding, Flatten

class IntentClassification:
    
    modelScope = 'G'
    
    def trainData(self, jsonData):

        try:
            flag =""
            modelType = ""
            input_column_name = ""
            train_column_name = ""
            logger.log(f"inside IntentClassification()","0")
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
            logger.log(f"colNamesLst::{colNamesLst}", "0")
            review_df.dropna(inplace=True)
            labels=review_df[colNamesLst[1]].factorize()  # creates 1-D Array
            commands=review_df.copy()
            commands[colNamesLst[1]]=labels[0]
            int_label = list(labels[0])
            str_label = list(labels[1])
            set_label=(set(int_label))
            predicted_label=dict(zip(set_label, str_label))
            logger.log(f"predicted_label::{predicted_label}","0")

            MAX_SEQUENCE_LENGTH = 50
            MAX_NUM_WORDS = 5000
            tokenizer = Tokenizer(num_words=MAX_NUM_WORDS)
            tokenizer.fit_on_texts(commands[colNamesLst[0]])
            sequences = tokenizer.texts_to_sequences(commands[colNamesLst[0]])
            word_index = tokenizer.word_index
            logger.log(f"Found {len(word_index)} unique tokens. ","0")
            data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)
            labels = to_categorical(np.asarray(commands[colNamesLst[1]]))
            logger.log(f"Shape of data tensor: {data.shape}","0")
            logger.log(f"Shape of label tensor: {labels.shape}","0")

            VALIDATION_SPLIT = 0.1
            indices = np.arange(data.shape[0])
            np.random.shuffle(indices)
            data = data[indices]
            labels = labels[indices]
            num_validation_samples = int(VALIDATION_SPLIT * data.shape[0])
            x_train = data[:-num_validation_samples]
            y_train = labels[:-num_validation_samples]
            x_val = data[-num_validation_samples:]
            y_val = labels[-num_validation_samples:]
            
            EMBEDDING_DIM = 60
            num_words = min(MAX_NUM_WORDS, len(word_index) + 1)
            embedding_layer = Embedding(num_words,EMBEDDING_DIM,input_length=MAX_SEQUENCE_LENGTH,trainable=True)

            sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
            embedded_sequences = embedding_layer(sequence_input)
            x = Conv1D(64, 3, activation='relu')(embedded_sequences)
            x = Conv1D(64, 3, activation='relu')(x)
            x = MaxPooling1D(2)(x)
            x=Flatten()(x)
            x = Dense(100, activation='relu')(x)
            preds = Dense(y_train.shape[1], activation='softmax')(x)
            model = Model(sequence_input, preds)
            model.compile(loss='categorical_crossentropy',optimizer='rmsprop',metrics=['accuracy'])
            model.summary()

            for i in range (1,50):
                model.fit(x_train, y_train,batch_size=50, epochs=3, validation_data=(x_val, y_val))
            scores = model.evaluate(x_val, y_val, verbose=0)
            logger.log(f"scores: {scores}","0")

        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)
        
        else:
            result=""
            
            modelPath = common.getTraineModelPath(modelType, modelName, self.modelScope, enterprise)
            model.save(modelPath)     
            with open(modelPath +'/tokenizer.dictionary', 'wb') as tokenizer_dictionary_file:
                pickle.dump(tokenizer, tokenizer_dictionary_file)
            with open(modelPath +'/label.dictionary', 'wb') as label_dictionary_file:
                pickle.dump(predicted_label, label_dictionary_file)
                flag = "SUCCESSFUL"
                logger.log("Intent Model has been trained and saved successfully.","0")
            
            result= common.createModelScope(self.modelScope, modelType, modelName, enterprise)
            logger.log(f"ModelScope result::{result}","0")
        
        return flag
    
    def prediction(self, textColumn, modelName,  modelType, modelScope, enterprise ):
        logger.log(f'\n Inside IntentClassification class prediction() ', "0")
        logger.log(f'\n LOCALS():::\t{locals()}\n', "0")
        predicted_Intent=None
        
        try: 
            modelPath = common.getTraineModelPath(modelType, modelName, modelScope, enterprise)
            logger.log(f"modelPath:::{modelPath} {type(modelPath)}","0")
            if modelType == 'intent_classification':
                with open(modelPath +'/tokenizer.dictionary', 'rb') as config_dictionary_file:
                    tokenizer = pickle.load(config_dictionary_file)
                    logger.log(f"tokenizer:{tokenizer}, {type(tokenizer)}","0")
                with open(modelPath +'/label.dictionary', 'rb') as label_dictionary_file:
                    predicted_label = pickle.load(label_dictionary_file)
                    loaded_Model = keras.models.load_model(modelPath )  
                    sequences_new = tokenizer.texts_to_sequences(textColumn)
                    data = pad_sequences(sequences_new, maxlen=50)
                    yprob = loaded_Model.predict(data)
                    yclasses=yprob.argmax(axis=-1)
                    logger.log(f"yclasses{yclasses}","0")
                    res=[predicted_label[i] for i in yclasses]
                    logger.log(f"res:{res}","0")
                    predicted_Intent = pd.DataFrame(res, columns=['predicted_intent'])

        except Exception as e:
            logger.log(f'\n In Training model exception stacktrace : ', "1")
            trace = traceback.format_exc()
            descr = str(e)
            returnErr = common.getErrorXml(descr, trace)
            logger.log(f'\n Print exception returnSring inside Training model : {returnErr}', "0")
            raise str(e)

        return predicted_Intent
