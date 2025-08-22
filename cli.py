#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "requests==2.32.5",
# ]
# ///

import sys
import argparse

import requests

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--markdown", action="store_true", help="send markdown message")
parser.add_argument("text", help="the content to send")
parser.add_argument("-t", "--to", help="the target to send to")
parser.add_argument("-u", "--url", help="the url to send to", default="http://localhost:8000")

def send_text(text, to=None):
    url = f"{args.url}/text"
    j = {"text": text}
    if to:
        j["to"] = to
    r = requests.post(url, json=j)
    print(r.text)
    
def send_markdown(text, to=None):
    url = f"{args.url}/markdown"
    j = {"text": text}
    if to:
        j["to"] = to
    r = requests.post(url, json=j)
    print(r.text)
    
if __name__ == "__main__":
    args = parser.parse_args()
    text = args.text
    if text == '-':
        text = sys.stdin.read()
    if args.markdown:
        send_markdown(text, args.to)
    else:
        send_text(text, args.to)