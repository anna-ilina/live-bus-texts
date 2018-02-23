from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from main import *

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

    stopNo, routeNo = parseStopAndRouteInput(message_body)

    print("stopNo = " + str(stopNo))
    print("routeNo = " + str(routeNo))
    r = getNextTripsForStop(routeNo, stopNo)    #todo: reverse order of params for consistency
    print("r = " + str(r))
    trips = parseNextTripsForStop(r)
    print("trips = " + str(trips))
    resultText = printNextTripsForStop(trips)

    resp = MessagingResponse()
    # resp.message('Hello {}, you said: {}'.format(number, message_body))
    resp.message(resultText)
    return str(resp)


if __name__ == "__main__":
    #app.run(debug=True)
    app.run()