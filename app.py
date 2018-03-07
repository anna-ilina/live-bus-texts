from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from urllib import parse
import psycopg2
from main import *


app = Flask(__name__)

parse.uses_netloc.append("postgres")
url = parse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()

# def createStopsDatabase():

@app.route("/")
def hello():
    return "Hummus runs the world!"

@app.route("/Hummus")
def hello1():
    return "HUMMUSSSSS!"

@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    message_body = request.form['Body']

    stopCode, routeNo = parseStopAndRouteInput(message_body, cur, conn)
    if stopCode is None or routeNo is None:
        resultText = "Invalid stop or route. Please again."
    else:
        print("stopCode = " + str(stopCode))
        print("routeNo = " + str(routeNo))
        r = getNextTripsForStop(stopCode, routeNo)    
        print("r = " + str(r))
        trips = parseNextTripsForStop(r)
        print("trips = " + str(trips))
        resultText = printNextTripsForStop(stopCode, trips, cur)

    resp = MessagingResponse()
    # resp.message('Hello {}, you said: {}'.format(number, message_body))
    resp.message(resultText)
    return str(resp)


if __name__ == "__main__":
    #app.run(debug=True)
    app.run()