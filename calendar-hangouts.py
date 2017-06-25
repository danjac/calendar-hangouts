import os
import pathlib
import httplib2
import arrow

import slackclient

from apiclient import discovery

from oauth2client import client, tools
from oauth2client.file import Storage

# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Calendar Hangouts Extractor'
DIVIDER = "-" * 30
TIMEZONE = "Europe/Helsinki"


class Slack:
    def __init__(self, client, username):
        self.client = client
        self.username = username

    def post_message(self, msg):
        self.client.api_call(
            "chat.postMessage",
            username=APPLICATION_NAME,
            channel="@" + self.username,
            text=msg,
        )


def get_credentials():
    home_dir = pathlib.Path("~").expanduser()
    creds_dir = home_dir / ".credentials"
    creds_dir.mkdir(exist_ok=True)
    creds_file = creds_dir / "calendar-hangouts.json"

    store = Storage(str(creds_file))
    creds = store.get()

    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        creds = tools.run_flow(flow, store)
    return creds


def get_slack_client():
    slack_client = slackclient.SlackClient(
        os.environ['CATCHAFIRE_SLACK_TOKEN']
    )

    slack = Slack(slack_client, os.environ['CATCHAFIRE_SLACK_USERNAME'])
    return slack


def create_event_message(event):

    hangout_link = event['hangoutLink'].replace(
        "plus.google.com",
        "hangouts.google.com"
    )

    attendees = [
        attendee['email'] for attendee in event['attendees']
    ]
    attendees.sort()

    starts = arrow.get(event['start']['dateTime'])

    msg = [
        "*%s: %s*" % (
            event['summary'],
            starts.to(TIMEZONE).
            format("dddd DD/MM/YYYY HH:mm ZZ")
        )
    ]
    msg.append("*Hangout:* %s" % hangout_link)
    msg.append("*Attendees:* %s" % ", ".join(attendees))
    return "\r\n".join(msg)


def main():
    http = get_credentials().authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    now = arrow.utcnow()
    time_min = now.to('UTC')
    time_max = now.replace(days=+7).to('UTC')
    result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            #maxResults=10,
            singleEvents=True,
            orderBy='startTime'
            ).execute()
    events = [
        event for event in result.get('items', [])
        if 'hangoutLink' in event
    ]

    if not events:
        print("No Hangout events found for next week")
        return

    print(len(events), "Hangout event(s) next week")

    message = [
        "*Hangout events for next 7 days starting %s*" %
        now.format("DD/MM/YYYY"),
        DIVIDER,
    ]

    slack = get_slack_client()

    for event in events:
        message.append(create_event_message(event))
        message.append(DIVIDER)

    print("\r\n".join(message))
    slack.post_message("\r\n".join(message))


if __name__ == "__main__":
    main()
