import datetime
import json
import random

import flask
import pytz
from flask import Flask, request

app = Flask(__name__)

# config section
TIMEZONE = pytz.timezone('Europe/Vienna')


with open('samples/CommonInverterData.json', 'r') as f:
    common_inverter_data = json.loads(f.read())

with open('samples/3PInverterData.json', 'r') as f:
    threep_inverter_data = json.loads(f.read())

with open('samples/MinMaxInverterData.json', 'r') as f:
    min_max_inverter_data = json.loads(f.read())

with open('samples/CumulationInverterData.json', 'r') as f:
    cumulation_inverter_data = json.loads(f.read())

with open('samples/MeterRealtimeData.json', 'r') as f:
    smart_meter_data = json.loads(f.read())

with open('samples/PowerFlowRealtimeData.json', 'r') as f:
    power_flow_data = json.loads(f.read())


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
    elif data_collection == 'CumulationInverterData':
        json_response = random.choice(cumulation_inverter_data)
    else:
        json_response = {}

    if json_response:
        json_response['Head']['Timestamp'] = now
    return json_response


@app.route('/solar_api/v1/GetPowerFlowRealtimeData.fcgi', methods=['GET'])
def get_power_flow_data() -> str:
    json_response = random.choice(power_flow_data)
    json_response['Head']['Timestamp'] = datetime.datetime.now(tz=TIMEZONE).isoformat('T')
    return json_response


@app.route('/solar_api/v1/GetMeterRealtimeData.cgi', methods=['GET'])
def get_smart_meter_data() -> str:
    scope = request.args.get('Scope')

    if scope == 'System':
        json_response = random.choice(smart_meter_data)
        json_response['Head']['Timestamp'] = datetime.datetime.now(tz=TIMEZONE).isoformat('T')
    else:
        json_response = {}
        flask.abort(400, f'No sample data for scope: {scope}')
    return json_response


if __name__ == '__main__':
    app.run(threaded=True)
