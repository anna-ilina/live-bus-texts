from flask import Flask, request
from twilio import twiml

#import * from main

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hummus runs the world!"

@app.route("/Jake")
def hello1():
    return "HUMMUSSSSS!"

@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    message_body = request.form['Body']

    resp = twiml.Response()
    resp.message('Hello {}, you said: {}'.format(number, message_body))
    return str(resp)


if __name__ == "__main__":
    #app.run(debug=True)
    app.run()