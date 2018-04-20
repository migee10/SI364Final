import requests
import json


API_KEY = "AIzaSyAmME85rRtDtzUW9-5svLd7vcT3No6e4pQ"
#Using the Google API, users will be able to search for a specific business based off a term. The default location right now is San Francisco, however, I am thinking about letting the user play with the location in the future.
def googletest(query):
    latitude = '37.7749295,-122.4194155'
    params = {}
    result =requests.get( 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+latitude+'&radius=900&types=food&name='+query+'&key='+API_KEY, params = params)

    jsondata = json.loads(result.text)
    print(jsondata['results'][0]['name'])
    print(jsondata['results'][0]['rating'])

if __name__ == '__main__':
	googletest("Taqueria")
