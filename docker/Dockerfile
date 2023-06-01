FROM python:3.9-slim-buster
WORKDIR /app

# upgrade pip
RUN python -m pip install --upgrade pip

# install dependencies
ADD ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# install python package
COPY . /app
RUN cd /app && \
    pip install .
