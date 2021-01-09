import geojson
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from .temps import TempFile
from .geo import Bbox
import io
import urllib.request

FA_URL="https://use.fontawesome.com/releases/v5.15.1/webfonts/fa-regular-400.ttf"
FA_SOLID_URL="https://use.fontawesome.com/releases/v5.15.1/webfonts/fa-solid-900.ttf"

@dataclass
class Dtile:
    tile: TempFile
    coords: Bbox

    def __post_init__(self):
        self.image = Image.open(self.tile.path)
        (w, h) = self.image.size
        self.ratio = get_ratio(w, h, self.coords)
        self.icons = None

    def save(self):
        ''' Save the underlying image and its changes to the TempFile '''
        self.image.save(self.tile.path)
    
    def resize(self, size=(600, 600), method=Image.LANCZOS):
        self.image = self.image.resize(size, method)
        (w, h) = size
        self.ratio = get_ratio(w, h, self.coords)
    
    def harmonious_resize(self, size=(600, 600), method=Image.LANCZOS):
        (w, h) = self.image.size
        (target_w, target_h) = size
        ratio = min(target_w/w, target_h/h)
        (w, h) = (w * ratio, h * ratio)
        w = round(w)
        h = round(h)
        self.image = self.image.resize((w, h), method)
        self.ratio = get_ratio(w, h, self.coords)
    
    def watermark(self, watermark, bg_color='#000000', color="#ffffff", text_padding=5, padding=10):
        w, h = self.image.size
        drawing = ImageDraw.Draw(self.image)
        font = ImageFont.load_default() # Default font; space for improvements
        # Gets raw size of watermark text
        wm_w, wm_h = drawing.textsize(watermark, font)

        # add paddings
        (wm_w, wm_h)=(wm_w + text_padding, wm_h + text_padding)
        pos = (w - wm_w) - padding, (h - wm_h) - padding
        
        #Create watermark as different image to apply fill, color, and alpha mask
        wm_image = Image.new('RGB', (wm_w, wm_h), color = bg_color)
        drawing = ImageDraw.Draw(wm_image)
        drawing.text((int(text_padding/2),int(text_padding/2)), watermark, fill=color, font=font)
        wm_image.putalpha(100)
        self.image.paste(wm_image, pos, wm_image)

    def load_geojson_file(self, json_file):
        ''' Load GeoJSON from a file '''
        json_str = open(json_file).read()
        self.geodata = geojson.loads(json_str)
    
    def load_geojson(self, json_str):
        ''' Load GeoJSON from a dump string '''
        self.geodata = geojson.loads(json_str)
    
    def load_iconset(self, iconset="fa-regular-400.ttf", size=20):
        self.icons = ImageFont.truetype(iconset, size)

    def load_iconset_url(self, url=FA_SOLID_URL, size=20):
        self.icons = ImageFont.truetype(_font_url(url), size)
    
    def crop_to_coords(self, bbox):
        ''' Crops the image to the Bounding Box '''
        w, h = self.image.size
        ref_frame = (self.coords.west, self.coords.south)
        left, top = parse_point((bbox.west, bbox.north), ref_frame, self.ratio)
        right, bottom = parse_point((bbox.east, bbox.south), ref_frame, self.ratio)
        top = h - top
        bottom = h - bottom

        self.image = self.image.crop((round(left), round(top), round(right), round(bottom)))
        # Gets new dimensions, new coords and new ratio
        w, h = self.image.size
        self.coords = bbox
        self.ratio = get_ratio(w, h, self.coords)


    def render_geojson(self):
        try:
            features = list(self.geodata['features'])
            draw = ImageDraw.Draw(self.image)
            ref_frame = (self.coords.west, self.coords.south)
            w, h = self.image.size
            for f in features:
                try:
                    f_type = f['geometry']['type']
                    # Get some properties
                    try:
                        color = f['geometry']['properties']['color']
                    except Exception:
                        color = (255,0,0)
                    
                    # Parse type and draw
                    if f_type == 'Point':
                        # Draw a Point
                        try:
                            r = f['geometry']['properties']['radius']
                        except Exception:
                            r = 3
                        try:
                            marker = f['geometry']['properties']['marker']
                            
                            if marker is True:
                                marker = chr(0xf3c5) # FA-MAP-MARKER-ALT
                        except Exception:
                            marker = None
                        x, y = parse_point(f['geometry']['coordinates'], ref_frame, self.ratio)
                        # correct inverse y; 
                        y = h - y
                        if (marker is not None) and (self.icons is not None):
                            # Draw a marker
                            draw.text((x, y), marker, fill=color, font=self.icons)                   
                        else:
                            # Draw an ellipse"
                            draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
                    
                    elif f_type == 'LineString':
                        # Draw a Line
                        try:
                            width = f['geometry']['properties']['width']
                        except Exception:
                            width = 2
                        line = []
                        for c in f['geometry']['coordinates']:
                            line.append(parse_point(c, ref_frame, self.ratio))
                        draw.line(line, fill=color, width=width, joint="curve")
                    
                    elif f_type == 'Polygon':
                        # Draw a Polygon
                        try:
                            fill = f['geometry']['properties']['outline']
                        except Exception:
                            fill = None
                        poly = []
                        for p in f['geometry']['coordinates']:
                            for c in p:
                                poly.append(parse_point(c, ref_frame, self.ratio))
                            draw.polygon(poly, fill=fill, outline=color)
                            # inverts colors for the interior polygon, saving alpha channel if present
                            if len(color) == 4:
                                color2 = tuple(255 - c for c in color[:-1])
                                color = color2 + (color[-1],)
                            else:
                                color = tuple(255 - c for c in color)
                    else:
                        pass
                except Exception:
                    pass
        except AttributeError:
            pass


def get_ratio(w, h, bbox: Bbox):
    ''' Returns a tuple containing the ratio of the pixel as geo entity '''
    r_W = abs(bbox.west - bbox.east) / w
    r_H = abs(bbox.north - bbox.south) / h
    return (r_W, r_H)

def parse_point(coords, reference_coords, ratio):
    (rx, ry) = ratio
    (lon, lat) = coords
    (x, y) = reference_coords
    # Shift of coordinates
    sx, sy = lon - x, lat - y
    # Change of measures
    return (sx / rx, sy / ry)

def _font_url(url):
    # See https://stackoverflow.com/questions/12020657/how-do-i-open-an-image-from-the-internet-in-pil
    fd = urllib.request.urlopen(url)
    font_file = io.BytesIO(fd.read())
    return font_file