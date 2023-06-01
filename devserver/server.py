import datetime
import json
import random

import pytz
from flask import Flask, request

app = Flask(__name__)

# config section
TIMEZONE = pytz.timezone('Europe/Vienna')


# TODO replace sample data with GEN24/Tauro data

with open('samples/CommonInverterData.json', 'r') as f:
    common_inverter_data = [json.loads(r) for r in f.readlines()]

with open('samples/3PInverterData.json', 'r') as f:
    threep_inverter_data = [json.loads(r) for r in f.readlines()]

with open('samples/MinMaxInverterData.json', 'r') as f:
    min_max_inverter_data = [json.loads(r) for r in f.readlines()]


@app.route('/solar_api/v1/GetInverterRealtimeData.cgi', methods=['GET'])
def get_inverter_realtime_data() -> str:
    scope = request.args.get('Scope')
    data_collection = request.args.get('DataCollection')
    device_id = request.args.get('DeviceId')

    now = datetime.datetime.now(tz=TIMEZONE).isoformat('T')
    if data_collection == 'CommonInverterData':
        json_response = random.choice(common_inverter_data)
    elif data_collection == '3PInverterData':
        json_response = random.choice(threep_inverter_data)
    elif data_collection == 'MinMaxInverterData':
        json_response = random.choice(min_max_inverter_data)
    else:
        json_response = {}

    if json_response:
        json_response['Head']['Timestamp'] = now
    return json_response


if __name__ == '__main__':
    app.run(threaded=True)
