import overpy
import geojson
from dataclasses import dataclass
from typing import List
from .geo import Bbox, LonLat

AMENITY_LIST=["administration","advertising","alm","animal_boarding","animal_breeding","animal_shelter",
    "architect_office","archive","arts_centre","artwork","atm","audiologist","baby_hatch","baking_oven",
    "bank","bar","bbq","bench","biergarten","bikeshed","binoculars","bird_bath","boat_rental","boat_sharing","boat_storage",
    "bts","bureau_de_change","cafe","carpet_washing","car_pooling","car_rental","car_repair","car_sharing",
    "car_wash","casino","charging_station","childcare","citymap_post","cloakroom","clock","clothes_dryer",
    "club","coast_guard","coast_radar_station","community_center","community_centre","concert_hall",
    "concession_stand","conference_centre","consulate","courthouse","coworking_space","crematorium",
    "crucifix","crypt","customs","dancing_school","dead_pub","dentist","device_charging_station","disused",
    "dog_bin","dog_toilet","dog_waste_bin","dressing_room","drinking_water","driver_training",
    "driving_school","dryer","education","embassy","emergency_phone","events_venue","ev_charging",
    "exhibition_centre","fast_food","food_court","feeding_place","ferry_terminal","festival_grounds","financial_advice","fire_hydrant",
    "fire_station","first_aid","fish_spa","fountain","fridge","fuel","funeral_hall","gambling","game_feeding",
    "garages","give_box","grit_bin","gym","health_post","hospice","hospital","hotel","hunting_stand",
    "hydrant","ice_cream","internet_cafe","jobcentre","Juice_bar","juice_bar","kiosk","kitchen",
    "Kneippbecken","kneipp_water_cure","language_school","lavoir","letter_box","library","lifeboat_station",
    "life_ring","loading_dock","lost_property_office","lounger","Luggage_Locker","marae","microwave",
    "milk_dispenser","mobile_library","mobile_money_agent","money_transfer","mortuary","motorcycle_parking",
    "motorcycle_rental","motorcycle_taxi","music_school","music_venue","nursery","nursing_home","office",
    "outfitter","park","parking_entrance","parking_space","payment_centre","payment_terminal","pharmacy",
    "piano","place_of_worship","planetarium","police","polling_station","post_box","post_depot","post_office",
    "prep_school","preschool","printer","prison","prison_camp","pub","public_bookcase","public_building",
    "ranger_station","ranger_station","reception","reception_area","reception_desk","reception_desk",
    "reception_point","refugee_housing","refugee_site","register_office","rescue_station",
    "research_institute","restaurant","retirement_home","rv_storage","sanatorium","sanitary_dump_station","sauna","seat",
    "shelter","shop","shower","ski_rental","ski_school","smoking_area","snow_removal_station","social_centre",
    "spa","sport_school","stables","stage","stool","studio","surf_school","swimming_pool","table","taxi",
    "telephone","television","theatre","ticket_booth","ticket_validator"]


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
        '''
        Gets the Result as GeoJSON 
        
        NOTICE: It returns only the nodes for now
        '''
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
            self.node_req += f"node [{k}={v}] {osm};\n"
    
    def way_kv(self, k: str, v_list: List[str]):
        osm = self.bbox.to_osm()
        for v in v_list:
            self.way_req += f"way [{k}={v}] {osm};\n"
    
    def rel_kv(self, k: str, v_list: List[str]):
        osm = self.bbox.to_osm()
        for v in v_list:
            self.rel_req += f"rel [{k}={v}] {osm};\n"
    
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
    
    def add_poi(self, poi):
        ''' Adds a Point Of Interest to the list of elements to retrieve '''
        # TODO add other known keys
        if poi in AMENITY_LIST:
            osm = self.bbox.to_osm()
            self.node_req += f"node [amenity={poi}] {osm};\n"


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
