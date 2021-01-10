from flask import Flask, request, Response
from geobot.tileget import Tileget
from geobot.tilerender import draw_image
from geobot.geo import Bbox, LonLat
from geobot.overpass import SimpleQuery
import os
import geojson
from shutil import rmtree
app = Flask(__name__)

@app.route('/')
def root_response():
    return 'Hello from DO App Platform!'

@app.route('/api/bbox/<w>/<n>/<e>/<s>', methods=['GET', 'POST'])
def show_bbox(w, n, e, s):
    '''
    Shows an Image contaning the selected bounding-box
    
    Optionally, some GeoJSON to be rendered can be passed as argument
    '''
    bbox = Bbox(float(w), float(n), float(e), float(s))
    try:
        content = request.get_json(force=True)
    except Exception:
        content = None

    # Build a Tile Getter
    getter = Tileget(os.getenv('MAPBOX_URL'), os.getenv('MAPBOX_TOKEN'))
    
    # Optional parameters
    cropped = request.args.get('cropped', False)
    cropped = True if not cropped is False else False

    # Build image
    out = draw_image(bbox, getter, watermark="© Mapbox", geo_json=content, crop_bbox=cropped)

    path = out.path
    out_dir = out.dir
    
    with open(path, 'rb') as f:
        data = f.readlines()
    out.remove()
    rmtree(out_dir)
    return Response(data, headers={
        'Content-Type': f"image/{out.ext}"
    })

@app.route('/api/poi_bbox/<float:w>/<float:n>/<float:e>/<float:s>', methods=['POST'])
def show_poi_bbox(w, n, e, s):
    ''' Shows an Image contaning the selected bounding-box, adding Points of Interest'''
    bbox = Bbox(w, n, e, s)
    content = request.get_json(force=True)
        
    if content is not None:
        try:
            poi = content['poi']
            q = SimpleQuery(bbox)
            for p in poi:
                q.add_poi(p)
            res = q.execute()
            geo_data = res.to_geojson(node_props={"marker": True})
            geo_data = geojson.dumps(geo_data)
        except Exception:
            geo_data = None
    else:
        geo_data = None

    # Build a Tile Getter
    getter = Tileget(os.getenv('MAPBOX_URL'), os.getenv('MAPBOX_TOKEN'))
    
    # Optional parameters
    cropped = request.args.get('cropped', False)
    cropped = True if cropped is not False else False
    
    # Build image
    out = draw_image(bbox, getter, watermark="© Mapbox, dataset © OpenStreetMap and contributors", geo_json=geo_data, crop_bbox=cropped)

    path = out.path
    out_dir = out.dir
    
    with open(path, 'rb') as f:
        data = f.readlines()
    out.remove()
    rmtree(out_dir)
    return Response(data, headers={
        'Content-Type': f"image/{out.ext}"
    })

@app.route('/api/point/<lon>/<lat>', methods=['GET', 'POST'])
def show_point(lon, lat):
    ''' 
    Shows an Image near the selected point
    
    Optionally, some GeoJSON to be rendered can be passed as argument
    '''
    lonlat = LonLat(float(lon), float(lat))
    try:
        content = request.get_json(force=True)
    except Exception:
        content = None

    # Build a Tile Getter
    getter = Tileget(os.getenv('MAPBOX_URL'), os.getenv('MAPBOX_TOKEN'))
    
    # Optional parameters
    near = int(request.args.get('near', 20))
    cropped = request.args.get('cropped', False)
    cropped = True if not cropped is False else False

    # Build Bbox with radius=near (in meters)
    ne = lonlat.get_offset(near, near)
    sw = lonlat.get_offset(-near, -near)
    bbox = Bbox(sw.lon, ne.lat, ne.lon, sw.lat)
    
    # Build image
    out = draw_image(bbox, getter, watermark="© Mapbox", geo_json=content, crop_bbox=cropped)

    path = out.path
    out_dir = out.dir
    
    with open(path, 'rb') as f:
        data = f.readlines()
    out.remove()
    rmtree(out_dir)
    return Response(data, headers={
        'Content-Type': f"image/{out.ext}"
    })

@app.route('/api/poi_point/<float:lon>/<float:lat>', methods=['POST'])
def show_poi_point(lon, lat):
    ''' Shows an Image near the selected point, adding Points of Interest '''
    lonlat = LonLat(lon, lat)
    try:
        content = request.get_json(force=True)
    except Exception:
        content = None
    
    # Build a Tile Getter
    getter = Tileget(os.getenv('MAPBOX_URL'), os.getenv('MAPBOX_TOKEN'))
    
    # Optional parameters
    near = int(request.args.get('near', 20))
    cropped = request.args.get('cropped', False)
    cropped = True if not cropped is False else False
    
    # Build Bbox with radius=near (in meters)
    ne = lonlat.get_offset(near, near)
    sw = lonlat.get_offset(-near, -near)
    bbox = Bbox(sw.lon, ne.lat, ne.lon, sw.lat)

    if content is not None:
        try:
            poi = content['poi']
            q = SimpleQuery(bbox)
            for p in poi:
                q.add_poi(p)
            res = q.execute()
            geo_data = res.to_geojson(node_props={"marker": True})
            geo_data = geojson.dumps(geo_data)
        except Exception:
            geo_data = None
    else:
        geo_data = None
    
    # Build image
    out = draw_image(bbox, getter, watermark="© Mapbox, dataset © OpenStreetMap and contributors", geo_json=geo_data, crop_bbox=cropped)

    path = out.path
    out_dir = out.dir
    
    with open(path, 'rb') as f:
        data = f.readlines()
    out.remove()
    rmtree(out_dir)
    return Response(data, headers={
        'Content-Type': f"image/{out.ext}"
    })