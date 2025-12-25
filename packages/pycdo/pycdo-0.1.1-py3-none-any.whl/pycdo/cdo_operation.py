import os
import tempfile
import subprocess
import shlex
import hashlib
from pathlib import Path

from . import debug
from .cdo_options import cdo_options, combine_options
from .cdo_operator import CdoOperator
from .cdo_cache import cdo_cache
from .ephemeral_file import EphemeralFile

inf=float("inf")

def cdo(input = None) -> "CdoOperation":
    """
    Create a CDO operation
    
    Parameters
    ----------
    input : str or list of str
            Path to the file or files. 
    
    Returns
    -------
    CdoOperation
        A no-op CDO operation. Chain methods to chain other CDO operators and execute
        the operation with the execute method. 
    
    Examples
    --------

    clim_sh_temperature = cdo("temperature.nc").\
        sellonlatbox(0, 360, -90, 0).\
        ymonmean().\
        execute()
    """

    return CdoOperation._start(ifile=input)

class CdoOperation:
    @staticmethod
    def _start(ifile):
        if isinstance(ifile, list):
            n_input = len(ifile)
            input = ifile
        elif ifile is None:
            n_input = 0
            input = [None]
        else:
            n_input = 1
            input = [ifile]

        noop_operator = CdoOperator(command = "noop", n_input = n_input, n_output = n_input, params = [])
        return CdoOperation(input = input, operator = noop_operator, params = {})
    
    def __init__(self, input, operator: "CdoOperator", params: dict = {}):
        self.operator = operator
        self.params = params
        self.input = input
        
    def _new_op(self, operator: "CdoOperator", inputs: list = [], params: dict = {}):
        prev_output = self.operator.n_output + len(inputs)
        
        operators_compatible = operator.n_input == inf or operator.n_input == prev_output
        

        if not operators_compatible: 
            raise ValueError(f"Chaining error: {operator.command} expects {operator.n_input} but {self.operator.command} outputs {prev_output} files.")

        inputs = [self] + inputs
        return CdoOperation(inputs, operator, params)

    def _hash(self):
        """Generate a hash for cache key from command, input files, and CDO version"""
        hash_input = []
        
        # Add the command
        hash_input.append(self._build())
        
        # Add input file metadata
        for inp in self.input:
            if isinstance(inp, str) and os.path.isfile(inp):
                stat = os.stat(inp)
                hash_input.append(f"{inp}:{stat.st_size}:{stat.st_mtime}")
            elif isinstance(inp, CdoOperation):
                # Recursively hash nested operations
                hash_input.append(inp._hash())
        
        # Add CDO version (you may need to query this)
        # For now, placeholder:
        hash_input.append("cdo_version_placeholder")
        
        # Create hash
        hash_str = "|".join(hash_input)
        return hashlib.md5(hash_str.encode()).hexdigest()

    def _build(self, top_level=True, options=None, options_replace: bool = False):
        cmd = []
        if top_level:
            cmd.append("cdo")
            options = combine_options(cdo_options.get(), options, replace=options_replace)
            options_str = " ".join(options)
            cmd.append(options_str)

        # Operator command and params
        if (self.operator.command == "noop"):
            op_str = [""]
        else:
            op_str = [f"-{self.operator.command}"]

        if self.params:
            param_values = [str(v) for k, v in self.params.items() if v is not None]
        else :
            param_values = []

        op_str.extend(param_values)
        op_str = ",".join(op_str)
        
        cmd.append(op_str)

        # Build input strings
        input_strs = []

        for inp in self.input:
            if isinstance(inp, CdoOperation):
                # Recursively build without 'cdo' and wrap in parentheses
                input_strs.append(f"{inp._build(top_level=False)}")
            elif inp is None:
                input_strs = ""
            else: 
                input_strs.append(shlex.quote(str(inp)))
             
        input_strs = " ".join(input_strs)

        if self.operator.command != "noop" and input_strs != "":
            input_strs  = "[ " + input_strs + " ] "
        
        cmd.append(input_strs)

        # Some parts can create double spaces. I remove it 
        # for cleaner output
        return " ".join(cmd).replace("  ", " ").rstrip()

    def execute(self, output=None, options=None, options_replace=False):
        """
        Execute a CdoOperation

        Parameters
        ----------
        output : str or None
            The path to the output or output paths to save the result. If None, 
            then a temporary file(s) will be used. If cache is turned off, the temporary file 
            is deleted when all references to it are garbage collected. 

        options : str or None
            Optional options to use for this operation. 
        options_replace : Boolean
            Whether to replace the global options defined in pycdo.cdo_options or just add them. 
        
        Returns
        -------
        str or list of str
            The output. If the operator returns one or more files, the path to the file(s). 
            If the operator prints info (such as cdo().griddes()) the output of that operator.
        
        """

        if (self.operator.command == "noop"):
            return self.input
        
        n_files = self.operator.n_output

        # Protect against other thread chaning out cache. 
        cdo_cache_local = cdo_cache._clone()

        use_cache = cdo_cache_local.is_enabled() and n_files == 1
        if use_cache:
            hash_current = self._hash()
            dir = cdo_cache_local.get()
            if output is None:
                output = Path(dir) / hash_current
            hash_cache = cdo_cache_local._hash_get(output)
            if (hash_cache == hash_current):
                return output

        if output is None:
            output = []
            for _ in range(n_files):
                # mktemp is "not safe" because another process could use the file
                # in between here and when we write to it. 
                # But I can't use mkstemp() because that creates the file and some cdo
                # operators need the file not to exist. 
                # In reality, we start to write to the file almost immediatly, 
                # so the risk is miniscule. 
                file = tempfile.mktemp()
                output.append(EphemeralFile(file))
                
        if isinstance(output, list):
            output_str = " ".join(output)
        else:
            output_str = output
        
        cmd = f"{self._build(options = options, options_replace = options_replace)} {output_str}"

        _DEBUG_SKIP_RUN = os.environ.get("_DEBUG_SKIP_RUN", "").lower() == "true"

        if not _DEBUG_SKIP_RUN:
            result = subprocess.run(cmd, shell = True, capture_output = True)
        else:
            if n_files == 0:
                result = debug.MockResult(output = "Test Output")
            else:
                result = debug.MockResult(output = output)

        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)
        if n_files == 0:
            return result.stdout
        
        if isinstance(output, list) and len(output) == 1:
            output = output[0]
        
        if use_cache:
            cdo_cache_local._hash_store(output, hash_current)

        return output

    def __repr__(self):
        n_files = self.operator.n_output
        if n_files > 0:
            placeholder = " {output}"
        else:
            placeholder = ""
        return("CDO operation.\n"+ self._build() + placeholder)

## <<start operators>>

    def info(self): # pragma: no cover
        r"""
        CDO operator: info
        """
        operator = CdoOperator(command="info",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def infon(self): # pragma: no cover
        r"""
        CDO operator: infon
        """
        operator = CdoOperator(command="infon",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def cinfo(self): # pragma: no cover
        r"""
        CDO operator: cinfo
        """
        operator = CdoOperator(command="cinfo",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def map(self): # pragma: no cover
        r"""
        CDO operator: map
        """
        operator = CdoOperator(command="map",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def sinfo(self): # pragma: no cover
        r"""
        CDO operator: sinfo
        """
        operator = CdoOperator(command="sinfo",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def sinfon(self): # pragma: no cover
        r"""
        CDO operator: sinfon
        """
        operator = CdoOperator(command="sinfon",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def xsinfo(self): # pragma: no cover
        r"""
        CDO operator: xsinfo
        """
        operator = CdoOperator(command="xsinfo",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def xsinfop(self): # pragma: no cover
        r"""
        CDO operator: xsinfop
        """
        operator = CdoOperator(command="xsinfop",
                               n_input=inf, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def diff(self, ifile2, maxcount = None, abslim = None, rellim = None, names = None): # pragma: no cover
        r"""
        CDO operator: diff
        Parameters:
           maxcount: INTEGER - Stop after maxcount different fields
           abslim: FLOAT - Limit of the maximum absolute difference (default: 0)
           rellim: FLOAT - Limit of the maximum relative difference (default: 1)
           names: STRING - Consideration of the variable names of only one input file (left/right) or the intersection of both (intersect).
        """
        operator = CdoOperator(command="diff",
                               n_input=2, 
                               n_output=0, 
                               params=['maxcount', 'abslim', 'rellim', 'names']) 
                               
        return self._new_op(operator, [ifile2], {"maxcount": maxcount, "abslim": abslim, "rellim": rellim, "names": names})

    def diffn(self, ifile2, maxcount = None, abslim = None, rellim = None, names = None): # pragma: no cover
        r"""
        CDO operator: diffn
        Parameters:
           maxcount: INTEGER - Stop after maxcount different fields
           abslim: FLOAT - Limit of the maximum absolute difference (default: 0)
           rellim: FLOAT - Limit of the maximum relative difference (default: 1)
           names: STRING - Consideration of the variable names of only one input file (left/right) or the intersection of both (intersect).
        """
        operator = CdoOperator(command="diffn",
                               n_input=2, 
                               n_output=0, 
                               params=['maxcount', 'abslim', 'rellim', 'names']) 
                               
        return self._new_op(operator, [ifile2], {"maxcount": maxcount, "abslim": abslim, "rellim": rellim, "names": names})

    def npar(self): # pragma: no cover
        r"""
        CDO operator: npar
        """
        operator = CdoOperator(command="npar",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def nlevel(self): # pragma: no cover
        r"""
        CDO operator: nlevel
        """
        operator = CdoOperator(command="nlevel",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def nyear(self): # pragma: no cover
        r"""
        CDO operator: nyear
        """
        operator = CdoOperator(command="nyear",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def nmon(self): # pragma: no cover
        r"""
        CDO operator: nmon
        """
        operator = CdoOperator(command="nmon",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ndate(self): # pragma: no cover
        r"""
        CDO operator: ndate
        """
        operator = CdoOperator(command="ndate",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ntime(self): # pragma: no cover
        r"""
        CDO operator: ntime
        """
        operator = CdoOperator(command="ntime",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ngridpoints(self): # pragma: no cover
        r"""
        CDO operator: ngridpoints
        """
        operator = CdoOperator(command="ngridpoints",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ngrids(self): # pragma: no cover
        r"""
        CDO operator: ngrids
        """
        operator = CdoOperator(command="ngrids",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showformat(self): # pragma: no cover
        r"""
        CDO operator: showformat
        """
        operator = CdoOperator(command="showformat",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showcode(self): # pragma: no cover
        r"""
        CDO operator: showcode
        """
        operator = CdoOperator(command="showcode",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showname(self): # pragma: no cover
        r"""
        CDO operator: showname
        """
        operator = CdoOperator(command="showname",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showstdname(self): # pragma: no cover
        r"""
        CDO operator: showstdname
        """
        operator = CdoOperator(command="showstdname",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showlevel(self): # pragma: no cover
        r"""
        CDO operator: showlevel
        """
        operator = CdoOperator(command="showlevel",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showltype(self): # pragma: no cover
        r"""
        CDO operator: showltype
        """
        operator = CdoOperator(command="showltype",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showyear(self): # pragma: no cover
        r"""
        CDO operator: showyear
        """
        operator = CdoOperator(command="showyear",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showmon(self): # pragma: no cover
        r"""
        CDO operator: showmon
        """
        operator = CdoOperator(command="showmon",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showdate(self): # pragma: no cover
        r"""
        CDO operator: showdate
        """
        operator = CdoOperator(command="showdate",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showtime(self): # pragma: no cover
        r"""
        CDO operator: showtime
        """
        operator = CdoOperator(command="showtime",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showtimestamp(self): # pragma: no cover
        r"""
        CDO operator: showtimestamp
        """
        operator = CdoOperator(command="showtimestamp",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showfilter(self): # pragma: no cover
        r"""
        CDO operator: showfilter
        """
        operator = CdoOperator(command="showfilter",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def showattribute(self, attributes = None): # pragma: no cover
        r"""
        CDO operator: showattribute
        Parameters:
           attributes: STRING - Comma-separated list of attributes.
        """
        operator = CdoOperator(command="showattribute",
                               n_input=1, 
                               n_output=0, 
                               params=['attributes']) 
                               
        return self._new_op(operator, [], {"attributes": attributes})

    def partab(self): # pragma: no cover
        r"""
        CDO operator: partab
        """
        operator = CdoOperator(command="partab",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def codetab(self): # pragma: no cover
        r"""
        CDO operator: codetab
        """
        operator = CdoOperator(command="codetab",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def griddes(self): # pragma: no cover
        r"""
        CDO operator: griddes
        """
        operator = CdoOperator(command="griddes",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def zaxisdes(self): # pragma: no cover
        r"""
        CDO operator: zaxisdes
        """
        operator = CdoOperator(command="zaxisdes",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def vct(self): # pragma: no cover
        r"""
        CDO operator: vct
        """
        operator = CdoOperator(command="vct",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def copy(self): # pragma: no cover
        r"""
        CDO operator: copy
        """
        operator = CdoOperator(command="copy",
                               n_input=inf, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def clone(self): # pragma: no cover
        r"""
        CDO operator: clone
        """
        operator = CdoOperator(command="clone",
                               n_input=inf, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def cat(self): # pragma: no cover
        r"""
        CDO operator: cat
        """
        operator = CdoOperator(command="cat",
                               n_input=inf, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def tee(self, outfile2 = None): # pragma: no cover
        r"""
        CDO operator: tee
        Parameters:
           outfile2: STRING - Destination filename for the copy of the input file
        """
        operator = CdoOperator(command="tee",
                               n_input=1, 
                               n_output=1, 
                               params=['outfile2']) 
                               
        return self._new_op(operator, [], {"outfile2": outfile2})

    def pack(self, printparam = None, filename = None): # pragma: no cover
        r"""
        CDO operator: pack
        Parameters:
           printparam: BOOL - Print pack parameters to stdout for each variable
           filename: STRING - Read pack parameters from file for each variable\[format: name=<> add_offset=<> scale_factor=<>\]
        """
        operator = CdoOperator(command="pack",
                               n_input=1, 
                               n_output=1, 
                               params=['printparam', 'filename']) 
                               
        return self._new_op(operator, [], {"printparam": printparam, "filename": filename})

    def unpack(self): # pragma: no cover
        r"""
        CDO operator: unpack
        """
        operator = CdoOperator(command="unpack",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def setfilter(self, filename = None): # pragma: no cover
        r"""
        CDO operator: setfilter
        Parameters:
           filename: STRING - Read filter specification per variable from file \[format: varname=\"<filterspec>\"\]
        """
        operator = CdoOperator(command="setfilter",
                               n_input=1, 
                               n_output=1, 
                               params=['filename']) 
                               
        return self._new_op(operator, [], {"filename": filename})

    def bitrounding(self, inflevel = None, addbits = None, minbits = None, maxbits = None, numsteps = None, numbits = None, printbits = None, filename = None): # pragma: no cover
        r"""
        CDO operator: bitrounding
        Parameters:
           inflevel: FLOAT - Information level (0 - 1) \[default: 0.9999\]
           addbits: INTEGER - Add bits to the number of significant bits \[default: 0\]
           minbits: INTEGER - Minimum value of the number of bits \[default: 1\]
           maxbits: INTEGER - Maximum value of the number of bits \[default: 23\]
           numsteps: INTEGER - Set to 1 to run the calculation only in the first time step
           numbits: INTEGER - Set number of significant bits
           printbits: BOOL - Print max. numbits per variable of 1st timestep to stdout \[format: name=numbits\]
           filename: STRING - Read number of significant bits per variable from file \[format: name=numbits\]
        """
        operator = CdoOperator(command="bitrounding",
                               n_input=1, 
                               n_output=1, 
                               params=['inflevel', 'addbits', 'minbits', 'maxbits', 'numsteps', 'numbits', 'printbits', 'filename']) 
                               
        return self._new_op(operator, [], {"inflevel": inflevel, "addbits": addbits, "minbits": minbits, "maxbits": maxbits, "numsteps": numsteps, "numbits": numbits, "printbits": printbits, "filename": filename})

    def replace(self, ifile2): # pragma: no cover
        r"""
        CDO operator: replace
        """
        operator = CdoOperator(command="replace",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def duplicate(self, ndup = None): # pragma: no cover
        r"""
        CDO operator: duplicate
        Parameters:
           ndup: INTEGER - Number of duplicates, default is 2.
        """
        operator = CdoOperator(command="duplicate",
                               n_input=1, 
                               n_output=1, 
                               params=['ndup']) 
                               
        return self._new_op(operator, [], {"ndup": ndup})

    def mergegrid(self, ifile2): # pragma: no cover
        r"""
        CDO operator: mergegrid
        """
        operator = CdoOperator(command="mergegrid",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def merge(self, skip_same_time = None, names = None): # pragma: no cover
        r"""
        CDO operator: merge
        Parameters:
           skip_same_time: BOOL - Skips all consecutive timesteps with a double entry of the same timestamp.
           names: STRING - Fill missing variable names with missing values (union) or use the intersection (intersect).
        """
        operator = CdoOperator(command="merge",
                               n_input=inf, 
                               n_output=1, 
                               params=['skip_same_time', 'names']) 
                               
        return self._new_op(operator, [], {"skip_same_time": skip_same_time, "names": names})

    def mergetime(self, skip_same_time = None, names = None): # pragma: no cover
        r"""
        CDO operator: mergetime
        Parameters:
           skip_same_time: BOOL - Skips all consecutive timesteps with a double entry of the same timestamp.
           names: STRING - Fill missing variable names with missing values (union) or use the intersection (intersect).
        """
        operator = CdoOperator(command="mergetime",
                               n_input=inf, 
                               n_output=1, 
                               params=['skip_same_time', 'names']) 
                               
        return self._new_op(operator, [], {"skip_same_time": skip_same_time, "names": names})

    def splitcode(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splitcode
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splitcode",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splitparam(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splitparam
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splitparam",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splitname(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splitname
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splitname",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splitlevel(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splitlevel
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splitlevel",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splitgrid(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splitgrid
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splitgrid",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splitzaxis(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splitzaxis
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splitzaxis",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splittabnum(self, swap = None, uuid = None): # pragma: no cover
        r"""
        CDO operator: splittabnum
        Parameters:
           swap: STRING - Swap the position of obase and xxx in the output filename
           uuid: STRING - Add a UUID as global attribute <attname> to each output file
        """
        operator = CdoOperator(command="splittabnum",
                               n_input=1, 
                               n_output=inf, 
                               params=['swap', 'uuid']) 
                               
        return self._new_op(operator, [], {"swap": swap, "uuid": uuid})

    def splithour(self, format = None): # pragma: no cover
        r"""
        CDO operator: splithour
        Parameters:
           format: STRING - C-style format for strftime() (e.g. %B for the full month name)
        """
        operator = CdoOperator(command="splithour",
                               n_input=1, 
                               n_output=inf, 
                               params=['format']) 
                               
        return self._new_op(operator, [], {"format": format})

    def splitday(self, format = None): # pragma: no cover
        r"""
        CDO operator: splitday
        Parameters:
           format: STRING - C-style format for strftime() (e.g. %B for the full month name)
        """
        operator = CdoOperator(command="splitday",
                               n_input=1, 
                               n_output=inf, 
                               params=['format']) 
                               
        return self._new_op(operator, [], {"format": format})

    def splitseas(self, format = None): # pragma: no cover
        r"""
        CDO operator: splitseas
        Parameters:
           format: STRING - C-style format for strftime() (e.g. %B for the full month name)
        """
        operator = CdoOperator(command="splitseas",
                               n_input=1, 
                               n_output=inf, 
                               params=['format']) 
                               
        return self._new_op(operator, [], {"format": format})

    def splityear(self, format = None): # pragma: no cover
        r"""
        CDO operator: splityear
        Parameters:
           format: STRING - C-style format for strftime() (e.g. %B for the full month name)
        """
        operator = CdoOperator(command="splityear",
                               n_input=1, 
                               n_output=inf, 
                               params=['format']) 
                               
        return self._new_op(operator, [], {"format": format})

    def splityearmon(self, format = None): # pragma: no cover
        r"""
        CDO operator: splityearmon
        Parameters:
           format: STRING - C-style format for strftime() (e.g. %B for the full month name)
        """
        operator = CdoOperator(command="splityearmon",
                               n_input=1, 
                               n_output=inf, 
                               params=['format']) 
                               
        return self._new_op(operator, [], {"format": format})

    def splitmon(self, format = None): # pragma: no cover
        r"""
        CDO operator: splitmon
        Parameters:
           format: STRING - C-style format for strftime() (e.g. %B for the full month name)
        """
        operator = CdoOperator(command="splitmon",
                               n_input=1, 
                               n_output=inf, 
                               params=['format']) 
                               
        return self._new_op(operator, [], {"format": format})

    def splitsel(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: splitsel
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output file
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="splitsel",
                               n_input=1, 
                               n_output=inf, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def splitdate(self): # pragma: no cover
        r"""
        CDO operator: splitdate
        """
        operator = CdoOperator(command="splitdate",
                               n_input=1, 
                               n_output=inf, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def distgrid(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: distgrid
        Parameters:
           nx: INTEGER - Number of regions in x direction, or number of pieces for unstructured grids
           ny: INTEGER - Number of regions in y direction \[default: 1\]
        """
        operator = CdoOperator(command="distgrid",
                               n_input=1, 
                               n_output=inf, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def collgrid(self, nx = None, names = None): # pragma: no cover
        r"""
        CDO operator: collgrid
        Parameters:
           nx: INTEGER - Number of regions in x direction \[default: number of input files\]
           names: STRING - Comma-separated list of variable names \[default: all variables\]
        """
        operator = CdoOperator(command="collgrid",
                               n_input=inf, 
                               n_output=1, 
                               params=['nx', 'names']) 
                               
        return self._new_op(operator, [], {"nx": nx, "names": names})

    def select(self, name = None, param = None, code = None, level = None, levrange = None, levidx = None, zaxisname = None, zaxisnum = None, ltype = None, gridname = None, gridnum = None, steptype = None, date = None, startdate = None, enddate = None, minute = None, hour = None, day = None, month = None, season = None, year = None, dom = None, timestep = None, timestep_of_year = None, timestepmask = None): # pragma: no cover
        r"""
        CDO operator: select
        Parameters:
           name: STRING - Comma-separated list of variable names.
           param: STRING - Comma-separated list of parameter identifiers.
           code: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           level: FLOAT - Comma-separated list of vertical levels.
           levrange: FLOAT - First and last value of the level range.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           zaxisname: STRING - Comma-separated list of zaxis names.
           zaxisnum: INTEGER - Comma-separated list or first/last\[/inc\] range of zaxis numbers.
           ltype: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           gridname: STRING - Comma-separated list of grid names.
           gridnum: INTEGER - Comma-separated list or first/last\[/inc\] range of grid numbers.
           steptype: STRING - Comma-separated list of timestep types (constant|avg|accum|min|max|range|diff|sum)
           date: STRING - Comma-separated list of dates (format: YYYY-MM-DDThh:mm:ss).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss).
           minute: INTEGER - Comma-separated list or first/last\[/inc\] range of minutes.
           hour: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           day: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           month: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           season: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           year: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           dom: STRING - Comma-separated list of the day of month (e.g. 29feb).
           timestep: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           timestep_of_year: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps of year.
           timestepmask: STRING - Read timesteps from a mask file.
        """
        operator = CdoOperator(command="select",
                               n_input=inf, 
                               n_output=1, 
                               params=['name', 'param', 'code', 'level', 'levrange', 'levidx', 'zaxisname', 'zaxisnum', 'ltype', 'gridname', 'gridnum', 'steptype', 'date', 'startdate', 'enddate', 'minute', 'hour', 'day', 'month', 'season', 'year', 'dom', 'timestep', 'timestep_of_year', 'timestepmask']) 
                               
        return self._new_op(operator, [], {"name": name, "param": param, "code": code, "level": level, "levrange": levrange, "levidx": levidx, "zaxisname": zaxisname, "zaxisnum": zaxisnum, "ltype": ltype, "gridname": gridname, "gridnum": gridnum, "steptype": steptype, "date": date, "startdate": startdate, "enddate": enddate, "minute": minute, "hour": hour, "day": day, "month": month, "season": season, "year": year, "dom": dom, "timestep": timestep, "timestep_of_year": timestep_of_year, "timestepmask": timestepmask})

    def delete(self, name = None, param = None, code = None, level = None, levrange = None, levidx = None, zaxisname = None, zaxisnum = None, ltype = None, gridname = None, gridnum = None, steptype = None, date = None, startdate = None, enddate = None, minute = None, hour = None, day = None, month = None, season = None, year = None, dom = None, timestep = None, timestep_of_year = None, timestepmask = None): # pragma: no cover
        r"""
        CDO operator: delete
        Parameters:
           name: STRING - Comma-separated list of variable names.
           param: STRING - Comma-separated list of parameter identifiers.
           code: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           level: FLOAT - Comma-separated list of vertical levels.
           levrange: FLOAT - First and last value of the level range.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           zaxisname: STRING - Comma-separated list of zaxis names.
           zaxisnum: INTEGER - Comma-separated list or first/last\[/inc\] range of zaxis numbers.
           ltype: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           gridname: STRING - Comma-separated list of grid names.
           gridnum: INTEGER - Comma-separated list or first/last\[/inc\] range of grid numbers.
           steptype: STRING - Comma-separated list of timestep types (constant|avg|accum|min|max|range|diff|sum)
           date: STRING - Comma-separated list of dates (format: YYYY-MM-DDThh:mm:ss).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss).
           minute: INTEGER - Comma-separated list or first/last\[/inc\] range of minutes.
           hour: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           day: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           month: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           season: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           year: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           dom: STRING - Comma-separated list of the day of month (e.g. 29feb).
           timestep: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           timestep_of_year: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps of year.
           timestepmask: STRING - Read timesteps from a mask file.
        """
        operator = CdoOperator(command="delete",
                               n_input=inf, 
                               n_output=1, 
                               params=['name', 'param', 'code', 'level', 'levrange', 'levidx', 'zaxisname', 'zaxisnum', 'ltype', 'gridname', 'gridnum', 'steptype', 'date', 'startdate', 'enddate', 'minute', 'hour', 'day', 'month', 'season', 'year', 'dom', 'timestep', 'timestep_of_year', 'timestepmask']) 
                               
        return self._new_op(operator, [], {"name": name, "param": param, "code": code, "level": level, "levrange": levrange, "levidx": levidx, "zaxisname": zaxisname, "zaxisnum": zaxisnum, "ltype": ltype, "gridname": gridname, "gridnum": gridnum, "steptype": steptype, "date": date, "startdate": startdate, "enddate": enddate, "minute": minute, "hour": hour, "day": day, "month": month, "season": season, "year": year, "dom": dom, "timestep": timestep, "timestep_of_year": timestep_of_year, "timestepmask": timestepmask})

    def selmulti(self): # pragma: no cover
        r"""
        CDO operator: selmulti
        """
        operator = CdoOperator(command="selmulti",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def delmulti(self): # pragma: no cover
        r"""
        CDO operator: delmulti
        """
        operator = CdoOperator(command="delmulti",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def changemulti(self): # pragma: no cover
        r"""
        CDO operator: changemulti
        """
        operator = CdoOperator(command="changemulti",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def selparam(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selparam
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selparam",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def delparam(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: delparam
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="delparam",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selcode(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selcode
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selcode",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def delcode(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: delcode
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="delcode",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selname(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selname
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selname",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def delname(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: delname
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="delname",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selstdname(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selstdname
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selstdname",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def sellevel(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: sellevel
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="sellevel",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def sellevidx(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: sellevidx
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="sellevidx",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selgrid(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selgrid
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selgrid",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selzaxis(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selzaxis
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selzaxis",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selzaxisname(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selzaxisname
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selzaxisname",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def selltype(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: selltype
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="selltype",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def seltabnum(self, parameter = None, codes = None, names = None, stdnames = None, levels = None, levidx = None, ltypes = None, grids = None, zaxes = None, zaxisnames = None, tabnums = None): # pragma: no cover
        r"""
        CDO operator: seltabnum
        Parameters:
           parameter: STRING - Comma-separated list of parameter identifiers.
           codes: INTEGER - Comma-separated list or first/last\[/inc\] range of code numbers.
           names: STRING - Comma-separated list of variable names.
           stdnames: STRING - Comma-separated list of standard names.
           levels: FLOAT - Comma-separated list of vertical levels.
           levidx: INTEGER - Comma-separated list or first/last\[/inc\] range of index of levels.
           ltypes: INTEGER - Comma-separated list or first/last\[/inc\] range of GRIB level types.
           grids: STRING - Comma-separated list of grid names or numbers.
           zaxes: STRING - Comma-separated list of z-axis types or numbers.
           zaxisnames: STRING - Comma-separated list of z-axis names.
           tabnums: INTEGER - Comma-separated list or range of parameter table numbers.
        """
        operator = CdoOperator(command="seltabnum",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter', 'codes', 'names', 'stdnames', 'levels', 'levidx', 'ltypes', 'grids', 'zaxes', 'zaxisnames', 'tabnums']) 
                               
        return self._new_op(operator, [], {"parameter": parameter, "codes": codes, "names": names, "stdnames": stdnames, "levels": levels, "levidx": levidx, "ltypes": ltypes, "grids": grids, "zaxes": zaxes, "zaxisnames": zaxisnames, "tabnums": tabnums})

    def seltimestep(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: seltimestep
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="seltimestep",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def seltime(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: seltime
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="seltime",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def selhour(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: selhour
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="selhour",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def selday(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: selday
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="selday",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def selmonth(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: selmonth
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="selmonth",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def selyear(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: selyear
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="selyear",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def selseason(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: selseason
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="selseason",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def seldate(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: seldate
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="seldate",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def selsmon(self, timesteps = None, times = None, hours = None, days = None, months = None, years = None, seasons = None, startdate = None, enddate = None, nts1 = None, nts2 = None): # pragma: no cover
        r"""
        CDO operator: selsmon
        Parameters:
           timesteps: INTEGER - Comma-separated list or first/last\[/inc\] range of timesteps. Negative values select timesteps from the end (NetCDF only).
           times: STRING - Comma-separated list of times (format hh:mm:ss).
           hours: INTEGER - Comma-separated list or first/last\[/inc\] range of hours.
           days: INTEGER - Comma-separated list or first/last\[/inc\] range of days.
           months: INTEGER - Comma-separated list or first/last\[/inc\] range of months.
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years.
           seasons: STRING - Comma-separated list of seasons (substring of DJFMAMJJASOND or ANN).
           startdate: STRING - Start date (format: YYYY-MM-DDThh:mm:ss).
           enddate: STRING - End date (format: YYYY-MM-DDThh:mm:ss) \[default: startdate\].
           nts1: INTEGER - Number of timesteps before the selected month \[default: 0\].
           nts2: INTEGER - Number of timesteps after the selected month \[default: nts1\].
        """
        operator = CdoOperator(command="selsmon",
                               n_input=1, 
                               n_output=1, 
                               params=['timesteps', 'times', 'hours', 'days', 'months', 'years', 'seasons', 'startdate', 'enddate', 'nts1', 'nts2']) 
                               
        return self._new_op(operator, [], {"timesteps": timesteps, "times": times, "hours": hours, "days": days, "months": months, "years": years, "seasons": seasons, "startdate": startdate, "enddate": enddate, "nts1": nts1, "nts2": nts2})

    def sellonlatbox(self, lon1 = None, lon2 = None, lat1 = None, lat2 = None, idx1 = None, idx2 = None, idy1 = None, idy2 = None): # pragma: no cover
        r"""
        CDO operator: sellonlatbox
        Parameters:
           lon1: FLOAT - Western longitude in degrees
           lon2: FLOAT - Eastern longitude in degrees
           lat1: FLOAT - Southern or northern latitude in degrees
           lat2: FLOAT - Northern or southern latitude in degrees
           idx1: INTEGER - Index of first longitude (1 - nlon)
           idx2: INTEGER - Index of last longitude (1 - nlon)
           idy1: INTEGER - Index of first latitude (1 - nlat)
           idy2: INTEGER - Index of last latitude (1 - nlat)
        """
        operator = CdoOperator(command="sellonlatbox",
                               n_input=1, 
                               n_output=1, 
                               params=['lon1', 'lon2', 'lat1', 'lat2', 'idx1', 'idx2', 'idy1', 'idy2']) 
                               
        return self._new_op(operator, [], {"lon1": lon1, "lon2": lon2, "lat1": lat1, "lat2": lat2, "idx1": idx1, "idx2": idx2, "idy1": idy1, "idy2": idy2})

    def selindexbox(self, lon1 = None, lon2 = None, lat1 = None, lat2 = None, idx1 = None, idx2 = None, idy1 = None, idy2 = None): # pragma: no cover
        r"""
        CDO operator: selindexbox
        Parameters:
           lon1: FLOAT - Western longitude in degrees
           lon2: FLOAT - Eastern longitude in degrees
           lat1: FLOAT - Southern or northern latitude in degrees
           lat2: FLOAT - Northern or southern latitude in degrees
           idx1: INTEGER - Index of first longitude (1 - nlon)
           idx2: INTEGER - Index of last longitude (1 - nlon)
           idy1: INTEGER - Index of first latitude (1 - nlat)
           idy2: INTEGER - Index of last latitude (1 - nlat)
        """
        operator = CdoOperator(command="selindexbox",
                               n_input=1, 
                               n_output=1, 
                               params=['lon1', 'lon2', 'lat1', 'lat2', 'idx1', 'idx2', 'idy1', 'idy2']) 
                               
        return self._new_op(operator, [], {"lon1": lon1, "lon2": lon2, "lat1": lat1, "lat2": lat2, "idx1": idx1, "idx2": idx2, "idy1": idy1, "idy2": idy2})

    def selregion(self, regions = None, lon = None, lat = None, radius = None): # pragma: no cover
        r"""
        CDO operator: selregion
        Parameters:
           regions: STRING - Comma-separated list of ASCII formatted files with different regions
           lon: FLOAT - Longitude of the center of the circle in degrees, default lon=0.0
           lat: FLOAT - Latitude of the center of the circle in degrees, default lat=0.0
           radius: STRING - Radius of the circle, default radius=1deg (units: deg, rad, km, m)
        """
        operator = CdoOperator(command="selregion",
                               n_input=1, 
                               n_output=1, 
                               params=['regions', 'lon', 'lat', 'radius']) 
                               
        return self._new_op(operator, [], {"regions": regions, "lon": lon, "lat": lat, "radius": radius})

    def selcircle(self, regions = None, lon = None, lat = None, radius = None): # pragma: no cover
        r"""
        CDO operator: selcircle
        Parameters:
           regions: STRING - Comma-separated list of ASCII formatted files with different regions
           lon: FLOAT - Longitude of the center of the circle in degrees, default lon=0.0
           lat: FLOAT - Latitude of the center of the circle in degrees, default lat=0.0
           radius: STRING - Radius of the circle, default radius=1deg (units: deg, rad, km, m)
        """
        operator = CdoOperator(command="selcircle",
                               n_input=1, 
                               n_output=1, 
                               params=['regions', 'lon', 'lat', 'radius']) 
                               
        return self._new_op(operator, [], {"regions": regions, "lon": lon, "lat": lat, "radius": radius})

    def selgridcell(self, indices = None): # pragma: no cover
        r"""
        CDO operator: selgridcell
        Parameters:
           indices: INTEGER - Comma-separated list or first/last\[/inc\] range of indices
        """
        operator = CdoOperator(command="selgridcell",
                               n_input=1, 
                               n_output=1, 
                               params=['indices']) 
                               
        return self._new_op(operator, [], {"indices": indices})

    def delgridcell(self, indices = None): # pragma: no cover
        r"""
        CDO operator: delgridcell
        Parameters:
           indices: INTEGER - Comma-separated list or first/last\[/inc\] range of indices
        """
        operator = CdoOperator(command="delgridcell",
                               n_input=1, 
                               n_output=1, 
                               params=['indices']) 
                               
        return self._new_op(operator, [], {"indices": indices})

    def samplegrid(self, factor = None): # pragma: no cover
        r"""
        CDO operator: samplegrid
        Parameters:
           factor: INTEGER - Resample factor, typically 2, which will half the resolution
        """
        operator = CdoOperator(command="samplegrid",
                               n_input=1, 
                               n_output=1, 
                               params=['factor']) 
                               
        return self._new_op(operator, [], {"factor": factor})

    def selyearidx(self, ifile2): # pragma: no cover
        r"""
        CDO operator: selyearidx
        """
        operator = CdoOperator(command="selyearidx",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def seltimeidx(self, ifile2): # pragma: no cover
        r"""
        CDO operator: seltimeidx
        """
        operator = CdoOperator(command="seltimeidx",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def bottomvalue(self, isovalue = None): # pragma: no cover
        r"""
        CDO operator: bottomvalue
        Parameters:
           isovalue: FLOAT - Isosurface value
        """
        operator = CdoOperator(command="bottomvalue",
                               n_input=1, 
                               n_output=1, 
                               params=['isovalue']) 
                               
        return self._new_op(operator, [], {"isovalue": isovalue})

    def topvalue(self, isovalue = None): # pragma: no cover
        r"""
        CDO operator: topvalue
        Parameters:
           isovalue: FLOAT - Isosurface value
        """
        operator = CdoOperator(command="topvalue",
                               n_input=1, 
                               n_output=1, 
                               params=['isovalue']) 
                               
        return self._new_op(operator, [], {"isovalue": isovalue})

    def isosurface(self, isovalue = None): # pragma: no cover
        r"""
        CDO operator: isosurface
        Parameters:
           isovalue: FLOAT - Isosurface value
        """
        operator = CdoOperator(command="isosurface",
                               n_input=1, 
                               n_output=1, 
                               params=['isovalue']) 
                               
        return self._new_op(operator, [], {"isovalue": isovalue})

    def ifthen(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ifthen
        """
        operator = CdoOperator(command="ifthen",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ifnotthen(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ifnotthen
        """
        operator = CdoOperator(command="ifnotthen",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ifthenelse(self, ifile2, ifile3): # pragma: no cover
        r"""
        CDO operator: ifthenelse
        """
        operator = CdoOperator(command="ifthenelse",
                               n_input=3, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2, ifile3], {})

    def ifthenc(self, c = None): # pragma: no cover
        r"""
        CDO operator: ifthenc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="ifthenc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def ifnotthenc(self, c = None): # pragma: no cover
        r"""
        CDO operator: ifnotthenc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="ifnotthenc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def reducegrid(self, mask = None, limitCoordsOutput = None): # pragma: no cover
        r"""
        CDO operator: reducegrid
        Parameters:
           mask: STRING - file which holds the mask field
           limitCoordsOutput: STRING - optional parameter to limit coordinates output: 'nobounds' disables coordinate bounds, 'nocoords' avoids all coordinate information
        """
        operator = CdoOperator(command="reducegrid",
                               n_input=1, 
                               n_output=1, 
                               params=['mask', 'limitCoordsOutput']) 
                               
        return self._new_op(operator, [], {"mask": mask, "limitCoordsOutput": limitCoordsOutput})

    def eq(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eq
        """
        operator = CdoOperator(command="eq",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ne(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ne
        """
        operator = CdoOperator(command="ne",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def le(self, ifile2): # pragma: no cover
        r"""
        CDO operator: le
        """
        operator = CdoOperator(command="le",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def lt(self, ifile2): # pragma: no cover
        r"""
        CDO operator: lt
        """
        operator = CdoOperator(command="lt",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ge(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ge
        """
        operator = CdoOperator(command="ge",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def gt(self, ifile2): # pragma: no cover
        r"""
        CDO operator: gt
        """
        operator = CdoOperator(command="gt",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eqc(self, c = None): # pragma: no cover
        r"""
        CDO operator: eqc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="eqc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def nec(self, c = None): # pragma: no cover
        r"""
        CDO operator: nec
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="nec",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def lec(self, c = None): # pragma: no cover
        r"""
        CDO operator: lec
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="lec",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def ltc(self, c = None): # pragma: no cover
        r"""
        CDO operator: ltc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="ltc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def gec(self, c = None): # pragma: no cover
        r"""
        CDO operator: gec
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="gec",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def gtc(self, c = None): # pragma: no cover
        r"""
        CDO operator: gtc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="gtc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def ymoneq(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymoneq
        """
        operator = CdoOperator(command="ymoneq",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonne(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonne
        """
        operator = CdoOperator(command="ymonne",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonle(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonle
        """
        operator = CdoOperator(command="ymonle",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonlt(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonlt
        """
        operator = CdoOperator(command="ymonlt",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonge(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonge
        """
        operator = CdoOperator(command="ymonge",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymongt(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymongt
        """
        operator = CdoOperator(command="ymongt",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def setattribute(self, attributes = None): # pragma: no cover
        r"""
        CDO operator: setattribute
        Parameters:
           attributes: STRING - Comma-separated list of attributes.
        """
        operator = CdoOperator(command="setattribute",
                               n_input=1, 
                               n_output=1, 
                               params=['attributes']) 
                               
        return self._new_op(operator, [], {"attributes": attributes})

    def delattribute(self, attributes = None): # pragma: no cover
        r"""
        CDO operator: delattribute
        Parameters:
           attributes: STRING - Comma-separated list of attributes.
        """
        operator = CdoOperator(command="delattribute",
                               n_input=1, 
                               n_output=1, 
                               params=['attributes']) 
                               
        return self._new_op(operator, [], {"attributes": attributes})

    def setpartabp(self, table = None, convert = None): # pragma: no cover
        r"""
        CDO operator: setpartabp
        Parameters:
           table: STRING - Parameter table file or name
           convert: STRING - Converts the units if necessary
        """
        operator = CdoOperator(command="setpartabp",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'convert']) 
                               
        return self._new_op(operator, [], {"table": table, "convert": convert})

    def setpartabn(self, table = None, convert = None): # pragma: no cover
        r"""
        CDO operator: setpartabn
        Parameters:
           table: STRING - Parameter table file or name
           convert: STRING - Converts the units if necessary
        """
        operator = CdoOperator(command="setpartabn",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'convert']) 
                               
        return self._new_op(operator, [], {"table": table, "convert": convert})

    def setcodetab(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setcodetab
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setcodetab",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setcode(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setcode
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setcode",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setparam(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setparam
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setparam",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setname(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setname
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setname",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setunit(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setunit
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setunit",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setlevel(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setlevel
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setlevel",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setltype(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setltype
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setltype",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setmaxsteps(self, table = None, code = None, param = None, name = None, level = None, ltype = None, maxsteps = None): # pragma: no cover
        r"""
        CDO operator: setmaxsteps
        Parameters:
           table: STRING - Parameter table file or name
           code: INTEGER - Code number
           param: STRING - Parameter identifier (GRIB1: code\[.tabnum\]; GRIB2: num\[.cat\[.dis\]\])
           name: STRING - Variable name
           level: FLOAT - New level
           ltype: INTEGER - GRIB level type
           maxsteps: INTEGER - Maximum number of timesteps
        """
        operator = CdoOperator(command="setmaxsteps",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'code', 'param', 'name', 'level', 'ltype', 'maxsteps']) 
                               
        return self._new_op(operator, [], {"table": table, "code": code, "param": param, "name": name, "level": level, "ltype": ltype, "maxsteps": maxsteps})

    def setdate(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: setdate
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="setdate",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def settime(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: settime
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="settime",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def setday(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: setday
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="setday",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def setmon(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: setmon
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="setmon",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def setyear(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: setyear
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="setyear",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def settunits(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: settunits
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="settunits",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def settaxis(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: settaxis
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="settaxis",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def settbounds(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: settbounds
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="settbounds",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def setreftime(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: setreftime
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="setreftime",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def setcalendar(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: setcalendar
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="setcalendar",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def shifttime(self, day = None, month = None, year = None, units = None, date = None, time = None, inc = None, frequency = None, calendar = None, shiftValue = None): # pragma: no cover
        r"""
        CDO operator: shifttime
        Parameters:
           day: INTEGER - Value of the new day
           month: INTEGER - Value of the new month
           year: INTEGER - Value of the new year
           units: STRING - Base units of the time axis (seconds|minutes|hours|days|months|years)
           date: STRING - Date (format: YYYY-MM-DD)
           time: STRING - Time (format: hh:mm:ss)
           inc: STRING - Optional increment (seconds|minutes|hours|days|months|years) \[default: 1hour\]
           frequency: STRING - Frequency of the time series (hour|day|month|year)
           calendar: STRING - Calendar (standard|proleptic_gregorian|360_day|365_day|366_day)
           shiftValue: STRING - Shift value (e.g. -3hour)
        """
        operator = CdoOperator(command="shifttime",
                               n_input=1, 
                               n_output=1, 
                               params=['day', 'month', 'year', 'units', 'date', 'time', 'inc', 'frequency', 'calendar', 'shiftValue']) 
                               
        return self._new_op(operator, [], {"day": day, "month": month, "year": year, "units": units, "date": date, "time": time, "inc": inc, "frequency": frequency, "calendar": calendar, "shiftValue": shiftValue})

    def chcode(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chcode
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chcode",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def chparam(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chparam
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chparam",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def chname(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chname
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chname",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def chunit(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chunit
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chunit",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def chlevel(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chlevel
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chlevel",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def chlevelc(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chlevelc
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chlevelc",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def chlevelv(self, code = None, oldcode = None, newcode = None, oldparam = None, newparam = None, name = None, oldname = None, newname = None, oldlev = None, newlev = None): # pragma: no cover
        r"""
        CDO operator: chlevelv
        Parameters:
           code: INTEGER - Code number
           oldcode: INTEGER - Pairs of old and new code numbers
           newcode: INTEGER - Pairs of old and new code numbers
           oldparam: STRING - Pairs of old and new parameter identifiers
           newparam: STRING - Pairs of old and new parameter identifiers
           name: STRING - Variable name
           oldname: STRING - Pairs of old and new variable names
           newname: STRING - Pairs of old and new variable names
           oldlev: FLOAT - Old level
           newlev: FLOAT - New level
        """
        operator = CdoOperator(command="chlevelv",
                               n_input=1, 
                               n_output=1, 
                               params=['code', 'oldcode', 'newcode', 'oldparam', 'newparam', 'name', 'oldname', 'newname', 'oldlev', 'newlev']) 
                               
        return self._new_op(operator, [], {"code": code, "oldcode": oldcode, "newcode": newcode, "oldparam": oldparam, "newparam": newparam, "name": name, "oldname": oldname, "newname": newname, "oldlev": oldlev, "newlev": newlev})

    def setgrid(self, grid = None, gridtype = None, gridarea = None, gridmask = None, projparams = None): # pragma: no cover
        r"""
        CDO operator: setgrid
        Parameters:
           grid: STRING - Grid description file or name
           gridtype: STRING - Grid type (curvilinear, unstructured, regular, lonlat, projection or dereference)
           gridarea: STRING - Data file, the first field is used as grid cell area
           gridmask: STRING - Data file, the first field is used as grid mask
           projparams: STRING - Proj library parameter (e.g.:+init=EPSG:3413)
        """
        operator = CdoOperator(command="setgrid",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'gridtype', 'gridarea', 'gridmask', 'projparams']) 
                               
        return self._new_op(operator, [], {"grid": grid, "gridtype": gridtype, "gridarea": gridarea, "gridmask": gridmask, "projparams": projparams})

    def setgridtype(self, grid = None, gridtype = None, gridarea = None, gridmask = None, projparams = None): # pragma: no cover
        r"""
        CDO operator: setgridtype
        Parameters:
           grid: STRING - Grid description file or name
           gridtype: STRING - Grid type (curvilinear, unstructured, regular, lonlat, projection or dereference)
           gridarea: STRING - Data file, the first field is used as grid cell area
           gridmask: STRING - Data file, the first field is used as grid mask
           projparams: STRING - Proj library parameter (e.g.:+init=EPSG:3413)
        """
        operator = CdoOperator(command="setgridtype",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'gridtype', 'gridarea', 'gridmask', 'projparams']) 
                               
        return self._new_op(operator, [], {"grid": grid, "gridtype": gridtype, "gridarea": gridarea, "gridmask": gridmask, "projparams": projparams})

    def setgridarea(self, grid = None, gridtype = None, gridarea = None, gridmask = None, projparams = None): # pragma: no cover
        r"""
        CDO operator: setgridarea
        Parameters:
           grid: STRING - Grid description file or name
           gridtype: STRING - Grid type (curvilinear, unstructured, regular, lonlat, projection or dereference)
           gridarea: STRING - Data file, the first field is used as grid cell area
           gridmask: STRING - Data file, the first field is used as grid mask
           projparams: STRING - Proj library parameter (e.g.:+init=EPSG:3413)
        """
        operator = CdoOperator(command="setgridarea",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'gridtype', 'gridarea', 'gridmask', 'projparams']) 
                               
        return self._new_op(operator, [], {"grid": grid, "gridtype": gridtype, "gridarea": gridarea, "gridmask": gridmask, "projparams": projparams})

    def setgridmask(self, grid = None, gridtype = None, gridarea = None, gridmask = None, projparams = None): # pragma: no cover
        r"""
        CDO operator: setgridmask
        Parameters:
           grid: STRING - Grid description file or name
           gridtype: STRING - Grid type (curvilinear, unstructured, regular, lonlat, projection or dereference)
           gridarea: STRING - Data file, the first field is used as grid cell area
           gridmask: STRING - Data file, the first field is used as grid mask
           projparams: STRING - Proj library parameter (e.g.:+init=EPSG:3413)
        """
        operator = CdoOperator(command="setgridmask",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'gridtype', 'gridarea', 'gridmask', 'projparams']) 
                               
        return self._new_op(operator, [], {"grid": grid, "gridtype": gridtype, "gridarea": gridarea, "gridmask": gridmask, "projparams": projparams})

    def setprojparams(self, grid = None, gridtype = None, gridarea = None, gridmask = None, projparams = None): # pragma: no cover
        r"""
        CDO operator: setprojparams
        Parameters:
           grid: STRING - Grid description file or name
           gridtype: STRING - Grid type (curvilinear, unstructured, regular, lonlat, projection or dereference)
           gridarea: STRING - Data file, the first field is used as grid cell area
           gridmask: STRING - Data file, the first field is used as grid mask
           projparams: STRING - Proj library parameter (e.g.:+init=EPSG:3413)
        """
        operator = CdoOperator(command="setprojparams",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'gridtype', 'gridarea', 'gridmask', 'projparams']) 
                               
        return self._new_op(operator, [], {"grid": grid, "gridtype": gridtype, "gridarea": gridarea, "gridmask": gridmask, "projparams": projparams})

    def setzaxis(self, zaxis = None, zbot = None, ztop = None): # pragma: no cover
        r"""
        CDO operator: setzaxis
        Parameters:
           zaxis: STRING - Z-axis description file or name of the target z-axis
           zbot: FLOAT - Specifying the bottom of the vertical column. Must have the same units as z-axis.
           ztop: FLOAT - Specifying the top of the vertical column. Must have the same units as z-axis.
        """
        operator = CdoOperator(command="setzaxis",
                               n_input=1, 
                               n_output=1, 
                               params=['zaxis', 'zbot', 'ztop']) 
                               
        return self._new_op(operator, [], {"zaxis": zaxis, "zbot": zbot, "ztop": ztop})

    def genlevelbounds(self, zaxis = None, zbot = None, ztop = None): # pragma: no cover
        r"""
        CDO operator: genlevelbounds
        Parameters:
           zaxis: STRING - Z-axis description file or name of the target z-axis
           zbot: FLOAT - Specifying the bottom of the vertical column. Must have the same units as z-axis.
           ztop: FLOAT - Specifying the top of the vertical column. Must have the same units as z-axis.
        """
        operator = CdoOperator(command="genlevelbounds",
                               n_input=1, 
                               n_output=1, 
                               params=['zaxis', 'zbot', 'ztop']) 
                               
        return self._new_op(operator, [], {"zaxis": zaxis, "zbot": zbot, "ztop": ztop})

    def invertlat(self): # pragma: no cover
        r"""
        CDO operator: invertlat
        """
        operator = CdoOperator(command="invertlat",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def invertlev(self): # pragma: no cover
        r"""
        CDO operator: invertlev
        """
        operator = CdoOperator(command="invertlev",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def shiftx(self, nshift = None, cyclic = None, coord = None): # pragma: no cover
        r"""
        CDO operator: shiftx
        Parameters:
           nshift: INTEGER - Number of grid cells to shift (default: 1)
           cyclic: STRING - If set, cells are filled up cyclic (default: missing value)
           coord: STRING - If set, coordinates are also shifted
        """
        operator = CdoOperator(command="shiftx",
                               n_input=1, 
                               n_output=1, 
                               params=['nshift', 'cyclic', 'coord']) 
                               
        return self._new_op(operator, [], {"nshift": nshift, "cyclic": cyclic, "coord": coord})

    def shifty(self, nshift = None, cyclic = None, coord = None): # pragma: no cover
        r"""
        CDO operator: shifty
        Parameters:
           nshift: INTEGER - Number of grid cells to shift (default: 1)
           cyclic: STRING - If set, cells are filled up cyclic (default: missing value)
           coord: STRING - If set, coordinates are also shifted
        """
        operator = CdoOperator(command="shifty",
                               n_input=1, 
                               n_output=1, 
                               params=['nshift', 'cyclic', 'coord']) 
                               
        return self._new_op(operator, [], {"nshift": nshift, "cyclic": cyclic, "coord": coord})

    def maskregion(self, regions = None): # pragma: no cover
        r"""
        CDO operator: maskregion
        Parameters:
           regions: STRING - Comma-separated list of ASCII formatted files with different regions
        """
        operator = CdoOperator(command="maskregion",
                               n_input=1, 
                               n_output=1, 
                               params=['regions']) 
                               
        return self._new_op(operator, [], {"regions": regions})

    def masklonlatbox(self, lon1 = None, lon2 = None, lat1 = None, lat2 = None, idx1 = None, idx2 = None, idy1 = None, idy2 = None): # pragma: no cover
        r"""
        CDO operator: masklonlatbox
        Parameters:
           lon1: FLOAT - Western longitude
           lon2: FLOAT - Eastern longitude
           lat1: FLOAT - Southern or northern latitude
           lat2: FLOAT - Northern or southern latitude
           idx1: INTEGER - Index of first longitude
           idx2: INTEGER - Index of last longitude
           idy1: INTEGER - Index of first latitude
           idy2: INTEGER - Index of last latitude
        """
        operator = CdoOperator(command="masklonlatbox",
                               n_input=1, 
                               n_output=1, 
                               params=['lon1', 'lon2', 'lat1', 'lat2', 'idx1', 'idx2', 'idy1', 'idy2']) 
                               
        return self._new_op(operator, [], {"lon1": lon1, "lon2": lon2, "lat1": lat1, "lat2": lat2, "idx1": idx1, "idx2": idx2, "idy1": idy1, "idy2": idy2})

    def maskindexbox(self, lon1 = None, lon2 = None, lat1 = None, lat2 = None, idx1 = None, idx2 = None, idy1 = None, idy2 = None): # pragma: no cover
        r"""
        CDO operator: maskindexbox
        Parameters:
           lon1: FLOAT - Western longitude
           lon2: FLOAT - Eastern longitude
           lat1: FLOAT - Southern or northern latitude
           lat2: FLOAT - Northern or southern latitude
           idx1: INTEGER - Index of first longitude
           idx2: INTEGER - Index of last longitude
           idy1: INTEGER - Index of first latitude
           idy2: INTEGER - Index of last latitude
        """
        operator = CdoOperator(command="maskindexbox",
                               n_input=1, 
                               n_output=1, 
                               params=['lon1', 'lon2', 'lat1', 'lat2', 'idx1', 'idx2', 'idy1', 'idy2']) 
                               
        return self._new_op(operator, [], {"lon1": lon1, "lon2": lon2, "lat1": lat1, "lat2": lat2, "idx1": idx1, "idx2": idx2, "idy1": idy1, "idy2": idy2})

    def setclonlatbox(self, c = None, lon1 = None, lon2 = None, lat1 = None, lat2 = None, idx1 = None, idx2 = None, idy1 = None, idy2 = None): # pragma: no cover
        r"""
        CDO operator: setclonlatbox
        Parameters:
           c: FLOAT - Constant
           lon1: FLOAT - Western longitude
           lon2: FLOAT - Eastern longitude
           lat1: FLOAT - Southern or northern latitude
           lat2: FLOAT - Northern or southern latitude
           idx1: INTEGER - Index of first longitude
           idx2: INTEGER - Index of last longitude
           idy1: INTEGER - Index of first latitude
           idy2: INTEGER - Index of last latitude
        """
        operator = CdoOperator(command="setclonlatbox",
                               n_input=1, 
                               n_output=1, 
                               params=['c', 'lon1', 'lon2', 'lat1', 'lat2', 'idx1', 'idx2', 'idy1', 'idy2']) 
                               
        return self._new_op(operator, [], {"c": c, "lon1": lon1, "lon2": lon2, "lat1": lat1, "lat2": lat2, "idx1": idx1, "idx2": idx2, "idy1": idy1, "idy2": idy2})

    def setcindexbox(self, c = None, lon1 = None, lon2 = None, lat1 = None, lat2 = None, idx1 = None, idx2 = None, idy1 = None, idy2 = None): # pragma: no cover
        r"""
        CDO operator: setcindexbox
        Parameters:
           c: FLOAT - Constant
           lon1: FLOAT - Western longitude
           lon2: FLOAT - Eastern longitude
           lat1: FLOAT - Southern or northern latitude
           lat2: FLOAT - Northern or southern latitude
           idx1: INTEGER - Index of first longitude
           idx2: INTEGER - Index of last longitude
           idy1: INTEGER - Index of first latitude
           idy2: INTEGER - Index of last latitude
        """
        operator = CdoOperator(command="setcindexbox",
                               n_input=1, 
                               n_output=1, 
                               params=['c', 'lon1', 'lon2', 'lat1', 'lat2', 'idx1', 'idx2', 'idy1', 'idy2']) 
                               
        return self._new_op(operator, [], {"c": c, "lon1": lon1, "lon2": lon2, "lat1": lat1, "lat2": lat2, "idx1": idx1, "idx2": idx2, "idy1": idy1, "idy2": idy2})

    def enlarge(self, grid = None): # pragma: no cover
        r"""
        CDO operator: enlarge
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="enlarge",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def setmissval(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setmissval
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setmissval",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def setctomiss(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setctomiss
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setctomiss",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def setmisstoc(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setmisstoc
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setmisstoc",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def setrtomiss(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setrtomiss
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setrtomiss",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def setvrange(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setvrange
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setvrange",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def setmisstonn(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setmisstonn
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setmisstonn",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def setmisstodis(self, neighbors = None, newmiss = None, c = None, rmin = None, rmax = None): # pragma: no cover
        r"""
        CDO operator: setmisstodis
        Parameters:
           neighbors: INTEGER - Number of nearest neighbors
           newmiss: FLOAT - New missing value
           c: FLOAT - Constant
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
        """
        operator = CdoOperator(command="setmisstodis",
                               n_input=1, 
                               n_output=1, 
                               params=['neighbors', 'newmiss', 'c', 'rmin', 'rmax']) 
                               
        return self._new_op(operator, [], {"neighbors": neighbors, "newmiss": newmiss, "c": c, "rmin": rmin, "rmax": rmax})

    def vertfillmiss(self, method = None, limit = None, max_gaps = None): # pragma: no cover
        r"""
        CDO operator: vertfillmiss
        Parameters:
           method: STRING - Fill method \[nearest|linear|forward|backward\] (default: nearest)
           limit: INTEGER - The maximum number of consecutive missing values to fill (default: all)
           max_gaps: INTEGER - The maximum number of gaps to fill (default: all)
        """
        operator = CdoOperator(command="vertfillmiss",
                               n_input=1, 
                               n_output=1, 
                               params=['method', 'limit', 'max_gaps']) 
                               
        return self._new_op(operator, [], {"method": method, "limit": limit, "max_gaps": max_gaps})

    def timfillmiss(self, method = None, limit = None, max_gaps = None): # pragma: no cover
        r"""
        CDO operator: timfillmiss
        Parameters:
           method: STRING - Fill method \[nearest|linear|forward|backward\] (default: nearest)
           limit: INTEGER - The maximum number of consecutive missing values to fill (default: all)
           max_gaps: INTEGER - The maximum number of gaps to fill (default: all)
        """
        operator = CdoOperator(command="timfillmiss",
                               n_input=1, 
                               n_output=1, 
                               params=['method', 'limit', 'max_gaps']) 
                               
        return self._new_op(operator, [], {"method": method, "limit": limit, "max_gaps": max_gaps})

    def setgridcell(self, value = None, cell = None, mask = None): # pragma: no cover
        r"""
        CDO operator: setgridcell
        Parameters:
           value: FLOAT - Value of the grid cell
           cell: INTEGER - Comma-separated list of grid cell indices
           mask: STRING - Name of the data file which contains the mask
        """
        operator = CdoOperator(command="setgridcell",
                               n_input=1, 
                               n_output=1, 
                               params=['value', 'cell', 'mask']) 
                               
        return self._new_op(operator, [], {"value": value, "cell": cell, "mask": mask})

    def expr(self, instr = None, filename = None): # pragma: no cover
        r"""
        CDO operator: expr
        Parameters:
           instr: STRING - Processing instructions (need to be 'quoted' in most cases)
           filename: STRING - File with processing instructions
        """
        operator = CdoOperator(command="expr",
                               n_input=1, 
                               n_output=1, 
                               params=['instr', 'filename']) 
                               
        return self._new_op(operator, [], {"instr": instr, "filename": filename})

    def exprf(self, instr = None, filename = None): # pragma: no cover
        r"""
        CDO operator: exprf
        Parameters:
           instr: STRING - Processing instructions (need to be 'quoted' in most cases)
           filename: STRING - File with processing instructions
        """
        operator = CdoOperator(command="exprf",
                               n_input=1, 
                               n_output=1, 
                               params=['instr', 'filename']) 
                               
        return self._new_op(operator, [], {"instr": instr, "filename": filename})

    def aexpr(self, instr = None, filename = None): # pragma: no cover
        r"""
        CDO operator: aexpr
        Parameters:
           instr: STRING - Processing instructions (need to be 'quoted' in most cases)
           filename: STRING - File with processing instructions
        """
        operator = CdoOperator(command="aexpr",
                               n_input=1, 
                               n_output=1, 
                               params=['instr', 'filename']) 
                               
        return self._new_op(operator, [], {"instr": instr, "filename": filename})

    def aexprf(self, instr = None, filename = None): # pragma: no cover
        r"""
        CDO operator: aexprf
        Parameters:
           instr: STRING - Processing instructions (need to be 'quoted' in most cases)
           filename: STRING - File with processing instructions
        """
        operator = CdoOperator(command="aexprf",
                               n_input=1, 
                               n_output=1, 
                               params=['instr', 'filename']) 
                               
        return self._new_op(operator, [], {"instr": instr, "filename": filename})

    def abs(self): # pragma: no cover
        r"""
        CDO operator: abs
        """
        operator = CdoOperator(command="abs",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def int(self): # pragma: no cover
        r"""
        CDO operator: int
        """
        operator = CdoOperator(command="int",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def nint(self): # pragma: no cover
        r"""
        CDO operator: nint
        """
        operator = CdoOperator(command="nint",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def pow(self): # pragma: no cover
        r"""
        CDO operator: pow
        """
        operator = CdoOperator(command="pow",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def sqr(self): # pragma: no cover
        r"""
        CDO operator: sqr
        """
        operator = CdoOperator(command="sqr",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def sqrt(self): # pragma: no cover
        r"""
        CDO operator: sqrt
        """
        operator = CdoOperator(command="sqrt",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def exp(self): # pragma: no cover
        r"""
        CDO operator: exp
        """
        operator = CdoOperator(command="exp",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ln(self): # pragma: no cover
        r"""
        CDO operator: ln
        """
        operator = CdoOperator(command="ln",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def log10(self): # pragma: no cover
        r"""
        CDO operator: log10
        """
        operator = CdoOperator(command="log10",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def sin(self): # pragma: no cover
        r"""
        CDO operator: sin
        """
        operator = CdoOperator(command="sin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def cos(self): # pragma: no cover
        r"""
        CDO operator: cos
        """
        operator = CdoOperator(command="cos",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def tan(self): # pragma: no cover
        r"""
        CDO operator: tan
        """
        operator = CdoOperator(command="tan",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def asin(self): # pragma: no cover
        r"""
        CDO operator: asin
        """
        operator = CdoOperator(command="asin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def acos(self): # pragma: no cover
        r"""
        CDO operator: acos
        """
        operator = CdoOperator(command="acos",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def atan(self): # pragma: no cover
        r"""
        CDO operator: atan
        """
        operator = CdoOperator(command="atan",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def reci(self): # pragma: no cover
        r"""
        CDO operator: reci
        """
        operator = CdoOperator(command="reci",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def negate(self): # pragma: no cover
        r"""
        CDO operator: not
        """
        operator = CdoOperator(command="not",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def addc(self, c = None): # pragma: no cover
        r"""
        CDO operator: addc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="addc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def subc(self, c = None): # pragma: no cover
        r"""
        CDO operator: subc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="subc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def mulc(self, c = None): # pragma: no cover
        r"""
        CDO operator: mulc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="mulc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def divc(self, c = None): # pragma: no cover
        r"""
        CDO operator: divc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="divc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def minc(self, c = None): # pragma: no cover
        r"""
        CDO operator: minc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="minc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def maxc(self, c = None): # pragma: no cover
        r"""
        CDO operator: maxc
        Parameters:
           c: FLOAT - Constant
        """
        operator = CdoOperator(command="maxc",
                               n_input=1, 
                               n_output=1, 
                               params=['c']) 
                               
        return self._new_op(operator, [], {"c": c})

    def add(self, ifile2): # pragma: no cover
        r"""
        CDO operator: add
        """
        operator = CdoOperator(command="add",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def sub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: sub
        """
        operator = CdoOperator(command="sub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def mul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: mul
        """
        operator = CdoOperator(command="mul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def div(self, ifile2): # pragma: no cover
        r"""
        CDO operator: div
        """
        operator = CdoOperator(command="div",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def min(self, ifile2): # pragma: no cover
        r"""
        CDO operator: min
        """
        operator = CdoOperator(command="min",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def max(self, ifile2): # pragma: no cover
        r"""
        CDO operator: max
        """
        operator = CdoOperator(command="max",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def atan2(self, ifile2): # pragma: no cover
        r"""
        CDO operator: atan2
        """
        operator = CdoOperator(command="atan2",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def dayadd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: dayadd
        """
        operator = CdoOperator(command="dayadd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def daysub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: daysub
        """
        operator = CdoOperator(command="daysub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def daymul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: daymul
        """
        operator = CdoOperator(command="daymul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def daydiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: daydiv
        """
        operator = CdoOperator(command="daydiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def monadd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: monadd
        """
        operator = CdoOperator(command="monadd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def monsub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: monsub
        """
        operator = CdoOperator(command="monsub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def monmul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: monmul
        """
        operator = CdoOperator(command="monmul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def mondiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: mondiv
        """
        operator = CdoOperator(command="mondiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yearadd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yearadd
        """
        operator = CdoOperator(command="yearadd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yearsub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yearsub
        """
        operator = CdoOperator(command="yearsub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yearmul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yearmul
        """
        operator = CdoOperator(command="yearmul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yeardiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yeardiv
        """
        operator = CdoOperator(command="yeardiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yhouradd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yhouradd
        """
        operator = CdoOperator(command="yhouradd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yhoursub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yhoursub
        """
        operator = CdoOperator(command="yhoursub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yhourmul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yhourmul
        """
        operator = CdoOperator(command="yhourmul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yhourdiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yhourdiv
        """
        operator = CdoOperator(command="yhourdiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ydayadd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ydayadd
        """
        operator = CdoOperator(command="ydayadd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ydaysub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ydaysub
        """
        operator = CdoOperator(command="ydaysub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ydaymul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ydaymul
        """
        operator = CdoOperator(command="ydaymul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ydaydiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ydaydiv
        """
        operator = CdoOperator(command="ydaydiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonadd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonadd
        """
        operator = CdoOperator(command="ymonadd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonsub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonsub
        """
        operator = CdoOperator(command="ymonsub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymonmul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymonmul
        """
        operator = CdoOperator(command="ymonmul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def ymondiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: ymondiv
        """
        operator = CdoOperator(command="ymondiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yseasadd(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yseasadd
        """
        operator = CdoOperator(command="yseasadd",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yseassub(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yseassub
        """
        operator = CdoOperator(command="yseassub",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yseasmul(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yseasmul
        """
        operator = CdoOperator(command="yseasmul",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def yseasdiv(self, ifile2): # pragma: no cover
        r"""
        CDO operator: yseasdiv
        """
        operator = CdoOperator(command="yseasdiv",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def muldpm(self): # pragma: no cover
        r"""
        CDO operator: muldpm
        """
        operator = CdoOperator(command="muldpm",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def divdpm(self): # pragma: no cover
        r"""
        CDO operator: divdpm
        """
        operator = CdoOperator(command="divdpm",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def muldpy(self): # pragma: no cover
        r"""
        CDO operator: muldpy
        """
        operator = CdoOperator(command="muldpy",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def divdpy(self): # pragma: no cover
        r"""
        CDO operator: divdpy
        """
        operator = CdoOperator(command="divdpy",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def mulcoslat(self): # pragma: no cover
        r"""
        CDO operator: mulcoslat
        """
        operator = CdoOperator(command="mulcoslat",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def divcoslat(self): # pragma: no cover
        r"""
        CDO operator: divcoslat
        """
        operator = CdoOperator(command="divcoslat",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timcumsum(self): # pragma: no cover
        r"""
        CDO operator: timcumsum
        """
        operator = CdoOperator(command="timcumsum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def consecsum(self): # pragma: no cover
        r"""
        CDO operator: consecsum
        """
        operator = CdoOperator(command="consecsum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def consects(self): # pragma: no cover
        r"""
        CDO operator: consects
        """
        operator = CdoOperator(command="consects",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsmin(self): # pragma: no cover
        r"""
        CDO operator: varsmin
        """
        operator = CdoOperator(command="varsmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsmax(self): # pragma: no cover
        r"""
        CDO operator: varsmax
        """
        operator = CdoOperator(command="varsmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsrange(self): # pragma: no cover
        r"""
        CDO operator: varsrange
        """
        operator = CdoOperator(command="varsrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varssum(self): # pragma: no cover
        r"""
        CDO operator: varssum
        """
        operator = CdoOperator(command="varssum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsmean(self): # pragma: no cover
        r"""
        CDO operator: varsmean
        """
        operator = CdoOperator(command="varsmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsavg(self): # pragma: no cover
        r"""
        CDO operator: varsavg
        """
        operator = CdoOperator(command="varsavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsstd(self): # pragma: no cover
        r"""
        CDO operator: varsstd
        """
        operator = CdoOperator(command="varsstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsstd1(self): # pragma: no cover
        r"""
        CDO operator: varsstd1
        """
        operator = CdoOperator(command="varsstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsvar(self): # pragma: no cover
        r"""
        CDO operator: varsvar
        """
        operator = CdoOperator(command="varsvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def varsvar1(self): # pragma: no cover
        r"""
        CDO operator: varsvar1
        """
        operator = CdoOperator(command="varsvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ensmin(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensmin
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensmin",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensmax(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensmax
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensmax",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensrange(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensrange
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensrange",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def enssum(self, p = None): # pragma: no cover
        r"""
        CDO operator: enssum
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="enssum",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensmean(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensmean
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensmean",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensavg(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensavg
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensavg",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensstd(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensstd
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensstd",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensstd1(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensstd1
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensstd1",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensvar(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensvar
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensvar",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensvar1(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensvar1
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensvar1",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensskew(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensskew
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensskew",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def enskurt(self, p = None): # pragma: no cover
        r"""
        CDO operator: enskurt
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="enskurt",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensmedian(self, p = None): # pragma: no cover
        r"""
        CDO operator: ensmedian
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ensmedian",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def enspctl(self, p = None): # pragma: no cover
        r"""
        CDO operator: enspctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="enspctl",
                               n_input=inf, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def ensrkhistspace(self): # pragma: no cover
        r"""
        CDO operator: ensrkhistspace
        """
        operator = CdoOperator(command="ensrkhistspace",
                               n_input=inf, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ensrkhisttime(self): # pragma: no cover
        r"""
        CDO operator: ensrkhisttime
        """
        operator = CdoOperator(command="ensrkhisttime",
                               n_input=inf, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ensroc(self): # pragma: no cover
        r"""
        CDO operator: ensroc
        """
        operator = CdoOperator(command="ensroc",
                               n_input=inf, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def enscrps(self): # pragma: no cover
        r"""
        CDO operator: enscrps
        """
        operator = CdoOperator(command="enscrps",
                               n_input=inf, 
                               n_output=inf, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ensbrs(self): # pragma: no cover
        r"""
        CDO operator: ensbrs
        """
        operator = CdoOperator(command="ensbrs",
                               n_input=inf, 
                               n_output=inf, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def fldmin(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldmin
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldmin",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldmax(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldmax
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldmax",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldrange(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldrange
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldrange",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldsum(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldsum
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldsum",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldint(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldint
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldint",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldmean(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldmean
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldmean",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldavg(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldavg
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldavg",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldstd(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldstd
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldstd",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldstd1(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldstd1
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldvar(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldvar
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldvar",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldvar1(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldvar1
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldskew(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldskew
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldskew",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldkurt(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldkurt
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldkurt",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldmedian(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldmedian
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldmedian",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldcount(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldcount
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldcount",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def fldpctl(self, weights = None, p = None): # pragma: no cover
        r"""
        CDO operator: fldpctl
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by grid cell area \[default: weights=TRUE\]
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="fldpctl",
                               n_input=1, 
                               n_output=1, 
                               params=['weights', 'p']) 
                               
        return self._new_op(operator, [], {"weights": weights, "p": p})

    def zonmin(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonmin
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonmin",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonmax(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonmax
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonmax",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonrange(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonrange
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonrange",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonsum(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonsum
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonsum",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonmean(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonmean
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonmean",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonavg(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonavg
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonavg",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonstd(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonstd
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonstd",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonstd1(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonstd1
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonvar(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonvar
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonvar",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonvar1(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonvar1
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonskew(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonskew
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonskew",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonkurt(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonkurt
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonkurt",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonmedian(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonmedian
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonmedian",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def zonpctl(self, p = None, zonaldes = None): # pragma: no cover
        r"""
        CDO operator: zonpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           zonaldes: STRING - Description of the zonal latitude bins needed for data on an unstructured grid. A predefined zonal description is zonal_<DY>. DY is the increment of the latitudes in degrees.
        """
        operator = CdoOperator(command="zonpctl",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'zonaldes']) 
                               
        return self._new_op(operator, [], {"p": p, "zonaldes": zonaldes})

    def mermin(self, p = None): # pragma: no cover
        r"""
        CDO operator: mermin
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mermin",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def mermax(self, p = None): # pragma: no cover
        r"""
        CDO operator: mermax
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mermax",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def merrange(self, p = None): # pragma: no cover
        r"""
        CDO operator: merrange
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="merrange",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def mersum(self, p = None): # pragma: no cover
        r"""
        CDO operator: mersum
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mersum",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def mermean(self, p = None): # pragma: no cover
        r"""
        CDO operator: mermean
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mermean",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def meravg(self, p = None): # pragma: no cover
        r"""
        CDO operator: meravg
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="meravg",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def merstd(self, p = None): # pragma: no cover
        r"""
        CDO operator: merstd
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="merstd",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def merstd1(self, p = None): # pragma: no cover
        r"""
        CDO operator: merstd1
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="merstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def mervar(self, p = None): # pragma: no cover
        r"""
        CDO operator: mervar
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mervar",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def mervar1(self, p = None): # pragma: no cover
        r"""
        CDO operator: mervar1
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mervar1",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def merskew(self, p = None): # pragma: no cover
        r"""
        CDO operator: merskew
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="merskew",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def merkurt(self, p = None): # pragma: no cover
        r"""
        CDO operator: merkurt
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="merkurt",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def mermedian(self, p = None): # pragma: no cover
        r"""
        CDO operator: mermedian
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="mermedian",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def merpctl(self, p = None): # pragma: no cover
        r"""
        CDO operator: merpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="merpctl",
                               n_input=1, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [], {"p": p})

    def gridboxmin(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxmin
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxmin",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxmax(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxmax
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxmax",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxrange(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxrange
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxrange",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxsum(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxsum
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxsum",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxmean(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxmean
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxmean",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxavg(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxavg
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxavg",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxstd(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxstd
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxstd",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxstd1(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxstd1
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxvar(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxvar
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxvar",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxvar1(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxvar1
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxskew(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxskew
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxskew",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxkurt(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxkurt
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxkurt",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def gridboxmedian(self, nx = None, ny = None): # pragma: no cover
        r"""
        CDO operator: gridboxmedian
        Parameters:
           nx: INTEGER - Number of grid boxes in x direction
           ny: INTEGER - Number of grid boxes in y direction
        """
        operator = CdoOperator(command="gridboxmedian",
                               n_input=1, 
                               n_output=1, 
                               params=['nx', 'ny']) 
                               
        return self._new_op(operator, [], {"nx": nx, "ny": ny})

    def remapmin(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapmin
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapmin",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapmax(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapmax
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapmax",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remaprange(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remaprange
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remaprange",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapsum(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapsum
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapsum",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapmean(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapmean
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapmean",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapavg(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapavg
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapavg",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapstd(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapstd
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapstd",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapstd1(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapstd1
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapvar(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapvar
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapvar",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapvar1(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapvar1
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapskew(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapskew
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapskew",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapkurt(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapkurt
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapkurt",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remapmedian(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remapmedian
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remapmedian",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def vertmin(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertmin
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertmin",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertmax(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertmax
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertmax",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertrange(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertrange
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertrange",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertsum(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertsum
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertsum",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertmean(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertmean
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertmean",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertavg(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertavg
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertavg",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertstd(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertstd
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertstd",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertstd1(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertstd1
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertvar(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertvar
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertvar",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def vertvar1(self, weights = None): # pragma: no cover
        r"""
        CDO operator: vertvar1
        Parameters:
           weights: BOOL - weights=FALSE disables weighting by layer thickness \[default: weights=TRUE\]
        """
        operator = CdoOperator(command="vertvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['weights']) 
                               
        return self._new_op(operator, [], {"weights": weights})

    def timselmin(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselmin
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselmin",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselmax(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselmax
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselmax",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselrange(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselrange
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselrange",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselsum(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselsum
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselsum",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselmean(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselmean
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselmean",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselavg(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselavg
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselavg",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselstd(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselstd
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselstd",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselstd1(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselstd1
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselvar(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselvar
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselvar",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselvar1(self, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselvar1
        Parameters:
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [], {"nsets": nsets, "noffset": noffset, "nskip": nskip})

    def timselpctl(self, ifile2, ifile3, p = None, nsets = None, noffset = None, nskip = None): # pragma: no cover
        r"""
        CDO operator: timselpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           nsets: INTEGER - Number of input timesteps for each output timestep
           noffset: INTEGER - Number of input timesteps skipped before the first timestep range (optional)
           nskip: INTEGER - Number of input timesteps skipped between timestep ranges (optional)
        """
        operator = CdoOperator(command="timselpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p', 'nsets', 'noffset', 'nskip']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p, "nsets": nsets, "noffset": noffset, "nskip": nskip})

    def runmin(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runmin
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runmin",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runmax(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runmax
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runmax",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runrange(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runrange
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runrange",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runsum(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runsum
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runsum",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runmean(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runmean
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runmean",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runavg(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runavg
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runavg",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runstd(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runstd
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runstd",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runstd1(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runstd1
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runvar(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runvar
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runvar",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runvar1(self, nts = None): # pragma: no cover
        r"""
        CDO operator: runvar1
        Parameters:
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['nts']) 
                               
        return self._new_op(operator, [], {"nts": nts})

    def runpctl(self, p = None, nts = None): # pragma: no cover
        r"""
        CDO operator: runpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           nts: INTEGER - Number of timesteps
        """
        operator = CdoOperator(command="runpctl",
                               n_input=1, 
                               n_output=1, 
                               params=['p', 'nts']) 
                               
        return self._new_op(operator, [], {"p": p, "nts": nts})

    def timmin(self): # pragma: no cover
        r"""
        CDO operator: timmin
        """
        operator = CdoOperator(command="timmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timmax(self): # pragma: no cover
        r"""
        CDO operator: timmax
        """
        operator = CdoOperator(command="timmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timminidx(self): # pragma: no cover
        r"""
        CDO operator: timminidx
        """
        operator = CdoOperator(command="timminidx",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timmaxidx(self): # pragma: no cover
        r"""
        CDO operator: timmaxidx
        """
        operator = CdoOperator(command="timmaxidx",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timrange(self): # pragma: no cover
        r"""
        CDO operator: timrange
        """
        operator = CdoOperator(command="timrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timsum(self): # pragma: no cover
        r"""
        CDO operator: timsum
        """
        operator = CdoOperator(command="timsum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timmean(self): # pragma: no cover
        r"""
        CDO operator: timmean
        """
        operator = CdoOperator(command="timmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timavg(self): # pragma: no cover
        r"""
        CDO operator: timavg
        """
        operator = CdoOperator(command="timavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timstd(self): # pragma: no cover
        r"""
        CDO operator: timstd
        """
        operator = CdoOperator(command="timstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timstd1(self): # pragma: no cover
        r"""
        CDO operator: timstd1
        """
        operator = CdoOperator(command="timstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timvar(self): # pragma: no cover
        r"""
        CDO operator: timvar
        """
        operator = CdoOperator(command="timvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timvar1(self): # pragma: no cover
        r"""
        CDO operator: timvar1
        """
        operator = CdoOperator(command="timvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def timpctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: timpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="timpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def hourmin(self): # pragma: no cover
        r"""
        CDO operator: hourmin
        """
        operator = CdoOperator(command="hourmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourmax(self): # pragma: no cover
        r"""
        CDO operator: hourmax
        """
        operator = CdoOperator(command="hourmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourrange(self): # pragma: no cover
        r"""
        CDO operator: hourrange
        """
        operator = CdoOperator(command="hourrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hoursum(self): # pragma: no cover
        r"""
        CDO operator: hoursum
        """
        operator = CdoOperator(command="hoursum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourmean(self): # pragma: no cover
        r"""
        CDO operator: hourmean
        """
        operator = CdoOperator(command="hourmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def houravg(self): # pragma: no cover
        r"""
        CDO operator: houravg
        """
        operator = CdoOperator(command="houravg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourstd(self): # pragma: no cover
        r"""
        CDO operator: hourstd
        """
        operator = CdoOperator(command="hourstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourstd1(self): # pragma: no cover
        r"""
        CDO operator: hourstd1
        """
        operator = CdoOperator(command="hourstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourvar(self): # pragma: no cover
        r"""
        CDO operator: hourvar
        """
        operator = CdoOperator(command="hourvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourvar1(self): # pragma: no cover
        r"""
        CDO operator: hourvar1
        """
        operator = CdoOperator(command="hourvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hourpctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: hourpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="hourpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def daymin(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: daymin
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="daymin",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def daymax(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: daymax
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="daymax",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def dayrange(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: dayrange
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="dayrange",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def daysum(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: daysum
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="daysum",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def daymean(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: daymean
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="daymean",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def dayavg(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: dayavg
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="dayavg",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def daystd(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: daystd
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="daystd",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def daystd1(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: daystd1
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="daystd1",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def dayvar(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: dayvar
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="dayvar",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def dayvar1(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: dayvar1
        Parameters:
           complete_only: BOOL - Process the last day only if it is complete
        """
        operator = CdoOperator(command="dayvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def daypctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: daypctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="daypctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def monmin(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monmin
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monmin",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monmax(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monmax
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monmax",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monrange(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monrange
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monrange",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monsum(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monsum
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monsum",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monmean(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monmean
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monmean",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monavg(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monavg
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monavg",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monstd(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monstd
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monstd",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monstd1(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monstd1
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monvar(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monvar
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monvar",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monvar1(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: monvar1
        Parameters:
           complete_only: BOOL - Process the last month only if it is complete
        """
        operator = CdoOperator(command="monvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def monpctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: monpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="monpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def yearmonmean(self): # pragma: no cover
        r"""
        CDO operator: yearmonmean
        """
        operator = CdoOperator(command="yearmonmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yearmin(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearmin
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearmin",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearmax(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearmax
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearmax",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearminidx(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearminidx
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearminidx",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearmaxidx(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearmaxidx
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearmaxidx",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearrange(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearrange
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearrange",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearsum(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearsum
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearsum",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearmean(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearmean
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearmean",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearavg(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearavg
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearavg",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearstd(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearstd
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearstd",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearstd1(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearstd1
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearvar(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearvar
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearvar",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearvar1(self, complete_only = None): # pragma: no cover
        r"""
        CDO operator: yearvar1
        Parameters:
           complete_only: BOOL - Process the last year only if it is complete
        """
        operator = CdoOperator(command="yearvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['complete_only']) 
                               
        return self._new_op(operator, [], {"complete_only": complete_only})

    def yearpctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: yearpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="yearpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def seasmin(self): # pragma: no cover
        r"""
        CDO operator: seasmin
        """
        operator = CdoOperator(command="seasmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasmax(self): # pragma: no cover
        r"""
        CDO operator: seasmax
        """
        operator = CdoOperator(command="seasmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasrange(self): # pragma: no cover
        r"""
        CDO operator: seasrange
        """
        operator = CdoOperator(command="seasrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seassum(self): # pragma: no cover
        r"""
        CDO operator: seassum
        """
        operator = CdoOperator(command="seassum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasmean(self): # pragma: no cover
        r"""
        CDO operator: seasmean
        """
        operator = CdoOperator(command="seasmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasavg(self): # pragma: no cover
        r"""
        CDO operator: seasavg
        """
        operator = CdoOperator(command="seasavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasstd(self): # pragma: no cover
        r"""
        CDO operator: seasstd
        """
        operator = CdoOperator(command="seasstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasstd1(self): # pragma: no cover
        r"""
        CDO operator: seasstd1
        """
        operator = CdoOperator(command="seasstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasvar(self): # pragma: no cover
        r"""
        CDO operator: seasvar
        """
        operator = CdoOperator(command="seasvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seasvar1(self): # pragma: no cover
        r"""
        CDO operator: seasvar1
        """
        operator = CdoOperator(command="seasvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def seaspctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: seaspctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="seaspctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def yhourmin(self): # pragma: no cover
        r"""
        CDO operator: yhourmin
        """
        operator = CdoOperator(command="yhourmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourmax(self): # pragma: no cover
        r"""
        CDO operator: yhourmax
        """
        operator = CdoOperator(command="yhourmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourrange(self): # pragma: no cover
        r"""
        CDO operator: yhourrange
        """
        operator = CdoOperator(command="yhourrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhoursum(self): # pragma: no cover
        r"""
        CDO operator: yhoursum
        """
        operator = CdoOperator(command="yhoursum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourmean(self): # pragma: no cover
        r"""
        CDO operator: yhourmean
        """
        operator = CdoOperator(command="yhourmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhouravg(self): # pragma: no cover
        r"""
        CDO operator: yhouravg
        """
        operator = CdoOperator(command="yhouravg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourstd(self): # pragma: no cover
        r"""
        CDO operator: yhourstd
        """
        operator = CdoOperator(command="yhourstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourstd1(self): # pragma: no cover
        r"""
        CDO operator: yhourstd1
        """
        operator = CdoOperator(command="yhourstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourvar(self): # pragma: no cover
        r"""
        CDO operator: yhourvar
        """
        operator = CdoOperator(command="yhourvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yhourvar1(self): # pragma: no cover
        r"""
        CDO operator: yhourvar1
        """
        operator = CdoOperator(command="yhourvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourmin(self): # pragma: no cover
        r"""
        CDO operator: dhourmin
        """
        operator = CdoOperator(command="dhourmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourmax(self): # pragma: no cover
        r"""
        CDO operator: dhourmax
        """
        operator = CdoOperator(command="dhourmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourrange(self): # pragma: no cover
        r"""
        CDO operator: dhourrange
        """
        operator = CdoOperator(command="dhourrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhoursum(self): # pragma: no cover
        r"""
        CDO operator: dhoursum
        """
        operator = CdoOperator(command="dhoursum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourmean(self): # pragma: no cover
        r"""
        CDO operator: dhourmean
        """
        operator = CdoOperator(command="dhourmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhouravg(self): # pragma: no cover
        r"""
        CDO operator: dhouravg
        """
        operator = CdoOperator(command="dhouravg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourstd(self): # pragma: no cover
        r"""
        CDO operator: dhourstd
        """
        operator = CdoOperator(command="dhourstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourstd1(self): # pragma: no cover
        r"""
        CDO operator: dhourstd1
        """
        operator = CdoOperator(command="dhourstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourvar(self): # pragma: no cover
        r"""
        CDO operator: dhourvar
        """
        operator = CdoOperator(command="dhourvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dhourvar1(self): # pragma: no cover
        r"""
        CDO operator: dhourvar1
        """
        operator = CdoOperator(command="dhourvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutemin(self): # pragma: no cover
        r"""
        CDO operator: dminutemin
        """
        operator = CdoOperator(command="dminutemin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutemax(self): # pragma: no cover
        r"""
        CDO operator: dminutemax
        """
        operator = CdoOperator(command="dminutemax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminuterange(self): # pragma: no cover
        r"""
        CDO operator: dminuterange
        """
        operator = CdoOperator(command="dminuterange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutesum(self): # pragma: no cover
        r"""
        CDO operator: dminutesum
        """
        operator = CdoOperator(command="dminutesum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutemean(self): # pragma: no cover
        r"""
        CDO operator: dminutemean
        """
        operator = CdoOperator(command="dminutemean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminuteavg(self): # pragma: no cover
        r"""
        CDO operator: dminuteavg
        """
        operator = CdoOperator(command="dminuteavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutestd(self): # pragma: no cover
        r"""
        CDO operator: dminutestd
        """
        operator = CdoOperator(command="dminutestd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutestd1(self): # pragma: no cover
        r"""
        CDO operator: dminutestd1
        """
        operator = CdoOperator(command="dminutestd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutevar(self): # pragma: no cover
        r"""
        CDO operator: dminutevar
        """
        operator = CdoOperator(command="dminutevar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dminutevar1(self): # pragma: no cover
        r"""
        CDO operator: dminutevar1
        """
        operator = CdoOperator(command="dminutevar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaymin(self): # pragma: no cover
        r"""
        CDO operator: ydaymin
        """
        operator = CdoOperator(command="ydaymin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaymax(self): # pragma: no cover
        r"""
        CDO operator: ydaymax
        """
        operator = CdoOperator(command="ydaymax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydayrange(self): # pragma: no cover
        r"""
        CDO operator: ydayrange
        """
        operator = CdoOperator(command="ydayrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaysum(self): # pragma: no cover
        r"""
        CDO operator: ydaysum
        """
        operator = CdoOperator(command="ydaysum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaymean(self): # pragma: no cover
        r"""
        CDO operator: ydaymean
        """
        operator = CdoOperator(command="ydaymean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydayavg(self): # pragma: no cover
        r"""
        CDO operator: ydayavg
        """
        operator = CdoOperator(command="ydayavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaystd(self): # pragma: no cover
        r"""
        CDO operator: ydaystd
        """
        operator = CdoOperator(command="ydaystd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaystd1(self): # pragma: no cover
        r"""
        CDO operator: ydaystd1
        """
        operator = CdoOperator(command="ydaystd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydayvar(self): # pragma: no cover
        r"""
        CDO operator: ydayvar
        """
        operator = CdoOperator(command="ydayvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydayvar1(self): # pragma: no cover
        r"""
        CDO operator: ydayvar1
        """
        operator = CdoOperator(command="ydayvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ydaypctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: ydaypctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ydaypctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def ymonmin(self): # pragma: no cover
        r"""
        CDO operator: ymonmin
        """
        operator = CdoOperator(command="ymonmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonmax(self): # pragma: no cover
        r"""
        CDO operator: ymonmax
        """
        operator = CdoOperator(command="ymonmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonrange(self): # pragma: no cover
        r"""
        CDO operator: ymonrange
        """
        operator = CdoOperator(command="ymonrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonsum(self): # pragma: no cover
        r"""
        CDO operator: ymonsum
        """
        operator = CdoOperator(command="ymonsum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonmean(self): # pragma: no cover
        r"""
        CDO operator: ymonmean
        """
        operator = CdoOperator(command="ymonmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonavg(self): # pragma: no cover
        r"""
        CDO operator: ymonavg
        """
        operator = CdoOperator(command="ymonavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonstd(self): # pragma: no cover
        r"""
        CDO operator: ymonstd
        """
        operator = CdoOperator(command="ymonstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonstd1(self): # pragma: no cover
        r"""
        CDO operator: ymonstd1
        """
        operator = CdoOperator(command="ymonstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonvar(self): # pragma: no cover
        r"""
        CDO operator: ymonvar
        """
        operator = CdoOperator(command="ymonvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonvar1(self): # pragma: no cover
        r"""
        CDO operator: ymonvar1
        """
        operator = CdoOperator(command="ymonvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def ymonpctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: ymonpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="ymonpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def yseasmin(self): # pragma: no cover
        r"""
        CDO operator: yseasmin
        """
        operator = CdoOperator(command="yseasmin",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasmax(self): # pragma: no cover
        r"""
        CDO operator: yseasmax
        """
        operator = CdoOperator(command="yseasmax",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasrange(self): # pragma: no cover
        r"""
        CDO operator: yseasrange
        """
        operator = CdoOperator(command="yseasrange",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseassum(self): # pragma: no cover
        r"""
        CDO operator: yseassum
        """
        operator = CdoOperator(command="yseassum",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasmean(self): # pragma: no cover
        r"""
        CDO operator: yseasmean
        """
        operator = CdoOperator(command="yseasmean",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasavg(self): # pragma: no cover
        r"""
        CDO operator: yseasavg
        """
        operator = CdoOperator(command="yseasavg",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasstd(self): # pragma: no cover
        r"""
        CDO operator: yseasstd
        """
        operator = CdoOperator(command="yseasstd",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasstd1(self): # pragma: no cover
        r"""
        CDO operator: yseasstd1
        """
        operator = CdoOperator(command="yseasstd1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasvar(self): # pragma: no cover
        r"""
        CDO operator: yseasvar
        """
        operator = CdoOperator(command="yseasvar",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseasvar1(self): # pragma: no cover
        r"""
        CDO operator: yseasvar1
        """
        operator = CdoOperator(command="yseasvar1",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def yseaspctl(self, ifile2, ifile3, p = None): # pragma: no cover
        r"""
        CDO operator: yseaspctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
        """
        operator = CdoOperator(command="yseaspctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p})

    def ydrunmin(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunmin
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunmin",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunmax(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunmax
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunmax",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunsum(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunsum
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunsum",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunmean(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunmean
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunmean",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunavg(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunavg
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunavg",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunstd(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunstd
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunstd",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunstd1(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunstd1
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunstd1",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunvar(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunvar
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunvar",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunvar1(self, nts = None, rm_c = None): # pragma: no cover
        r"""
        CDO operator: ydrunvar1
        Parameters:
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
        """
        operator = CdoOperator(command="ydrunvar1",
                               n_input=1, 
                               n_output=1, 
                               params=['nts', 'rm_c']) 
                               
        return self._new_op(operator, [], {"nts": nts, "rm_c": rm_c})

    def ydrunpctl(self, ifile2, ifile3, p = None, nts = None, rm_c = None, pm_r8 = None): # pragma: no cover
        r"""
        CDO operator: ydrunpctl
        Parameters:
           p: FLOAT - Percentile number in \{0, ..., 100\}
           nts: INTEGER - Number of timesteps
           rm_c: STRING - Read method circular
           pm_r8: STRING - Percentile method rtype8
        """
        operator = CdoOperator(command="ydrunpctl",
                               n_input=3, 
                               n_output=1, 
                               params=['p', 'nts', 'rm_c', 'pm_r8']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"p": p, "nts": nts, "rm_c": rm_c, "pm_r8": pm_r8})

    def fldcor(self, ifile2): # pragma: no cover
        r"""
        CDO operator: fldcor
        """
        operator = CdoOperator(command="fldcor",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def timcor(self, ifile2): # pragma: no cover
        r"""
        CDO operator: timcor
        """
        operator = CdoOperator(command="timcor",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def fldcovar(self, ifile2): # pragma: no cover
        r"""
        CDO operator: fldcovar
        """
        operator = CdoOperator(command="fldcovar",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def timcovar(self, ifile2): # pragma: no cover
        r"""
        CDO operator: timcovar
        """
        operator = CdoOperator(command="timcovar",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def regres(self, equal = None): # pragma: no cover
        r"""
        CDO operator: regres
        Parameters:
           equal: BOOL - Set to false for unequal distributed timesteps (default: true)
        """
        operator = CdoOperator(command="regres",
                               n_input=1, 
                               n_output=1, 
                               params=['equal']) 
                               
        return self._new_op(operator, [], {"equal": equal})

    def detrend(self, equal = None): # pragma: no cover
        r"""
        CDO operator: detrend
        Parameters:
           equal: BOOL - Set to false for unequal distributed timesteps (default: true)
        """
        operator = CdoOperator(command="detrend",
                               n_input=1, 
                               n_output=1, 
                               params=['equal']) 
                               
        return self._new_op(operator, [], {"equal": equal})

    def trend(self, equal = None): # pragma: no cover
        r"""
        CDO operator: trend
        Parameters:
           equal: BOOL - Set to false for unequal distributed timesteps (default: true)
        """
        operator = CdoOperator(command="trend",
                               n_input=1, 
                               n_output=2, 
                               params=['equal']) 
                               
        return self._new_op(operator, [], {"equal": equal})

    def addtrend(self, ifile2, ifile3, equal = None): # pragma: no cover
        r"""
        CDO operator: addtrend
        Parameters:
           equal: BOOL - Set to false for unequal distributed timesteps (default: true)
        """
        operator = CdoOperator(command="addtrend",
                               n_input=3, 
                               n_output=1, 
                               params=['equal']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"equal": equal})

    def subtrend(self, ifile2, ifile3, equal = None): # pragma: no cover
        r"""
        CDO operator: subtrend
        Parameters:
           equal: BOOL - Set to false for unequal distributed timesteps (default: true)
        """
        operator = CdoOperator(command="subtrend",
                               n_input=3, 
                               n_output=1, 
                               params=['equal']) 
                               
        return self._new_op(operator, [ifile2, ifile3], {"equal": equal})

    def eof(self, neof = None): # pragma: no cover
        r"""
        CDO operator: eof
        Parameters:
           neof: INTEGER - Number of eigen functions
        """
        operator = CdoOperator(command="eof",
                               n_input=1, 
                               n_output=2, 
                               params=['neof']) 
                               
        return self._new_op(operator, [], {"neof": neof})

    def eoftime(self, neof = None): # pragma: no cover
        r"""
        CDO operator: eoftime
        Parameters:
           neof: INTEGER - Number of eigen functions
        """
        operator = CdoOperator(command="eoftime",
                               n_input=1, 
                               n_output=2, 
                               params=['neof']) 
                               
        return self._new_op(operator, [], {"neof": neof})

    def eofspatial(self, neof = None): # pragma: no cover
        r"""
        CDO operator: eofspatial
        Parameters:
           neof: INTEGER - Number of eigen functions
        """
        operator = CdoOperator(command="eofspatial",
                               n_input=1, 
                               n_output=2, 
                               params=['neof']) 
                               
        return self._new_op(operator, [], {"neof": neof})

    def eof3d(self, neof = None): # pragma: no cover
        r"""
        CDO operator: eof3d
        Parameters:
           neof: INTEGER - Number of eigen functions
        """
        operator = CdoOperator(command="eof3d",
                               n_input=1, 
                               n_output=2, 
                               params=['neof']) 
                               
        return self._new_op(operator, [], {"neof": neof})

    def eofcoeff(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eofcoeff
        """
        operator = CdoOperator(command="eofcoeff",
                               n_input=2, 
                               n_output=inf, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def remapbil(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: remapbil
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="remapbil",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def genbil(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: genbil
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="genbil",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def remapbic(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: remapbic
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="remapbic",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def genbic(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: genbic
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="genbic",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def remapnn(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: remapnn
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="remapnn",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def gennn(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: gennn
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="gennn",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def remapdis(self, grid = None, neighbors = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: remapdis
        Parameters:
           grid: STRING - Target grid description file or name
           neighbors: INTEGER - Number of nearest neighbors \[default: 4\]
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="remapdis",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'neighbors', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "neighbors": neighbors, "map3d": map3d})

    def gendis(self, grid = None, neighbors = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: gendis
        Parameters:
           grid: STRING - Target grid description file or name
           neighbors: INTEGER - Number of nearest neighbors \[default: 4\]
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="gendis",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'neighbors', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "neighbors": neighbors, "map3d": map3d})

    def remapcon(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: remapcon
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="remapcon",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def gencon(self, grid = None, map3d = None): # pragma: no cover
        r"""
        CDO operator: gencon
        Parameters:
           grid: STRING - Target grid description file or name
           map3d: BOOL - Generate all mapfiles of the first 3D field
        """
        operator = CdoOperator(command="gencon",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'map3d']) 
                               
        return self._new_op(operator, [], {"grid": grid, "map3d": map3d})

    def remaplaf(self, grid = None): # pragma: no cover
        r"""
        CDO operator: remaplaf
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="remaplaf",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def genlaf(self, grid = None): # pragma: no cover
        r"""
        CDO operator: genlaf
        Parameters:
           grid: STRING - Target grid description file or name
        """
        operator = CdoOperator(command="genlaf",
                               n_input=1, 
                               n_output=1, 
                               params=['grid']) 
                               
        return self._new_op(operator, [], {"grid": grid})

    def remap(self, grid = None, weights = None): # pragma: no cover
        r"""
        CDO operator: remap
        Parameters:
           grid: STRING - Target grid description file or name
           weights: STRING - Interpolation weights (SCRIP NetCDF file)
        """
        operator = CdoOperator(command="remap",
                               n_input=1, 
                               n_output=1, 
                               params=['grid', 'weights']) 
                               
        return self._new_op(operator, [], {"grid": grid, "weights": weights})

    def remapeta(self, vct = None, oro = None): # pragma: no cover
        r"""
        CDO operator: remapeta
        Parameters:
           vct: STRING - File name of an ASCII dataset with the vertical coordinate table
           oro: STRING - File name with the orography (surf. geopotential) of the target dataset (optional)
        """
        operator = CdoOperator(command="remapeta",
                               n_input=1, 
                               n_output=1, 
                               params=['vct', 'oro']) 
                               
        return self._new_op(operator, [], {"vct": vct, "oro": oro})

    def ml2pl(self, plevels = None, hlevels = None): # pragma: no cover
        r"""
        CDO operator: ml2pl
        Parameters:
           plevels: FLOAT - Pressure levels in pascal
           hlevels: FLOAT - Height levels in meter
        """
        operator = CdoOperator(command="ml2pl",
                               n_input=1, 
                               n_output=1, 
                               params=['plevels', 'hlevels']) 
                               
        return self._new_op(operator, [], {"plevels": plevels, "hlevels": hlevels})

    def ml2hl(self, plevels = None, hlevels = None): # pragma: no cover
        r"""
        CDO operator: ml2hl
        Parameters:
           plevels: FLOAT - Pressure levels in pascal
           hlevels: FLOAT - Height levels in meter
        """
        operator = CdoOperator(command="ml2hl",
                               n_input=1, 
                               n_output=1, 
                               params=['plevels', 'hlevels']) 
                               
        return self._new_op(operator, [], {"plevels": plevels, "hlevels": hlevels})

    def ap2pl(self, plevels = None): # pragma: no cover
        r"""
        CDO operator: ap2pl
        Parameters:
           plevels: FLOAT - Comma-separated list of pressure levels in pascal
        """
        operator = CdoOperator(command="ap2pl",
                               n_input=1, 
                               n_output=1, 
                               params=['plevels']) 
                               
        return self._new_op(operator, [], {"plevels": plevels})

    def gh2hl(self, hlevels = None): # pragma: no cover
        r"""
        CDO operator: gh2hl
        Parameters:
           hlevels: FLOAT - Comma-separated list of height levels in meter
        """
        operator = CdoOperator(command="gh2hl",
                               n_input=1, 
                               n_output=1, 
                               params=['hlevels']) 
                               
        return self._new_op(operator, [], {"hlevels": hlevels})

    def intlevel(self, level = None, zdescription = None, zvarname = None, extrapolate = None): # pragma: no cover
        r"""
        CDO operator: intlevel
        Parameters:
           level: FLOAT - Comma-separated list of target levels
           zdescription: STRING - Path to a file containing a description of the Z-axis
           zvarname: STRING - Use zvarname as the vertical 3D source coordinate instead of the 1D coordinate variable
           extrapolate: BOOL - Fill target layers out of the source layer range with the nearest source layer
        """
        operator = CdoOperator(command="intlevel",
                               n_input=1, 
                               n_output=1, 
                               params=['level', 'zdescription', 'zvarname', 'extrapolate']) 
                               
        return self._new_op(operator, [], {"level": level, "zdescription": zdescription, "zvarname": zvarname, "extrapolate": extrapolate})

    def intlevel3d(self, ifile2, tgtcoordinate = None): # pragma: no cover
        r"""
        CDO operator: intlevel3d
        Parameters:
           tgtcoordinate: STRING - filename for 3D vertical target coordinates
        """
        operator = CdoOperator(command="intlevel3d",
                               n_input=2, 
                               n_output=1, 
                               params=['tgtcoordinate']) 
                               
        return self._new_op(operator, [ifile2], {"tgtcoordinate": tgtcoordinate})

    def intlevelx3d(self, ifile2, tgtcoordinate = None): # pragma: no cover
        r"""
        CDO operator: intlevelx3d
        Parameters:
           tgtcoordinate: STRING - filename for 3D vertical target coordinates
        """
        operator = CdoOperator(command="intlevelx3d",
                               n_input=2, 
                               n_output=1, 
                               params=['tgtcoordinate']) 
                               
        return self._new_op(operator, [ifile2], {"tgtcoordinate": tgtcoordinate})

    def inttime(self, date = None, time = None, inc = None, n = None): # pragma: no cover
        r"""
        CDO operator: inttime
        Parameters:
           date: STRING - Start date (format YYYY-MM-DD)
           time: STRING - Start time (format hh:mm:ss)
           inc: STRING - Optional increment (seconds, minutes, hours, days, months, years) \[default: 0hour\]
           n: INTEGER - Number of timesteps from one timestep to the next
        """
        operator = CdoOperator(command="inttime",
                               n_input=1, 
                               n_output=1, 
                               params=['date', 'time', 'inc', 'n']) 
                               
        return self._new_op(operator, [], {"date": date, "time": time, "inc": inc, "n": n})

    def intntime(self, date = None, time = None, inc = None, n = None): # pragma: no cover
        r"""
        CDO operator: intntime
        Parameters:
           date: STRING - Start date (format YYYY-MM-DD)
           time: STRING - Start time (format hh:mm:ss)
           inc: STRING - Optional increment (seconds, minutes, hours, days, months, years) \[default: 0hour\]
           n: INTEGER - Number of timesteps from one timestep to the next
        """
        operator = CdoOperator(command="intntime",
                               n_input=1, 
                               n_output=1, 
                               params=['date', 'time', 'inc', 'n']) 
                               
        return self._new_op(operator, [], {"date": date, "time": time, "inc": inc, "n": n})

    def intyear(self, ifile2, years = None): # pragma: no cover
        r"""
        CDO operator: intyear
        Parameters:
           years: INTEGER - Comma-separated list or first/last\[/inc\] range of years
        """
        operator = CdoOperator(command="intyear",
                               n_input=2, 
                               n_output=inf, 
                               params=['years']) 
                               
        return self._new_op(operator, [ifile2], {"years": years})

    def sp2gp(self, type = None, trunc = None): # pragma: no cover
        r"""
        CDO operator: sp2gp
        Parameters:
           type: STRING - Type of the grid: quadratic, linear, cubic (default: type=quadratic)
           trunc: STRING - Triangular truncation
        """
        operator = CdoOperator(command="sp2gp",
                               n_input=1, 
                               n_output=1, 
                               params=['type', 'trunc']) 
                               
        return self._new_op(operator, [], {"type": type, "trunc": trunc})

    def gp2sp(self, type = None, trunc = None): # pragma: no cover
        r"""
        CDO operator: gp2sp
        Parameters:
           type: STRING - Type of the grid: quadratic, linear, cubic (default: type=quadratic)
           trunc: STRING - Triangular truncation
        """
        operator = CdoOperator(command="gp2sp",
                               n_input=1, 
                               n_output=1, 
                               params=['type', 'trunc']) 
                               
        return self._new_op(operator, [], {"type": type, "trunc": trunc})

    def sp2sp(self, trunc = None): # pragma: no cover
        r"""
        CDO operator: sp2sp
        Parameters:
           trunc: INTEGER - New spectral resolution
        """
        operator = CdoOperator(command="sp2sp",
                               n_input=1, 
                               n_output=1, 
                               params=['trunc']) 
                               
        return self._new_op(operator, [], {"trunc": trunc})

    def dv2ps(self): # pragma: no cover
        r"""
        CDO operator: dv2ps
        """
        operator = CdoOperator(command="dv2ps",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def dv2uv(self, gridtype = None): # pragma: no cover
        r"""
        CDO operator: dv2uv
        Parameters:
           gridtype: STRING - Type of the grid: quadratic, linear, cubic (default: quadratic)
        """
        operator = CdoOperator(command="dv2uv",
                               n_input=1, 
                               n_output=1, 
                               params=['gridtype']) 
                               
        return self._new_op(operator, [], {"gridtype": gridtype})

    def uv2dv(self, gridtype = None): # pragma: no cover
        r"""
        CDO operator: uv2dv
        Parameters:
           gridtype: STRING - Type of the grid: quadratic, linear, cubic (default: quadratic)
        """
        operator = CdoOperator(command="uv2dv",
                               n_input=1, 
                               n_output=1, 
                               params=['gridtype']) 
                               
        return self._new_op(operator, [], {"gridtype": gridtype})

    def fourier(self, epsilon = None): # pragma: no cover
        r"""
        CDO operator: fourier
        Parameters:
           epsilon: INTEGER - -1: forward transformation; 1: backward transformation
        """
        operator = CdoOperator(command="fourier",
                               n_input=1, 
                               n_output=1, 
                               params=['epsilon']) 
                               
        return self._new_op(operator, [], {"epsilon": epsilon})

    def import_binary(self): # pragma: no cover
        r"""
        CDO operator: import_binary
        """
        operator = CdoOperator(command="import_binary",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def import_cmsaf(self): # pragma: no cover
        r"""
        CDO operator: import_cmsaf
        """
        operator = CdoOperator(command="import_cmsaf",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def import_amsr(self): # pragma: no cover
        r"""
        CDO operator: import_amsr
        """
        operator = CdoOperator(command="import_amsr",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def input(self, grid = None, zaxis = None): # pragma: no cover
        r"""
        CDO operator: input
        Parameters:
           grid: STRING - Grid description file or name
           zaxis: STRING - Z-axis description file
        """
        operator = CdoOperator(command="input",
                               n_input=0, 
                               n_output=1, 
                               params=['grid', 'zaxis']) 
                               
        return self._new_op(operator, [], {"grid": grid, "zaxis": zaxis})

    def inputsrv(self, grid = None, zaxis = None): # pragma: no cover
        r"""
        CDO operator: inputsrv
        Parameters:
           grid: STRING - Grid description file or name
           zaxis: STRING - Z-axis description file
        """
        operator = CdoOperator(command="inputsrv",
                               n_input=0, 
                               n_output=1, 
                               params=['grid', 'zaxis']) 
                               
        return self._new_op(operator, [], {"grid": grid, "zaxis": zaxis})

    def inputext(self, grid = None, zaxis = None): # pragma: no cover
        r"""
        CDO operator: inputext
        Parameters:
           grid: STRING - Grid description file or name
           zaxis: STRING - Z-axis description file
        """
        operator = CdoOperator(command="inputext",
                               n_input=0, 
                               n_output=1, 
                               params=['grid', 'zaxis']) 
                               
        return self._new_op(operator, [], {"grid": grid, "zaxis": zaxis})

    def output(self, format = None, nelem = None): # pragma: no cover
        r"""
        CDO operator: output
        Parameters:
           format: STRING - C-style format for one element (e.g. %13.6g)
           nelem: INTEGER - Number of elements for each row (default: nelem = 1)
        """
        operator = CdoOperator(command="output",
                               n_input=inf, 
                               n_output=0, 
                               params=['format', 'nelem']) 
                               
        return self._new_op(operator, [], {"format": format, "nelem": nelem})

    def outputf(self, format = None, nelem = None): # pragma: no cover
        r"""
        CDO operator: outputf
        Parameters:
           format: STRING - C-style format for one element (e.g. %13.6g)
           nelem: INTEGER - Number of elements for each row (default: nelem = 1)
        """
        operator = CdoOperator(command="outputf",
                               n_input=inf, 
                               n_output=0, 
                               params=['format', 'nelem']) 
                               
        return self._new_op(operator, [], {"format": format, "nelem": nelem})

    def outputint(self, format = None, nelem = None): # pragma: no cover
        r"""
        CDO operator: outputint
        Parameters:
           format: STRING - C-style format for one element (e.g. %13.6g)
           nelem: INTEGER - Number of elements for each row (default: nelem = 1)
        """
        operator = CdoOperator(command="outputint",
                               n_input=inf, 
                               n_output=0, 
                               params=['format', 'nelem']) 
                               
        return self._new_op(operator, [], {"format": format, "nelem": nelem})

    def outputsrv(self, format = None, nelem = None): # pragma: no cover
        r"""
        CDO operator: outputsrv
        Parameters:
           format: STRING - C-style format for one element (e.g. %13.6g)
           nelem: INTEGER - Number of elements for each row (default: nelem = 1)
        """
        operator = CdoOperator(command="outputsrv",
                               n_input=inf, 
                               n_output=0, 
                               params=['format', 'nelem']) 
                               
        return self._new_op(operator, [], {"format": format, "nelem": nelem})

    def outputext(self, format = None, nelem = None): # pragma: no cover
        r"""
        CDO operator: outputext
        Parameters:
           format: STRING - C-style format for one element (e.g. %13.6g)
           nelem: INTEGER - Number of elements for each row (default: nelem = 1)
        """
        operator = CdoOperator(command="outputext",
                               n_input=inf, 
                               n_output=0, 
                               params=['format', 'nelem']) 
                               
        return self._new_op(operator, [], {"format": format, "nelem": nelem})

    def outputtab(self, parameter = None): # pragma: no cover
        r"""
        CDO operator: outputtab
        Parameters:
           parameter: STRING - Comma-separated list of keynames, one for each column of the table
        """
        operator = CdoOperator(command="outputtab",
                               n_input=inf, 
                               n_output=0, 
                               params=['parameter']) 
                               
        return self._new_op(operator, [], {"parameter": parameter})

    def gmtxyz(self): # pragma: no cover
        r"""
        CDO operator: gmtxyz
        """
        operator = CdoOperator(command="gmtxyz",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def gmtcells(self): # pragma: no cover
        r"""
        CDO operator: gmtcells
        """
        operator = CdoOperator(command="gmtcells",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def gradsdes(self, mapversion = None): # pragma: no cover
        r"""
        CDO operator: gradsdes
        Parameters:
           mapversion: INTEGER - Format version of the GrADS map file for GRIB1 datasets. Use 1 for a machinespecific version 1 GrADS map file, 2 for a machine independent version 2 GrADS map fileand 4 to support GRIB files >2GB.A version 2 map file can be used only with GrADS version 1.8 or newer.A version 4 map file can be used only with GrADS version 2.0 or newer.The default is 4 for files >2GB, otherwise 2.
        """
        operator = CdoOperator(command="gradsdes",
                               n_input=1, 
                               n_output=0, 
                               params=['mapversion']) 
                               
        return self._new_op(operator, [], {"mapversion": mapversion})

    def after(self, vct = None): # pragma: no cover
        r"""
        CDO operator: after
        Parameters:
           vct: STRING - File with VCT in ASCII format
        """
        operator = CdoOperator(command="after",
                               n_input=inf, 
                               n_output=1, 
                               params=['vct']) 
                               
        return self._new_op(operator, [], {"vct": vct})

    def bandpass(self, fmin = None, fmax = None): # pragma: no cover
        r"""
        CDO operator: bandpass
        Parameters:
           fmin: FLOAT	Minimum - frequency per year that passes the filter.
           fmax: FLOAT	Maximum - frequency per year that passes the filter.
        """
        operator = CdoOperator(command="bandpass",
                               n_input=1, 
                               n_output=1, 
                               params=['fmin', 'fmax']) 
                               
        return self._new_op(operator, [], {"fmin": fmin, "fmax": fmax})

    def lowpass(self, fmin = None, fmax = None): # pragma: no cover
        r"""
        CDO operator: lowpass
        Parameters:
           fmin: FLOAT	Minimum - frequency per year that passes the filter.
           fmax: FLOAT	Maximum - frequency per year that passes the filter.
        """
        operator = CdoOperator(command="lowpass",
                               n_input=1, 
                               n_output=1, 
                               params=['fmin', 'fmax']) 
                               
        return self._new_op(operator, [], {"fmin": fmin, "fmax": fmax})

    def highpass(self, fmin = None, fmax = None): # pragma: no cover
        r"""
        CDO operator: highpass
        Parameters:
           fmin: FLOAT	Minimum - frequency per year that passes the filter.
           fmax: FLOAT	Maximum - frequency per year that passes the filter.
        """
        operator = CdoOperator(command="highpass",
                               n_input=1, 
                               n_output=1, 
                               params=['fmin', 'fmax']) 
                               
        return self._new_op(operator, [], {"fmin": fmin, "fmax": fmax})

    def gridarea(self, radius = None): # pragma: no cover
        r"""
        CDO operator: gridarea
        Parameters:
           radius: FLOAT - Planet radius in meter
        """
        operator = CdoOperator(command="gridarea",
                               n_input=1, 
                               n_output=1, 
                               params=['radius']) 
                               
        return self._new_op(operator, [], {"radius": radius})

    def gridweights(self, radius = None): # pragma: no cover
        r"""
        CDO operator: gridweights
        Parameters:
           radius: FLOAT - Planet radius in meter
        """
        operator = CdoOperator(command="gridweights",
                               n_input=1, 
                               n_output=1, 
                               params=['radius']) 
                               
        return self._new_op(operator, [], {"radius": radius})

    def smooth(self, nsmooth = None, radius = None, maxpoints = None, weighted = None, weight0 = None, weightR = None): # pragma: no cover
        r"""
        CDO operator: smooth
        Parameters:
           nsmooth: INTEGER - Number of times to smooth, default nsmooth=1
           radius: STRING - Search radius, default radius=1deg (units: deg, rad, km, m)
           maxpoints: INTEGER - Maximum number of points, default maxpoints=<gridsize>
           weighted: STRING - Weighting method, default weighted=linear
           weight0: FLOAT - Weight at distance 0, default weight0=0.25
           weightR: FLOAT - Weight at the search radius, default weightR=0.25
        """
        operator = CdoOperator(command="smooth",
                               n_input=1, 
                               n_output=1, 
                               params=['nsmooth', 'radius', 'maxpoints', 'weighted', 'weight0', 'weightR']) 
                               
        return self._new_op(operator, [], {"nsmooth": nsmooth, "radius": radius, "maxpoints": maxpoints, "weighted": weighted, "weight0": weight0, "weightR": weightR})

    def smooth9(self, nsmooth = None, radius = None, maxpoints = None, weighted = None, weight0 = None, weightR = None): # pragma: no cover
        r"""
        CDO operator: smooth9
        Parameters:
           nsmooth: INTEGER - Number of times to smooth, default nsmooth=1
           radius: STRING - Search radius, default radius=1deg (units: deg, rad, km, m)
           maxpoints: INTEGER - Maximum number of points, default maxpoints=<gridsize>
           weighted: STRING - Weighting method, default weighted=linear
           weight0: FLOAT - Weight at distance 0, default weight0=0.25
           weightR: FLOAT - Weight at the search radius, default weightR=0.25
        """
        operator = CdoOperator(command="smooth9",
                               n_input=1, 
                               n_output=1, 
                               params=['nsmooth', 'radius', 'maxpoints', 'weighted', 'weight0', 'weightR']) 
                               
        return self._new_op(operator, [], {"nsmooth": nsmooth, "radius": radius, "maxpoints": maxpoints, "weighted": weighted, "weight0": weight0, "weightR": weightR})

    def deltat(self): # pragma: no cover
        r"""
        CDO operator: deltat
        """
        operator = CdoOperator(command="deltat",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def setvals(self, oldval = None, newval = None, rmin = None, rmax = None, c = None, c2 = None): # pragma: no cover
        r"""
        CDO operator: setvals
        Parameters:
           oldval: FLOAT - Pairs of old and new values
           newval: FLOAT - Pairs of old and new values
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
           c: FLOAT - New value - inside range
           c2: FLOAT - New value - outside range
        """
        operator = CdoOperator(command="setvals",
                               n_input=1, 
                               n_output=1, 
                               params=['oldval', 'newval', 'rmin', 'rmax', 'c', 'c2']) 
                               
        return self._new_op(operator, [], {"oldval": oldval, "newval": newval, "rmin": rmin, "rmax": rmax, "c": c, "c2": c2})

    def setrtoc(self, oldval = None, newval = None, rmin = None, rmax = None, c = None, c2 = None): # pragma: no cover
        r"""
        CDO operator: setrtoc
        Parameters:
           oldval: FLOAT - Pairs of old and new values
           newval: FLOAT - Pairs of old and new values
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
           c: FLOAT - New value - inside range
           c2: FLOAT - New value - outside range
        """
        operator = CdoOperator(command="setrtoc",
                               n_input=1, 
                               n_output=1, 
                               params=['oldval', 'newval', 'rmin', 'rmax', 'c', 'c2']) 
                               
        return self._new_op(operator, [], {"oldval": oldval, "newval": newval, "rmin": rmin, "rmax": rmax, "c": c, "c2": c2})

    def setrtoc2(self, oldval = None, newval = None, rmin = None, rmax = None, c = None, c2 = None): # pragma: no cover
        r"""
        CDO operator: setrtoc2
        Parameters:
           oldval: FLOAT - Pairs of old and new values
           newval: FLOAT - Pairs of old and new values
           rmin: FLOAT - Lower bound
           rmax: FLOAT - Upper bound
           c: FLOAT - New value - inside range
           c2: FLOAT - New value - outside range
        """
        operator = CdoOperator(command="setrtoc2",
                               n_input=1, 
                               n_output=1, 
                               params=['oldval', 'newval', 'rmin', 'rmax', 'c', 'c2']) 
                               
        return self._new_op(operator, [], {"oldval": oldval, "newval": newval, "rmin": rmin, "rmax": rmax, "c": c, "c2": c2})

    def gridcellindex(self, lon = None, lat = None): # pragma: no cover
        r"""
        CDO operator: gridcellindex
        Parameters:
           lon: INTEGER - Longitude of the grid cell in degree
           lat: INTEGER - Latitude of the grid cell in degree
        """
        operator = CdoOperator(command="gridcellindex",
                               n_input=1, 
                               n_output=0, 
                               params=['lon', 'lat']) 
                               
        return self._new_op(operator, [], {"lon": lon, "lat": lat})

    def const(self, const = None, seed = None, grid = None, start = None, end = None, inc = None, levels = None): # pragma: no cover
        r"""
        CDO operator: const
        Parameters:
           const: FLOAT - Constant
           seed: INTEGER - The seed for a new sequence of pseudo-random numbers \[default: 1\]
           grid: STRING - Target grid description file or name
           start: FLOAT - Start value of the loop
           end: FLOAT - End value of the loop
           inc: FLOAT - Increment of the loop \[default: 1\]
           levels: FLOAT - Target levels in metre above surface
        """
        operator = CdoOperator(command="const",
                               n_input=0, 
                               n_output=1, 
                               params=['const', 'seed', 'grid', 'start', 'end', 'inc', 'levels']) 
                               
        return self._new_op(operator, [], {"const": const, "seed": seed, "grid": grid, "start": start, "end": end, "inc": inc, "levels": levels})

    def random(self, const = None, seed = None, grid = None, start = None, end = None, inc = None, levels = None): # pragma: no cover
        r"""
        CDO operator: random
        Parameters:
           const: FLOAT - Constant
           seed: INTEGER - The seed for a new sequence of pseudo-random numbers \[default: 1\]
           grid: STRING - Target grid description file or name
           start: FLOAT - Start value of the loop
           end: FLOAT - End value of the loop
           inc: FLOAT - Increment of the loop \[default: 1\]
           levels: FLOAT - Target levels in metre above surface
        """
        operator = CdoOperator(command="random",
                               n_input=0, 
                               n_output=1, 
                               params=['const', 'seed', 'grid', 'start', 'end', 'inc', 'levels']) 
                               
        return self._new_op(operator, [], {"const": const, "seed": seed, "grid": grid, "start": start, "end": end, "inc": inc, "levels": levels})

    def topo(self, const = None, seed = None, grid = None, start = None, end = None, inc = None, levels = None): # pragma: no cover
        r"""
        CDO operator: topo
        Parameters:
           const: FLOAT - Constant
           seed: INTEGER - The seed for a new sequence of pseudo-random numbers \[default: 1\]
           grid: STRING - Target grid description file or name
           start: FLOAT - Start value of the loop
           end: FLOAT - End value of the loop
           inc: FLOAT - Increment of the loop \[default: 1\]
           levels: FLOAT - Target levels in metre above surface
        """
        operator = CdoOperator(command="topo",
                               n_input=0, 
                               n_output=1, 
                               params=['const', 'seed', 'grid', 'start', 'end', 'inc', 'levels']) 
                               
        return self._new_op(operator, [], {"const": const, "seed": seed, "grid": grid, "start": start, "end": end, "inc": inc, "levels": levels})

    def seq(self, const = None, seed = None, grid = None, start = None, end = None, inc = None, levels = None): # pragma: no cover
        r"""
        CDO operator: seq
        Parameters:
           const: FLOAT - Constant
           seed: INTEGER - The seed for a new sequence of pseudo-random numbers \[default: 1\]
           grid: STRING - Target grid description file or name
           start: FLOAT - Start value of the loop
           end: FLOAT - End value of the loop
           inc: FLOAT - Increment of the loop \[default: 1\]
           levels: FLOAT - Target levels in metre above surface
        """
        operator = CdoOperator(command="seq",
                               n_input=0, 
                               n_output=1, 
                               params=['const', 'seed', 'grid', 'start', 'end', 'inc', 'levels']) 
                               
        return self._new_op(operator, [], {"const": const, "seed": seed, "grid": grid, "start": start, "end": end, "inc": inc, "levels": levels})

    def stdatm(self, const = None, seed = None, grid = None, start = None, end = None, inc = None, levels = None): # pragma: no cover
        r"""
        CDO operator: stdatm
        Parameters:
           const: FLOAT - Constant
           seed: INTEGER - The seed for a new sequence of pseudo-random numbers \[default: 1\]
           grid: STRING - Target grid description file or name
           start: FLOAT - Start value of the loop
           end: FLOAT - End value of the loop
           inc: FLOAT - Increment of the loop \[default: 1\]
           levels: FLOAT - Target levels in metre above surface
        """
        operator = CdoOperator(command="stdatm",
                               n_input=0, 
                               n_output=1, 
                               params=['const', 'seed', 'grid', 'start', 'end', 'inc', 'levels']) 
                               
        return self._new_op(operator, [], {"const": const, "seed": seed, "grid": grid, "start": start, "end": end, "inc": inc, "levels": levels})

    def timsort(self): # pragma: no cover
        r"""
        CDO operator: timsort
        """
        operator = CdoOperator(command="timsort",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def rotuvb(self, u = None, v = None): # pragma: no cover
        r"""
        CDO operator: rotuvb
        Parameters:
           u: STRING - Pairs of zonal and meridional velocity components (use variable names or code numbers)
           v: STRING - Pairs of zonal and meridional velocity components (use variable names or code numbers)
        """
        operator = CdoOperator(command="rotuvb",
                               n_input=1, 
                               n_output=1, 
                               params=['u', 'v']) 
                               
        return self._new_op(operator, [], {"u": u, "v": v})

    def mrotuvb(self, ifile2): # pragma: no cover
        r"""
        CDO operator: mrotuvb
        """
        operator = CdoOperator(command="mrotuvb",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def mastrfu(self): # pragma: no cover
        r"""
        CDO operator: mastrfu
        """
        operator = CdoOperator(command="mastrfu",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def pressure_half(self): # pragma: no cover
        r"""
        CDO operator: pressure_half
        """
        operator = CdoOperator(command="pressure_half",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def pressure(self): # pragma: no cover
        r"""
        CDO operator: pressure
        """
        operator = CdoOperator(command="pressure",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def delta_pressure(self): # pragma: no cover
        r"""
        CDO operator: delta_pressure
        """
        operator = CdoOperator(command="delta_pressure",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def sealevelpressure(self): # pragma: no cover
        r"""
        CDO operator: sealevelpressure
        """
        operator = CdoOperator(command="sealevelpressure",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def gheight(self): # pragma: no cover
        r"""
        CDO operator: gheight
        """
        operator = CdoOperator(command="gheight",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def gheight_half(self): # pragma: no cover
        r"""
        CDO operator: gheight_half
        """
        operator = CdoOperator(command="gheight_half",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def adisit(self, pressure = None): # pragma: no cover
        r"""
        CDO operator: adisit
        Parameters:
           pressure: FLOAT - Pressure in bar (constant value assigned to all levels)
        """
        operator = CdoOperator(command="adisit",
                               n_input=1, 
                               n_output=1, 
                               params=['pressure']) 
                               
        return self._new_op(operator, [], {"pressure": pressure})

    def adipot(self, pressure = None): # pragma: no cover
        r"""
        CDO operator: adipot
        Parameters:
           pressure: FLOAT - Pressure in bar (constant value assigned to all levels)
        """
        operator = CdoOperator(command="adipot",
                               n_input=1, 
                               n_output=1, 
                               params=['pressure']) 
                               
        return self._new_op(operator, [], {"pressure": pressure})

    def rhopot(self, pressure = None): # pragma: no cover
        r"""
        CDO operator: rhopot
        Parameters:
           pressure: FLOAT - Pressure in bar (constant value assigned to all levels)
        """
        operator = CdoOperator(command="rhopot",
                               n_input=1, 
                               n_output=1, 
                               params=['pressure']) 
                               
        return self._new_op(operator, [], {"pressure": pressure})

    def histcount(self, bounds = None): # pragma: no cover
        r"""
        CDO operator: histcount
        Parameters:
           bounds: FLOAT - Comma-separated list of the bin bounds (-inf and inf valid)
        """
        operator = CdoOperator(command="histcount",
                               n_input=1, 
                               n_output=1, 
                               params=['bounds']) 
                               
        return self._new_op(operator, [], {"bounds": bounds})

    def histsum(self, bounds = None): # pragma: no cover
        r"""
        CDO operator: histsum
        Parameters:
           bounds: FLOAT - Comma-separated list of the bin bounds (-inf and inf valid)
        """
        operator = CdoOperator(command="histsum",
                               n_input=1, 
                               n_output=1, 
                               params=['bounds']) 
                               
        return self._new_op(operator, [], {"bounds": bounds})

    def histmean(self, bounds = None): # pragma: no cover
        r"""
        CDO operator: histmean
        Parameters:
           bounds: FLOAT - Comma-separated list of the bin bounds (-inf and inf valid)
        """
        operator = CdoOperator(command="histmean",
                               n_input=1, 
                               n_output=1, 
                               params=['bounds']) 
                               
        return self._new_op(operator, [], {"bounds": bounds})

    def histfreq(self, bounds = None): # pragma: no cover
        r"""
        CDO operator: histfreq
        Parameters:
           bounds: FLOAT - Comma-separated list of the bin bounds (-inf and inf valid)
        """
        operator = CdoOperator(command="histfreq",
                               n_input=1, 
                               n_output=1, 
                               params=['bounds']) 
                               
        return self._new_op(operator, [], {"bounds": bounds})

    def sethalo(self, east = None, west = None, south = None, north = None, value = None): # pragma: no cover
        r"""
        CDO operator: sethalo
        Parameters:
           east: INTEGER - East halo
           west: INTEGER - West halo
           south: INTEGER - South halo
           north: INTEGER - North halo
           value: FLOAT - Fill value (default is the missing value)
        """
        operator = CdoOperator(command="sethalo",
                               n_input=1, 
                               n_output=1, 
                               params=['east', 'west', 'south', 'north', 'value']) 
                               
        return self._new_op(operator, [], {"east": east, "west": west, "south": south, "north": north, "value": value})

    def wct(self, ifile2): # pragma: no cover
        r"""
        CDO operator: wct
        """
        operator = CdoOperator(command="wct",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def fdns(self, ifile2): # pragma: no cover
        r"""
        CDO operator: fdns
        """
        operator = CdoOperator(command="fdns",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def strwin(self, v = None): # pragma: no cover
        r"""
        CDO operator: strwin
        Parameters:
           v: FLOAT - Horizontal wind speed threshold (m/s, default v = 10.5 m/s)
        """
        operator = CdoOperator(command="strwin",
                               n_input=1, 
                               n_output=1, 
                               params=['v']) 
                               
        return self._new_op(operator, [], {"v": v})

    def strbre(self): # pragma: no cover
        r"""
        CDO operator: strbre
        """
        operator = CdoOperator(command="strbre",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def strgal(self): # pragma: no cover
        r"""
        CDO operator: strgal
        """
        operator = CdoOperator(command="strgal",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hurr(self): # pragma: no cover
        r"""
        CDO operator: hurr
        """
        operator = CdoOperator(command="hurr",
                               n_input=1, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def cmorlite(self, table = None, convert = None): # pragma: no cover
        r"""
        CDO operator: cmorlite
        Parameters:
           table: STRING - Name of the CMOR table as specified from PCMDI
           convert: STRING - Converts the units if necessary
        """
        operator = CdoOperator(command="cmorlite",
                               n_input=1, 
                               n_output=1, 
                               params=['table', 'convert']) 
                               
        return self._new_op(operator, [], {"table": table, "convert": convert})

    def verifygrid(self): # pragma: no cover
        r"""
        CDO operator: verifygrid
        """
        operator = CdoOperator(command="verifygrid",
                               n_input=1, 
                               n_output=0, 
                               params=[]) 
                               
        return self._new_op(operator, [], {})

    def hpdegrade(self, nside = None, order = None, power = None): # pragma: no cover
        r"""
        CDO operator: hpdegrade
        Parameters:
           nside: INTEGER - The nside of the target healpix, must be a power of two \[default: same as input\].
           order: STRING - Pixel ordering of the target healpix ('nested' or 'ring').
           power: FLOAT - If non-zero, divide the result by (nside\[in\]/nside\[out\])**power. power=-2 keeps the sum of the map invariant.
        """
        operator = CdoOperator(command="hpdegrade",
                               n_input=1, 
                               n_output=1, 
                               params=['nside', 'order', 'power']) 
                               
        return self._new_op(operator, [], {"nside": nside, "order": order, "power": power})

    def hpupgrade(self, nside = None, order = None, power = None): # pragma: no cover
        r"""
        CDO operator: hpupgrade
        Parameters:
           nside: INTEGER - The nside of the target healpix, must be a power of two \[default: same as input\].
           order: STRING - Pixel ordering of the target healpix ('nested' or 'ring').
           power: FLOAT - If non-zero, divide the result by (nside\[in\]/nside\[out\])**power. power=-2 keeps the sum of the map invariant.
        """
        operator = CdoOperator(command="hpupgrade",
                               n_input=1, 
                               n_output=1, 
                               params=['nside', 'order', 'power']) 
                               
        return self._new_op(operator, [], {"nside": nside, "order": order, "power": power})

    def uv2vr_cfd(self, u = None, v = None, boundOpt = None, outMode = None): # pragma: no cover
        r"""
        CDO operator: uv2vr_cfd
        Parameters:
           u: STRING - Name of variable u (default: u)
           v: STRING - Name of variable v (default: v)
           boundOpt: INTEGER - Boundary condition option (0-3) (default: 0/1 for cyclic grids)
           outMode: STRING - Output mode new/append (default: new)
        """
        operator = CdoOperator(command="uv2vr_cfd",
                               n_input=1, 
                               n_output=1, 
                               params=['u', 'v', 'boundOpt', 'outMode']) 
                               
        return self._new_op(operator, [], {"u": u, "v": v, "boundOpt": boundOpt, "outMode": outMode})

    def uv2dv_cfd(self, u = None, v = None, boundOpt = None, outMode = None): # pragma: no cover
        r"""
        CDO operator: uv2dv_cfd
        Parameters:
           u: STRING - Name of variable u (default: u)
           v: STRING - Name of variable v (default: v)
           boundOpt: INTEGER - Boundary condition option (0-3) (default: 0/1 for cyclic grids)
           outMode: STRING - Output mode new/append (default: new)
        """
        operator = CdoOperator(command="uv2dv_cfd",
                               n_input=1, 
                               n_output=1, 
                               params=['u', 'v', 'boundOpt', 'outMode']) 
                               
        return self._new_op(operator, [], {"u": u, "v": v, "boundOpt": boundOpt, "outMode": outMode})

    def contour(self, parameter = None): # pragma: no cover
        r"""
        CDO operator: contour
        Parameters:
           parameter: STRING - Comma-separated list of plot parameters
        """
        operator = CdoOperator(command="contour",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter']) 
                               
        return self._new_op(operator, [], {"parameter": parameter})

    def shaded(self, parameter = None): # pragma: no cover
        r"""
        CDO operator: shaded
        Parameters:
           parameter: STRING - Comma-separated list of plot parameters
        """
        operator = CdoOperator(command="shaded",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter']) 
                               
        return self._new_op(operator, [], {"parameter": parameter})

    def grfill(self, parameter = None): # pragma: no cover
        r"""
        CDO operator: grfill
        Parameters:
           parameter: STRING - Comma-separated list of plot parameters
        """
        operator = CdoOperator(command="grfill",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter']) 
                               
        return self._new_op(operator, [], {"parameter": parameter})

    def vector(self, parameter = None): # pragma: no cover
        r"""
        CDO operator: vector
        Parameters:
           parameter: STRING - Comma-separated list of plot parameters
        """
        operator = CdoOperator(command="vector",
                               n_input=1, 
                               n_output=1, 
                               params=['parameter']) 
                               
        return self._new_op(operator, [], {"parameter": parameter})

    def graph(self, parameter = None): # pragma: no cover
        r"""
        CDO operator: graph
        Parameters:
           parameter: STRING - Comma-separated list of plot parameters
        """
        operator = CdoOperator(command="graph",
                               n_input=inf, 
                               n_output=1, 
                               params=['parameter']) 
                               
        return self._new_op(operator, [], {"parameter": parameter})

    def eca_cdd(self, R = None, N = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_cdd
        Parameters:
           R: FLOAT - Precipitation threshold (unit: mm; default: R = 1 mm)
           N: INTEGER - Minimum number of days exceeded (default: N = 5)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_cdd",
                               n_input=1, 
                               n_output=1, 
                               params=['R', 'N', 'freq']) 
                               
        return self._new_op(operator, [], {"R": R, "N": N, "freq": freq})

    def etccdi_cdd(self, R = None, N = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_cdd
        Parameters:
           R: FLOAT - Precipitation threshold (unit: mm; default: R = 1 mm)
           N: INTEGER - Minimum number of days exceeded (default: N = 5)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_cdd",
                               n_input=1, 
                               n_output=1, 
                               params=['R', 'N', 'freq']) 
                               
        return self._new_op(operator, [], {"R": R, "N": N, "freq": freq})

    def eca_cfd(self, N = None): # pragma: no cover
        r"""
        CDO operator: eca_cfd
        Parameters:
           N: INTEGER - Minimum number of days exceeded (default: N = 5)
        """
        operator = CdoOperator(command="eca_cfd",
                               n_input=1, 
                               n_output=1, 
                               params=['N']) 
                               
        return self._new_op(operator, [], {"N": N})

    def eca_csu(self, T = None, N = None): # pragma: no cover
        r"""
        CDO operator: eca_csu
        Parameters:
           T: FLOAT - Temperature threshold (unit: °C; default: T = 25°C)
           N: INTEGER - Minimum number of days exceeded (default: N = 5)
        """
        operator = CdoOperator(command="eca_csu",
                               n_input=1, 
                               n_output=1, 
                               params=['T', 'N']) 
                               
        return self._new_op(operator, [], {"T": T, "N": N})

    def eca_cwd(self, R = None, N = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_cwd
        Parameters:
           R: FLOAT - Precipitation threshold (unit: mm; default: R = 1 mm)
           N: INTEGER - Minimum number of days exceeded (default: N = 5)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_cwd",
                               n_input=1, 
                               n_output=1, 
                               params=['R', 'N', 'freq']) 
                               
        return self._new_op(operator, [], {"R": R, "N": N, "freq": freq})

    def etccdi_cwd(self, R = None, N = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_cwd
        Parameters:
           R: FLOAT - Precipitation threshold (unit: mm; default: R = 1 mm)
           N: INTEGER - Minimum number of days exceeded (default: N = 5)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_cwd",
                               n_input=1, 
                               n_output=1, 
                               params=['R', 'N', 'freq']) 
                               
        return self._new_op(operator, [], {"R": R, "N": N, "freq": freq})

    def eca_cwdi(self, ifile2, nday = None, T = None): # pragma: no cover
        r"""
        CDO operator: eca_cwdi
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           T: FLOAT - Temperature offset (unit: °C; default: T = 5°C)
        """
        operator = CdoOperator(command="eca_cwdi",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'T']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "T": T})

    def eca_cwfi(self, ifile2, nday = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_cwfi
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_cwfi",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'freq']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "freq": freq})

    def etccdi_csdi(self, ifile2, nday = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_csdi
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_csdi",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'freq']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "freq": freq})

    def eca_etr(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_etr
        """
        operator = CdoOperator(command="eca_etr",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_fd(self, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_fd
        Parameters:
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_fd",
                               n_input=1, 
                               n_output=1, 
                               params=['freq']) 
                               
        return self._new_op(operator, [], {"freq": freq})

    def etccdi_fd(self, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_fd
        Parameters:
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_fd",
                               n_input=1, 
                               n_output=1, 
                               params=['freq']) 
                               
        return self._new_op(operator, [], {"freq": freq})

    def eca_gsl(self, ifile2, nday = None, T = None, fland = None): # pragma: no cover
        r"""
        CDO operator: eca_gsl
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           T: FLOAT - Temperature threshold (unit: °C; default: T = 5°C)
           fland: FLOAT - Land fraction threshold (default: fland = 0.5)
        """
        operator = CdoOperator(command="eca_gsl",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'T', 'fland']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "T": T, "fland": fland})

    def eca_hd(self, T1 = None, T2 = None): # pragma: no cover
        r"""
        CDO operator: eca_hd
        Parameters:
           T1: FLOAT - Temperature limit (unit: °C; default: T1 = 17°C)
           T2: FLOAT - Temperature limit (unit: °C; default: T2 = T1)
        """
        operator = CdoOperator(command="eca_hd",
                               n_input=1, 
                               n_output=1, 
                               params=['T1', 'T2']) 
                               
        return self._new_op(operator, [], {"T1": T1, "T2": T2})

    def eca_hwdi(self, ifile2, nday = None, T = None): # pragma: no cover
        r"""
        CDO operator: eca_hwdi
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           T: FLOAT - Temperature offset (unit: °C; default: T = 5°C)
        """
        operator = CdoOperator(command="eca_hwdi",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'T']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "T": T})

    def eca_hwfi(self, ifile2, nday = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_hwfi
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_hwfi",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'freq']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "freq": freq})

    def etccdi_wsdi(self, ifile2, nday = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_wsdi
        Parameters:
           nday: INTEGER - Number of consecutive days (default: nday = 6)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_wsdi",
                               n_input=2, 
                               n_output=1, 
                               params=['nday', 'freq']) 
                               
        return self._new_op(operator, [ifile2], {"nday": nday, "freq": freq})

    def eca_id(self, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_id
        Parameters:
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_id",
                               n_input=1, 
                               n_output=1, 
                               params=['freq']) 
                               
        return self._new_op(operator, [], {"freq": freq})

    def etccdi_id(self, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_id
        Parameters:
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_id",
                               n_input=1, 
                               n_output=1, 
                               params=['freq']) 
                               
        return self._new_op(operator, [], {"freq": freq})

    def eca_r75p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r75p
        """
        operator = CdoOperator(command="eca_r75p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r75ptot(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r75ptot
        """
        operator = CdoOperator(command="eca_r75ptot",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r90p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r90p
        """
        operator = CdoOperator(command="eca_r90p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r90ptot(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r90ptot
        """
        operator = CdoOperator(command="eca_r90ptot",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r95p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r95p
        """
        operator = CdoOperator(command="eca_r95p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r95ptot(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r95ptot
        """
        operator = CdoOperator(command="eca_r95ptot",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r99p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r99p
        """
        operator = CdoOperator(command="eca_r99p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_r99ptot(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_r99ptot
        """
        operator = CdoOperator(command="eca_r99ptot",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_pd(self, x = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_pd
        Parameters:
           x: FLOAT - Daily precipitation amount threshold in \[mm\]
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_pd",
                               n_input=1, 
                               n_output=1, 
                               params=['x', 'freq']) 
                               
        return self._new_op(operator, [], {"x": x, "freq": freq})

    def eca_r10mm(self, x = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_r10mm
        Parameters:
           x: FLOAT - Daily precipitation amount threshold in \[mm\]
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_r10mm",
                               n_input=1, 
                               n_output=1, 
                               params=['x', 'freq']) 
                               
        return self._new_op(operator, [], {"x": x, "freq": freq})

    def eca_r20mm(self, x = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_r20mm
        Parameters:
           x: FLOAT - Daily precipitation amount threshold in \[mm\]
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_r20mm",
                               n_input=1, 
                               n_output=1, 
                               params=['x', 'freq']) 
                               
        return self._new_op(operator, [], {"x": x, "freq": freq})

    def etccdi_r1mm(self, x = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_r1mm
        Parameters:
           x: FLOAT - Daily precipitation amount threshold in \[mm\]
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_r1mm",
                               n_input=1, 
                               n_output=1, 
                               params=['x', 'freq']) 
                               
        return self._new_op(operator, [], {"x": x, "freq": freq})

    def eca_rr1(self, R = None): # pragma: no cover
        r"""
        CDO operator: eca_rr1
        Parameters:
           R: FLOAT - Precipitation threshold (unit: mm; default: R = 1 mm)
        """
        operator = CdoOperator(command="eca_rr1",
                               n_input=1, 
                               n_output=1, 
                               params=['R']) 
                               
        return self._new_op(operator, [], {"R": R})

    def eca_rx1day(self, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_rx1day
        Parameters:
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_rx1day",
                               n_input=1, 
                               n_output=1, 
                               params=['freq']) 
                               
        return self._new_op(operator, [], {"freq": freq})

    def etccdi_rx1day(self, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_rx1day
        Parameters:
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_rx1day",
                               n_input=1, 
                               n_output=1, 
                               params=['freq']) 
                               
        return self._new_op(operator, [], {"freq": freq})

    def eca_rx5day(self, x = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_rx5day
        Parameters:
           x: FLOAT - Precipitation threshold (unit: mm; default: x = 50 mm)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_rx5day",
                               n_input=1, 
                               n_output=1, 
                               params=['x', 'freq']) 
                               
        return self._new_op(operator, [], {"x": x, "freq": freq})

    def etccdi_rx5day(self, x = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_rx5day
        Parameters:
           x: FLOAT - Precipitation threshold (unit: mm; default: x = 50 mm)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_rx5day",
                               n_input=1, 
                               n_output=1, 
                               params=['x', 'freq']) 
                               
        return self._new_op(operator, [], {"x": x, "freq": freq})

    def eca_sdii(self, R = None): # pragma: no cover
        r"""
        CDO operator: eca_sdii
        Parameters:
           R: FLOAT - Precipitation threshold (unit: mm; default: R = 1 mm)
        """
        operator = CdoOperator(command="eca_sdii",
                               n_input=1, 
                               n_output=1, 
                               params=['R']) 
                               
        return self._new_op(operator, [], {"R": R})

    def eca_su(self, T = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_su
        Parameters:
           T: FLOAT - Temperature threshold (unit: °C; default: T = 25°C)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_su",
                               n_input=1, 
                               n_output=1, 
                               params=['T', 'freq']) 
                               
        return self._new_op(operator, [], {"T": T, "freq": freq})

    def etccdi_su(self, T = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_su
        Parameters:
           T: FLOAT - Temperature threshold (unit: °C; default: T = 25°C)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_su",
                               n_input=1, 
                               n_output=1, 
                               params=['T', 'freq']) 
                               
        return self._new_op(operator, [], {"T": T, "freq": freq})

    def eca_tg10p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_tg10p
        """
        operator = CdoOperator(command="eca_tg10p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_tg90p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_tg90p
        """
        operator = CdoOperator(command="eca_tg90p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_tn10p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_tn10p
        """
        operator = CdoOperator(command="eca_tn10p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_tn90p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_tn90p
        """
        operator = CdoOperator(command="eca_tn90p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_tr(self, T = None, freq = None): # pragma: no cover
        r"""
        CDO operator: eca_tr
        Parameters:
           T: FLOAT - Temperature threshold (unit: °C; default: T = 20°C)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="eca_tr",
                               n_input=1, 
                               n_output=1, 
                               params=['T', 'freq']) 
                               
        return self._new_op(operator, [], {"T": T, "freq": freq})

    def etccdi_tr(self, T = None, freq = None): # pragma: no cover
        r"""
        CDO operator: etccdi_tr
        Parameters:
           T: FLOAT - Temperature threshold (unit: °C; default: T = 20°C)
           freq: STRING - Output frequency (year, month)
        """
        operator = CdoOperator(command="etccdi_tr",
                               n_input=1, 
                               n_output=1, 
                               params=['T', 'freq']) 
                               
        return self._new_op(operator, [], {"T": T, "freq": freq})

    def eca_tx10p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_tx10p
        """
        operator = CdoOperator(command="eca_tx10p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})

    def eca_tx90p(self, ifile2): # pragma: no cover
        r"""
        CDO operator: eca_tx90p
        """
        operator = CdoOperator(command="eca_tx90p",
                               n_input=2, 
                               n_output=1, 
                               params=[]) 
                               
        return self._new_op(operator, [ifile2], {})
