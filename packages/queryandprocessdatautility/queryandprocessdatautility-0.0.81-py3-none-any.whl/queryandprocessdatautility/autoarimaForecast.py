import loggerutility as logger
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA


class autoarimaclass:

    def autoarimaMethod(self,datestring,y,Forecast_Period,forecastfrequecy):
        logger.log(f"Executing autoarimaMethod","0" )
        season_length = 12
        horizon = int(Forecast_Period)
        datavalue = {'unique_id':[1 for i in range(len(datestring))],
                     'ds':[i for i in datestring],
                     'y':[i for i in y]}
        Y_train_df = pd.DataFrame(datavalue)
        # print(y)
        # print('type printing',type(Y_train_df))
        models = [ AutoARIMA(season_length=season_length) ]
        model = StatsForecast(
                        df=Y_train_df,
                        models=models,
                        freq=forecastfrequecy,
                        n_jobs=-1)
        # print('value',Y_train_df)
        forecast = model.forecast(horizon).reset_index()
        forecast.rename(columns={'AutoARIMA': 'trend'}, inplace=True)
        return forecast