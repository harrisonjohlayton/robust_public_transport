
def get_altitude(lat:float, lon:float):
    return 0.0

def read_stop_file(stop_filename):
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
    lines.pop(0)

    stop_data = []
    for line in lines:
        words = line.split(',')
        if (len(words) < 4):
            continue
        stop_dict = dict()
        stop_dict['id'] = words[ID]
        stop_dict['name'] = words[NAME]
        stop_dict['lat'] = words[LAT]
        stop_dict['lon'] = words[LON]
        stop_data.append(stop_dict)
    return stop_data

def read_connections_file(connections_filename):
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
        if (len(words < 2)):
            continue
        stop_1_id = int(words[0])
        stop_connections = [stop_1_id]
        for i in range(1, len(words)):
            stop_2_id = int(words[i].split(':')[0])
            time = int(words[i].split(':')[1])
            stop_connections.append([stop_2_id, time])
        connections_data.append(stop_connections)
    return connections_data

def read_route_file(route_filename):
    '''
    read important data from route files
    '''
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
    
    return get_stop_positions(route_data)

def get_stop_positions(route_data):
    '''
    read lat and long data for stops from file
    '''
    ID = 0
    LAT = -7
    LON = -6

    todo_ids = []
    for stop_dict in route_data:
        todo_ids.append(stop_dict['id'])


    in_fd = open('data/raw_data/Bus-train-stop-ids.csv', 'r')
    lines = in_fd.readlines()
    #get rid of titles
    lines.pop(0)

    for line in lines:
        words = line.split(',')
        
        try:
            next_id = int(words[ID])
            if (next_id in todo_ids):
                todo_ids.remove(next_id)
                for stop_dict in route_data:
                    if (stop_dict['id'] == next_id):
                        stop_dict['lat'] = float(words[LAT])
                        stop_dict['lon'] = float(words[LON])
                        break
        except ValueError:
            # print('error parsing stop posistions')
            # print(f'id: {words[ID]}')
            # print(f'lat: {words[LAT]}')
            # print(f'lon: {words[LON]}')
            # exit(0)
            continue

    
    return route_data

