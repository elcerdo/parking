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
        self.relations = {}

        self.start_methods = {"bounds": self.__set_bounds,"node":self.__add_node,"way":self.__start_way,"relation":self.__start_relation}
        self.end_methods   = {"node":self.__end_node,"way":self.__end_way,"relation":self.__end_relation}

    def startElement(self,name,attrs):
        if name in self.start_methods: self.start_methods[name](attrs) 
        else: print "unhandled start element %s" % name
    def endElement(self,name):
        if name in self.end_methods: self.end_methods[name]()

    def __set_bounds(self,attrs):
        assert(self.bounds is None)
        self.bounds = map(float,(attrs.get("minlon"),attrs.get("maxlon"),attrs.get("minlat"),attrs.get("maxlat")))
    def __add_node(self,attrs):
        id = int(attrs.get("id"))
        assert(id not in self.nodes)
        self.nodes[id] = map(float,(attrs.get("lon"),attrs.get("lat")))
        self.nodes_ways[id] = []
        def node_tag(attrs):
            pass
        self.start_methods["tag"] = node_tag
    def __end_node(self):
        del self.start_methods["tag"]

    def __start_way(self,attrs):
        id = int(attrs.get("id"))
        assert(id not in self.ways)
        current_way = []
        self.ways[id] = current_way
        def add_way_node(attrs):
            ref = int(attrs.get("ref"))
            assert(ref in self.nodes)
            current_way.append(self.nodes[ref])
            self.nodes_ways[ref].append(current_way)
        def way_tag(attrs):
            pass
        self.start_methods["nd"] = add_way_node
        self.start_methods["tag"] = way_tag
    def __end_way(self):
        del self.start_methods["nd"]
        del self.start_methods["tag"]

    def __start_relation(self,attrs):
        id = int(attrs.get("id"))
        assert(id not in self.relations)
        current_relation_ways,current_relation_nodes = [],[]
        self.relations[id] = (current_relation_ways,current_relation_nodes)
        def add_member(attrs):
            type = attrs.get("type")
            ref = int(attrs.get("ref"))
            if type == "way" and ref in self.ways:
                current_relation_ways.append(ref)
            elif type == "node" and ref in self.nodes:
                current_relation_nodes.append(ref)
            else:
                print "unknow member type=%s ref=%d" % (type,ref)
        def relation_tag(attrs):
            pass
        self.start_methods["member"] = add_member
        self.start_methods["tag"] = relation_tag
    def __end_relation(self):
        del self.start_methods["member"]
        del self.start_methods["tag"]

    def __repr__(self):
        return "bounds=%s nnodes=%d nways=%d nrelation=%d" % (repr(self.bounds),len(self.nodes),len(self.ways),len(self.relations))

    def prune_nodes_and_ways_in_relation(self):
        pruned_nodes = []
        pruned_ways = []
        for relation_ways,relation_nodes in self.relations.values():
            for wayid in relation_ways:
                try:
                    pruned_ways.append(self.ways[wayid])
                    del self.ways[wayid]
                except KeyError:
                    pass
            for nodeid in relation_nodes:
                pruned_nodes.append(self.nodes[nodeid])
                del self.nodes[nodeid]
        print "pruned %d nodes and %d ways while removing relation" % (len(pruned_nodes),len(pruned_ways))
        return pruned_nodes
    def prune_unused_nodes(self):
        pruned_nodes = []
        for id,node in self.nodes.items():
            if not self.nodes_ways[id]:
                pruned_nodes.append(node)
                del self.nodes[id]
        print "pruned %d unused nodes" % len(pruned_nodes)
        return pruned_nodes
        
def load_osm(filename):
    handler = MapHandler()
    parse(filename,handler)
    return handler

map = load_osm("quetigny.osm")
map.prune_nodes_and_ways_in_relation()
unused_nodes = map.prune_unused_nodes()
unused_nodes = array(unused_nodes)
print map

figure()
crossing_nodes = array([node for id,node in map.nodes.items() if len(map.nodes_ways[id]) > 1])
plot(unused_nodes[:,0],unused_nodes[:,1],'ro')
plot(crossing_nodes[:,0],crossing_nodes[:,1],'go')

for way in map.ways.values():
    foo = array(way)
    plot(foo[:,0],foo[:,1])

show()


