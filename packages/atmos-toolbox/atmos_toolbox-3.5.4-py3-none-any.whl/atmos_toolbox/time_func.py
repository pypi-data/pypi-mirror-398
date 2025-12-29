import numpy as np
import pandas as pd
import datetime

def dt64_to_dt(dt64):
    """
    transform datetime64 to datetime
    """
    t1 = pd.to_datetime(dt64)
    t2 = datetime.datetime(t1.year, t1.month, t1.day, t1.hour, t1.minute, t1.second)
    return t2

def days2events(days, gap=1):
    """
    Parameters
    ----------
    days : an array consists of datetime

    Returns
    -------
    eve : events consisting of consecutive days 
    """
    eve = []
    evek = []
    for k in range(len(days)):
        if k==0:
            evek.append(days[k])
        elif k>0:
            tdk = days[k]
            ddk = (days[k]-days[k-1]).days
            
            if ddk<=gap:
                evek.append(tdk)
            else:
                eve.append(evek)
                evek = []
                evek.append(tdk)
            
            if k==(len(days)-1):
                eve.append(evek)
    
    return eve










