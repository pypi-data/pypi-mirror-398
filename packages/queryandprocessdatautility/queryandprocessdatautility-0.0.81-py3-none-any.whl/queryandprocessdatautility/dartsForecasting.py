from darts import TimeSeries
from darts.models import ExponentialSmoothing
import loggerutility as logger
import pandas as pd
import numpy as np

class dartsclass:

    def dartsMethod(self,datestring,y,Forecast_Period,forecastfrequecy):
        logger.log(f"Executing darts","0" )
        print(datestring)
        datavalue = {'ds':[i for i in datestring],
                     'y':[i for i in y]}
        Y_train_df = pd.DataFrame(datavalue)
        train = TimeSeries.from_dataframe(Y_train_df,"ds","y",fill_missing_dates=True,freq=None)
        model = ExponentialSmoothing()
        model.fit((train))
        prediction = model.predict(int(Forecast_Period))
        predictdataset = {'trend':[i for i in prediction.pd_dataframe()['y'].values],
                          'ds':[i for i in prediction.pd_dataframe()['y'].keys().values]}
        forecast = pd.DataFrame(predictdataset)
        return forecast
