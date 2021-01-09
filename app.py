from flask import Flask, request, Response
from geobot.tileget import Tileget
from geobot.tilerender import draw_image
from geobot.geo import Bbox
import os
from shutil import rmtree
app = Flask(__name__)

@app.route('/')
def root_response():
    return 'Hello from DO App Platform!'

@app.route('/api/bbox/<float:w>/<float:n>/<float:e>/<float:s>/')
def show_bbox(w, n, e, s):
    ''' Shows an Image contaning the selected bounding-box '''
    bbox = Bbox(w, n, e, s)

    # Build a Tile Getter
    getter = Tileget(os.getenv('MAPBOX_URL'), os.getenv('MAPBOX_TOKEN'))
    
    # Optional parameters
    cropped = request.args.get('cropped', False)
    out = draw_image(bbox, getter, watermark="© Mapbox", crop_bbox=cropped)

    path = out.path
    out_dir = out.dir
    
    with open(path, 'rb') as f:
        data = f.readlines()
    out.remove()
    rmtree(out_dir)
    return Response(data, headers={
        'Content-Type': f"image/{out.ext}"
    })
