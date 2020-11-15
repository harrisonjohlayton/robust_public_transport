import requests
import pandas as pd
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