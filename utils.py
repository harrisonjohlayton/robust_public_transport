import requests
import pandas as pd
import math
from json.decoder import JSONDecodeError

#lists containing elevation data
stop_elevations = []
connection_elevations = []
#flag to determine if lists are loaded
loaded = False


def cache_elevations(stop_filename='data/stop_elevations.csv', connection_filename='data/connection_elevations.csv'):
    '''
    save elevation data in lists to file to speed up subsequent runs
    '''
    out_fd = open(stop_filename, 'w')
    for stop_elevation in stop_elevations:
        stop_id = stop_elevation[0]
        elevation = stop_elevation[1]
        out_fd.write(f'{stop_id},{elevation}\n')
    out_fd.close()

    out_fd = open(connection_filename, 'w')
    for connection in connection_elevations:
        stop_1_id = connection[0]
        stop_2_id = connection[1]
        elevation = connection[2]
        out_fd.write(f'{stop_1_id},{stop_2_id},{elevation}\n')
    out_fd.close()


def get_elevation(lat:float, lon:float, stop, stop_1_id, stop_2_id, stop_filename='data/stop_elevations.csv', connection_filename='data/connection_elevations.csv'):
    '''
    load elevation data for given latitude and longitude.
    this data is cached in a set of lists that are saved when the program exits.

    stop: indicated whether this elevation is for a stop (True) or connection (False)
    '''
    #load lists from file
    global loaded
    if (not loaded):
        #load elevations from saved file
        loaded = True
        in_fd = open(stop_filename, 'r')
        lines = in_fd.readlines()
        in_fd.close()
        for line in lines:
            words = line.split(',')
            if (len(words) < 2):
                continue
            next_stop_id = int(words[0])
            elevation = int(words[1])
            stop_elevations.append([next_stop_id, elevation])

        in_fd = open(connection_filename, 'r')
        lines = in_fd.readlines()
        in_fd.close()
        for line in lines:
            words = line.split(',')
            if (len(words) < 3):
                continue
            next_stop_1_id = int(words[0])
            next_stop_2_id = int(words[1])
            elevation = int(words[2])
            connection_elevations.append([next_stop_1_id, next_stop_2_id, elevation])
    
    #see if elevation is in list, if so return it
    if (stop):
        for elevation_data in stop_elevations:
            if (elevation_data[0] == stop_1_id):
                return elevation_data[1]
    else:
        for elevation_data in connection_elevations:
            if ((elevation_data[0] == stop_1_id and elevation_data[1] == stop_2_id) or 
                (elevation_data[0] == stop_2_id and elevation_data[1] == stop_1_id)):
                return elevation_data[2]
    
    #elevation not in list, ping server and add to list
    try:
        query = ('https://api.open-elevation.com/api/v1/lookup'
                f'?locations={lat},{lon}')
        r = requests.get(query).json()
        elevation = pd.io.json.json_normalize(r, 'results')['elevation'].values[0]
        if (stop):
            print(f'{stop_1_id}: {elevation}')
            stop_elevations.append([stop_1_id, elevation])
        else:
            print(f'{stop_1_id},{stop_2_id}: {elevation}')
            connection_elevations.append([stop_1_id, stop_2_id, elevation])
    except JSONDecodeError:
        print('timeout, retrying')
        return get_elevation(lat, lon, stop, stop_1_id, stop_2_id)
    return elevation


def read_stop_file(stop_filename='data/stops.csv'):
    '''
    read important data from stop file
    '''
    ID = 0
    NAME = 1
    LAT = 2
    LON = 3

    in_fd = open(stop_filename, 'r')
    lines = in_fd.readlines()
    in_fd.close()

    stop_data = []
    for line in lines:
        words = line.split(',')
        if (len(words) < 4):
            continue
        stop_dict = dict()
        stop_dict['id'] = int(words[ID])
        stop_dict['name'] = words[NAME]
        stop_dict['lat'] = float(words[LAT])
        stop_dict['lon'] = float(words[LON])
        stop_data.append(stop_dict)
    return stop_data

def read_connections_file(connections_filename='data/connections.csv'):
    '''
    read important data from connections file
    '''
    in_fd = open(connections_filename, 'r')
    lines = in_fd.readlines()
    in_fd.close()
    lines.pop(0)

    connections_data = []
    for line in lines:
        words = line.split(',')
        if (len(words) < 2):
            continue
        stop_1_id = int(words[0])
        stop_connections = [stop_1_id]
        for i in range(1, len(words)):
            stop_2_id = int(words[i].split(':')[0])
            time = int(words[i].split(':')[1])
            stop_connections.append([stop_2_id, time])
        connections_data.append(stop_connections)
    return connections_data

def read_departure_times(departure_times_file='data/departure_times.csv'):
    '''
    read in the departure times and return as a list
    '''
    TIME_SINCE_LAST=0
    ROUTE_NUM=2

    in_fd = open(departure_times_file, 'r')
    lines = in_fd.readlines()
    in_fd.close()

    departure_times_list = []

    current_time = 0
    for line in lines:
        words = line.split(',')

        route_num = int(words[ROUTE_NUM])
        minutes = int(words[TIME_SINCE_LAST].split(':')[0])
        seconds = int(words[TIME_SINCE_LAST].split(':')[1])
        current_time += seconds + (60*minutes)
        departure_times_list.append([route_num, current_time])
    return departure_times_list


def read_trips_file(stop_ids, chancellors_place_id, indooroopilly_interchange_id, trips_filename='data/trips.csv'):
    '''
    reads trips from file
    assumes dest stops marked 'n/a' arrive at indooroopilly_interchange
    multiplies the number of trips by 1.5 for worst case scenario
    '''
    ROUTE = 0
    ORIGIN_STOP=2
    DESTINATION_STOP=3
    QUANTITY=4

    #num weekdays in the month of August 2019
    NUM_WEEKDAYS = 20

    uq_chancellor_place_stops = {
        1801: 'A',
        1799: 'B',
        1798: 'C',
        1797: 'D',
        1802: 'E',
    }

    indooroopilly_stops = {
        2004: 'Interchange',
        2205: 'Station Rd',
    }

    in_fd = open(trips_filename, 'r')
    lines = in_fd.readlines()
    in_fd.close()

    #passsenger_dict[route][origin_stop][destination_stop] = no of passengers
    passenger_dict = dict()
    
    for line in lines:
        words = line.split(',')

        #get route number
        route_num = int(words[ROUTE])

        #get origin stop. replace chancellors place ids with single id
        orig_stop = int(words[ORIGIN_STOP])
        if (orig_stop in uq_chancellor_place_stops.keys()):
            orig_stop = chancellors_place_id

        #get origin stop. replace n/a with indooroopilly interchange. replace multiple indooroopilly id's with single id
        if (words[DESTINATION_STOP] == 'n/a'):
            dest_stop = indooroopilly_interchange_id
        else:
            dest_stop = int(words[DESTINATION_STOP])
        if (dest_stop in indooroopilly_stops.keys()):
            dest_stop = indooroopilly_interchange_id
        
        #check that the trip is relevant
        if ((dest_stop in stop_ids) and (orig_stop in stop_ids)):

            #add route to dict if its not there
            if (not(route_num in passenger_dict.keys())):
                passenger_dict[route_num] = dict()
            
            if (not(orig_stop in passenger_dict[route_num].keys())):
                passenger_dict[route_num][orig_stop] = dict()
            
            passenger_dict[route_num][orig_stop][dest_stop] = math.ceil((1.5*int(words[QUANTITY]))/NUM_WEEKDAYS)
    
    return passenger_dict

        

def read_route_file(route_no):
    '''
    read important data from route files
    '''
    route_filename = f'data/route_{route_no}.csv'
    ID = 0
    NAME = 1
    TIME = 3
    in_fd = open(route_filename, 'r')
    lines = in_fd.readlines()
    
    lines.pop(0)

    route_data = []

    for line in lines:
        stop_dict = dict()
        words = line.split(',')
        stop_dict['id'] = int(words[ID])
        stop_dict['name'] = words[NAME]
        #convert time from minutes to seconds
        stop_dict['time'] = int(float(words[TIME])*60)
        route_data.append(stop_dict)
    
    return route_data