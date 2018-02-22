from auth import OCTRANSPO_ID, OCTRANSPO_KEY
import json
import requests

baseURL = "https://api.octranspo1.com/v1.2/"

# AdjustedScheduleTime is the number of minutes to the arrival of the bus to that stop.
# AdjustmentAge is the number of minutes since AdjustedScheduleTime was updated.
# If the AdjustmentAge is a negative value, it indicates that the AdjustedScheduleTime contains the planned scheduled time.

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
    for route in routes:
        print ("%d %s") % (route[0], route[1])

def getNextTripsForStop(routeNo, stopNo):
    payload = defaultParams()
    payload['routeNo'] = routeNo
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetNextTripsForStop", params=payload)
    return r.json()

def parseNextTripsForStop(r):
    routesByDirection = r['GetNextTripsForStopResult']['Route']['RouteDirection']
    trips = []
    for routeDir in routesByDirection:
        routeNo = routeDir['RouteNo']
        direction = routeDir['Direction']
        tripsThisDirection = []
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
    for direction in tripsByDirection:
        print("Next %s trips:") % (direction['Direction'])
        for trip in direction['Trips']:
            if trip[3] == True:             # arrival time is live (gps-adjusted)
                print("%d %s arrives in %d minutes (GPS).") % (trip[0], trip[1], trip[2])
            else:                           # GPS data not available. Arrival time by schedule
                print("%d %s arrives in %d minutes (not GPS).") % (trip[0], trip[1], trip[2])



def getNextTripsForStopAllRoutes(stopNo):
    payload = defaultParams()
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetNextTripsForStopAllRoutes", params=payload)
    return r.json()

def main():

    print("\nLet's check all buses for Baseline Station (stop#3017)...\n")

    r = getRouteSummaryStop(3017)
    # print(json.dumps(r, indent = 4))
    stopNo, stopName, routes = parseRouteSummaryStop(r)
    printRoutesForStop (stopNo, stopName, routes)

    print("\nLet's check arrival times for the 94...\n")

    r = getNextTripsForStop(94, 3017)
    # print (json.dumps(r, indent = 4))
    trips = parseNextTripsForStop(r)
    printNextTripsForStop(trips)

    #r = getNextTripsForStopAllRoutes(3017)



if __name__ == '__main__':
    main()