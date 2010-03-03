#!/usr/bin/env python

from pylab import *
from xml.sax import parse
from xml.sax.handler import ContentHandler

class MapHandler(ContentHandler):
    def __init__(self):
        ContentHandler.__init__(self)
        self.bounds = None
        self.nodes = {}
        self.nodes_ways = {}
        self.ways = {}
        self.current_way = None
        self.current_way_id = None
        self.relations = {}
        self.current_relation = None

        self.start_methods = {"bounds": self.__set_bounds,"node":self.__add_node,"way":self.__start_way,"nd":self.__add_way_node,"relation":self.__start_relation}
        self.end_methods   = {"way":self.__end_way,"relation":self.__end_relation}

    def startElement(self,name,attrs):
        if name in self.start_methods: self.start_methods[name](attrs) 
        else: print "unhandled start element %s" % name
    def endElement(self,name):
        if name in self.end_methods: self.end_methods[name]()
        else: print "unhandled end element %s" % name

    def __set_bounds(self,attrs):
        assert(self.bounds is None)
        self.bounds = map(float,(attrs.get("minlon"),attrs.get("maxlon"),attrs.get("minlat"),attrs.get("maxlat")))
    def __add_node(self,attrs):
        id = int(attrs.get("id"))
        assert(id not in self.nodes)
        self.nodes[id] = map(float,(attrs.get("lon"),attrs.get("lat")))
        self.nodes_ways[id] = []
    def __start_way(self,attrs):
        assert(self.current_way is None)
        id = int(attrs.get("id"))
        assert(id not in self.ways)
        self.current_way_id = id
        self.current_way = []
        self.ways[id] = self.current_way
    def __add_way_node(self,attrs):
        assert(self.current_way is not None)
        ref = int(attrs.get("ref"))
        assert(ref in self.nodes)
        self.current_way.append(self.nodes[ref])
        self.nodes_ways[ref].append(self.current_way)
    def __end_way(self):
        assert(self.current_way is not None)
        self.current_way = None
        self.current_way_id = None
    def __start_relation(self,attrs):
        assert(self.current_relation is None)
        id = int(attrs.get("id"))
        assert(id not in self.relations)
        self.current_relation = []
        self.relations[id] = self.current_relation
    def __end_relation(self):
        assert(self.current_relation is not None)
        self.current_relation = None

    def __repr__(self):
        return "bounds=%s nnodes=%d nways=%d" % (repr(self.bounds),len(self.nodes),len(self.ways))
    def prune_unused_nodes(self):
        unused_nodes = []
        for id,node in self.nodes.items():
            if not self.nodes_ways[id]:
                unused_nodes.append(node)
                del self.nodes[id]
        return unused_nodes
        
def load_osm(filename):
    handler = MapHandler()
    parse(filename,handler)
    return handler

map = load_osm("quetigny.osm")
unused_nodes = array(map.prune_unused_nodes())
print map

figure()
crossing_nodes = array([node for id,node in map.nodes.items() if len(map.nodes_ways[id]) > 1])
plot(unused_nodes[:,0],unused_nodes[:,1],'ro')
plot(crossing_nodes[:,0],crossing_nodes[:,1],'go')

for way in map.ways.values():
    foo = array(way)
    plot(foo[:,0],foo[:,1])

show()


