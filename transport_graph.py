from utils import get_elevation, read_route_file, read_connections_file, read_stop_file, cache_elevations

CHANCELLORS_PLACE_IDS = [1798, 1799, 1801]
INDOOROOPILLY_IDS = [2004, 2205]

class Stop():
    '''
    Represents a bus stop. This is a vertex in the graph.
    '''
    
    def __init__(self, id, name:str, lat:float, lon:float):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.elevation = get_elevation(lat, lon, True, self.id, None)
        self.people = []
        # self.is_flooded = False
    
    def __str__(self):
        return str(f'{self.id}')


class Connection():
    '''
    Represents a series of roads connecting a bus stop. This is an
    edge in the graph.
    '''

    def __init__(self, stop_1, stop_2, time:int):
        self.stop_1 = stop_1
        self.stop_2 = stop_2

        self.elevation = get_elevation((stop_1.lat + stop_2.lat)/2,
            (stop_1.lon + stop_2.lon)/2, False, stop_1.id, stop_2.id)

        self.time=time
        # self.is_flooded = False

    def __str__(self):
        return f'{self.stop_1} <- {self.time}s -> {self.stop_2}'

class Route():
    '''
    Represents a bus route. This is a series of bus stops that must be
    visited.

    In the graph, this represents the shortest path starting at
    the vertiex origin_stop that contains all vertices in required_stops
    '''

    def __init__(self, route_num:int, first_stop, network):
        self.route_num=route_num
        self.origin_stop = first_stop
        self.current_route = []
        self.required_stops = [self.origin_stop]
        self.parent_network = network
    
    def add_required_stop(self, stop):
        self.required_stops.append(stop)
    
            
    def __str__(self):
        return str(self.route_num)
    

# class Passenger():

#     def __init__(self, origin_stop, dest_stop):

class Bus():
    
    def __init__(self, route, departure_time):
        self.route = route
        self.departure_time = departure_time
        self.passengers = []


class Network():
    '''
    class representing the graph containing the state of the transport network.
    '''

    def __init__(self, disaster_resistant=False):
        self.disaster_resistant = disaster_resistant
        self.chancellors_place = Stop(1799, 'Chancellors Place', -27.497974, 153.011139)
        self.indooroopilly_interchange = Stop(2205, 'Indooroopilly Shopping Center', -27.500941, 152.971946)
        self.connections = []
        self.routes = []
        self.stops = [self.indooroopilly_interchange, self.chancellors_place]

        #caching for efficiency
        self.stop_connections = dict()

        #add stops, connections and routes
        self.init_stops()
        self.init_connections()
        self.add_route(414)
        self.add_route(427)
        self.add_route(428)
        self.add_route(432)

        #cache elevations to save expensive call
        cache_elevations()
        
    
    def init_stops(self):
        '''
        add stops to graph
        '''
        stops_data = read_stop_file()
        for stop_data in stops_data:
            self.stops.append(Stop(stop_data['id'], stop_data['name'], stop_data['lat'], stop_data['lon']))
    
    def init_connections(self):
        '''
        add connections to graph
        '''
        connections_data = read_connections_file()
        for connection_data in connections_data:
            stop_1 = self.get_stop(connection_data[0])
            for i in range(1, len(connection_data)):
                stop_2 = self.get_stop(connection_data[i][0])
                if (self.is_connected(stop_1, stop_2)):
                    #don't load connections twice
                    continue
                time = connection_data[i][1]
                self.connections.append(Connection(stop_1, stop_2, time))

    
    def add_route(self, route_num:int):
        '''
        add the route definied by the file to the graph
        '''
        #get route data from file
        route_data = read_route_file(route_num)
        route = Route(route_num, self.chancellors_place, self)

        #add stops to route
        for i in range(len(route_data)-1):
            stop_dict = route_data[i]
            next_stop =  self.get_stop(stop_dict['id'])
            route.add_required_stop(next_stop)

        route.add_required_stop(self.indooroopilly_interchange)
        self.routes.append(route)

    
    def get_stop(self, id):
        '''
        return stop with given ID or None if no such stop exists
        '''
        for stop in self.stops:
            if stop.id == id:
                return stop
        print(f'No stop with id: {id}')
        return None
    
    def is_connected(self, stop_1, stop_2):
        '''
        check if two stops are connected
        '''
        for connection in self.connections:
            if (connection.stop_1 == stop_1 and connection.stop_2 == stop_2):
                return 
            elif (connection.stop_2 == stop_1 and connection.stop_1 == stop_2):
                return True
        return False
    
    def get_connection(self, stop_1, stop_2):
        '''
        return connection for two stops or None
        '''
        for connection in self.connections:
            if ((connection.stop_1 == stop_1 and connection.stop_2 == stop_2) or
                (connection.stop_2 == stop_1 and connection.stop_1 == stop_2)):
                return connection
        return None
    
    def get_connections_for_stop(self, stop):
        '''
        return all connections for a given stop
        '''
        if (not (stop in self.stop_connections.keys())):
            relevant_connections = []
            for connection in self.connections:
                if (connection.stop_1 == stop or connection.stop_2 == stop):
                    relevant_connections.append(connection)
            self.stop_connections[stop] = relevant_connections
            return relevant_connections
        return self.stop_connections[stop]

    
    def __str__(self):
        return_str = 'Routes\n'
        for route in self.routes:
            return_str = return_str + f'\t{route}\n'
        return_str = return_str + 'Stops:\n'
        for stop in self.stops:
            return_str = return_str + f'\t{stop}\n'
        return_str = return_str + 'Connections:\n'
        for connection in self.connections:
            return_str = return_str + f'\t{connection}\n'
        return return_str