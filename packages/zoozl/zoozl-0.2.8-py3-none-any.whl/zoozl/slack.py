"""Slack functions to route slack events for chat completion."""

import json
from urllib import request

import slack_sdk

from zoozl.chatbot import Message


def get_attachments(body, slack_token):
    """Return list of attachments from body.

    Return list of tuples of (binary, file_type).
    """
    files = []
    for f_body in body.get("files", []):
        file_type = f_body["filetype"]
        fname = f_body["url_private_download"]
        binary = get_slack_file(fname, slack_token)
        files.append((binary, file_type))
    return files


def get_slack_file(private_url, token):
    """Download slack private url."""
    req = request.Request(private_url, headers={"Authorization": f"Bearer {token}"})
    with request.urlopen(req) as response:
        return response.read()


def send_slack(slack_token: str, channel: str, message: Message):
    """Send a Slack message."""
    for part in message.parts:
        if part.binary:
            client = slack_sdk.WebClient(token=slack_token)
            client.files_upload_v2(
                channel=channel,
                title=part.text,
                file=part.binary,
                filename=part.filename,
            )
        else:
            headers = {"Authorization": f"Bearer {slack_token}"}
            headers["Content-type"] = "application/json"
            data = {"channel": channel, "text": part.text}
            req = request.Request(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                data=json.dumps(data).encode(),
                method="POST",
            )
            with request.urlopen(req):
                pass
