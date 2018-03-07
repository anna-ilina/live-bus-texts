#from auth import OCTRANSPO_ID, OCTRANSPO_KEY
import os
import json
import requests
import psycopg2


OCTRANSPO_ID = os.environ['OCTRANSPO_ID']
OCTRANSPO_KEY = os.environ['OCTRANSPO_KEY']
BASE_URL = "https://api.octranspo1.com/v1.2/"
MAX_TRIES_TO_ENTER_VALID_ROUTE_NO = 5


#todo: decode accented french vowels
#todo: allow user to retry if they entered the wrong stop code/name. Use input key, maybe "restart"
#todo: some stops serve too many routes to fit in one text. Shorten output.
#todo: allow user to enter multiple routes
#todo: set a limit on number of routes a user can enter at a time. To stay within text message limit.
#todo: deal with "STATION" vs "STN" text input
#todo: check why some STOP_CODES in stops.txt are not unique (correspond to several different STOP_ID's)?
#todo: some bus stations are named unintuitively, such as "BASELINE 1B". Fix. --> "BASELINE STATION"
#todo: look into why some bus stops have missing stop_code in google_transit/stops.txt


def defaultParams():
    return {'appID': OCTRANSPO_ID, 'apiKey': OCTRANSPO_KEY, 'format': "JSON"}


def getRouteSummaryStop(stopCode):
    payload = defaultParams()
    payload['stopNo'] = stopCode
    r = requests.post(BASE_URL + "GetRouteSummaryForStop", params=payload)
    return r.json()


def parseRouteSummaryStop(r):
    stopCode = int(r['GetRouteSummaryForStopResult']['stopCode'])
    stopName = r['GetRouteSummaryForStopResult']['StopDescription']
    routes = []
    for route in r['GetRouteSummaryForStopResult']['Routes']['Route']:
        routeNo = int(route['RouteNo'])
        routeHeading = route['RouteHeading']#.encode('utf-8')
        if routeHeading != "":
            routes.append([routeNo, routeHeading])
        else:
            direction = route['Direction']#.encode('utf-8')
            routes.append([routeNo, direction])
    return stopCode, stopName, routes


def printRoutesForStop(stopCode, stopName, routes):
    print("All routes for {} (stop#{}):".format(stopName, stopCode))
    result = ""
    for route in routes:
        print ("{} {}".format(route[0], route[1]))
        result = result + ("{} {}\n".format(route[0], route[1]))
    return result


def getNextTripsForStop(stopCode, routeNo):
    payload = defaultParams()
    payload['routeNo'] = routeNo
    payload['stopNo'] = stopCode
    r = requests.post(BASE_URL + "GetNextTripsForStop", params=payload)
    return r.json()


# AdjustedScheduleTime is the number of minutes to the arrival of the bus to that stop.
# AdjustmentAge is the number of minutes since AdjustedScheduleTime was updated.
# If the AdjustmentAge is a negative value, it indicates that the AdjustedScheduleTime contains the planned scheduled time.
def parseNextTripsForStop(r):
    routesByDirection = r['GetNextTripsForStopResult']['Route']['RouteDirection']
    trips = []
    if not isinstance(routesByDirection, list):      #some bus stops have multiple directions and store this in a list
        routesByDirection = [routesByDirection]
    for routeDir in routesByDirection:
        routeNo = routeDir['RouteNo']
        direction = routeDir['Direction']
        tripsThisDirection = []
        if routeDir['Trips'] == {}:
            print("No more buses scheduled today for route {} {}.".format(int(routeNo), direction))
        else:
            for trip in routeDir['Trips']['Trip']:
                timeEstimateIsLive = True
                destination = trip['TripDestination']
                minutesToArrival = int(trip['AdjustedScheduleTime'])
                gpsLastAdjusted = float(trip['AdjustmentAge'])      #number of minutes since AdjustedScheduleTime was last updated
                if gpsLastAdjusted < 0:
                    timeEstimateIsLive = False
                tripsThisDirection.append([routeNo, destination, minutesToArrival, timeEstimateIsLive])
            trips.append({'Direction': direction, 'Trips': tripsThisDirection})
    return trips


def printNextTripsForStop(stopCode, tripsByDirection, cur):
    stopName = getBusStopNameFromStopCode(stopCode, cur)
    result = ""
    print(stopName)
    result = stopName + "\n"
    for direction in tripsByDirection:
        print(direction)
        print("Next {} trips:".format(direction['Direction']))
        result = result + ("Next {} trips:\n".format(direction['Direction']))
        for trip in direction['Trips']:
            if trip[3] == True:             # arrival time is live (gps-adjusted)
                print("{} {} arrives in {} minutes (GPS).".format(trip[0], trip[1], trip[2]))
                result = result + ("{} {} arrives in {} minutes (GPS).\n".format(trip[0], trip[1], trip[2]))
            else:                           # GPS data not available. Arrival time by schedule
                print("{} {} arrives in {} minutes (not GPS).".format(trip[0], trip[1], trip[2]))
                result = result + ("{} {} arrives in {} minutes (not GPS).\n".format(trip[0], trip[1], trip[2]))
    return result


def getNextTripsForStopAllRoutes(stopCode):
    payload = defaultParams()
    payload['stopCode'] = stopCode
    r = requests.post(BASE_URL + "GetNextTripsForStopAllRoutes", params=payload)
    return r.json()


def getAllBusStops(file):
    with open(file, 'r') as infile:
        lines = infile.readlines()
        busStops = []
        for line in lines[1:]:      #ignore header line
            line = line.split(',')
            stopCode = line[1]
            stopName = line[2]
            stopName = stopName.replace("\"", "") # get rid of quotation marks
            busStops.append([stopCode, stopName])
    return busStops


def getBusStopInput(cityBusStops):
    validStopNumbers = [int(x) for x,_ in cityBusStops if x != ''] 
    cityBusStopNames = [y.replace("'", "") for _,y in cityBusStops]
    cityBusStopNames = [y.replace('.', "") for y in cityBusStopNames]
    cityBusStopNames = [y.upper() for y in cityBusStopNames]
    cityBusStopNames = [y.replace("\\", "/") for y in cityBusStopNames] # replace back slashes with forward slashes

    while(True):
        busStopInput = input("Please enter bus stop name or 4-digit stop number: ")
        try:
            # see if user entered a bus stop code
            stop = busStopInput.strip()
            stop = int(busStopInput)
            if stop in validStopNumbers:
                return stop
            else:
                print("Invalid bus stop number entered. Try again.")
        except:
            # assume user entered a bus stop name
            busStopInput = busStopInput.upper()
            busStopInput = busStopInput.replace("'", "")        #get rid of quotes
            busStopInput = busStopInput.replace(".", "")        #get rid of periods
            busStopInput = busStopInput.replace("/", " / ")
            busStopInput = busStopInput.replace(" AND ", " / ")
            busStopInput = busStopInput.replace("&", " / ")
            busStopInput = busStopInput.replace("+", " / ")
            busStopInput = ' '.join(busStopInput.split())       #get rid of double spaces
            try:
                index = cityBusStopNames.index(busStopInput)
                stopCode = cityBusStops[index][0]
                return int(stopCode)
            except:
                print("Unable to find stop with given name. Please try again.")


def formatStopName(busStopInput):
    busStopInput = busStopInput.upper()
    busStopInput = busStopInput.replace("'", "")        #get rid of quotes      #todo: format db similarly
    busStopInput = busStopInput.replace(".", "")        #get rid of periods
    busStopInput = busStopInput.replace("/", " / ")
    busStopInput = busStopInput.replace(" AND ", " / ")
    busStopInput = busStopInput.replace("&", " / ")
    busStopInput = busStopInput.replace("+", " / ")
    busStopInput = ' '.join(busStopInput.split())       #get rid of double spaces
    return busStopInput


def isValidStopCode(stopCode, cur, conn):
    try:
        cur.execute("SELECT * FROM stops WHERE stop_code = %s", (stopCode,))
        # print(cur.fetchone()) # returns None, if invalid stop
        # print(cur.fetchall()) # returns [], if invalid stop
        if cur.fetchone() is None:
            print("Invalid stop code")
            return False
        else:
            return True
    except:
        conn.rollback()
        return False


def getBusStopNameFromStopCode(stopCode, cur):
    cur.execute("SELECT stop_name FROM stops WHERE stop_code = %s", (stopCode,))
    return cur.fetchone()[0] #todo: what if null value?


def getBusStopCodeFromStopName(stopName, cur):
    stopName = formatStopName(stopName)
    print(stopName)
    cur.execute("SELECT stop_code FROM stops WHERE stop_name = %s", (stopName,))
    stopCode = cur.fetchon()
    if stopCode is None:
        return None
    stopCode = cur.fetchone()[0]
    print("test")
    print(stopCode)
    print(cur.fetchall())
    return stopCode


def getRouteNumberInput(routes):
    counter = 0
    validRouteNumbers = [x for x,_ in routes]
    routeNumbers = []
    while(counter < MAX_TRIES_TO_ENTER_VALID_ROUTE_NO):
        routeNoInput = input("Please enter the route number(s) you are interested in (just the number(s)): ")
        routeNoInput = routeNoInput.replace(",", " ")   #in case user separated number by commas
        routes = routeNoInput.split()
        for route in routes:
            try:
                routeNo = int(route)
                if routeNo in validRouteNumbers:
                    routeNumbers.append(routeNo)
                else: 
                    print("Selected stop does not service route number {}. Try again.".format(routeNo))
                    break
            except:
                print("Non-numeric route number entered. Try again.")
                break
            counter += 1
        return routeNumbers
    print("You have entered an invalid route number {} times. Please start again from beginning.".format(counter))
    exit(1)


# Have the user enter bus stop code, followed by a single bus route
def parseStopAndRouteInput(inputText, cur, conn):
    inputWords = inputText.split()
    route = inputWords[-1]
    stop = " ".join(inputWords[:-1])
    if isValidStopCode(stop, cur, conn):
        return int(stop), int(route)
    else:
        try:
            print(stop)
            stopCode = getBusStopCodeFromStopName(stop, cur)
            #todo: check if bad stopname, will it cause exception?
            return int(stopCode), int(route)
        except psycopg2.Error as e:
            print("Invalid stop code or stop name.")
            print(e.diag.severity)
            print(e.diag.message_primary)
    return None, None


def main():
    cityBusStops = getAllBusStops("google_transit/stops.txt")

    stopCode = getBusStopInput(cityBusStops)
    stopName = getBusStopNameFromStopCode(stopCode, cityBusStops)
    print("You have selected {} (stop#{}).".format(stopName, stopCode))

    r = getRouteSummaryStop(stopCode)
    stopCode, stopName, routes = parseRouteSummaryStop(r)
    resultText = printRoutesForStop (stopCode, stopName, routes)

    routeNumbers = getRouteNumberInput(routes)
    for routeNo in routeNumbers:
        r = getNextTripsForStop(stopCode, routeNo)
        trips = parseNextTripsForStop(r)
        resultText = printNextTripsForStop(stopCode, trips)

    # r = getNextTripsForStopAllRoutes(3017)


if __name__ == '__main__':
    main()