# SpeederBot

Fork of BerkshireCar/SpeederBot [here](https://github.com/BerkshireCar/SpeederBot)

## Not a Twitter bot

The upstream project is a Twitter bot, but this fork is not. This fork collects speeds, filtered to a specific location, and stores them in a database. The data is then used to generate a graph of the speeds over time.
There is a simple reason for this: In my capacity as a parish councillor and member of our Community Speedwatch team, I wanted to collect data on the speeds of vehicles passing through our village. This fork is the result.

There is a python script app/app.py which does all the work - although main.py has some useful early iterations of the code, before I refactored it to use a flask webserver.

## Requirements

- you must have a developer account with here.com and an API key so that you can access their traffic flow data
- you must have a postgres database to store the data (in this project I actually us the OmniIndex Postgresbc blockchain implementation as I am hyper vigilent with privacy and security) - using OmniIndex Postgresbc is optional, but you will need to change the code to use a standard postgres database - I prefer my data homomorphically encrypted and stored in a blockchain, but that's just me.

## Installation

1. Clone the repository
1. Create a virtual environment with `python -m venv venv`
1. Install the requirements with `pip install -r requirements.txt`
1. Run the app with `python app/app.py`

## Configuration

The app is configured with environment variables. The following are required:

`API_KEY`=<your api key>
`FILTER`=<your location filter eg. Tangmere>
`BBOX`=<the bounding box of choice eg. -0.722437,50.846435,-0.712888,50.855701>
`POSTGRES_HOST`=<ip address of your postgres server>
`POSTGRES_DB`=<database>
`POSTGRES_USER`=<username>
`POSTGRES_PASSWORD`=<user password>
`POSTGRES_PORT`=<database port>
`CHAIN`=<database scheme if using OmniIndex Postgresbc blockchain implementation>

## Usage

you will want to play with the output of some `curl` requests, I used postman to model the data first, so that I could see the 'location' description data first, then I could filter within the data for the specific location I wanted to monitor.

There are 4 endpoints:

- webserver:5000/ - this is the main page, which shows the graph of speeds over time
- webserver:5000/traffic-env - this allows you to update the .env file with the required environment variables for boundary box and location filter
- webserver:5000/traffic-data - this is the main endpoint, which collects the data from the here.com API and stores it in the database - my settings are to run every 5 seconds for an hour to build a sample
- webserver:5000/traffic-data-view - this is a simple endpoint to view the data in the database in a simple analytics table
