import logging
from typing import Dict, List


class DataCollectionError(Exception):
    pass


class WrongFroniusData(Exception):
    pass


def _get_float_or_zero(data, value: str) -> float:
    if value in data:
        return float(data[value].get('Value', 0))
    return 0.0


class DataProcessor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process(self, response: Dict) -> List[Dict]:
        try:
            collection = response['Head']['RequestArguments']['DataCollection']
            timestamp = response['Head']['Timestamp']
            data = response['Body']['Data']
        except KeyError:
            raise WrongFroniusData('Response structure is not healthy.')

        # workaround for wrong timezone on Symo GEN24
        timestamp = timestamp.replace("+00:00", "")

        self.logger.debug(f"process {collection}, {timestamp}: {data}")
        if collection == 'CommonInverterData':
            device_status = {
                'measurement': 'DeviceStatus',
                'time': timestamp,
                'fields': data['DeviceStatus']
            }

            inverter_data = {
                'measurement': collection,
                'time': timestamp,
                'fields': {
                    'FAC': _get_float_or_zero(data, 'FAC'),
                    'IAC': _get_float_or_zero(data, 'IAC'),
                    'IDC': _get_float_or_zero(data, 'IDC'),
                    'PAC': _get_float_or_zero(data, 'PAC'),
                    'UAC': _get_float_or_zero(data, 'UAC'),
                    'UDC': _get_float_or_zero(data, 'UDC'),
                    'DAY_ENERGY': _get_float_or_zero(data, 'DAY_ENERGY'),
                    'YEAR_ENERGY': _get_float_or_zero(data, 'YEAR_ENERGY'),
                    'TOTAL_ENERGY': _get_float_or_zero(data, 'TOTAL_ENERGY'),
                }
            }

            # add additional fields for Symo GEN24
            strings_fields = []
            if 'SAC' in data:
                strings_fields.append('SAC')
            if 'IDC_2' in data:
                strings_fields.extend(['IDC_2', 'UDC_2'])
            if 'IDC_3' in data:
                strings_fields.extend(['IDC_3', 'UDC_3'])
            if 'IDC_4' in data:
                strings_fields.extend(['IDC_4', 'UDC_4'])

            for field in strings_fields:
                inverter_data['fields'][field] = _get_float_or_zero(data, field)

            return [device_status, inverter_data]
        elif collection == '3PInverterData':
            return [
                {
                    'measurement': collection,
                    'time': timestamp,
                    'fields': {
                        'IAC_L1': _get_float_or_zero(data, 'IAC_L1'),
                        'IAC_L2': _get_float_or_zero(data, 'IAC_L2'),
                        'IAC_L3': _get_float_or_zero(data, 'IAC_L3'),
                        'UAC_L1': _get_float_or_zero(data, 'UAC_L1'),
                        'UAC_L2': _get_float_or_zero(data, 'UAC_L2'),
                        'UAC_L3': _get_float_or_zero(data, 'UAC_L3'),
                    }
                }
            ]
        elif collection == 'MinMaxInverterData':
            return [
                {
                    'measurement': collection,
                    'time': timestamp,
                    'fields': {
                        'DAY_PMAX': _get_float_or_zero(data, 'DAY_PMAX'),
                        'DAY_UACMAX': _get_float_or_zero(data, 'DAY_UACMAX'),
                        'DAY_UDCMAX': _get_float_or_zero(data, 'DAY_UDCMAX'),
                        'YEAR_PMAX': _get_float_or_zero(data, 'YEAR_PMAX'),
                        'YEAR_UACMAX': _get_float_or_zero(data, 'YEAR_UACMAX'),
                        'YEAR_UDCMAX': _get_float_or_zero(data, 'YEAR_UDCMAX'),
                        'TOTAL_PMAX': _get_float_or_zero(data, 'TOTAL_PMAX'),
                        'TOTAL_UACMAX': _get_float_or_zero(data, 'TOTAL_UACMAX'),
                        'TOTAL_UDCMAX': _get_float_or_zero(data, 'TOTAL_UDCMAX'),
                    }
                }
            ]
        else:
            raise DataCollectionError("Unknown data collection type.")
