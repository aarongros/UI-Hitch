# UI-Hitch

A better U of I Bus App

### Data Collection

Using the CUMTD API, we were able to get data and format it into something like this:

| name        | scheduled_time            | expected_time             | diff                      | 
|-------------|---------------------------|---------------------------|---------------------------| 
| 220N Illini | 2018-10-31 20:48:24-05:00 | 2018-10-31 20:50:45-05:00 | 0 days 00:02:21.000000000 | 
| 220N Illini | 2018-10-31 20:58:24-05:00 | 2018-10-31 20:59:56-05:00 | 0 days 00:01:32.000000000 | 
| 220N Illini | 2018-10-31 21:08:24-05:00 | 2018-10-31 21:11:42-05:00 | 0 days 00:03:18.000000000 | 
| 220N Illini | 2018-10-31 21:18:24-05:00 | 2018-10-31 21:18:24-05:00 | 0 days 00:00:00.000000000 | 
| 220N Illini | 2018-10-31 21:28:24-05:00 | 2018-10-31 21:28:24-05:00 | 0 days 00:00:00.000000000 | 
| 220N Illini | 2018-10-31 21:38:24-05:00 | 2018-10-31 21:41:22-05:00 | 0 days 00:02:58.000000000 | 
| 220N Illini | 2018-10-31 21:48:24-05:00 | 2018-10-31 21:48:24-05:00 | 0 days 00:00:00.000000000 | 

to figure out the difference between the expected and schedule time. Besides just simple
data analysis on this difference data to potentially figure out an "expected time" for each
bus, our plan is to try to incorporate this data with someone's Google Calendar in order to 
personalize their transportation schedule, and help them out with their daily lives.

### Contributors

- Aaron Gros
- Shaw Kagawa
- Sudhesh Sahu

Mentor: Karthik Shankar

### Reference Links
- [Midpoint Presentation](https://docs.google.com/presentation/d/1h3yaCI4ZFQ-jj2gOQ_fZUf455Lsxr5-1NUgchRtpApg/edit?ts=5bda55f4)