import sys
import pathlib
import configparser
import httplib2
import arrow

import slackclient

from apiclient import discovery

from oauth2client import client, tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Calendar Hangouts Extractor'
DIVIDER = "-" * 30


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


class Extractor:
    def __init__(self, cfg):
        self.cfg = cfg

    def get_credentials(self):
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

    def get_slack_client(self):
        slack_client = slackclient.SlackClient(
            self.cfg['slack']['token']
        )

        slack = Slack(slack_client, self.cfg['slack']['user'])
        return slack

    def create_event_message(self, event):

        # make a link readable by Android
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
                starts.to(self.cfg['DEFAULT']['timezone']).
                format("dddd DD/MM/YYYY HH:mm ZZ")
            )
        ]
        msg.append("*Hangout:* %s" % hangout_link)
        msg.append("*Attendees:* %s" % ", ".join(attendees))
        return "\r\n".join(msg)

    def run(self):

        http = self.get_credentials().authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        now = arrow.utcnow()

        time_min = now.to('UTC')
        time_max = now.replace(hours=+24).to('UTC')

        result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
                ).execute()
        events = [
            event for event in result.get('items', [])
            if 'hangoutLink' in event
        ]

        if not events:
            print("No Hangout events for 24 hours")
            return

        print(len(events), "Hangout event(s) for next 24 hours")

        message = [
            "*Hangout events for next 24 hours starting %s*" %
            now.format("DD/MM/YYYY HH:mm ZZ"),
            DIVIDER,
        ]

        slack = self.get_slack_client()

        for event in events:
            message.append(self.create_event_message(event))
            message.append(DIVIDER)

        print("\r\n".join(message))
        slack.post_message("\r\n".join(message))


if __name__ == "__main__":

    try:
        config_file = pathlib.Path(sys.argv[1])
    except IndexError:
        config_file = pathlib.Path(".") / "config.ini"

    if not config_file.exists():
        sys.stderr.write(
            "File %s not found!!!" % config_file
        )
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg.read([str(config_file)])

    ex = Extractor(cfg)
    ex.run()
