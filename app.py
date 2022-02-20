"""
PATH FINDER by Jae Park (JP), Jae Oh, Geonho Kim

Gunicorn, Flask, Twilio, Google Maps Platform API, GeoPy
"""

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

from dotenv import load_dotenv

from geopy.distance import distance
from operator import itemgetter
from collections import OrderedDict

import os
import logging
import requests
import threading

import googlemaps as gm

from pprint import pformat, pprint


logging.basicConfig(filename='.log', level=logging.DEBUG)

## Secrets
load_dotenv('.env')
TWILIO_ACCOUNT_SID  = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN   = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER       = os.getenv('TWILIO_NUMBER')
GOOGLE_MAP_API_KEY  = os.getenv('GOOGLE_MAP_API_KEY')

## API wrappers
app = Flask(__name__)
gmaps = gm.Client(key=GOOGLE_MAP_API_KEY)
twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

## Location bias for Athens for place search
# 5000 meters from the center of Athens
ATHENS_BIAS = "circle:5000@{},{}".format(33.95194635408134, -83.37511151075749)
URL = "https://routes.uga.edu/"

STOP = {}
STOP_TO_PATTERNS = {}
PATTERN_TO_STOPS = {}
PATTERN_TO_ROUTE = {}

## Message templates
HELP1 = "PATH FINDER for UGA campus transit made by Jae Park (JP), Jae Oh, and Geonho Kim.\n\n" \
         "If you tell us your location and the destination, we will provide you with the quickest way " \
         "to get to your destination!\n\nPlease send us a message in the following format:\n\nCURRENT LOCATION > DESTINATION"
         
HELP2 = "TIP! You can use any landmarks nearby to help us locate. For example, building, landmark, or street name."

INCORRECT = "Oops! I couldn't understand what you meant. Text HELP to learn how to use our service!"

FOUND = "Found! Take the {route_name} at {src_stop} and get off at {dst_stop}.\n\n" \
        "The bus will arrive in {src_arrival} minutes and will arrive at the destination stop in {dst_arrival} minutes."
    
NOTFOUND = ":( I could not find a route for you... Maybe try with another location?"  

        
pp = lambda x: pformat(x, indent=4, width=400)


def ask(endpoint, *args):
    if args: endpoint = endpoint.format(*args)
    res = requests.get(URL + endpoint)
    return res.json() if res.status_code == 200 else None 


def prepare():
    STOP.clear()
    STOP_TO_PATTERNS.clear()
    PATTERN_TO_STOPS.clear()
    PATTERN_TO_ROUTE.clear()
    
    routes_json = ask('region/0/routes')
    if routes_json: # routes
        for route_json in routes_json:
            route_id = route_json['ID']
            patterns = route_json['Patterns']
            
            for pattern in patterns: # patterns
                pattern_id = pattern['ID']
                PATTERN_TO_ROUTE[pattern_id] = route_id
                PATTERN_TO_STOPS[pattern_id] = set()
                
                stops_json = ask('route/{}/direction/{}/stops', pattern_id, route_id)
                for stop in stops_json: # stops
                    stop_id = stop['ID']
                    stop_name = stop['Name']
                    stop_lat = stop['Latitude']
                    stop_lng = stop['Longitude']
                    
                    if stop_id not in STOP:
                        STOP[stop_id] = (stop_name, stop_lat, stop_lng)
                    
                    if stop_id not in STOP_TO_PATTERNS:
                        STOP_TO_PATTERNS[stop_id] = set()
                    
                    STOP_TO_PATTERNS[stop_id].add(pattern_id)
                    PATTERN_TO_STOPS[pattern_id].add(stop_id)
                
    app.logger.debug('Prepared')
    app.logger.info(pp(STOP))
    app.logger.info(pp(STOP_TO_PATTERNS))
    app.logger.info(pp(PATTERN_TO_STOPS))
    app.logger.info(pp(PATTERN_TO_ROUTE))
            

def distance_to_stops(src):
    od = {stop_id: distance(src, (stop[1], stop[2])).ft for stop_id, stop in STOP.items()}
    return OrderedDict(sorted(od.items(), key=itemgetter(1)))


def best_stops(stops_dist):
    best_patterns = OrderedDict()
    best_stops = OrderedDict()
    for stop_id in stops_dist.keys():
        patterns = STOP_TO_PATTERNS[stop_id]
        
        candidates = set()
        
        for pattern in patterns:
            if pattern not in best_patterns:
                best_patterns[pattern] = stop_id
                candidates.add(pattern)
        
        if candidates:
            best_stops[stop_id] = candidates
    
    return best_stops, best_patterns

                

def walking_time(src, stop_ids):
    dests = [(STOP[sid][1], STOP[sid][2]) for sid in stop_ids]
    matrix = gmaps.distance_matrix(src, destinations=dests, mode='walking', units='imperial')
    return {stop_ids[i]: element['duration']['value'] for i, element in enumerate(matrix['rows'][0]['elements'])}
    
    
def duration_between(pattern, src_stop, dst_stop):
    src_arrival_routes = ask('stop/{}/arrivals', src_stop)
    dst_arrival_routes = ask('stop/{}/arrivals', dst_stop)
    
    if src_arrival_routes is None or dst_arrival_routes is None:
        return None
    
    src_arrivals = next(filter(lambda sar: sar['RouteID'] == pattern, src_arrival_routes), None)
    dst_arrivals = next(filter(lambda dar: dar['RouteID'] == pattern, dst_arrival_routes), None)
    
    if src_arrivals is None or dst_arrivals is None:
        return None
    
    src_arrivals = src_arrivals['Arrivals']
    dst_arrivals = dst_arrivals['Arrivals']
    
    src_arrival = src_arrivals[0]
    src_arrival_minutes = src_arrival['Minutes']
    src_vehicle_id = src_arrival['VehicleID']
    route_name = src_arrival['RouteName']
    
    dst_arrival = next(filter(lambda da: da['VehicleID'] == src_vehicle_id and da['Minutes'] > src_arrival_minutes, dst_arrivals), None)
    if dst_arrival is None:
        return None
    
    return src_arrival_minutes, dst_arrival['Minutes'], route_name
    

def find_route(src_str, dst_str, to):
    src = gmaps.find_place(
        input=src_str,
        input_type='textquery',
        fields=['geometry'],
        location_bias=ATHENS_BIAS
    )['candidates'][0]['geometry']['location']
    
    dst = gmaps.find_place(
        input=dst_str,
        input_type='textquery',
        fields=['geometry'],
        location_bias=ATHENS_BIAS
    )['candidates'][0]['geometry']['location']
    
    src_loc = src['lat'], src['lng']
    dst_loc = dst['lat'], dst['lng']
    
    src_to_stops = distance_to_stops(src_loc)
    dst_to_stops = distance_to_stops(dst_loc)
    
    src_best_stops, src_best_patterns = best_stops(src_to_stops)
    dst_best_stops, dst_best_patterns = best_stops(dst_to_stops)
    
    src_walking = walking_time(src_loc, list(src_best_stops.keys()))
    dst_walking = walking_time(dst_loc, list(dst_best_stops.keys()))
    
    best_route = None
    best_route_info = None
    best_time = None
    
    for src_pattern, src_stop_id in src_best_patterns.items():
        duration = duration_between(src_pattern, src_stop_id, dst_best_patterns[src_pattern])
        if duration:
            src_arrival_minutes, dst_arrival_minutes, route_name = duration
            if best_route is None or dst_arrival_minutes * 60 + dst_walking < best_time:
                best_route = src_pattern
                best_route_info = duration
                best_time = dst_arrival_minutes * 60 + dst_walking
    
    if best_route:
        src_arrival, dst_arrival, route_name = best_route_info
        src_stop = STOP[src_best_patterns[best_route]][0]
        dst_stop = STOP[dst_best_patterns[best_route]][0]
        
        twilio.messages.create(
            to, from_=TWILIO_NUMBER, 
            body=FOUND.format(route_name=route_name, src_stop=src_stop, dst_stop=dst_stop,
                              src_arrival=src_arrival, dst_arrival=dst_arrival)
        )
    else:
        twilio.messages.create(
            to, from_=TWILIO_NUMBER,
            body=NOTFOUND
        )
    
        
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    message = request.values
    from_ = message.get('From', None)
    body_ = message.get('Body', None)
    
    if body_.strip().upper() == "HELP":
        resp = MessagingResponse()
        resp.message(HELP1)
        resp.message(HELP2)
        return str(resp) 
            
    tokens = body_.split('>')
    if len(tokens) != 2:
        resp = MessagingResponse()
        resp.message(INCORRECT)
        return str(resp)
    
    src, dst = tokens
    src_str = src.strip()
    dst_str = dst.strip()
    threading.Thread(target=find_route, args=(src_str, dst_str, from_)).start()
    
    resp = MessagingResponse()
    resp.message(f"Finding the quickest bus route to get you from {src.capitalize()} to {dst.capitalize()}.\n\nPlease wait...")
    return str(resp)

prepare()