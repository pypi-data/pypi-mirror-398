from prophet import Prophet
import loggerutility as logger
import pandas as pd

class prophetclass:

    def prophetMethod(self,datestring,y,Forecast_Period):
        logger.log(f"Executing prophetMethod","0" )
        m = Prophet()
        df_for_prophet = pd.DataFrame(dict(ds=datestring, y=y))
        m.fit(df_for_prophet)
        future = m.make_future_dataframe(periods=int(Forecast_Period))
        forecast = m.predict(future)
        return forecast
