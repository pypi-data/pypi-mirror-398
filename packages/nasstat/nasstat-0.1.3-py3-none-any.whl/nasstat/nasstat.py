#####################################################################
#####################################################################
#####███╗░░██╗░█████╗░░██████╗░██████╗████████╗░█████╗░████████╗#####
#####████╗░██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝#####
#####██╔██╗██║███████║╚█████╗░╚█████╗░░░░██║░░░███████║░░░██║░░░#####
#####██║╚████║██╔══██║░╚═══██╗░╚═══██╗░░░██║░░░██╔══██║░░░██║░░░#####
#####██║░╚███║██║░░██║██████╔╝██████╔╝░░░██║░░░██║░░██║░░░██║░░░#####
#####╚═╝░░╚══╝╚═╝░░╚═╝╚═════╝░╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝░░░╚═╝░░░#####
##### A WRAPPER OF FAA AIRSPACE DATA BY DARIEL CRUZ RODRIGUEZ #######
#####################################################################
#####################################################################

import requests
import json
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone, timedelta
import pytz

class Airport():
    """
    Class that represents an airport, and provides methods to retrieve data from it.
    """
    def __init__(self, airportid):
        """
        Constructor for the Airport class, takes only one input, the FAA airport ID.

        Inputs:
            - FAA Airport ID (string): The FAA airport ID.

        Outputs:
            - None

        Example:
            > airport = Airport("MCO")
            Retrieves information from Orlando International Airport in Orlando, Florida, which uses
            the FAA airport ID "MCO". Only valid for U.S. domestic airports.
        """
        self.airportid = airportid
        self.lastupdate = None
        self.airportclosures = None
        self.airportdelays = None
        self.possibledelays = None

    def getDelays(self):
            """
            Fetches live airport delay data from the FAA NAS Status API and updates self.airportdelays.

            Outputs:
                - None (updates self.airportdelays)
            """
            
            try:
                response = requests.get("https://nasstatus.faa.gov/api/airport-status-information")
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching data: {e}")
                return

            # Helper function: Convert text like "1 hour and 24 minutes" to minute format
            def parse_minutes(time_str):
                numbers = re.findall(r"(\d+)", time_str.lower())
                if "hour" in time_str.lower():
                    hours = int(numbers[0]) if len(numbers) >= 1 else 0
                    minutes = int(numbers[1]) if len(numbers) >= 2 else 0
                    return hours * 60 + minutes
                elif "minute" in time_str.lower():
                    return int(numbers[0]) if numbers else 0
                return 0

            # Helper function: Parse end time string (e.g., "4:45 pm EST") and convert to UTC
            def parse_end_time(end_time_str):
                try:
                    # Parse the time string (e.g., "4:45 pm EST")
                    # Includes all US timezones: Eastern, Central, Mountain, Pacific, Alaska, Hawaii, Atlantic (Puerto Rico/USVI), Samoa, Chamorro (Guam/CNMI)
                    time_match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)\s*(EST|EDT|CST|CDT|MST|MDT|PST|PDT|AKST|AKDT|HST|AST|ADT|SST|ChST)', end_time_str, re.IGNORECASE)
                    if not time_match:
                        return None, end_time_str, 0

                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    am_pm = time_match.group(3).lower()
                    tz_str = time_match.group(4).upper()

                    # Convert to 24-hour format
                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0

                    # Map timezone strings to pytz timezones
                    tz_map = {
                        'EST': 'US/Eastern', 'EDT': 'US/Eastern',
                        'CST': 'US/Central', 'CDT': 'US/Central',
                        'MST': 'US/Mountain', 'MDT': 'US/Mountain',
                        'PST': 'US/Pacific', 'PDT': 'US/Pacific',
                        'AKST': 'US/Alaska', 'AKDT': 'US/Alaska',
                        'HST': 'US/Hawaii',
                        'AST': 'America/Puerto_Rico', 'ADT': 'America/Puerto_Rico',
                        'SST': 'Pacific/Pago_Pago',
                        'CHST': 'Pacific/Guam'
                    }

                    # Get current time in UTC
                    now_utc = datetime.now(timezone.utc)

                    # Get timezone
                    local_tz = pytz.timezone(tz_map.get(tz_str, 'US/Eastern'))

                    # Create datetime for today with the parsed time in local timezone
                    now_local = now_utc.astimezone(local_tz)
                    end_time_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # If the time has already passed today, assume it's for tomorrow
                    if end_time_local < now_local:
                        end_time_local += timedelta(days=1)

                    # Convert to UTC
                    end_time_utc = end_time_local.astimezone(timezone.utc)

                    # Calculate minutes until end time
                    minutes_until_end = int((end_time_utc - now_utc).total_seconds() / 60)

                    return end_time_utc.isoformat(), end_time_str, max(0, minutes_until_end)

                except Exception:
                    return None, end_time_str, 0

            # Helper function: search FAA's XML for airport delays
            def parse_faa_xml(xml_string):
                root = ET.fromstring(xml_string)
                delays = {}

                for delay_type in root.findall("Delay_type"):

                    # Ground Stops
                    for ground_stop in delay_type.findall(".//Ground_Stop_List/Program"):
                        arpt = ground_stop.find("ARPT").text if ground_stop.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            reason = ground_stop.find("Reason").text if ground_stop.find("Reason") is not None else "Unknown"
                            end_time_str = ground_stop.find("End_Time").text if ground_stop.find("End_Time") is not None else None

                            # Parse end time and calculate minutes until end
                            if end_time_str:
                                end_time_utc, end_time_local, minutes_until_end = parse_end_time(end_time_str)
                            else:
                                end_time_utc, end_time_local, minutes_until_end = None, None, None

                            delays["GroundStop"] = {
                                "minDelay": minutes_until_end,
                                "maxDelay": minutes_until_end,
                                "avgDelay": minutes_until_end,
                                "reason": reason,
                                "endTime": end_time_utc,
                                "endTimeLocal": end_time_local
                            }

                    # Ground Delays
                    for ground_delay in delay_type.findall(".//Ground_Delay"):
                        arpt = ground_delay.find("ARPT").text if ground_delay.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            reason = ground_delay.find("Reason").text if ground_delay.find("Reason") is not None else "Unknown"
                            max_delay = ground_delay.find("Max").text if ground_delay.find("Max") is not None else "0 minutes"
                            avg_delay = ground_delay.find("Avg").text if ground_delay.find("Avg") is not None else "0 minutes"
                            min_delay = avg_delay  # Approximate min delay as avg for missing data

                            delays["Ground"] = {
                                "minDelay": parse_minutes(min_delay),
                                "maxDelay": parse_minutes(max_delay),
                                "avgDelay": parse_minutes(avg_delay),
                                "reason": reason
                            }

                    # Arrival/Departure Delays
                    for delay in delay_type.findall(".//Delay"):
                        arpt = delay.find("ARPT").text if delay.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            reason = delay.find("Reason").text if delay.find("Reason") is not None else "Unknown"

                            for arr_dep in delay.findall("Arrival_Departure"):
                                delay_category = arr_dep.get("Type", "Unknown")
                                min_delay = arr_dep.find("Min").text if arr_dep.find("Min") is not None else "0 minutes"
                                max_delay = arr_dep.find("Max").text if arr_dep.find("Max") is not None else "0 minutes"
                                avg_delay = (parse_minutes(min_delay) + parse_minutes(max_delay)) // 2  # Approximate avg

                                delays[delay_category] = {
                                    "minDelay": parse_minutes(min_delay),
                                    "maxDelay": parse_minutes(max_delay),
                                    "avgDelay": avg_delay,
                                    "reason": reason
                                }

                return delays if delays else None

            self.airportdelays = parse_faa_xml(response.text)
            self.lastupdate = datetime.now(timezone.utc).isoformat()
            return self.airportdelays

    def getDepartureDelays(self):
        """
        Fetches departure delay data only.

        Outputs:
            - departure_delays (dict): A dictionary of departure delays with details, or None if no delays are found.
        """
        if self.airportdelays is None:
            try:
                self.getDelays()
            except Exception as e:
                print(f"Error while fetching airport events: {e}")
                return None

        departure_delays = {}
        if self.airportdelays is not None:
            for category, data in self.airportdelays.items():
                if "Departure" in category:
                    departure_delays[category] = data

        return departure_delays if departure_delays else None
    
    def getArrivalDelays(self):
        """
        Fetches arrival delay data only.

        Outputs:
            - arrival_delays (dict): A dictionary of arrival delays with details, or None if no delays are found.
        """
        if self.airportdelays is None:
            try:
                self.getDelays()
            except Exception as e:
                print(f"Error while fetching airport events: {e}")
                return None

        arrival_delays = {}
        if self.airportdelays is not None:
            for category, data in self.airportdelays.items():
                if "Arrival" in category:
                    arrival_delays[category] = data

        return arrival_delays if arrival_delays else None

    def getGroundDelays(self):
            """
            Fetches ground delay data only.

            Outputs:
                - ground_delays (dict): A dictionary of ground delay details, or None if no ground delays are found.
            """
            if self.airportdelays is None:
                try:
                    self.getDelays()
                except Exception as e:
                    print(f"Error while fetching airport events: {e}")
                    return None

            ground_delays = {}
            if self.airportdelays is not None:
                for category, data in self.airportdelays.items():
                    if category == "Ground":
                        ground_delays[category] = data
            else:
                return None

            return ground_delays if ground_delays else None

    def getGroundStops(self):
        """
        Fetches ground stop data only.

        Outputs:
            - ground_stops (dict): A dictionary of ground stop details, or None if no ground stops are found.
        """
        if self.airportdelays is None:
            try:
                self.getDelays()
            except Exception as e:
                print(f"Error while fetching airport events: {e}")
                return None

        ground_stops = {}
        if self.airportdelays is not None:
            for category, data in self.airportdelays.items():
                if category == "GroundStop":
                    ground_stops[category] = data
        else:
            return None

        return ground_stops if ground_stops else None

    def getClosures(self):
        """
        Fetches airport closure data from the FAA NAS Status API and updates self.airportclosures.
        
        Returns:
            dict: A dictionary of airport closures with details, or None if no closures are found.
        """
        try:
            response = requests.get("https://nasstatus.faa.gov/api/airport-status-information")
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

        def parse_closures(xml_string):
            root = ET.fromstring(xml_string)
            closures = []

            for delay_type in root.findall("Delay_type"):
                if delay_type.find("Name") is not None and delay_type.find("Name").text == "Airport Closures":
                    for airport in delay_type.findall(".//Airport"):
                        arpt = airport.find("ARPT").text if airport.find("ARPT") is not None else None
                        if arpt and arpt.upper() == self.airportid:
                            closure = {
                                "reason": airport.find("Reason").text if airport.find("Reason") is not None else "Unknown",
                                "start": airport.find("Start").text if airport.find("Start") is not None else "Unknown",
                                "reopen": airport.find("Reopen").text if airport.find("Reopen") is not None else "Unknown"
                            }
                            closures.append(closure)

            return closures if closures else None

        self.airportclosures = parse_closures(response.text)
        self.lastupdate = datetime.now(timezone.utc).isoformat()
        return self.airportclosures

    def averageDelay(self):
        """
        Calculates the average delay across all delay categories.

        Returns:
            float: The average delay in minutes across all categories, or 0 if no delays exist.
        """
        if self.airportdelays is None:
            try:
                self.getDelays()
            except Exception as e:
                print(f"Error while fetching airport delays: {e}")
                return 0

        if not self.airportdelays:
            return 0

        total_delay = 0
        count = 0

        for category, data in self.airportdelays.items():
            if "avgDelay" in data:
                total_delay += data["avgDelay"]
                count += 1

        return total_delay / count if count > 0 else 0

    def lastUpdated(self):
        """
        Returns the timestamp of the last update.

        Returns:
            str: The timestamp of the last update, or None if no update has occurred.
        """
        return self.lastupdate

    def delayReasons(self):
        """
        Returns a formatted string with all delay reasons.

        Returns:
            str: Comma-separated list of delay reasons, with 'and' before the last reason, 
                 or 'No delays reported' if no delays exist.
        """
        if self.airportdelays is None:
            try:
                self.getDelays()
            except Exception as e:
                print(f"Error while fetching airport delays: {e}")
                return None

        if not self.airportdelays:
            return None

        reasons = []
        for category, data in self.airportdelays.items():
            if "reason" in data and data["reason"] not in reasons:
                reasons.append(data["reason"])

        if not reasons:
            return "No specific reasons reported"
        elif len(reasons) == 1:
            return reasons[0]
        elif len(reasons) == 2:
            return f"{reasons[0]} and {reasons[1]}"
        else:
            return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"
    
    def isDelay(self):
        """
        Returns True if the airport is experiencing delays, False otherwise.

        Inputs:
            - None
        Outputs:
            - Boolean: True if the airport is experiencing delays, False otherwise.
        """
        if self.airportdelays is None:
            try:
                self.getDelays()
            except Exception as e:
                print(f"Error while fetching airport events: {e}")
                return False 

        return self.airportdelays is not None
    
    def getPossibleDelays(self):
        """
        Fetches possible future delays from the FAA operations plan API.
        Only retrieves events that specifically mention the airport code.

        Updates:
            self.possibledelays: Dictionary of possible delays or None if no data available
        """
        try:
            response = requests.get("https://nasstatus.faa.gov/api/operations-plan")
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Error fetching operations plan: {e}")
            self.possibledelays = None
            return

        possible_delays = {}
        
        # Check terminal planned events
        if "terminalPlanned" in data:
            for event in data["terminalPlanned"]:
                event_text = event.get("event", "")
                if self.airportid in event_text:
                    delay_type = re.sub(r'/([A-Z]{3})\b', '', event_text)
                    delay_type = re.sub(r'^([A-Z]{3})\b/?', '', delay_type).strip()
                    possible_delays[delay_type] = event.get("time", "")
        
        # Check enroute planned events
        if "enRoutePlanned" in data:
            for event in data["enRoutePlanned"]:
                event_text = event.get("event", "")
                if self.airportid in event_text:
                    delay_type = re.sub(r'/[A-Z]{3}', '', event_text)
                    delay_type = re.sub(r'^[A-Z]{3}/?', '', delay_type).strip()
                    possible_delays[delay_type] = event.get("time", "")
        
        self.possibledelays = possible_delays if possible_delays else None
        self.lastupdate = datetime.now(timezone.utc).isoformat()
        return self.possibledelays
