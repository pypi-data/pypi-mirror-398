from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

def slack_notify_failed(job_id,msg):
    slack_token = config['slack']['bot_auth']
    client = WebClient(token=slack_token)
    try:
        client.chat_postMessage(
            channel="C07KNHQS2G2",
            text=f"",
            attachments=[
                {
                    "color": "#ff0000",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": f"Failed\n Environment: {config['env']['env']}\n Job Id: {job_id}\n {msg}",
                                "emoji": True
                            }
                        }
                    ]
                }
            ]
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]