import shutil
import os
import tempfile
from pathlib import Path

class CdoCache:
    def __init__(self, path = None, enabled = False, old = None):
        self._validate_path(path, enabled)
        self.path = path
        self.enabled = enabled
        self.old = old

    def _clone(self):
        return CdoCache(path = self.path, enabled = self.enabled, old = self.old)

    def _validate_path(self, path, enabled):
        if path is None and enabled:
            raise ValueError("Cannot enable cache with path None")

    def set(self, path):
        self._validate_path(path, True)
        # Create a new instance to return 
        old = self._clone()
        enabled = True
        # Support cache.set(old) syntax
        if isinstance(path, CdoCache): 
            enabled = path.enabled
            path = path.path

        self.path = path
        self.enabled = enabled
        self.old = old
        
        return old 
    
    def get(self):
        return self.path

    def restore(self):
        if self.old is None:
            raise ValueError("Cannot restore cache: no previous cache state saved")

        self.path = self.old.path
        self.enabled = self.old.enabled
        self.old = self.old.old


    def disable(self):
        old = self._clone()
        self.enabled = False
        self.old = old
        return old

    def enable(self):
        if self.path is None:
            self.path = tempfile.mkdtemp()
        old = self._clone()
        self.enabled = True
        self.old = old
        return old
    
    def is_enabled(self):
        return self.enabled


    def forget(self):
        restore = Path(self.path).exists
        if self.path is not None:
            shutil.rmtree(self.path)
        if restore:
            os.makedirs(self.path) 

    def _hash_get(self, file):
        # File is the full path because the user 
        # might be saving the file outside the cache folder
        file = file + ".hash"
        if Path(file).is_file():
            with open(file) as f:
                return f.readline()
            
        else:
            return ""
    
    def _hash_store(self, file, hash):
        hash_file = file + ".hash"
        if not Path(os.path.dirname(hash_file)).exists:
            os.mkdir(os.path.dirname(hash_file))

        with open(hash_file, "w") as f:
            f.write(hash)





# Global cache to use by the package
cdo_cache = CdoCache()

