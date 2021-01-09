import urllib3
import shutil
from .temps import TempFile, TempDir

class Tileget:
    '''
    Replacement for system wget (or curl)

    since it is not possibe to install C libraries and use pyCurl
    (which would be much faster), this function is an ad-hoc replacement
    for curl o wget, in order to download tiles.
    '''
    def __init__(self, tile_server_address, apikey="", keyname="access_token", chunk_size=2**16, retina_suffix='@2x'):
        '''
        Init of tileserver wget

        It cache the server url.
        It can also cache the apikey needed to access the resources.
        '''
        self.http = urllib3.PoolManager()
        self.tile_server_address = tile_server_address
        self.chunk_size = chunk_size
        if apikey != "":
            self.encoded_key = f"{keyname}={apikey}"
        else:
            self.encoded_key = False
        self.retina=retina_suffix
    
    def get_tile(self, z, x, y, ext, save_path=None, out_file=None, retina=False):
        '''
        GET function specific for a tile server
        '''
        if '.' in ext:
            ext = ext.replace('.', '')
        retina = self.retina if retina is True else ""
        
        url= f"{self.tile_server_address}/{z}/{x}/{y}{retina}.{ext}"
        if save_path is None:
            save_dir = TempDir()
            save_path = save_dir.path
        if out_file is None:
            save_file = TempFile(dir=save_path, ext=ext)
            out_file = save_file.path
        if self.encoded_key is not False:
            url = f"{url}?{self.encoded_key}"
        try:
            with self.http.request('GET', url, preload_content=False) as r, open(out_file, 'wb') as out: 
                while True:
                    data = r.read(self.chunk_size)
                    if not data:
                        break
                    out.write(data)
            return out_file
        except Exception as e:
            print(e)
            return None
