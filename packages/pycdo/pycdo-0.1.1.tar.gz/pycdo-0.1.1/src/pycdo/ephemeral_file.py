import os
from pathlib import Path

class EphemeralFile(str):
    """
    A file path string that automatically deletes the file when garbage collected.
    
    A subclass of str that represents a file path and automatically removes the 
    associated file from the filesystem when the object is garbage collected or 
    goes out of scope.
    
    Parameters
    ----------
    path : str
        The file path to create and manage. 
    
    Attributes
    ----------
    path : str
        The underlying file path string.
    
    Notes
    -----
    This class inherits from str to enable direct usage as a file path in functions
    expecting string arguments. The __fspath__ method allows it to be used with 
    functions accepting path-like objects.
    
    Examples
    --------
    >>> temp_file = EphemeralFile("temp.txt")
    >>> with open(temp_file, 'w') as f:
    ...     f.write("temporary data")
    >>> # File exists at this point
    >>> del temp_file  # File is automatically deleted
    """
    def __new__(cls, path):
        instance = str.__new__(cls, path)
        instance.path = path
        return instance
       
    def __del__(self):
        print("removing " + self.path)
        dir = os.path.dirname(self.path)
        if Path(self.path).exists():
          
            os.remove(self.path)
        
        if Path(dir).exists():
            try:
                os.rmdir(dir)  # Only removes if empty
            except OSError:
                pass  # Directory not empty, leave it
