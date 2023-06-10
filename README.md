# Fronius Solar API v1 to InfluxDB
Collect Fronius inverter and Smartmeter data with Fronius Solar API v1 and put it into an InfluxDB database.

References:
- [Fronius Solar API](https://www.fronius.com/de/solarenergie/installateure-partner/technische-daten/alle-produkte/anlagen-monitoring/offene-schnittstellen/fronius-solar-api-json-)

# Setup
## Create own config file
Create a new configuration file (e.g. './config/my_config.yaml') for the user-specific system setup. You can use the configuration file './config/sample_config.yaml' as a template for creating your own configuration file.

## Local environment
Install python package and dependencies
```
cd fronius-solar-to-influxdb
pip install -e .
```

Run the application with your own config file.
```
python ./src/influx_bridge.py --config ./config/my_config.yaml
```

## Docker based environment
Build the docker image
```
cd fronius-solar-to-influxdb
docker build -t fronius-solar-to-influxdb:latest -f ./docker/Dockerfile .
```

Run application inside a docker container
```
docker run --rm -d --network host --name symo2influx -v ./config/:/config fronius-solar-to-influxdb:latest python -u ./src/influx_bridge.py --config /config/my_config.yaml
```

Show log output
```
docker logs -f symo2influx
```

## Development environment
Use `pip install -e .[dev]` to install development dependencies.

Run Flask Mock-Server
```
cd fronius-solar-to-influxdb
flask --app devserver/server.py run
```

# Credits
This project is inspired by [fronius-to-influx](https://github.com/szymi-/fronius-to-influx) and reuses some parts of the code, many thanks to [szymi-](https://github.com/szymi-).
