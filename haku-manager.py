#!/bin/python3

import flask, requests
import time, json, threading

flaskApp = flask.Flask(__name__)

HOST = '127.0.0.1'
PORT = 8080

HAKUHOST = '127.0.0.1'
HAKUPORT = 8000

def new_event(msgDict):
    print(msgDict)
    try:
        requests.post(url=f'http://{HAKUHOST}:{HAKUPORT}/', json=msgDict)
    except Exception as e:
        print(e)

# 事件触发
@flaskApp.route('/', methods=['POST'])
def newMsg():
    msgDict = flask.request.get_json()
    newThread = threading.Thread(target=new_event, args=[msgDict], daemon=True)
    newThread.start()
    return ''


# 运行flask
if __name__ == "__main__":
    flaskApp.run(host=HOST, port=PORT, debug=False, threaded=False, processes=1)
