# CUMTD Data Collection

### See [link](https://shawkagawa.com/cumtddatacollection) for live version of data

## Overview

- Use [CUMTD's API](developer.cumtd.com) to pull general data about the buses
- Create a SQL database (stop_times.db)
- Every hour (how many minutes in advance to pull data for is parameterized), 
pull realtime bus arrival data from CUMTD's API and store it in the SQL database

Has been running on Colaboratory because of its hosted runtime feature, so
stop_times.db isn't the most updated.

## `stop_times.db` SQLite3 Database

### Why SQLite3?

No real reason, it was the first thing we learned existed and the database is 
relatively small (255,689 rows in original database, will append columns to it).
There are some limitations such as the lack of concurrency

### Format

#### Table: stop_times

| **trip_id** | **arrival_time** | **stop_id** | **stop_sequence** | **route_id** | **2018-11-09** | **2018-11-10** |
|---------------------------------------------------------|--------------|----------|---------------|----------------|------------|------------|
| [@7.0.41950648@][1244056065453]/242__I4-3_UIF           | 25:26:39     | 1STARY:4 | 20            | ILLINI EVENING | 162        | null       |
| [@7.0.41200832@][2][1249401318109]/4__I2_UIF            | 19:48:02     | 1STARY:4 | 20            | ILLINI         | 0          | null       |
| [@7.0.41200832@][2][1238430887312]/205__I8/4S_UIMTH_SCH | 19:08:02     | 1STARY:4 | 20            | ILLINI         | -5         | null       |
| [@7.0.41200832@][2][1249401318109]/1__I1UIMF            | 19:18:02     | 1STARY:4 | 20            | ILLINI         | 184        | null       |

The date columns (2018-11-09, ...) indicate the date the data was taken 
(since this table articulates every single bus arrival/departure for a total 
of 255k rows). Each date column will be populated with the number of seconds off of 
the "scheduled" time provided to Google through its static database (negative times 
equate to early arrivals, null represents buses that didn't have any departure/
arrival during that day- possible if some routes only run on weekends/altered 
schedules). Some of these columns might not be completely necessary right now, 
however, we have decided to keep some of them in case they will be useful in the
future.

#### Table: unscheduled_stops

There may be some unscheduled arrivals/departures that are given by the API, so to
deal with those cases there is another table inside the database that stores any
of these unscheduled stops. 

## Environment

`cumtd_data_collection.py` will create a 'stop_times.db' file to store the SQLite3
database. Required is the Google Transit data (static dataset of all buses' arrival
and departure times and identifying information about them) in the form of the
'google_transit' folder available to download from [Developer Resources | CUMTD](
https://developer.cumtd.com).

## Future Goals

- Run the analyzer for a longer period of time so that more data is collected
- Create statistics by route name, specific bus, specific areas of campus, etc.
- Integrate Google Traffic data into database to better understand bus delays
	- Understanding the Google Transit API to figure out what parts of the street
		correspond to routes on certain buses
	- Gathering data from another API and tying it in with this data
- Creating a simple interface to allow users to interface with this data



