from flask import Flask, request
from geobot.tileget import Tileget
from geobot.tilerender import draw_image
from geobot.geo import Bbox
import os
app = Flask(__name__)

@app.route('/')
def root_response():
    return 'Hello from DO App Platform!'

@app.route('/api/(<float:w>,<float:n>,<float:e>,<float:s>)')
def show_bbox(w, n, e, s):
    ''' Shows an Image contaning the selected bounding-box '''
    bbox = Bbox(w, n, e, s)

    # Build a Tile Getter
    getter = Tileget(os.getenv('MAPBOX_URL'), os.getenv('MAPBOX_TOKEN'))
    
    # Optional parameters
    cropped = request.args.get('cropped', False)
    out = draw_image(bbox, getter, watermark="© Mapbox", crop_bbox=cropped)

    path = out.path
    def generate_response():
        with open(path) as f:
            yield from f

        os.remove(path)

    r = app.response_class(generate_response(), mimetype=f"image/{out.ext}")
    r.headers.set('Content-Disposition', 'attachment', filename=f"{out.name}{out.ext}")
    return r
