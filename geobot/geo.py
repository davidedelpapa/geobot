'''
Shoutout: some algorithms heavily inspired by https://github.com/mapbox/mercantile
'''
import math
import geojson
from dataclasses import dataclass

class GeoError(Exception):
    ''' Base exception '''

class ParseError(GeoError):
    ''' Raised when parsing '''


@dataclass
class Bbox:
    '''
    Class that represents a boundng box, as a West (lon), North (lat), East (lon), South (lat) coordinates.
    
    It can be thought of also as X1, Y1, X2, Y2 bounding box (it makes more sense in the first quadrant geometry),
    as a way to correlate longitude and latitude to the cartesian plane.
    '''
    west: float
    north: float
    east: float
    south: float

    def to_tuple(self):
        ''' Returns a tuple of its coordinates (Raw Bbox) '''
        return(self.west, self.north, self.east, self.south)
    
    def to_osm(self):
        ''' Returns a tuple of its coordinates for use with OSM data '''
        return(self.south, self.west, self.north, self.east)

    def to_tileset(self, zoom):
        '''
        Returns all the tiles overlapped by a the Bbox at a set zoom.

        zoom: is the given tileset zoom
        '''
        # Constant. Useful to avoid limit cases
        DELTA = 1e-11
        
        tileset = []
        ll1 = ragularize_lonlat(self.east, self.north)
        ll2 = ragularize_lonlat(self.west, self.south)
        east, north = ll1.lon, ll1.lat
        west, south = ll2.lon, ll2.lat
        
        # In case the box is straddling the line of change of date
        if west > east:
            bbox_west = (-180.0, north, east, south)
            bbox_east = (west, north, 180.0, south)
            bboxes = [bbox_west, bbox_east]
        else:
            bboxes = [(west, north, east, south)]
        
        for west, north, east, south  in bboxes:
            # Clamp bounding values.
            w = max(-180.0, west)
            n = min(85.051129, north)
            e = min(180.0, east)        
            s = max(-85.051129, south)
            first_tile = LonLat(w, n).tile(zoom)
            last_tile = LonLat(e - DELTA, s + DELTA).tile(zoom)
            x1 = first_tile.x
            x2 = last_tile.x
            y1 = first_tile.y
            y2 = last_tile.y
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            
            for i in range(x1, x2 + 1):
                for j in range(y1, y2 + 1):
                    tileset.append(Tile(zoom, i, j))

        return tileset

    def infer_zoom(self, visible_tiles=None):
        '''
        Infers the max zoom at which the Bbox is visible in its entirety in n visible tiles (default 1)

        The algorythm uses a brute-force method.
        '''
        visible_tiles = 1 if visible_tiles is None else visible_tiles
        
        if (visible_tiles != int(visible_tiles)) or (visible_tiles < 1):
            raise ParseError("Visible tile number must be a non-negative integer, 1 or more")
        zoom = 0
        while visible_tiles >= len(self.to_tileset(zoom + 1)):
            zoom += 1
        if visible_tiles > len(self.to_tileset(zoom)):
            zoom += 1
        return zoom
    
    def fit_tileset(self, visible_tiles=None):
        '''
        Returns all the tiles overlapped by the Bbox at a set zoom, inferring the zoom.

        Optionally the number of visible tiles to be covered by the Bbox can be set as visible_tiles=n.

        visible_tiles: is the given tileset dimension (approx)
        '''
        visible_tiles = 1 if visible_tiles is None else visible_tiles
        
        if (visible_tiles != int(visible_tiles)) or (visible_tiles < 1):
            raise ParseError("Visible tile number must be a non-negative integer, 1 or more")
        
        zoom = 0
        tileset = self.to_tileset(zoom)
        while visible_tiles >= len(self.to_tileset(zoom + 1)):
            zoom += 1
            tileset = self.to_tileset(zoom)
        if visible_tiles > len(self.to_tileset(zoom)):
            tileset = self.to_tileset(zoom + 1)
        return tileset

    def to_geojson(self, props=None):
        ''' Gets the Bbox as GeoJSON Polygon '''
        w = float(self.west)
        n = float(self.north)
        e = float(self.east)
        s = float(self.south)
        p = geojson.Polygon([[(w, n), (w, s), (e, s), (e, n), (w, n)]])
        if props is not None:
            p["properties"] = props
        return p

@dataclass
class Tile:
    ''' Class that represents a Tile, as a Zoom plus X, Y coordinates '''
    z: int
    x: int
    y: int

    def longlat(self, center = True, lr = False):
        '''
        Gets a LonLat point given the Tile

        By default it gets the upper-left coordinates of the tile
        If center=True, gets the center coords
        If lr = True, gets the lower-right corner coordinates
        ''' 
        if lr:
            x = self.x + 1
            y = self.y + 1    
        elif center:
            x = self.x + 0.5
            y = self.y + 0.5
        else:
            x = self.x
            y = self.y
        
        n = 2.0 ** self.z
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return LonLat(lon_deg, lat_deg)
    
    def to_bbox(self):
        ''' Returns a Bbox containing the whole tile '''
        ul = self.longlat(center=False, lr = False)
        lr = self.longlat(center=False, lr = True)
        west = ul.lon
        north = ul.lat
        east = lr.lon
        south = lr.lat
        return Bbox(min(west, east), max(south, north), max(west, east), min(south, north))

    def quadkey(self):
        ''' Gets the Quadkey of the tile '''
        key = []
        for z in range(self.z, 0, -1):
            digit = 0
            mask = 1 << (z - 1)
            if self.x & mask:
                digit += 1
            if self.y & mask:
                digit += 2
            key.append(str(digit))
        return "".join(key)
    
    def parent(self, zoom=None):
        '''
        Gets the parent of the tile at given zoom, or the direct parent if not specified
        
        If zoom == the tile zoom, the same tile is returned
        '''
        zoom = self.z - 1 if zoom is None else zoom
        if (zoom != int(zoom)) or (zoom < 0):
            raise ParseError("Zoom must be a non-negative integer")
        elif self.z < zoom: 
            raise ParseError(f"Parent zoom(requested: {zoom}) must be less than current tile zoom({self.z})")
        elif self.z == 0:
            raise ParseError("Current tile is Tile(0): can't have a parent")
                        
        return_tile = Tile(self.z, self.x, self.y)

        while return_tile.z > zoom:
            x, y, z = return_tile.x, return_tile.y, return_tile.z
            if x % 2 == 0 and y % 2 == 0:
                return_tile = Tile( z - 1, x // 2, y // 2)
            elif x % 2 == 0:
                return_tile = Tile( z - 1, x // 2, (y - 1) // 2)
            elif not x % 2 == 0 and y % 2 == 0:
                return_tile = Tile( z - 1, (x - 1) // 2, y // 2)
            else:
                return_tile = Tile( z - 1, (x - 1) // 2, (y - 1) // 2)
        return return_tile

    def children(self, zoom=None):
        '''
        Gets the children of the tile at given zoom, or the direct parent if not specified
        
        If zoom == the tile zoom, the same tile is returned
        '''
        zoom = self.z + 1 if zoom is None else zoom
        if (zoom != int(zoom)) or (zoom < 0):
            raise ParseError("Zoom must be a non-negative integer")
        elif self.z > zoom: 
            raise ParseError(f"Children zoom(requested: {zoom}) must be greater than current tile zoom({self.z})")
        
        curr_tile = Tile(self.z, self.x, self.y)
        return_tileset =[curr_tile]

        while return_tileset[0].z < zoom:
            t = return_tileset.pop(0)
            return_tileset += [
                Tile(t.z + 1, t.x * 2, t.y * 2),
                Tile(t.z + 1, t.x * 2 + 1, t.y * 2),
                Tile(t.z + 1, t.x * 2 + 1, t.y * 2 + 1),
                Tile(t.z + 1, t.x * 2, t.y * 2 + 1),
            ]
        return return_tileset

@dataclass
class LonLat:
    ''' Represents a geographic point as (Longitude, Latitude) '''

    lon: float
    lat: float

    def tile(self, zoom: int):
        '''
        Gets X and Y for a given coordinate at given zoom-level
        '''
        lat_rad = math.radians(self.lat)
        n = 2.0 ** zoom
        x = int((self.lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return Tile(zoom, x, y)
    
    def to_geojson(self, props=None):
        ''' Gets the LonLat as GeoJSON Point '''
        ln = float(self.lon)
        lt = float(self.lat)
        p = geojson.Point((ln, lt))
        if props is not None:
            p["properties"] = props
        return p

def ragularize_lonlat(lon, lat):
    if lon > 180.0:
        lon = 180.0
    elif lon < -180.0:
        lon = -180.0
    if lat > 90.0:
        lat = 90.0
    elif lat < -90.0:
        lat = -90.0
    return LonLat(lon=lon, lat=lat)

def parse_tile(z, x, y):
    ''' Returns a Tile from a (z, x, y) trilplet '''
    return Tile(z=z, x=x, y=y)

def parse_lonlat(lon, lat):
    ''' Returns a regularized LonLat from a (lon, lat)'''
    return ragularize_lonlat(lon, lat)

def parse_quadkey(quadkey):
    ''' Returna a Tile from a given Quadkey '''
    if len(quadkey) == 0:
        return Tile(0, 0, 0)
    x, y = 0, 0
    for i, digit in enumerate(reversed(quadkey)):
        mask = 1 << i
        if digit == "1":
            x = x | mask
        elif digit == "2":
            y= y | mask
        elif digit == "3":
            x = x | mask
            y = y | mask
        elif digit != "0":
            raise ParseError(f"Unexpected quadkey digit: {digit}")
    return Tile(i + 1, x, y)

def tileset2bbox(tileset):
    ''' Gets the Bbox including the whole tileset '''
    # Constant. Useful to avoid limit cases
    DELTA = 1e-11
    bbox = []
    coord_list = [t.to_bbox().to_tuple() for t in tileset]
    for i in range(0, 4):
        res = sorted(coord_list, key=lambda x: x[i])
        bbox.append((res[0][i], res[-1][i]))
    return Bbox(bbox[0][0] + DELTA, bbox[1][1] - DELTA, bbox[2][1] - DELTA, bbox[3][0] + DELTA)

def feature2bbox(feat):
    '''
    Returns a Bbox out of a GeoJSON Feature
    '''
    bbox = []
    coord_list = list(geojson.utils.coords(feat))
    for i in (0, 1):
        res = sorted(coord_list, key=lambda x: x[i])
        bbox.append((res[0][i], res[-1][i]))
    return Bbox(bbox[0][0], bbox[1][0], bbox[0][1], bbox[1][1])

def point_in_poly(lonlat: LonLat, polygon)-> bool:
    '''
    Determine if the point is contained in the polygon.

    Check: https://en.wikipedia.org/wiki/Even%E2%80%93odd_rule
    '''
    coord_list = list(geojson.utils.coords(polygon))
    num = len(coord_list)
    i = 0
    j = num - 1
    c = False
    for i in range(num):
        if ((coord_list[i][1] > lonlat.lat) != (coord_list[j][1] > lonlat.lat)) and \
            (lonlat.lon < coord_list[i][0] + (coord_list[j][0] - coord_list[i][0]) * 
                (lonlat.lat - coord_list[i][1]) / (coord_list[j][1] - coord_list[i][1])):
            c = not c
        j = i
    return c
