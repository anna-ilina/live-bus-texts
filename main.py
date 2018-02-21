from auth import ID, KEY
import requests

baseURL = "https://api.octranspo1.com/v1.2/"

def defaultParams():
    return {'appID': ID, 'apiKey': KEY, 'format': "JSON"}

def getRouteSummaryStop(stopNo):
    payload = defaultParams()
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetRouteSummaryForStop", params=payload)
    return r.json()

def getNextTripsForStop(routeNo, stopNo):
    payload = defaultParams()
    payload['routeNo'] = routeNo
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetNextTripsForStop", params=payload)
    return r.json()

def getNextTripsForStopAllRoutes(stopNo):
    payload = defaultParams()
    payload['stopNo'] = stopNo
    r = requests.post(baseURL + "GetNextTripsForStopAllRoutes", params=payload)
    return r.json()

def main():
    print(getRouteSummaryStop(3017))
    print("")
    print(getNextTripsForStop(94, 3017))
    print("")
    print(getNextTripsForStopAllRoutes(3017))


if __name__ == '__main__':
    main()