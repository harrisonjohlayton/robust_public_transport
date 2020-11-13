
def get_altitude(lat:float, lon:float):
    return 0.0

def read_route_file(route_filename):
    '''
    read important data from route files
    '''
    ID = 0
    NAME = 1
    TIME = 2
    in_fd = open(route_filename, 'r')
    lines = in_fd.readlines()
    
    lines.pop(0)

    route_data = []

    for line in lines:
        stop_dict = dict()
        words = line.split(',')
        stop_dict['id'] = int(words[ID])
        stop_dict['name'] = words[NAME]
        stop_dict['time'] = float(words[TIME])
        route_data.append(stop_dict)
    
    return get_stop_positions(route_data)

def get_stop_positions(route_data):
    '''
    read lat and long data for stops from file
    '''
    ID = 0
    LAT = 4
    LON = 5

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
                        stop_dict['lat'] = words[LAT]
                        stop_dict['lon'] = words[LON]
                        break
        except ValueError:
            continue
    
    return route_data

