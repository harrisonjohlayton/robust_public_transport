

class NetworkController():

    def __init__(self, network, distaster_resistant=False, start_water_level=0.0, end_water_level=20.0, seconds_per_tick=120):
        self.start_water_level=start_water_level
        self.end_water_level=end_water_level
        self.current_water_level = start_water_level
        
        self.distaster_resistant = distaster_resistant
        self.network = network

        #start and end time in seconds
        self.end_time = 4*60*60
        self.current_time = 0
        self.seconds_per_tick = seconds_per_tick
        self.max_time_per_walk = self.get_max_time_per_walk()

        #dict mapping routes to the last calculated optimal walk
        self.shortest_paths = self.init_shortest_paths()
        self.prev_optimal_walks = dict()
        self.init_walks()
    
    def get_max_time_per_walk(self):
        '''
        get the maximum time per trip before pruning from search tree
        '''
        return 37*60

    def update(self):
        self.current_time += self.seconds_per_tick
        self.current_water_level = self.get_water_level_for_time(self.current_time)
        # self.update_stops()
        # self.update_connections()
        self.update_routes()
        self.update_buses()
        self.update_passengers()
        print(f'time: {self.current_time} / {self.end_time}    water:{self.current_water_level}m')
    
    # def update_stops(self):
    #     '''
    #     update stops for new tick
    #     '''
    #     for stop in self.network.stops:
    #         if (stop.elevation < self.current_water_level):
    #             stop.is_flooded = True
    
    # def update_connections(self):
    #     '''
    #     update connections for new tick
    #     '''
    #     for connection in self.network.connections:
    #         if (connection.elevation < self.current_water_level):
    #             connection.is_flooded = True
    #         elif(connection.stop_1.is_flooded or connection.stop_2.is_flooded):
    #             connection.is_flooded = True
    
    def update_buses(self):
        '''
        update current buses for new tick
        '''
        pass
    
    def update_passengers(self):
        '''
        update passengers for new tick
        '''
        pass
    
    def update_routes(self):
        '''
        update routes for new tick
        '''
        pass
    
    def is_complete(self):
        return self.current_time >= self.end_time
    
    def init_shortest_paths(self):
        '''
        find shortest paths between all stops using djikstras
        '''
        #min_dist[stop_1][stop_2] is the minimum time connecting stop_1 to stop_2 
        STOP = 0
        TIME = 1
        INF = 10e8
        min_dist = dict()

        for main_stop in self.network.stops:
            #nodes take the form [stop, time]
            open_nodes = [[main_stop, 0]]
            visited_stops = set()
            main_stop_min_dist = dict()

            #initlialize open nodes
            for stop in self.network.stops:
                if (stop != main_stop):
                    open_nodes.append([stop, INF])
                open_nodes.sort(key=lambda x: x[TIME])

            #main search loop
            while(len(open_nodes) > 0):
                current_node = open_nodes.pop(0)
                
                for connection in self.network.get_connections_for_stop(current_node[STOP]):
                    if (current_node[STOP] == connection.stop_1):
                        next_stop = connection.stop_2
                    else:
                        next_stop = connection.stop_1
                    
                    if (next_stop in visited_stops):
                        continue
                    
                    next_time = current_node[TIME] + connection.time
                    for node in open_nodes:
                        if node[STOP] == next_stop:
                            node[TIME] = min(next_time, node[TIME])
                            break
                main_stop_min_dist[current_node[STOP]] = current_node[TIME]
                visited_stops.add(current_node[STOP])
                open_nodes.sort(key=lambda x: x[TIME])
            min_dist[main_stop] = main_stop_min_dist
        return min_dist
    

    def init_walks(self):
        '''
        find the initial walks
        '''
        for route in self.network.routes:
            print(f'initializing route for {route.route_num}')
            self.prev_optimal_walks[route] = self.optimal_walk_search(route, 0)

    def get_optimal_walk(self, route, time):
        '''
        return the optimum walk for the given route starting at the given timestep
        '''
        prev_optimal_walk = self.prev_optimal_walks[route]
        if ((prev_optimal_walk is None) or self.is_walk_valid(prev_optimal_walk, time)):
            return prev_optimal_walk
        elif (self.distaster_resistant):
            #if changing routes, search for new route and return it (None if no route exists)
            new_optimal_walk = self.optimal_walk_search(route, time)
            self.prev_optimal_walks[route] = new_optimal_walk
            return new_optimal_walk
        else:
            #if not changing routes, then there is no other walk than the default
            self.prev_optimal_walks[route] = None
            return None


    def optimal_walk_search(self, route, time, trail=False):
        '''
        search for the optimum walk for the given route starting at the given timestep
        if trail is true, do not allow repeated edges
        TODO:
            run dikstras to find shortest route between all points
            add heruistic - time from current stop to furthest unvisited required stop
            add to pruning - current time + heuristic > max time?
            tune max time - initial time for each route + 10 minutes
            go through and check that everything is running snappy (probs isn't too bad since paths are fine)
            remove duplicates - same visited required stops and same current stop
            
            if this still isn't enough, require that indooroopilly is the final stop
                heuristic = time to furthest univisited required stop + time from that stop to
                            indooroopilly
        '''
        
        CURRENT_STOP=0
        TIME=1
        WALK=2
        HEURISTIC=3
        #nodes take the form [current_stop, current_time, stops_visited_in_order (first to last)]
        root_node = [self.network.chancellors_place, time, [], time + self.get_heuristic(route, [], self.network.chancellors_place)]
        node_list = [root_node]

        while(len(node_list) > 0):
            # print(len(node_list[-1][WALK]))
            node = node_list.pop(0)

            #check if walk is complete
            if (self.is_walk_complete(node[WALK], route)):
                return node[WALK]
            
            #make new node for each connection
            prev_stop = node[CURRENT_STOP]
            for connection in self.network.get_connections_for_stop(prev_stop):
                if (prev_stop == connection.stop_1):
                    next_stop = connection.stop_2
                else:
                    next_stop = connection.stop_1
                
                if (trail and (connection in node[WALK])):
                    continue
                
                #check the step is valid, get next time and check if time is over max
                valid, next_time = self.is_step_valid(prev_stop, next_stop, connection, node[TIME])
                if ((not valid) or (next_time > self.max_time_per_walk)):
                    continue
                
                #get new walk
                next_walk = node[WALK].copy()
                next_walk.append(connection)
                if (self.is_walk_suboptimal(next_walk, connection)):
                    # print('subopt')
                    continue
                
                next_node = [next_stop, next_time, next_walk, next_time + self.get_heuristic(route, next_walk, next_stop)]
                if (next_node[HEURISTIC] - time > self.max_time_per_walk):
                    continue
                
                #append new node to open list
                node_list.append(next_node)
            node_list.sort(key=lambda x: x[HEURISTIC])
        return None

    def get_heuristic(self, route, walk, current_stop):
        '''
        return time plus heuristic for A*
        heuristic is minumum time to the furthest unvisited stop in route.required_stops
        '''
        max_time = 0
        walk_stops = set()
        for connection in walk:
            walk_stops.add(connection.stop_1)
            walk_stops.add(connection.stop_2)
        for stop in route.required_stops:
            if (not (stop in walk_stops)):
                max_time = max(max_time, self.shortest_paths[current_stop][stop])
        return max_time

    
    def is_walk_suboptimal(self, walk, connection):
        '''
        checks to see if the walk is suboptimal on the given stop
        '''
        num_occurances = walk.count(connection)
        # max_num_occurances = len(self.network.get_connections_for_stop(stop))
        return num_occurances > 2

    def is_walk_complete(self, walk, route):
        '''
        return True if the walk contains all stops in the routes required_stops
        '''
        stops = []
        for connection in walk:
            stops.append(connection.stop_1)
            stops.append(connection.stop_2)
        for stop in route.required_stops:
            if stop in stops:
                continue
            return False
        return True


    def is_walk_valid(self, walk, time):
        '''
        test if a walk is valid starting at the given time
        '''
        #PREV CODE FOR STOP BASED WALK
        # for connection in walk):
        #     # connection = self.network.get_connection(walk[i-1], walk[i])
        #     valid, time = self.is_step_valid(walk[i-1], walk[i], connection, time)
        #     if ((not valid) or (time > self.max_time_per_walk)):
        #         return False
        next_stop = self.network.chancellors_place
        for connection in walk:
            prev_stop = next_stop
            if (connection.stop_1 == prev_stop):
                next_stop = connection.stop_2
            else:
                next_stop = connection.stop_1
            valid, time = self.is_step_valid(prev_stop, next_stop, connection, time)
            if ((not valid) or (time > self.max_time_per_walk)):
                return False
        return True
            
    
    def is_step_valid(self, start_stop, end_stop, connection, time):
        '''
        returns True and the new time if the step from one stop to another is valid
        for the given start time. Returns False, -1 otherwise

        assumes its valid for the bus to be at the start stop for the given 
        start_time
        '''
        end_time = time + connection.time
        end_water_level = self.get_water_level_for_time(end_time)
        if ((connection.elevation <= end_water_level) or
            (end_stop.elevation <= end_water_level)):
            return False, -1
        return True, end_time

    def get_water_level_for_time(self, time):
        water_level_diff = ((self.end_water_level - self.start_water_level) / (self.end_time)) * time
        return min(water_level_diff + self.start_water_level, self.end_water_level)