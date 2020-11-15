'''
manipulate the given csv data into a more useful format
'''

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

def export_small_stops(in_filename='raw_data/bus-train-stop-ids.csv', out_filename='start_and_end_stops.csv'):
    '''
    read through the csv file containing all bust stops and save a new file containing only
    the stops at UQ chancellors place or near the Indooroopilly Interchange
    '''
    in_fd = open(in_filename, 'r')
    lines = in_fd.readlines()
    in_fd.close()
    new_lines = [lines.pop(0)]
    for line in lines:
        try:
            stop_val = int(line.split(',')[0])
        except ValueError:
            continue
        if ((stop_val in indooroopilly_stops.keys()) or (stop_val in uq_chancellor_place_stops.keys())):
            new_lines.append(line)
    out_fd = open(out_filename, 'w')
    out_fd.writelines(new_lines)
    out_fd.close()


def export_routes_list(in_filename='raw_data/raw_trips.csv', out_filename='routes_list.txt'):
    '''
    read through the csv file containing all trips and get only those routes
    that originate from uq_chancellor_place_stops and end at indooroopilly_stops
    '''
    in_fd = open(in_filename, 'r')
    lines = in_fd.readlines()
    lines.pop(0)
    in_fd.close()
    route_start_list = []
    route_end_list = []
    for line in lines:
        try:
            route_number = int(line.split(',')[2])
        except ValueError:
            continue

        try:
            origin_stop = int(line.split(',')[6])
            if ((origin_stop in uq_chancellor_place_stops.keys()) and (not(route_number in route_start_list))):
                route_start_list.append(route_number)
        except ValueError:
            #do nothing
            pass
        
        try:
            destination_stop = int(line.split(',')[7])
            if ((destination_stop in indooroopilly_stops.keys()) and (not(route_number in route_end_list))):
                route_end_list.append(route_number)
        except ValueError:
            #do nothing
            pass
    
    routes = []
    for route in route_start_list:
        if (route in route_end_list):
            routes.append(f'{route}\n')
    
    out_fd = open(out_filename, 'w')
    out_fd.writelines(routes)
    out_fd.close()


def export_short_trips(trips_filename='raw_data/raw_trips.csv', routes_filename='routes_list.txt', out_filename='trips.csv'):
    '''
    read through the trips file and export only the data for the given routes
    that are outbound and between 3pm and 7pm
    '''
    ROUTE=2
    DIRECTION=3
    TIME=4
    TICKET_TYPE=5
    ORIGIN_STOP=6
    DESTINATION_STOP=7
    QUANTITY=8 

    #load routes from file
    routes = []
    routes_fd = open(routes_filename, 'r')
    for line in routes_fd.readlines():
        #not empty end string
        if (len(line)>=3):
            routes.append(int(line[0:-1]))
    routes_fd.close()

    #export trips data for the given routes only
    trips_fd = open(trips_filename, 'r')
    lines = trips_fd.readlines()
    trips_fd.close()
    titles = lines.pop(0).split(',')
    new_lines = [f'{titles[ROUTE]},{titles[TICKET_TYPE]},{titles[ORIGIN_STOP]},{titles[DESTINATION_STOP]},{titles[QUANTITY]}']
    for line in lines:
        words = line.split(',')
        try:
            route_no = int(words[ROUTE])
        except ValueError:
            continue

        #only get outbound trips
        direction = words[DIRECTION]
        if (direction != 'Outbound'):
            continue

        #only get weekday trips from 3pm to 7pm
        day = words[TIME]
        if (day != 'Weekday (3:00pm-6:59:59pm)'):
            continue

        #append important data
        if (route_no in routes):
            new_lines.append(f'{words[ROUTE]},{words[TICKET_TYPE]},{words[ORIGIN_STOP]},{words[DESTINATION_STOP]},{words[QUANTITY]}')


        

    out_fd = open(out_filename, 'w')
    out_fd.writelines(new_lines)
    out_fd.close()


def get_stops_for_routes(in_filename='trips.csv', out_filename='destination_stops'):

    ROUTE=0
    TICKET_TYPE=1
    ORIGIN_STOP=2
    DESTINATION_STOP=3
    QUANTITY=4

    in_fd = open(in_filename, 'r')
    lines = in_fd.readlines()
    in_fd.close()
    lines.pop(0)

    dest_map = dict()
    origin_map = dict()

    for line in lines:

        words = line.split(',')

        #get route number
        try:
            route_no = int(words[ROUTE])
        except ValueError:
            continue

        #add route number to dict
        if (not(route_no in dest_map.keys())):
            dest_map[route_no] = []

        #add route number to dict
        if (not(route_no in origin_map.keys())):
            origin_map[route_no] = []
        
        #add dest stop
        dest_stop = words[DESTINATION_STOP]
        if (not(dest_stop in dest_map[route_no])):
            dest_map[route_no].append(dest_stop)
        
        #add origin stop
        origin_stop = words[ORIGIN_STOP]
        if (not(origin_stop in origin_map[route_no])):
            origin_map[route_no].append(origin_stop)

    # print('ORIGIN STOPS')
    # for key in origin_map.keys():
    #     print(key)
    #     for stop in origin_map[key]:
    #         print(f'\t{stop}')
    
    # print('DESTINATION STOPS')
    # for key in dest_map.keys():
    #     print(key)
    #     for stop in dest_map[key]:
    #         print(f'\t{stop}')

    # print('OVERLAP STOPS')
    # for key in dest_map.keys():
    #     print(key)
    #     for stop in dest_map[key]:
    #         if (stop in origin_map[key]):
    #             print(f'\t{stop}')

    return origin_map, dest_map

def print_stop_ids_and_names(in_filename='raw_data/Bus-train-stop-ids.csv', route=414):
    origin_map, dest_map = get_stops_for_routes()

    origin_ids = origin_map[route]
    dest_ids = dest_map[route]
    done_ids = []

    in_fd = open(in_filename, 'r')
    lines = in_fd.readlines()
    in_fd.close()
    lines.pop(0)
    for line in lines:
        words = line.split(',')
        stop_val = words[0]
        if (stop_val in done_ids):
            continue
        elif ((stop_val in origin_ids) or (stop_val in dest_ids)):
            print(f'{stop_val}: {words[2]}')



if __name__ == '__main__':
    # export_small_stops()
    # export_routes_list()
    # export_short_trips()
    # get_stops_for_routes()
    # print_stop_ids_and_names(route=432)
