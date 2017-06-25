Google Hangouts Extractor
-------------------------

Requires Python 3.5+

1. pip install -r requirements.txt
2. Set CATCHAFIRE_SLACK_TOKEN and CATCHAFIRE_SLACK_USERNAME in your environment (e.g. .bashrc) (See Slack dev pages to get your token)
3. Download credentials file as set out here: https://console.developers.google.com/apis/credentials/wizard?api=calendar-json.googleapis.com&project=electric-node-171809&authuser=1
4. Copy credentials file to this directory and save as *client_secret.json*
5. Run application (*python calendar-hangouts.py*) and grant permissions in browser as instructed
