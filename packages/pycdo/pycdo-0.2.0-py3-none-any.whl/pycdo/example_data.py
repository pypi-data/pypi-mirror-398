"""Access example datasets included with pycdo."""

from pathlib import Path


def get_example_data(name: str) -> Path:
    """
    Get path to an example dataset.
    
    Parameters
    ----------
    name : str
        Name of the example dataset (e.g., 'test.nc', 'hgt_ncep.nc')
    
    Returns
    -------
    Path
        Path to the example data file
    
    Raises
    ------
    FileNotFoundError
        If the dataset doesn't exist
    
    Examples
    --------
    >>> import pycdo
    >>> path = pycdo.example_data('test.nc')
    >>> print(path)
    """
    data_dir = Path(__file__).parent / "data"
    filepath = data_dir / name
    
    if not filepath.exists():
        available = ", ".join(f.name for f in data_dir.glob("*") if f.is_file())
        raise FileNotFoundError(
            f"Dataset '{name}' not found. Available datasets: {available}"
        )
    
    return str(filepath)

geopotential = get_example_data("geopotential.nc")