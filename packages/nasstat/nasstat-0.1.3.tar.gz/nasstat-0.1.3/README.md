# NASSTAT - National AirSpace STATistics
```
#####################################################################
#####################################################################
#####███╗░░██╗░█████╗░░██████╗░██████╗████████╗░█████╗░████████╗#####
#####████╗░██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝#####
#####██╔██╗██║███████║╚█████╗░╚█████╗░░░░██║░░░███████║░░░██║░░░#####
#####██║╚████║██╔══██║░╚═══██╗░╚═══██╗░░░██║░░░██╔══██║░░░██║░░░#####
#####██║░╚███║██║░░██║██████╔╝██████╔╝░░░██║░░░██║░░██║░░░██║░░░#####
#####╚═╝░░╚══╝╚═╝░░╚═╝╚═════╝░╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░#####
#####################################################################
#####################################################################
```
*Last updated: `Thu December 19 2025`*

A python wrapper of the United States Federal Aviation Authority's [National Airspace System](https://nasstatus.faa.gov/) API developed by [Dariel Cruz Rodriguez](dariel.us).

## Table of Contents
- [Installation](#installation)
- [Dependencies](#dependencies)
- [Quick Start](#quick-start)
- [Attribution & Licensing](#attribution--licensing)
- [Models](#models)
  - [Airport()](#airport)
- [Methods](#methods)
  - [.getDelays()](#airportgetdelays)
  - [.getDepartureDelays()](#airportgetdelays)
  - [.getArrivalDelays()](#airportgetdelays)
  - [.getGroundDelays()](#airportgetdelays)
  - [.getGroundStops()](#airportgetgroundstops)
  - [.averageDelay()](#airportaveragedelay)
  - [.delayReasons()](#airportdelayreasons)
  - [.isDelay()](#airportisdelay)
  - [.getPossibleDelays()](#airportgetpossibledelays)
  - [.getClosures()](#airportgetclosures)
## Installation

Install NASSTAT via pip:

```bash
pip install nasstat
```

That's it! All dependencies will be installed automatically.

## Dependencies

NASSTAT requires:
- **Python 3.11 or higher**
- `requests>=2.20.0` - for making HTTP requests to the FAA's API (installed automatically)
- `pytz>=2023.3` - for timezone conversions (installed automatically)

The following standard library modules are also used (included with Python):
- `xml.etree.ElementTree` - for parsing the XML response from the FAA's API
- `json` - for parsing the JSON response from the FAA's API
- `re` - for regular expression matching
- `datetime` - for timestamp handling

## Quick Start

```python
import nasstat

# Create an airport object
airport = nasstat.Airport("JFK")

# Check for delays
if airport.isDelay():
    print(f"Delays at JFK: {airport.averageDelay()} minutes")
    print(f"Reason: {airport.delayReasons()}")
else:
    print("No delays at JFK")

# Get detailed delay information
delays = airport.getDelays()
print(delays)
```

## Attribution & Licensing
### Attribution
Although it is not required, please attribute use of this package to the author, Dariel Cruz Rodriguez, by including a link to [dariel.us](https://dariel.us) in your project. As a college student, your attribution can be really helpful in building my portfolio and building a reputation in the data science community. If you are unable to attribute, or it doesn't make sense for your project, please feel free to [email me](mailto:hello@dariel.us) about your project so I can keep an internal note of it, I would love to hear about how you are using NASSTAT!

Additionally, the data provided by the FAA is licensed under the [Open Government License](https://www.data.gov/open-government-licensing/), which allows for free use and redistribution of the data. Thank you Uncle Sam!

### MIT License

Copyright (c) 2024 Dariel Cruz Rodriguez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Models
### Airport()
#### Importing

You can import the Airport class in two ways:

**Option 1: Import the module**
```python
import nasstat

MCO = nasstat.Airport("MCO")  # loads in an instance of MCO and all associated data with it
```

**Option 2: Import the class directly**
```python
from nasstat import Airport

MCO = Airport("MCO")  # loads in an instance of MCO and all associated data with it
```
#### Attributes
- `airportid` (str): The airport IATA/ICAO code (e.g., "MCO", "KATL")
- `lastupdate` (datetime): The timestamp of when the airport data was last updated
- `airportclosures` (dict): Information about current airport closures, if any
- `airportdelays` (dict): Details about current delays including minimum, maximum, average delay times, and reasons
- `possibledelays` (dict): Information about potential upcoming delays

## Methods
### Airport.getDelays()
Fetches all types of delays including ground stops, ground delays, arrival delays, and departure delays. If you want to filter for specific delay types, use:
- `Airport.getDepartureDelays()` - for departure delays only
- `Airport.getArrivalDelays()` - for arrival delays only
- `Airport.getGroundDelays()` - for ground delay programs only
- `Airport.getGroundStops()` - for ground stop programs only

```python
airportcode = "MCO"
airport = Airport(airportcode)
delays = airport.getDelays()
print(delays)

# > {'Departure': {'minDelay': 31, 'maxDelay': 45, 'avgDelay': 38, 'reason': 'TM INITIATIVES:MIT:STOP&VOL'}}
```

```python
airportcode = "EWR"
airport = Airport(airportcode)
delays = airport.getDelays()
print(delays)

# > {'GroundStop': {
#     'minDelay': 75,
#     'maxDelay': 75,
#     'avgDelay': 75,
#     'reason': 'thunderstorms',
#     'endTime': '2025-12-19T21:45:00+00:00',
#     'endTimeLocal': '4:45 pm EST'
# }}
```

```python
# In plain language, you can access items in the dictionary to form a string.
airportcode = "MCO"
airport = Airport(airportcode)
airport.getDelays()

if airport.airportdelays is None:
    print("There are no delays.")
else:
    for key, value in airport.airportdelays.items():
        print(f"There is a delay on {airportcode} {key}s averaging {value['avgDelay']} minutes (btwn. {value['minDelay']}-{value['maxDelay']} min) due to {value['reason']}.")

# > There is a delay on MCO Departures averaging 38 minutes (btwn. 31-45 min) due to TM INITIATIVES:MIT:STOP&VOL.
```

### Airport.averageDelay()
```python
airportcode = "MCO"
airport = Airport(airportcode)
print(airport.averageDelay())

# > 38.0
```

### Airport.delayReasons()
```python
airportcode = "PBI"
airport = Airport(airportcode)
print(airport.delayReasons())
# > "runway construction"
```

```python
# This method also returns multiple reasons as a plain language string (adding 'and' at the end of the list for the last reason)

airportcode = "LGA"
airport = Airport(airportcode)
print(airport.delayReasons())
# > "runway construction, wind, and TM INITIATIVES:MIT:STOP&VOL"
```

### Airport.getGroundStops()
Fetches ground stop program data only. Ground stops are issued when the FAA temporarily stops all departures to a specific airport, typically due to severe weather or other safety concerns.

```python
airportcode = "EWR"
airport = Airport(airportcode)
ground_stops = airport.getGroundStops()

if ground_stops:
    for category, data in ground_stops.items():
        print(f"Ground stop at {airportcode}:")
        print(f"  Reason: {data['reason']}")
        print(f"  End Time (local): {data['endTimeLocal']}")
        print(f"  Minutes until end: {data['avgDelay']}")
else:
    print("No ground stops")

# Output:
# Ground stop at EWR:
#   Reason: thunderstorms
#   End Time (local): 4:45 pm EST
#   Minutes until end: 75
```

The ground stop data structure is more unique than other delay types:
- `minDelay` (int): Minutes until the ground stop ends (same as avgDelay)
- `maxDelay` (int): Minutes until the ground stop ends (same as avgDelay)
- `avgDelay` (int): Minutes until the ground stop ends
- `reason` (str): Reason for the ground stop (e.g., "thunderstorms", "wind")
- `endTime` (str): ISO format UTC timestamp when the ground stop is expected to end
- `endTimeLocal` (str): Local time when the ground stop ends (e.g., "4:45 pm EST")

minDelay, maxDelay, avgDelay are all equal to eachother to maintain the same data structure as other delay types. It takes the local timezone of the airport's end time for ground stop, converts to UTC and subtracts it from the current UTC time, then returns the difference in minutes. If an unsupported timezone is fed through, it returns None for all fields. All mainland/territorial U.S. timezones are supported.

### Airport.isDelay()
```python
airportcode = "MCO"
airport = Airport(airportcode)
print(airport.isDelay())

# > True
```
```python
airportcode = "DEN"
airport = Airport(airportcode)
print(airport.isDelay())

# > "NAASTATUS Airport Delays is empty, attempting to refresh..."
# > False
```

### Airport.getPossibleDelays()
```python
airportcode = "DCA"
airport = Airport(airportcode)
print(airport.getPossibleDelays())

# > {'GROUND STOP/DELAY PROGRAM POSSIBLE': 'AFTER 1930'}
```
### Airport.getClosures()
```python
airportcode = "LAS"
airport = Airport(airportcode)
print(airport.getClosures())

# > [{'reason': '!LAS 03/121 LAS AD AP CLSD TO NON SKED TRANSIENT GA ACFT EXC 24HR PPR 702-261-7775 2503171851-2506252300', 'start': 'Mar 17 at 18:51 UTC.', 'reopen': 'Jun 25 at 23:00 UTC.'}]
```