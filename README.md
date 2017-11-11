Google Hangouts Extractor
-------------------------

Requires Python 3.5+ and pipenv (pip install pipenv)

1. pipenv install && pipenv shell
2. Copy config.ini.example to config.ini and edit settings accordingly
3. Download credentials file as set out here: https://console.developers.google.com/apis/credentials/wizard?api=calendar-json.googleapis.com&project=electric-node-171809&authuser=1
4. Copy credentials file to this directory and save as *client_secret.json*
5. Run application (*python calendar-hangouts.py*) and grant permissions in browser as instructed
