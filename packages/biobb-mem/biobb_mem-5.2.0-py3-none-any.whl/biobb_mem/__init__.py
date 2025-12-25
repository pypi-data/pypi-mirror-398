import warnings
from Bio import BiopythonDeprecationWarning
warnings.simplefilter('ignore', BiopythonDeprecationWarning)
# Warnings comming from  MDAnalysis imports: The Bio.Application modules and modules relying on it have been deprecated....

name = "biobb_mem"
__all__ = ["ambertools", "fatslim", "gorder", "lipyphilic_biobb", "mdanalysis_biobb"]
__version__ = "5.2.0"
