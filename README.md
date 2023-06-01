# Fronius Solar API v1 to InfluxDB
Collect Fronius inverter and SMA data with Fronius Solar API v1 and store it in InfluxDB

Resources:
- [Fronius Solar API](https://www.fronius.com/de/solarenergie/installateure-partner/technische-daten/alle-produkte/anlagen-monitoring/offene-schnittstellen/fronius-solar-api-json-)
- [Fronius OpenAPI interface spec file for GEN24/Tauro inverters](https://www.fronius.com/QR-link/0025)

# Setup
## Local environment
Install python package and dependencies
```
cd fronius-solar-to-influxdb
pip install -e .
```

Use `pip install -e .[dev]` to install development dependencies.

Run application
```
python ./src/influx_bridge.py --config ./config/dev_config.yaml
```

## Docker based environment
Build the docker image
```
cd fronius-solar-to-influxdb
docker build -t fronius-solar-to-influxdb:0.1.0 -f ./docker/Dockerfile .
```

Run application inside a docker container
```
docker run --rm -d --network host --name symo2influx -v ./config/:/config fronius-solar-to-influxdb:0.1.0 python -u ./src/influx_bridge.py --config /config/dev_config.yaml
```

Show log output
```
docker logs -f symo2influx
```

## Development
Run Test-Server
```
cd fronius-solar-to-influxdb
flask --app devserver/server.py run
```

# Credits
This project is inspired by [fronius-to-influx](https://github.com/szymi-/fronius-to-influx) and reuses some parts of the code, many thanks to [szymi-](https://github.com/szymi-).
