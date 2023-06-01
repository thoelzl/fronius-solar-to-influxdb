from typing import Tuple, Dict, List

import yaml
from astral import LocationInfo

from dataclasses import dataclass

from astral.location import Location


@dataclass
class Config:
    @dataclass
    class Inverter:
        url: str
        name: str
        device_id: int
        metrics: List[str]

    inverter: Inverter
    location: Location
    influx_bucket: str
    ignore_sun_down: bool = False


def load_config(config_path: str) -> Tuple[Config, Dict]:
    with open(config_path, "r") as yml_file:
        cfg = yaml.load(yml_file, Loader=yaml.FullLoader)
        inverter = Config.Inverter(
            name=cfg['inverter']['name'],
            url=cfg['inverter']['url'],
            device_id=cfg['inverter']['device_id'],
            metrics=cfg['inverter']['metrics']
        )

        location_info = LocationInfo(
            name=cfg['location']['name'],
            region=cfg['location']['region'],
            timezone=cfg['location']['timezone'],
            latitude=cfg['location']['latitude'],
            longitude=cfg['location']['longitude'],
        )

        config = Config(
            inverter=inverter,
            location=Location(location_info),
            influx_bucket=cfg['influxdb']['bucket'],
        )

        client_config = {
            'url': cfg['influxdb']['url'],
            'org': cfg['influxdb']['organization'],
            'verify_ssl': cfg['influxdb']['verify_ssl']
        }

        if 'username' in cfg['influxdb'] and 'password' in cfg['influxdb']:
            client_config['username'] = cfg['influxdb']['username']
            client_config['password'] = cfg['influxdb']['password']
        elif 'auth_token' in cfg['influxdb']:
            client_config['token'] = cfg['influxdb']['auth_token']
        else:
            raise ValueError('No authentication token or username/password provided for InfluxDB')

        return config, client_config
