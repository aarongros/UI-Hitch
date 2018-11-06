
# coding: utf-8

# In[29]:


import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

get_ipython().run_line_magic('run', '"../../apikey.py" #outside actual git repo, make sure to add file/replace with own apikey')
VERSION = "v2.2"
OUTPUT_FORMAT = "json"
API_KEY = keys['CUMTD']


# In[18]:


def cumtdRequestUrl(methodname, other_args={}, version=VERSION, output=OUTPUT_FORMAT, key=API_KEY):
    rooturl = "https://developer.cumtd.com/api/{v}/{f}/".format(v=VERSION, f=OUTPUT_FORMAT)
    url = rooturl + methodname + "?key={}".format(key)
    for param, value in other_args.items():
        url = url + "&{}={}".format(param, value)
    return url


# In[30]:


# check API usage, cuz why not
requests.get(cumtdRequestUrl("getapiusage")).json()


# In[20]:


# get all stops
r = requests.get(cumtdRequestUrl("getstops"))
json = r.json()


# In[21]:


# arrange into csv
def generateAllStopsCsv(filename):
    r = requests.get(cumtdRequestUrl("getstops"))
    json = r.json()
    
    stops = {'stop_id': [], 'stop_name': [], 'code': [], 'distance': [], 'specific_stop_code': [], 'specific_stop_stop_id': [], 'specific_stop_stop_lat': [], 'specific_stop_stop_lon': [], 'specific_stop_stop_name': []}

    for stop in json['stops']:
        for key in stop.keys():
            if key in ['stop_id', 'stop_name', 'code', 'distance']:
                stops[key].append(stop[key])
            elif key == 'stop_points': pass
        for key in ['specific_stop_code', 'specific_stop_stop_id', 'specific_stop_stop_lat', 'specific_stop_stop_lon', 'specific_stop_stop_name']:
            stops[key].append('')
        for specific_stop in stop['stop_points']:
            for key in specific_stop.keys():
                if key in ['code', 'stop_id', 'stop_lat', 'stop_lon', 'stop_name']:
                    stops['specific_stop_' + key].append(specific_stop[key])
            for key in ['stop_id', 'stop_name', 'code', 'distance']:
                stops[key].append('')

    pd.DataFrame(stops).to_csv(filename, index=False)
    
# run once per folder
# generateAllStopsCsv('all_stops.csv')


# In[22]:


def nameToStopId(name):
    stops = pd.read_csv('all_stops.csv')
    if name in list(stops['stop_name']):
        return stops[stops['stop_name'] == name].iloc[0]['stop_id']
    elif name in list(stops['specific_stop_stop_name']):
        return stops[stops['specific_stop_stop_name'] == name].iloc[0]['specific_stop_stop_id']
    else:
        return None
    
nameToStopId('U.S. 150 and Dale')


# In[25]:


STOP = nameToStopId('Goodwin & Main (SE Corner)')
r = requests.get(cumtdRequestUrl("getdeparturesbystop", {'stop_id': STOP, 'pt': 60}))
json = r.json()

print(json['status']['msg'])


# In[32]:


names = []
scheduled = []
expected = []
diff = []

for departure in json['departures']:
    names.append(departure['headsign'])
    scheduled_time = datetime.fromisoformat(departure['scheduled'])
    expected_time = datetime.fromisoformat(departure['expected'])
    diff.append(expected_time - scheduled_time)
    scheduled.append(scheduled_time)
    expected.append(expected_time)
    
df = pd.DataFrame({'name': names, 'scheduled_time': scheduled, 'expected_time': expected, 'diff': diff})
df


# In[ ]:


stop_times_all = pd.read_csv('google_transit/stop_times.txt')
stop_times_all.head()


# In[ ]:


trip_id = '[@2.0.80548152@][12][1425572286750]/26__BB2_MF'
departure_time = '15:29:00'
expected_time = '15:29:06'
day = '10/30'
stop_times_all.loc[(stop_times_all['trip_id'] == trip_id) & (stop_times_all['departure_time'] == departure_time),day] = expected_time
stop_times_all[(stop_times_all['trip_id'] == trip_id) & (stop_times_all['departure_time'] == departure_time)]

