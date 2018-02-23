# from auth import OCTRANSPO_ID, OCTRANSPO_KEY
import os
import json
import requests

OCTRANSPO_ID = os.environ['OCTRANSPO_ID']
OCTRANSPO_KEY = os.environ['OCTRANSPO_KEY']

baseURL = "https://api.octranspo1.com/v1.2/"
MAX_TRIES_TO_ENTER_VALID_ROUTE_NO = 5

#todo: decode accented french vowels
#todo: allow user to retry if they entered the wrong stop code/name. Use input key, maybe "restart"
#todo: some stops serve too many routes to fit in one text. Shorten output.
#todo: set a limit on number of routes a user can enter at a time. To stay within text message limit.
#todo: deal with "STATION" vs "STN" text input
#todo: check why some STOP_CODES in stops.txt correspond to several different STOP_ID's ?
#todo: some bus stations are named unintuitively, such as "BASELINE 1B". Fix.
#todo: new users need to be verified (?)


def defaultParams():
    return {'appID': OCTRANSPO_ID, 'apiKey': OCTRANSPO_KEY, 'format': "JSON"}


def getRouteSummaryStop(stopNo):
    payload = defaultParams()
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetRouteSummaryForStop", params=payload)
    return r.json()


def parseRouteSummaryStop(r):
    stopNo = int(r['GetRouteSummaryForStopResult']['StopNo'])
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
    return stopNo, stopName, routes


def printRoutesForStop(stopNo, stopName, routes):
    print("All routes for %s (stop#%s):") % (stopName, stopNo)
    result = ""
    for route in routes:
        print ("%d %s") % (route[0], route[1])
        result = result + ("%d %s\n") % (route[0], route[1])
    return result



def getNextTripsForStop(routeNo, stopNo):
    payload = defaultParams()
    payload['routeNo'] = routeNo
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetNextTripsForStop", params=payload)
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
            print("No more buses scheduled today for route %d %s.") % (int(routeNo), direction)
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


def printNextTripsForStop(tripsByDirection):
    result = ""
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


def getNextTripsForStopAllRoutes(stopNo):
    payload = defaultParams()
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetNextTripsForStopAllRoutes", params=payload)
    return r.json()


def getAllBusStops(file):
    with open(file, 'rb') as infile:
        lines = infile.readlines()
        busStops = []
        for line in lines[1:]:      #ignore header line
            line = line.split(",")
            stopNo = line[1]
            stopName = line[2]
            stopName = stopName.replace("\"", "") # get rid of quotation marks
            busStops.append([stopNo, stopName])
    return busStops


def getBusStopInput(cityBusStops):
    validStopNumbers = [int(x) for x,_ in cityBusStops if x != ''] 
    cityBusStopNames = [y.replace("'", "") for _,y in cityBusStops]
    cityBusStopNames = [y.replace('.', "") for y in cityBusStopNames]
    cityBusStopNames = [y.upper() for y in cityBusStopNames]
    cityBusStopNames = [y.replace("\\", "/") for y in cityBusStopNames] # replace back slashes with forward slashes

    while(True):
        busStopInput = raw_input("Please enter bus stop name or 4-digit stop number: ")
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
                stopNo = cityBusStops[index][0]
                return int(stopNo)
            except:
                print("Unable to find stop with given name. Please try again.")

#todo: finish this function
def getBusStopCodeFromInput(stopInput, cityBusStops):
    pass

def getBusStopNameFromStopCode(stopNo, cityBusStops):
    cityBusStopNumbers = [int(x) if x != '' else x for x,_ in cityBusStops] 
    index = cityBusStopNumbers.index(stopNo)
    stopName = cityBusStops[index][1]
    return stopName


def getRouteNumberInput(routes):
    counter = 0
    validRouteNumbers = [x for x,_ in routes]
    routeNumbers = []
    while(counter < MAX_TRIES_TO_ENTER_VALID_ROUTE_NO):
        routeNoInput = raw_input("Please enter the route number(s) you are interested in (just the number(s)): ")
        routeNoInput = routeNoInput.replace(",", " ")   #in case user separated number by commas
        routes = routeNoInput.split()
        for route in routes:
            try:
                routeNo = int(route)
                if routeNo in validRouteNumbers:
                    routeNumbers.append(routeNo)
                else: 
                    print("Selected stop does not service route number %d. Try again.") %(routeNo)
                    break
            except:
                print("Non-numeric route number entered. Try again.")
                break
            counter += 1
        return routeNumbers
    print("You have entered an invalid route number %d times. Please start again from beginning.")
    exit(1)

# Have the user enter bus stop code, followed by a single bus route
def parseStopAndRouteInput(inputText):
    inputWords = inputText.split()
    route = inputWords[-1]
    stop = " ".join(inputWords[:-1])
    return int(stop), int(route)

def main():
    cityBusStops = getAllBusStops("google_transit/stops.txt")

    stopNo = getBusStopInput(cityBusStops)
    stopName = getBusStopNameFromStopCode(stopNo, cityBusStops)
    print("You have selected %s (stop#%d).") % (stopName, stopNo)

    r = getRouteSummaryStop(stopNo)
    stopNo, stopName, routes = parseRouteSummaryStop(r)
    resultText = printRoutesForStop (stopNo, stopName, routes)

    routeNumbers = getRouteNumberInput(routes)
    for routeNo in routeNumbers:
        r = getNextTripsForStop(routeNo, stopNo)
        trips = parseNextTripsForStop(r)
        resultText = printNextTripsForStop(trips)

    # r = getNextTripsForStopAllRoutes(3017)


if __name__ == '__main__':
    main()