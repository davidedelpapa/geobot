import overpy
import geojson
from dataclasses import dataclass
from typing import List
from .geo import Bbox, LonLat

@dataclass
class Result:
    result: overpy.Result

    def nodes(self):
        return self.result.nodes
    def relations(self):
        return self.result.relations
    def ways(self):
        return self.result.ways

    def nodes_coords(self):
        return [LonLat(n.lon, n.lat) for n in self.result.nodes]
    def relations_coords(self):
        return [LonLat(r.lon, r.lat) for r in self.result.relations]
    def ways_coords(self):
        return [LonLat(w.lon, w.lat) for w in self.result.ways]
    
    def nodes_ids(self):
        return [n.id for n in self.result.nodes]
    def relations_ids(self):
        return [r.id for r in self.result.relations]
    def ways_ids(self):
        return [w.id for w in self.result.ways]
    
    def to_geojson(self, props=None, node_props=None):
        ''' Gets the Result as GeoJSON '''
        nodes = []
        for n in self.nodes_coords():
            nodes.append(geojson.Feature(geometry=n.to_geojson(props=node_props)))
        """
        # TODO make polygons out of these
        ways = [way.get_nodes(resolve_missing=True) for way in self.ways()]
        relations = [relation.get_nodes(resolve_missing=True) for relation in self.relations()]

        for w in ways:
            nodes.append(geojson.Feature(geometry=w.to_geojson(props=node_props)))
        for r in relations:
            nodes.append(geojson.Feature(geometry=r.to_geojson(props=node_props)))     
        """
        fc = geojson.FeatureCollection(nodes)
        if props is not None:
            fc["properties"] = props
        return fc

        

@dataclass
class SimpleQuery:
    bbox: Bbox

    def __post_init__(self):
        self.api = overpy.Overpass()
        self.node_req = ""
        self.way_req  = ""
        self.rel_req  = ""

    def node_kv(self, k: str, v_list: List[str]):
        osm = self.bbox.to_osm()
        for v in v_list:
            self.node_req += f"node [{k}={v}] {osm};"
    
    def way_kv(self, k: str, v_list: List[str]):
        osm = self.bbox.to_osm()
        for v in v_list:
            self.way_req += f"way [{k}={v}] {osm};"
    
    def rel_kv(self, k: str, v_list: List[str]):
        osm = self.bbox.to_osm()
        for v in v_list:
            self.rel_req += f"rel [{k}={v}] {osm};"
    
    def execute(self, out='json'):
        query = f"""
            [out:{out}];
            (
            {self.node_req}
            {self.way_req}
            {self.rel_req}
            );
            out;
        """
        return Result(self.api.query(query))


# TODO: Work-In-Progress
@dataclass
class BuilderQuery:
    query: str

    def __post_init__(self):
        self.api = overpy.Overpass()
    
    def execute(self):
        return Result(self.api.query(self.query))

    def add_head(self, kv_list):
        head = ""
        for (k, v) in kv_list:
            head += f"[{k}:{v}]"
        self.query = head + ';\n' + self.query


