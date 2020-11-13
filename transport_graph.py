from utils import get_altitude, read_route_file

CHANCELLORS_PLACE_IDS = [1798, 1799, 1801]
INDOOROOPILLY_IDS = [2004, 2205]

class Stop():
    
    def __init__(self, id, name:str, lat:float, lon:float):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.altitude = get_altitude(lat, lon)
        self.people = []


class Connection():

    def __init__(self, stop_1, stop_2, weight:int):
        self.stop_1 = stop_1
        self.stop_2 = stop_2
        self.altitude = get_altitude((stop_1.lat + stop_2.lat)/2,
            (stop_1.lon + stop_2.lon)/2)
        self.weight=weight

class Route():

    def __init__(self, route_num:int, first_stop, network):
        self.route_num=route_num
        self.origin_stop = first_stop
        self.required_stops = [self.origin_stop]
        self.parent_network = network
    
    def add_required_stop(self, stop):
        self.required_stops.append(stop)

# class Passenger():

#     def __init__(self, origin_stop, dest_stop):

# class Bus():
#

class Network():

    def __init__(self):
        self.stops = []
        self.connections = []
        self.routes = []
        self.chancellors_place = Stop(1799, 'Chancellors Place', 0, 0)
        self.indooroopilly_interchange = Stop(2205, 'Indooroopilly Shopping Center', 0, 0)

        #add routes
        self.add_route('data/raw_data/route_414.csv', 414)
        self.add_route('data/raw_data/route_427.csv', 427)
        self.add_route('data/raw_data/route_428.csv', 428)
        self.add_route('data/raw_data/route_432.csv', 432)
    
    def add_route(self, route_filename:str, route_num:int):
        '''
        add the route definied by the file to the graph
        '''
        #get route data from file
        route_data = read_route_file(route_filename)
        route = Route(route_num, self.chancellors_place, self)

        #add stops to route
        for i in range(len(route_data)-1):
            stop_dict = route_data[i]
            next_stop =  self.get_stop(stop_dict['id'])
            if (next_stop is None):
                next_stop = Stop(stop_dict['id'], stop_dict['name'], stop_dict['lat'], stop_dict['lon'])
                self.stops.append(next_stop)
            if (not connection_exists(next_stop, route.required_stops[-1])):
                self.connections.append(Connection(next_stop, route.required_stops[-1], stop_dict['time']))
            route.add_required_stop(next_stop)

        #add final stop to route
        if (not is_connected(route.required_stops[-1], self.indooroopilly_interchange)):
            self.connections.append(Connection(self.indooroopilly_interchange,
                    route.required_stops[-1], route_data[-1]['time']))
        route.add_required_stop(self.indooroopilly_interchange)

        self.routes.append(route)

    
    def get_stop(self, id):
        '''
        return stop with given ID
        '''
        for stop in self.stops:
            if stop.id == id:
                return stop
        return None
    
    def is_connected(self, stop_1, stop_2):
        '''
        check if the two stops are connected
        '''
        for connection in self.connections:
            if (connection.stop_1 == stop_1 and connection.stop_2 == stop_2):
                return 
            elif (connection.stop_2 == stop_1 and connection.stop_1 == stop_2)::
                return True
        return False