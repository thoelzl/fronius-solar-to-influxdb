import logging
from typing import Dict, List, Optional, Tuple

import datetime


class DataCollectionError(Exception):
    pass


class WrongFroniusData(Exception):
    pass


def _get_float_value(data, value: str) -> float:
    if value in data and data[value].get('Value', None) is not None:
        return float(data[value].get('Value', 0))
    return 0.0


def _get_float(data, value: str) -> float:
    if value in data and data[value] is not None:
        return float(data[value])
    return 0.0


def _get_int(data, value: str) -> int:
    if value in data and data[value] is not None:
        return int(data[value])
    return 0


def _get_string(data, value: str) -> str:
    if value in data and data[value] is not None:
        return data[value]
    return ""


def _get_bool(data, value: str) -> bool:
    if value in data and data[value] is not None:
        return bool(data[value])
    return False


INVERTER_METRICS = [
    "CumulationInverterData",
    "CommonInverterData",
    "3PInverterData",
    "MinMaxInverterData",       # not supported by GEN24/Tauro
    "MeterRealtimeData",
    "PowerFlowRealtimeData",
    # "InverterInfo",           # not supported yet
    # "ActiveDeviceInfo",       # not supported yet
    # "StorageRealtimeData",    # not supported yet
    # "OhmPilotRealtimeData",   # not supported yet
    # "SensorRealtimeData",     # not supported by GEN24/Tauro
    # "StringRealtimeData",     # not supported by GEN24/Tauro
    # "LoggerInfo",             # not supported by GEN24/Tauro
    # "LoggerLEDInfo",          # not supported by GEN24/Tauro
]


class DataProcessor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.inverter_map = {}

    def _check_response(self, response: Dict) -> Optional[Tuple]:
        try:
            if response['Head']['Status']['Code'] != 0:
                self.logger.warning(f"Response status code is not 0: code={response['Head']['Status']['Code']}")
                return None
            
            timestamp = response['Head']['Timestamp']
            data = response['Body']['Data']
        except KeyError:
            raise WrongFroniusData('Response structure is not healthy.')

        # workaround for wrong timezone on Symo GEN24
        timestamp = timestamp.replace("+00:00", "")
        return timestamp, data

    def update_inverters(self, response: Dict):
        tpl = self._check_response(response)
        if not tpl:
            return
        _, data = tpl

        self.inverter_map = {}
        
        # iterate over inverters
        for id, info in data.items():
            self.inverter_map[id] = info['UniqueID']

    def process(self, metric: str, response: Dict) -> List[Dict]:
        tpl = self._check_response(response)
        if not tpl:
            return []
        timestamp, data = tpl   

        if metric in ["CumulationInverterData", "CommonInverterData", "3PInverterData", "MinMaxInverterData"]:
            collection = response['Head']['RequestArguments']['DataCollection']
            device_id = response['Head']['RequestArguments']['DeviceId']
            return self._process_inverter_data(device_id, collection, timestamp, data)
        elif metric == "MeterRealtimeData":
            return self._process_meter_data(timestamp, data)
        elif metric == "PowerFlowRealtimeData":
            return self._process_power_flow_data(timestamp, data)
        else:
            raise ValueError(f"Metric '{metric}' not supported yet")

    def _process_inverter_data(self, device_id: str, collection: str, timestamp: str, data: Dict) -> List[Dict]:
        self.logger.debug(f"process device_id={device_id}, {collection}, {timestamp}: {data}")
        if collection == 'CommonInverterData':
            device_status = {
                'measurement': 'InverterDeviceStatus',
                'time': timestamp,
                'fields': data['DeviceStatus'],
                'tags': {
                    'DeviceId': device_id,
                    'Serial': self.inverter_map.get(device_id, "None")
                }
            }

            inverter_data = {
                'measurement': collection,
                'time': timestamp,
                'fields': {
                    'IAC': _get_float_value(data, 'IAC'),
                    'UAC': _get_float_value(data, 'UAC'),
                    'PAC': _get_float_value(data, 'PAC'),
                    'FAC': _get_float_value(data, 'FAC'),
                    'IDC_MPP1': _get_float_value(data, 'IDC'),
                    'UDC_MPP1': _get_float_value(data, 'UDC'),
                    'DAY_ENERGY': _get_float_value(data, 'DAY_ENERGY'),
                    'YEAR_ENERGY': _get_float_value(data, 'YEAR_ENERGY'),
                    'TOTAL_ENERGY': _get_float_value(data, 'TOTAL_ENERGY'),
                },
                'tags': {
                    'DeviceId': device_id,
                    'Serial': self.inverter_map.get(device_id, "None")
                }
            }

            # add additional fields for Symo GEN24
            if 'SAC' in data:
                inverter_data['fields']['SAC'] = _get_float_value(data, 'SAC')
            if 'IDC_2' in data:
                inverter_data['fields']['IDC_MPP2'] = _get_float_value(data, 'IDC_2')
                inverter_data['fields']['UDC_MPP2'] = _get_float_value(data, 'UDC_2')
            if 'IDC_3' in data:
                inverter_data['fields']['IDC_MPP3'] = _get_float_value(data, 'IDC_3')
                inverter_data['fields']['UDC_MPP3'] = _get_float_value(data, 'UDC_3')
            if 'IDC_4' in data:
                inverter_data['fields']['IDC_MPP4'] = _get_float_value(data, 'IDC_4')
                inverter_data['fields']['UDC_MPP4'] = _get_float_value(data, 'UDC_4')

            return [device_status, inverter_data]
        elif collection == '3PInverterData':
            return [
                {
                    'measurement': collection,
                    'time': timestamp,
                    'fields': {
                        'IAC_L1': _get_float_value(data, 'IAC_L1'),
                        'IAC_L2': _get_float_value(data, 'IAC_L2'),
                        'IAC_L3': _get_float_value(data, 'IAC_L3'),
                        'UAC_L1': _get_float_value(data, 'UAC_L1'),
                        'UAC_L2': _get_float_value(data, 'UAC_L2'),
                        'UAC_L3': _get_float_value(data, 'UAC_L3'),
                    },
                    'tags': {
                        'DeviceId': device_id,
                        'Serial': self.inverter_map.get(device_id, "None")
                    }
                }
            ]
        elif collection == 'MinMaxInverterData':
            return [
                {
                    'measurement': collection,
                    'time': timestamp,
                    'fields': {
                        'DAY_PMAX': _get_float_value(data, 'DAY_PMAX'),
                        'DAY_UACMAX': _get_float_value(data, 'DAY_UACMAX'),
                        'DAY_UDCMAX': _get_float_value(data, 'DAY_UDCMAX'),
                        'YEAR_PMAX': _get_float_value(data, 'YEAR_PMAX'),
                        'YEAR_UACMAX': _get_float_value(data, 'YEAR_UACMAX'),
                        'YEAR_UDCMAX': _get_float_value(data, 'YEAR_UDCMAX'),
                        'TOTAL_PMAX': _get_float_value(data, 'TOTAL_PMAX'),
                        'TOTAL_UACMAX': _get_float_value(data, 'TOTAL_UACMAX'),
                        'TOTAL_UDCMAX': _get_float_value(data, 'TOTAL_UDCMAX'),
                    }
                }
            ]
        elif collection == 'CumulationInverterData':
            return [
                {
                    'measurement': collection,
                    'time': timestamp,
                    'fields': {
                        'PAC': _get_float_value(data, 'PAC'),
                        'DAY_ENERGY': _get_float_value(data, 'DAY_ENERGY'),
                        'YEAR_ENERGY': _get_float_value(data, 'YEAR_ENERGY'),
                        'TOTAL_ENERGY': _get_float_value(data, 'TOTAL_ENERGY'),
                    },
                    'tags': {
                        'DeviceId': device_id,
                        'Serial': self.inverter_map.get(device_id, "None")
                    }
                }
            ]
        else:
            raise DataCollectionError("Unknown data collection type.")
        
    def _process_meter_data(self, timestamp: str, data_map: Dict) -> List[Dict]:
        data_list = []

        # iterate over smart meter dictionary
        for id, data in data_map.items():
            # check SmartMeter type
            details = data['Details']

            if details["Manufacturer"] == "Fronius":
                if details['Model'] not in ['Smart Meter 63A-3', 'Smart Meter 50kA-3', 'Smart Meter TS 65A-3', 'Smart Meter TS 5kA-3']:
                    self.logger.warning(f"Unsupported SmartMeter type: {details['Model']}")
                    continue

                meter_timestamp = datetime.datetime.utcfromtimestamp(int(data['TimeStamp']))

                # Dataformat for SmartMeter TS65A-3
                meter_data = {
                    'measurement': 'MeterRealtimeData',
                    'time': meter_timestamp,
                    'fields': {
                        'IAC_L1': _get_float(data, 'Current_AC_Phase_1'),
                        'IAC_L2': _get_float(data, 'Current_AC_Phase_2'),
                        'IAC_L3': _get_float(data, 'Current_AC_Phase_3'),
                        'IAC_Sum': _get_float(data, 'Current_AC_Sum'),
                        'Enable': _get_int(data, 'Enable'),
                        'E_VArAC_Consumed': _get_float(data, 'EnergyReactive_VArAC_Sum_Consumed'),
                        'E_VArAC_Produced': _get_float(data, 'EnergyReactive_VArAC_Sum_Produced'),
                        'E_WAC_Minus_Absolute': _get_float(data, 'EnergyReal_WAC_Minus_Absolute'),  # system specific view
                        'E_WAC_Plus_Absolute': _get_float(data, 'EnergyReal_WAC_Plus_Absolute'),    # system specific view
                        'E_WAC_Consumed': _get_float(data, 'EnergyReal_WAC_Sum_Consumed'),      # meter specific view
                        'E_WAC_Produced': _get_float(data, 'EnergyReal_WAC_Sum_Produced'),      # meter specific view
                        'Freq_Avg': _get_float(data, 'Frequency_Phase_Average'),
                        'Meter_Location_Current': _get_float(data, 'Meter_Location_Current'),
                        'S_L1': _get_float(data, 'PowerApparent_S_Phase_1'),
                        'S_L2': _get_float(data, 'PowerApparent_S_Phase_2'),
                        'S_L3': _get_float(data, 'PowerApparent_S_Phase_3'),
                        'S_Sum': _get_float(data, 'PowerApparent_S_Sum'),
                        'CosPhi_L1': _get_float(data, 'PowerFactor_Phase_1'),
                        'CosPhi_L2': _get_float(data, 'PowerFactor_Phase_2'),
                        'CosPhi_L3': _get_float(data, 'PowerFactor_Phase_3'),
                        'CosPhi_Sum': _get_float(data, 'PowerFactor_Sum'),
                        'Q_L1': _get_float(data, 'PowerReactive_Q_Phase_1'),
                        'Q_L2': _get_float(data, 'PowerReactive_Q_Phase_2'),
                        'Q_L3': _get_float(data, 'PowerReactive_Q_Phase_3'),
                        'Q_Sum': _get_float(data, 'PowerReactive_Q_Sum'),
                        'P_L1': _get_float(data, 'PowerReal_P_Phase_1'),
                        'P_L2': _get_float(data, 'PowerReal_P_Phase_2'),
                        'P_L3': _get_float(data, 'PowerReal_P_Phase_3'),
                        'P_Sum': _get_float(data, 'PowerReal_P_Sum'),
                        'Visible': _get_int(data, 'Visible'),
                        'UAC_L1-L2': _get_float(data, 'Voltage_AC_PhaseToPhase_12'),
                        'UAC_L2-L3': _get_float(data, 'Voltage_AC_PhaseToPhase_23'),
                        'UAC_L3-L1': _get_float(data, 'Voltage_AC_PhaseToPhase_31'),
                        'UAC_L1': _get_float(data, 'Voltage_AC_Phase_1'),
                        'UAC_L2': _get_float(data, 'Voltage_AC_Phase_2'),
                        'UAC_L3': _get_float(data, 'Voltage_AC_Phase_3'),
                    },
                    'tags': {
                        'Model': details['Model'],
                        'Serial': details['Serial'],
                        'DeviceId': id
                    }
                }

                data_list.append(meter_data)
            else:
                self.logger.warning(f"Unsupported SmartMeter manufacturer: {details['Manufacturer']}")

        return data_list
    
    def _process_power_flow_data(self, timestamp: str, data: Dict) -> List[Dict]:
        data_list = []

        # Iterate over inverters
        for device_id, inverter in data['Inverters'].items():
            inverter_data = {
                'measurement': 'PowerFlowDataInverter',
                'time': timestamp,
                'fields': {
                    'E_Day': _get_float(inverter, 'E_Day'),
                    'E_Total': _get_float(inverter, 'E_Total'),
                    'E_Year': _get_float(inverter, 'E_Year'),
                    'P': _get_float(inverter, 'P'),
                },
                'tags': {
                    'DeviceId': device_id,
                    'Serial': self.inverter_map.get(device_id, "None"),
                    'Version': _get_string(data, 'Version'),
                },
            }
            if 'Battery_Mode' in inverter:
                inverter_data['fields']['Battery_Mode'] = _get_string(inverter, 'Battery_Mode')
            if 'SOC' in inverter:
                inverter_data['fields']['SOC'] = _get_float(inverter, 'SOC')

            data_list.append(inverter_data)

        # Map primary SmartMeter data
        site_data = data['Site']
        meter_data = {
            'measurement': 'PowerFlowDataSite',
            'time': timestamp,
            'fields': {
                'BackupMode': _get_bool(site_data, 'BackupMode'),
                'E_Day': _get_float(site_data, 'E_Day'),
                'E_Total': _get_float(site_data, 'E_Total'),
                'E_Year': _get_float(site_data, 'E_Year'),
                'Mode': _get_string(site_data, 'Mode'),
                'P_Akku': _get_float(site_data, 'P_Akku'),
                'P_Grid': _get_float(site_data, 'P_Grid'),
                'P_Load': _get_float(site_data, 'P_Load'),
                'P_PV': _get_float(site_data, 'P_PV'),
                'rel_Autonomy': _get_float(site_data, 'rel_Autonomy'),
                'rel_SelfConsumption': _get_float(site_data, 'rel_SelfConsumption'),
            },
            'tags': {
                'Version': _get_string(data, 'Version'),
                'Location': _get_string(site_data, 'Meter_Location'),
            },
        }
        if 'BatteryStandby' in site_data:
            meter_data['fields']['BatteryStandby'] = _get_bool(site_data, 'BatteryStandby')

        data_list.append(meter_data)

        # TODO Map Secondary Meters

        # TODO Map Smartloads

        return data_list
