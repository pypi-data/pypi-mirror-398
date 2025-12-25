import loggerutility as logger
import datetime
import json
import pandas as pd 
import numpy as np

class outlierClass:

    def outlierMainFunction(self,calculationData,df):
        try:
            logger.log(f'\nOutlier function start time, {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
            convert = json.loads(calculationData['columndataTypes'])
            string_list = []
            unique_string_list = []
            numeric_list = []
            list1 = []
            length_of_dataset = 0
            
            for k in calculationData['column']:
                colname = k['col_name']
                expression1 = k['calc_expression']
            
            replace1 = expression1.split('(')[-1].replace(")","").replace("'","")      #   To Get The Outlier threshold value
            Split1 = replace1.split(',')
            list1 = []
            for i in Split1:
                list1.append(i.strip().replace(' ',"_").lower())

            Outlier_threshold = list1[-1]
            global da
            for m,i in enumerate(convert):
                if convert[i] == 'string':
                    unique_string_list.append(i)

                elif convert[i] == 'number':
                    numeric_list.append(i)

            if len(unique_string_list) != 0:
                for listval in unique_string_list:
                    if listval in list1:
                        string_list.append(listval)

            if len(string_list) != 0:
                new = df.filter([i for i in string_list], axis=1)
                drop_dataframe = new.drop_duplicates()    #### for drop duplicate value
                drop_dataframe.index = [i for i in range(0,len(drop_dataframe))]   ####   for contine index   
                for i in range(0,len(drop_dataframe)):
                    y = []
                    lis = []
                    indexvaluelist = []
                    valuesofdataframe = [0]
                    logger.log(f'\Outlier New DataFrame creation and finding the same data, start time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    newo =pd.DataFrame(drop_dataframe.iloc[[i]])
                    newo.index=valuesofdataframe
                    k=newo.values
                    newdataframe = newo.copy()                                                                                                                                            
                    newdataframe['marker'] = True
                    joined = pd.merge(new, newdataframe, on=[i for i in new], how='left')
                    val = joined[pd.notnull(joined['marker'])][new.columns]

                    lis = val.index.tolist()
                    logger.log(f'\Outlier New DataFrame creation and finding the same data, end time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    for ind in lis:
                        indexvaluelist.append(ind)
                        y.append(df[numeric_list[0]].values[ind])
                        length_of_dataset = length_of_dataset + 1

                    list_values = self.outlierSearchMethod(y,Outlier_threshold)
                    logger.log(f'\Outlier function return no of outlier values : {len(list_values)}',"0")
                    if len(list_values) != 0:
                        for v in list_values:
                            df.at[indexvaluelist[v],colname] = 1
                    else:
                        for v in indexvaluelist:
                            df.at[v,colname] = 0
                
                logger.log(f'\nOutlier function end time :  {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                df=df.fillna(0)
                return df

            elif len(string_list) == 0:
                y = []
                for num, numbervalue in enumerate(convert):
                    if numbervalue == numeric_list[0]:
                        for numbervalue in range(len(df)):
                            y.append(df[numeric_list[0]].values[numbervalue])

                logger.log(f'\nForcast function process start time : 145 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                list_values = self.outlierSearchMethod(y,Outlier_threshold)
                logger.log(f'\Outlier function return no of outlier values : {len(list_values)}',"0")
                if len(list_values) != 0:
                    for listvalues in list_values:
                        df.at[listvalues,colname] = 1
                else:
                    df[colname] = 0
                
                df=df.fillna(0)
                return df
        except Exception as e:
            return str(e)


    def outlierSearchMethod(self,datavalue, threshold):
        logger.log(f'\nOutlier Input Integer Values :  {datavalue}',"0")
        data = np.array(datavalue)
        mean = np.mean(data)
        std = np.std(data)
        z_scores = np.abs((data - mean) / std)
        outliers_indices = np.where(z_scores > int(threshold))[0]
        return outliers_indices