#!/home/agentofgod/.local/bin/python
"""
This Python script automates scheduled API calls based on specified UTC times and days of the week.

It dynamically selects the correct HTTP method (e.g., GET) using the `requests` library and checks whether the current time falls within a defined interval.
The script is designed to run indefinitely, checking tasks every minute.
"""

import logging
from datetime import datetime, timezone
import time
import requests
from api_url_endpoint import api_url_endpoint
from zoneinfo import ZoneInfo

logging.basicConfig(format="{levelname} - {name} - {message}", style="{", level=logging.INFO)

successful_response = []
errored_response = []
LOCAL_TIMEZONE = ZoneInfo("US/Eastern")

class ApiEndpoint:
    def __init__(self):
        self.url_list = api_url_endpoint()

    def current_date_time(self):
        local_time = datetime.now(LOCAL_TIMEZONE)
        return {
            'day': local_time.strftime("%A"),
            'hour': local_time.hour,
            'minute': local_time.minute
        }


    def each_url(self):
        for each_url in self.url_list:
            self.process_automation_base_on_when_to_execute(each_url)

    def process_automation_base_on_when_to_execute(self, each_url_object):
        try:
            current_day_time = self.current_date_time()
            logging.info(f"Processing: {each_url_object['name']} for schedule: {each_url_object['day']}")
            # Weekly condition
            if each_url_object['day'].startswith("weekly") and each_url_object['day'].split('_')[1] == current_day_time['day'].lower()  and current_day_time['hour'] == each_url_object.get('utc_hour', 0) and current_day_time['minute'] == each_url_object.get('utc_minute', 0):
                self.process_api_request(each_url_object)
            # Daily condition
            elif each_url_object['day'] == "daily" and current_day_time['hour'] == each_url_object.get('utc_hour', 0) and current_day_time['minute'] == each_url_object.get('utc_minute', 0):
                self.process_api_request(each_url_object)
            # Every minute condition
            elif each_url_object['day'] == "every_minute":
                self.process_api_request(each_url_object)
            # Every 15 minutes condition
            elif each_url_object['day'] == "every_fifteen_minutes" and current_day_time['minute'] % 15 == 0:
                logging.info(f"Executing every_fifteen_minutes task: {each_url_object['name']}")
                self.process_api_request(each_url_object)
            # Hourly condition
            elif each_url_object['day'] == "hourly" and current_day_time['minute'] == 0:
                self.process_api_request(each_url_object)
            # Additional quarter-hour conditions
            elif each_url_object['day'] == "first_quarter_hour" and current_day_time['minute'] == 15:
                self.process_api_request(each_url_object)
            elif each_url_object['day'] == "second_quarter_hour" and current_day_time['minute'] == 30:
                self.process_api_request(each_url_object)
            elif each_url_object['day'] == "third_quarter_hour" and current_day_time['minute'] == 45:
                self.process_api_request(each_url_object)
            else:
                logging.debug(f"Task skipped: {each_url_object['name']} - Does not match the condition for {each_url_object['day']}")
        except Exception as e:
            logging.error(f"Error in processing {each_url_object['name']}: {str(e)}")

    def process_api_request(self, each_url_object):
        try:
            method_name = each_url_object['method']
            http_method = getattr(requests, method_name)
            response = http_method(each_url_object['url'], json=each_url_object.get('data', None))
            self.process_successful_results(each_url_object, response.text)
        except Exception as e:
            logging.error(f"Error calling {each_url_object['name']}: {str(e)}")
            errored_response.append({'endpoint name called': each_url_object['name'], 'error': str(e)})

    def process_successful_results(self, each_url_object, response):
        successful_response.append({
            'endpoint name called': each_url_object['name'],
            'endpoint description': each_url_object['description'],
            'day of execution': each_url_object['day'],
            'url': each_url_object['url'],
            'time of execution': f"{each_url_object.get('utc_hour', 'No Dedicated Hour')}:{each_url_object.get('utc_minute', 'No Dedicated Minute')}",
            'response': response
        })

    def main(self):
        self.each_url()
        logging.info(f"Successful responses: {successful_response}")
        logging.error(f"Errored responses: {errored_response}")


if __name__ == "__main__":
    api_instance = ApiEndpoint()

    # Continuous loop to run every minute
    while True:
        start_time = time.time()
        api_instance.main()
        # Sleep to ensure the loop executes at one-minute intervals
        time.sleep(max(0, 60 - (time.time() - start_time)))
