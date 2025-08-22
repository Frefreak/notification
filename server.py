#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "pycryptodome==3.23.0",
#   "fastapi==0.116.1",
#   "uvicorn==0.35.0",
#   "pydantic==2.11.7",
#   "requests==2.32.5",
#   "python-dotenv==1.1.1",
# ]
# ///


import os
import base64
import json
import argparse
from pydantic import BaseModel

import requests
import uvicorn
import dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

import WXBizJsonMsgCrypt

parser = argparse.ArgumentParser()
parser.add_argument("-g", '--gen-env', action='store_true', help='generate .env file')
args = parser.parse_args()

if args.gen_env:
    print(f"TOKEN=")
    print(f"ENCODING_AES_KEY=")
    print(f"CORP_ID=")
    print(f"AGENT_ID=")
    print(f"AGENT_SECRET=")
    exit(0)

dotenv.load_dotenv()

TOKEN = os.getenv("TOKEN")
ENCODING_AES_KEY = os.getenv("ENCODING_AES_KEY")
CORP_ID = os.getenv("CORP_ID")
AGENT_ID = os.getenv("AGENT_ID")
AGENT_SECRET = os.getenv("AGENT_SECRET")

if not TOKEN or not ENCODING_AES_KEY or not CORP_ID or not AGENT_ID or not AGENT_SECRET:
    raise ValueError("Missing environment variables, please run with `-g` to generate an env file to start")


app = FastAPI()

crypto = WXBizJsonMsgCrypt.WXBizJsonMsgCrypt( TOKEN, ENCODING_AES_KEY, AGENT_ID)

wecom_cid = CORP_ID
wecom_aid = AGENT_ID
wecom_secret = AGENT_SECRET


def verify(msg_signature: str, timestamp: str, nonce: str, echostr: str):
    ret, echo_str = crypto.VerifyURL(msg_signature, timestamp, nonce, echostr)
    if ret == 0:
        return PlainTextResponse(echo_str)
    else:
        return PlainTextResponse(status_code=400, content="error")


def send_to_wecom(text, wecom_touid="@all"):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get("access_token")
    if access_token and len(access_token) > 0:
        send_msg_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "text",
            "text": {"content": text},
            "duplicate_check_interval": 600,
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


def send_to_wecom_image(base64_content, wecom_touid="@all"):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get("access_token")
    if access_token and len(access_token) > 0:
        upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image"
        upload_response = requests.post(
            upload_url, files={"picture": base64.b64decode(base64_content)}
        ).json()
        if "media_id" in upload_response:
            media_id = upload_response["media_id"]
        else:
            return False

        send_msg_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "image",
            "image": {"media_id": media_id},
            "duplicate_check_interval": 600,
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


def send_to_wecom_markdown(text, wecom_touid="@all"):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get("access_token")
    if access_token and len(access_token) > 0:
        send_msg_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
            "msgtype": "markdown",
            "markdown": {"content": text},
            "duplicate_check_interval": 600,
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


class SendRequest(BaseModel):
    text: str
    to: str = "@all"


def send_text(req: SendRequest):
    if not (r := send_to_wecom(req.text, req.to)):
        return PlainTextResponse(status_code=500, content="error")
    rj = json.loads(r)
    if 'errcode' in rj and rj['errcode'] != 0:
        return PlainTextResponse(status_code=500, content=rj['errmsg'])
    return PlainTextResponse(status_code=200, content=f"ok: {rj['msgid']}")

def send_markdown(req: SendRequest):
    if not (r := send_to_wecom_markdown(req.text, req.to)):
        return PlainTextResponse(status_code=500, content="error")
    rj = json.loads(r)
    if 'errcode' in rj and rj['errcode'] != 0:
        return PlainTextResponse(status_code=500, content=rj['errmsg'])
    return PlainTextResponse(status_code=200, content=f"ok: {rj['msgid']}")


app.add_api_route("/", verify, methods=["GET"])
app.add_api_route("/send", send_text, methods=["POST"])
app.add_api_route("/send/markdown", send_markdown, methods=["POST"])


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
