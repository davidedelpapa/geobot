from os import listdir
from os.path import isfile, join, basename
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from .tiledraw import Dtile

from .temps import TempDir, TempFile
from .tileget import Tileget
from .geo import Bbox, Tile, tileset2bbox

def get_raw_bbox(bbox:Bbox, getter: Tileget, visible_tiles=4, img_type = ".png", retina=False):
    '''
    Get tiles corresponding to the bounding specified box.

    Returns a temporary directory, an a list of the temporary files created, containing the tiles
    The user MUST DELETE the files and the directory after use.

    bbox: the target bounding box
    getter: Tileget
    visible_tiles: is the given tileset dimension (approx)
    img_type: Image type as file extension (default: "png")
    '''
    temp_dir = TempDir()
    temp_dir_files=[]
    ideal_zoom = bbox.infer_zoom(visible_tiles)
    tileset = bbox.to_tileset(ideal_zoom)
    # TODO spawn threads
    for tile in tileset:
        file_name = f"{tile.x}-{tile.y}"
        temp_file = TempFile(name=file_name, ext=img_type, dir=temp_dir.path)
        temp_dir_files.append(temp_file)
        result = getter.get_tile(ideal_zoom, tile.x, tile.y, img_type, temp_dir.path, temp_file.path, retina)
        if result is False:
            # TODO: create a blank tile (grey) or a failsafe
            pass
    return temp_dir, temp_dir_files, tileset

def tiles2image(temp_dir, img_type = "png"):
    '''
    Gets a single image out of different tiles
    
    temp_dir: is a string path 
    img_type: Image type as file extension (default: "png")
    '''
    img_type = img_type.lstrip(".")
    
    tiles = [f for f in listdir(temp_dir) if isfile(join(temp_dir, f))]
    xx = []
    yy = []
    
    for f in tiles:
        name, _ = f.split('.', 1)
        x, y = name.split('-', 1)
        xx.append(x)
        yy.append(y)
    xx = list(dict.fromkeys(xx))
    yy = list(dict.fromkeys(yy))
    xx.sort(key = int) 
    yy.sort(key = int) 

    ynames = [f"{y}.{img_type}" for y in yy]

    temp_file = TempFile(ext=img_type, dir=temp_dir)

    swaths = []

    # create swaths
    for x in xx:
        swaths_names = [f"{temp_dir}/{x}-{y}" for y in ynames]
        images =  list(map(Image.open, swaths_names))
        widths, heights = zip(*(i.size for i in images))
        total_height = sum(heights) 
        max_width = max(widths) # should be 256px...
        new_im = Image.new('RGB', (max_width, total_height))
        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += im.size[1]
        swaths.append(new_im)
    
    # create a unique image from all swath
    widths, heights = zip(*(i.size for i in swaths))
    total_width = sum(widths)
    max_height = max(heights)
    mosaic = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for im in swaths:
        mosaic.paste(im, (x_offset,0))
        x_offset += im.size[0]
    mosaic.save(temp_file.path)
    
    return temp_file
    

def draw_image(bbox: Bbox, getter: Tileget, out_size=(600, 600), geo_json=None, img_type = ".png", visible_tiles=4, watermark=None, crop_bbox=False, retina=False):
    '''
    Preferred way to create an image from a Bounding Box an optional GeoJSON Layer, and a set size

    out_size: (X, Y) size of the output image in pixel. Default: (600, 600)
        If None, it is the size given by the sum of the tiles
    getter: Tileget
    visible_tiles: is the given tileset dimension (approx)
    img_type: Image type as file extension (default: "png")
    watermark: Is a Copyright text notice. Default: None
        Please remeber to credit with a Copyright notice the tiles provider,
        either on the image itself with this function(preferred) or somewhere else.
    '''
    try:
        # Get tiles and create a mosaic
        dir, file_list, tileset = get_raw_bbox(bbox, getter, visible_tiles, img_type, retina=True)
        out_file = tiles2image(dir.path, img_type)

        image = Dtile(out_file, tileset2bbox(tileset))

        # Draw GeoJSON
        if geo_json is not None:
            image.load_iconset_url()
            image.load_geojson(geo_json)
            image.render_geojson()

        # Crop to Bbox
        if crop_bbox is True:
            image.crop_to_coords(bbox)

        # Resize
        if out_size is not None:
            if crop_bbox is True:
                image.harmonious_resize(out_size)
            else:
                image.resize(out_size)

        # Copyright Watermark
        if watermark is not None:
            image.watermark(watermark)

        # Save image
        image.save()

        # Cleanup tiles
        for f in file_list:
            f.remove()

    except Exception as e:
        print(f"Err: {e}")
        return None
    
    return out_file
