import pandas as pd
import pyaf.ForecastEngine as autof
import loggerutility as logger

class pyafclass:

    def pyafMethod(self,datestring,y,Forecast_Period,forecastfrequecy):

        logger.log(f"Executing Python Automatic Forecasting","0" )
        horizon = int(Forecast_Period)
        datavalue = {'ds':[i for i in datestring],
                     'y':[i for i in y]}
        Y_train_df = pd.DataFrame(datavalue)
        lEngine = autof.cForecastEngine()
        lEngine.train(iInputDS=Y_train_df, iTime='ds', iSignal='y', iHorizon=horizon)
        forecast_df= lEngine.forecast(Y_train_df, horizon)

        length = len(forecast_df['y'].dropna())
        predictdataset = {'trend':forecast_df['y_Forecast'][length:],
                          'ds':forecast_df['ds'][length:]}
        forecast = pd.DataFrame(predictdataset)
        forecast.index = [i for i in range(0,len(forecast))]
        return forecast