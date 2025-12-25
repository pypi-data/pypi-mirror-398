class CdoOptions:
    """
    Manage CDO options
    
    Parameters
    ----------
    options : str 
        Options for CDO to use globally (e.g. "-L")
    
        

    Examples
    --------
    from pycdo import cdo_options
    # Use thread safe implementation
    cdo_options$set("-L")

    # Remove all options
    cdo_options$clear()
    """
    def __init__(self):
        self._options = None

    def set(self, options):
        """Set default CDO options (string or list of strings)."""
        old = self._options
        self._options = options
        return old

    def get(self):
        """Get current default CDO options."""
        return self._options
        
    def clear(self):
        old = self._options
        self._options = None
        return old

# Create a global options object
cdo_options = CdoOptions()


def combine_options(global_options=None, user_options=None, replace=False):
    """
    Combine or replace global and user options.
    - If replace=True: use user_options only.
    - If replace=False: combine global_options and user_options.
    """

    def to_list(opts):
        if opts is None or opts == "":
            return []
        if isinstance(opts, list):
            return opts
        if isinstance(opts, str):
            return [opts]
        raise TypeError("Options must be a string or a list of strings.")

    if replace:
        return to_list(user_options)

    if user_options is None:
        return to_list(global_options)
    
    # Combine both (as list or string)
    return to_list(global_options) + to_list(user_options)


