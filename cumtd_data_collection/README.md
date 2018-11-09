# CUMTD Data Collection

## Overview

- Use [CUMTD's API](developer.cumtd.com) to pull general data about the buses
- Create a SQL database (stop_times.db)
- Every hour (how many minutes in advance to pull data for is parameterized), 
pull realtime bus arrival data from CUMTD's API and store it in the SQL database

Has been running on Colaboratory because of its hosted runtime feature, so
stop_times.db isn't the most updated.

## stop_times Database

In format:

|**trip_id**|**arrival_time**|**stop_id**|**stop_sequence**|**stop_headsign**|**arrival_id**|**2018-11-08**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:02:35|FRLN:1|64|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:02:35|-125
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:02:55|ADRSNFRLN:3|65|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:02:55|93
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:03:15|ADRSNMI:4|66|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:03:15|93
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:04:25|CTGRVPA:3|69|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:04:25|-6
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:04:45|FLCTGRV:4|70|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:04:45|-6
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:05:00|FLLNDN:3|71|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:05:00|-83
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:05:20|FLSUN:3|72|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:05:20|-83
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:06:00|FLPHILO:3|73|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:06:00|-83
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:06:15|FLADAMS:3|74|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:06:15|-6
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:06:40|FLJASCHER:3|75|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:06:40|-6
[@15.0.66064718@][3][1356532933096]/0__GN1_MF|09:07:00|FLCRTS:3|76|nan|[@15.0.66064718@][3][1356532933096]/0__GN1_MF 09:07:00|-6

where the date columns (2018-11-08, ...) indicate the date the data was taken 
(since this table articulates every single bus arrival/departure for a total 
of 255k rows). Each date column will be populated with the number of seconds off of the 
"scheduled" time provided to Google through its static database (negative times equate 
to early arrivals). The `arrival_id` is a unique identifier for each row, since 
`trip_id` and some other means of identification weren't completely unique.