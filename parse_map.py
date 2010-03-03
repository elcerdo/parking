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
            current_way.append((ref,self.nodes[ref]))
            self.nodes_ways[ref].append((id,current_way))
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
                current_relation_ways.append((ref,self.ways[ref]))
            elif type == "node" and ref in self.nodes:
                current_relation_nodes.append((ref,self.nodes[ref]))
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

    def __prune_node(self,nodeid,node,pruned_nodes):
        try:
            pruned_nodes.append(node)
            del self.nodes[nodeid]
        except KeyError:
            pass
            #print "unknown nodeid %d while pruning" % nodeid

    def __prune_way(self,wayid,way,pruned_nodes,pruned_ways):
        try:
            pruned_ways.append(way)
            del self.ways[wayid]
            for nodeid,node in way: self.__prune_node(nodeid,node,pruned_nodes)
        except KeyError:
            pass
            #print "unknown wayid %d while pruning" % wayid

    def prune_nodes_and_ways_in_relation(self, pruned_nodes, pruned_ways):
        for relation_ways,relation_nodes in self.relations.values():
            for wayid,way in relation_ways: self.__prune_way(wayid,way,pruned_nodes,pruned_ways)
            for nodeid,node in relation_nodes: self.__prune_node(nodeid,node,pruned_nodes)
        print "pruned %d nodes and %d ways while removing %d relations" % (len(pruned_nodes),len(pruned_ways),len(self.relations))
    def prune_cycle_ways(self, pruned_nodes, pruned_ways):
        for wayid,way in self.ways.items():
            nnode_connected = 0
            has_cycle = False
            nodeids = []
            for nodeid,node in way:
                if len(self.nodes_ways[nodeid]) > 1:
                    nnode_connected += 1
                if not has_cycle and nodeid in nodeids:
                    has_cycle = True
                nodeids.append(nodeid)
            if has_cycle and nnode_connected == 2:
                self.__prune_way(wayid,way,pruned_nodes,pruned_ways)
        print "pruned %d nodes and %d ways while removing cycles" % (len(pruned_nodes),len(pruned_ways))
    def prune_unused_nodes(self,pruned_nodes):
        for id,node in self.nodes.items():
            if not self.nodes_ways[id]: self.__prune_node(id,node,pruned_nodes)
        print "pruned %d unused nodes" % len(pruned_nodes)
        
def load_osm(filename):
    handler = MapHandler()
    parse(filename,handler)
    return handler

map = load_osm("quetigny.osm")
unused_nodes = []
unused_ways = []
map.prune_nodes_and_ways_in_relation(unused_nodes,unused_ways)
map.prune_cycle_ways(unused_nodes,unused_ways)
map.prune_unused_nodes(unused_nodes)
print map

figure()
title("pruned data")
unused_nodes = array(unused_nodes)
plot(unused_nodes[:,0],unused_nodes[:,1],'ro')
nodes = array(map.nodes.values())
plot(nodes[:,0],nodes[:,1],'go')

for way in unused_ways:
    foo = array([node for id,node in way])
    plot(foo[:,0],foo[:,1],'r')

for way in map.ways.values():
    foo = array([node for id,node in way])
    plot(foo[:,0],foo[:,1],'g')

figure()
crossing_nodes = array([node for id,node in map.nodes.items() if len(map.nodes_ways[id]) > 1])
plot(crossing_nodes[:,0],crossing_nodes[:,1],'og')
for way in map.ways.values():
    foo = array([node for id,node in way])
    plot(foo[:,0],foo[:,1])


show()


