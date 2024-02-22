import argparse
import datetime
import logging
import time
import urllib
from typing import Dict

import pytz
import requests
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from config import load_config, Config
from data_processor import DataProcessor


class SunIsDown(Exception):
    pass


class InfluxBridge:
    def __init__(self, config: Config, influx_client: InfluxDBClient):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.config = config
        self.influx_client = influx_client
        self.processor = DataProcessor()
        self.endpoints = self._get_endpoints()

        self.logger.info("initialize application")
        self.logger.info(f"- inverter config: {self.config.inverter}")
        self.logger.info(f"- location info: {self.config.location}")
        self.logger.info(f"- influxdb bucket: {self.config.influx_bucket}")

    def run(self):
        self.logger.info("starting application")

        while True:
            try:
                if not self.processor.inverter_map:
                    url = f"{self.config.inverter.url}/solar_api/v1/GetInverterInfo.cgi"
                    self.logger.info(f"update inverter map: {url}")
                    response = requests.get(url)
                    self.processor.update_inverters(response.json())

                self._sun_is_shining()

                collected_data = []
                for metric, url in self.endpoints.items():
                    self.logger.info(f"requesting {url}")
                    response = requests.get(url)
                    data = self.processor.process(metric, response.json())
                    collected_data.extend(data)
                    time.sleep(self.config.record.request_interval)

                if collected_data:
                    self._write_data_points(collected_data)
            except SunIsDown:
                self.logger.info("waiting for sunrise")
                time.sleep(60)
                self.logger.info('waited 60 seconds for sunrise')
            except ConnectionError:
                self.logger.info("waiting for connection...")
                time.sleep(10)
                self.logger.info('waited 10 seconds for connection')
            except Exception as e:
                self.logger.warning("Exception: {}".format(e), exc_info=True)
                time.sleep(10)

    def close(self):
        self.logger.info("closing application")

    def _get_endpoints(self) -> Dict[str, str]:
        base_url = f"{self.config.inverter.url}/solar_api/v1"

        endpoints = {}
        for metric in self.config.inverter.metrics:
            params = None
            if metric in ["CumulationInverterData", "CommonInverterData", "3PInverterData", "MinMaxInverterData"]:
                route = 'GetInverterRealtimeData.cgi'
                params = {
                    'Scope': 'Device',
                    'DataCollection': metric,
                    'DeviceId': self.config.inverter.device_id
                }
            elif metric == "MeterRealtimeData":
                route = 'GetMeterRealtimeData.cgi'
                params = {
                    'Scope': 'System',
                }
            elif metric == "PowerFlowRealtimeData":
                route = 'GetPowerFlowRealtimeData.fcgi'
            elif metric == "InverterInfo":
                route = 'GetInverterInfo.cgi'
            elif metric == "ActiveDeviceInfo":
                route = 'GetActiveDeviceInfo.cgi'
            elif metric == "StorageRealtimeData":
                route = 'GetStorageRealtimeData.cgi'
                params = {
                    'Scope': 'System',
                }
            elif metric == "OhmPilotRealtimeData":
                route = 'GetOhmPilotRealtimeData.cgi',
                params = {
                    'Scope': 'System',
                }
            else:
                raise ValueError(f"Metric '{metric}' is not supported")

            # build endpoint
            endpoint = f"{base_url}/{route}"
            if params:
                endpoint += "?" + urllib.parse.urlencode(params)
            endpoints[metric] = endpoint

        return endpoints

    def _write_data_points(self, collected_data):
        self.logger.info(f"writing data: {[d['measurement'] for d in collected_data]}")

        write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=self.config.influx_bucket, record=collected_data)

    def _sun_is_shining(self):
        if self.config.record.ignore_sunset:
            return

        sun = self.config.location.sun()
        tz = pytz.timezone(self.config.location.timezone)
        if sun['sunset'] < datetime.datetime.now(tz=tz) < sun['sunrise']:
            raise SunIsDown
        return


def main():
    # configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    # configure argument parser
    parser = argparse.ArgumentParser(prog='Fronius Solar API to InfluxDB Bridge',
                                     description='Collect Fronius inverter and SMA and store it in InfluxDB')
    parser.add_argument('--config', type=str, default='./config/sample_config.yaml', help='Path to YAML config file')
    args = parser.parse_args()

    # load config file and initialize InfluxDB client
    config, client_config = load_config(args.config)
    client = InfluxDBClient(**client_config)

    # init and start application
    influx_bridge = InfluxBridge(config, client)
    try:
        influx_bridge.run()
    except KeyboardInterrupt:
        influx_bridge.close()


if __name__ == '__main__':
    main()
