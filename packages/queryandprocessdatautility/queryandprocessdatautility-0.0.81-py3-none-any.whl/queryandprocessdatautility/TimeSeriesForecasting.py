from prophet import Prophet
import loggerutility as logger
import datetime
import json
from pandas import to_datetime
import pandas as pd 
from .prophetForecast import prophetclass
from .autoarimaForecast import autoarimaclass
from .autoetsForecast import autoetsclass
from .dartsForecasting import dartsclass
from .pyaForecasting import pyafclass


class timeseriesforecasting:

    def forecast(self,calculationData,df):
        try:
            logger.log(f'\nForcast function start time, {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
            convert = json.loads(calculationData['columndataTypes'])
            length_of_string_col = 0
            string_list = []
            numeric_list_Int = []
            numeric_list = []
            length_of_dataset = 0
            
            for k in calculationData['column']:
                colname = k['col_name']
                expression1 = k['calc_expression']

            periodsof=expression1.split(",")
            forecastmethod = periodsof[0].replace("(","")       #   To Get The ForecastMethod
            forecastfrequecy = periodsof[1]                     #   To Get The Forecast Frequecy
            forecastperiod = periodsof[-1].replace(")","")      #   To Get The Forecast  Period
            global da
            for m,i in enumerate(convert):
                if convert[i] == 'string':
                    string_list.append(i)
                elif convert[i] == 'date' or convert[i] == 'date string':
                    da = i
                    dateindex = m
                elif convert[i] == 'number':
                    numeric_list.append(i)
                    numeric_list_Int.append(m)
                    pos=m

            for num, numbervalue in enumerate(convert):
                    if numbervalue == numeric_list[0]:
                        for numbervalue in range(len(df)):
                            df.at[numbervalue, colname] = df[df.columns[num]].values[numbervalue]  ####   To add the input integer data into forecast column

            if len(string_list) != 0:
                new = df.filter([i for i in string_list], axis=1)
                drop_dataframe = new.drop_duplicates()    #### for drop duplicate value
                drop_dataframe.index = [i for i in range(0,len(drop_dataframe))]   ####   for contine index   
                for i in range(0,len(drop_dataframe)):
                    datestring = []
                    y = []
                    head = []
                    valuesofdataframe = [0]
                    logger.log(f'\nForcast New DataFrame creation and finding the same data, start time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    newo =pd.DataFrame(drop_dataframe.iloc[[i]])
                    newo.index=valuesofdataframe
                    k=newo.values
                    newdataframe = newo.copy()                                                                                                                                            
                    newdataframe['marker'] = True
                    joined = pd.merge(new, newdataframe, on=[i for i in new], how='left')
                    val = joined[pd.notnull(joined['marker'])][new.columns]
                    lis = []
                    lis = val.index.tolist()
                    logger.log(f'\nForcast New DataFrame creation and finding the same data, end time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    logger.log(f'\nForcast function process start time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    for ind in lis:
                        datestring.append(df[df.columns[dateindex]].values[ind])
                        y.append(df[df.columns[numeric_list_Int[0]]].values[ind])
                        length_of_dataset = length_of_dataset + 1

                    if all(item == 0 for item in y) or len(y) < 2:
                        continue

                    if 'Prophet' in forecastmethod:
                        prophetMethod = prophetclass()
                        forecast = prophetMethod.prophetMethod(datestring,y,forecastperiod)
                        # forecast = self.prophetMethod(datestring,y,per[0])

                    elif 'Autoarima' in forecastmethod and len(y)>3:
                        autoarimaMethod = autoarimaclass()
                        forecast = autoarimaMethod.autoarimaMethod(datestring,y,forecastperiod,forecastfrequecy)
                        # forecast = self.autoarimaMethod(datestring,y,per[0])

                    elif 'Autoets' in forecastmethod and len(y)>3:
                        autoetsMethod = autoetsclass()
                        forecast = autoetsMethod.autoetsMethod(datestring,y,forecastperiod,forecastfrequecy)
                        # forecast = self.autoarimaMethod(datestring,y,per[0])

                    elif 'Darts' in forecastmethod:
                        dartsMethod = dartsclass()
                        forecast = dartsMethod.dartsMethod(datestring,y,forecastperiod,forecastfrequecy)
                        # forecast = self.darts(datestring,y,forecastperiod,forecastfrequecy)

                    elif 'PYAF' in forecastmethod:
                        pyafMethod = pyafclass()
                        forecast = pyafMethod.pyafMethod(datestring,y,forecastperiod,forecastfrequecy)


                    # m = Prophet()
                    # df_for_prophet = pd.DataFrame(dict(ds=datestring, y=y))
                    # m.fit(df_for_prophet)
                    # future = m.make_future_dataframe(periods=int(per[0]))
                    # forecast = m.predict(future)
                    logger.log(f'\nForcast function process End time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                    for l, val in enumerate(forecast["trend"]):
                        df2 = {da: to_datetime([forecast["ds"][l]]), colname: [val]}
                        dd = pd.DataFrame(dict(df2))
                        df3 = pd.concat([newo, dd], axis=1)
                        df4 = df3[~df3[da].isin(datestring)]
                        df = df.append(df4, ignore_index = True)
                    
                df.drop_duplicates(subset=da, keep='first', inplace=True)
                logger.log(f'\nForcast function end time :  {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                return df

            elif len(string_list) == 0:
                ds = []
                y = []
                
                for num, numbervalue in enumerate(convert):
                    if numbervalue == numeric_list[0]:
                        for numbervalue in range(len(df)):
                            pos = num
                            y.append(df[df.columns[num]].values[numbervalue])

                for num, datevalue in enumerate(convert):
                    if convert[datevalue] == "date" or convert[datevalue] == 'date string':
                        d = num
                        date = datevalue
                        for datevalue in range(len(df)):
                            ds.append(df[df.columns[num]].values[datevalue])

                logger.log(f'\nForcast function process start time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                dit = []
                if 'Prophet' in forecastmethod:
                        prophetMethod = prophetclass()
                        forecast = prophetMethod.prophetMethod(ds,y,forecastperiod)
                        # forecast = self.prophetMethod(datestring,y,per[0])

                elif 'Autoarima' in forecastmethod and len(y)>3:
                    autoarimaMethod = autoarimaclass()
                    forecast = autoarimaMethod.autoarimaMethod(ds,y,forecastperiod,forecastfrequecy)
                    # forecast = self.autoarimaMethod(datestring,y,per[0])

                elif 'Autoets' in forecastmethod and len(y)>3:
                    autoetsMethod = autoetsclass()
                    forecast = autoetsMethod.autoetsMethod(ds,y,forecastperiod,forecastfrequecy)
                    # forecast = self.autoarimaMethod(datestring,y,per[0])

                elif 'Darts' in forecastmethod:
                    dartsMethod = dartsclass()
                    forecast = dartsMethod.dartsMethod(ds,y,forecastperiod,forecastfrequecy)

                elif 'PYAF' in forecastmethod:
                    pyafMethod = pyafclass()
                    forecast = pyafMethod.pyafMethod(ds,y,forecastperiod,forecastfrequecy)
                # m = Prophet()
                # df_for_prophet = pd.DataFrame(dict(ds=ds, y=y))
                # m.fit(df_for_prophet)
                # future = m.make_future_dataframe(periods=int(per[0]))
                # forecast = m.predict(future)
                logger.log(f'\nForcast function process End time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                for l, val in enumerate(forecast["trend"]):
                    df2 = {da: forecast["ds"][l],colname: val}
                    df = df.append(df2, ignore_index=True)

                logger.log(f'\nForcast function end time : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',"0")
                df  = df.drop_duplicates(subset=[da], keep='first', inplace=False, ignore_index=False)
                return df
            
        except Exception as e:
            return str(e)



