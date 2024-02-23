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

    @dataclass
    class Record:
        influxdb_bucket: str
        request_interval: float
        ignore_sunset: bool

    inverter: Inverter
    record: Record
    location: Location


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as yml_file:
        cfg = yaml.load(yml_file, Loader=yaml.FullLoader)
        inverter = Config.Inverter(
            name=cfg['inverter']['name'],
            url=cfg['inverter']['url'],
            device_id=cfg['inverter']['device_id'],
            metrics=cfg['inverter']['metrics']
        )

        record = Config.Record(
            influxdb_bucket=cfg['record']['influxdb_bucket'],
            request_interval=cfg['record']['request_interval'],
            ignore_sunset=cfg['record']['ignore_sunset']
        )

        if record.request_interval < 2.0 or record.request_interval > 3600.0:
            raise ValueError(f'invalid request interval: {record.request_interval} s')

        location_info = LocationInfo(
            name=cfg['location']['name'],
            region=cfg['location']['region'],
            timezone=cfg['location']['timezone'],
            latitude=cfg['location']['latitude'],
            longitude=cfg['location']['longitude'],
        )

        config = Config(
            inverter=inverter,
            record=record,
            location=Location(location_info),
        )

        return config
