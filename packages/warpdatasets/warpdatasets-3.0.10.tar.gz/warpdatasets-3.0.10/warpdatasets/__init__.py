"""WarpDatasets v3 - Remote-first dataset library for ML training."""

from warpdatasets.api.dataset import Dataset, dataset, from_manifest
from warpdatasets import ingest
from warpdatasets import compat

__version__ = "3.0.10"
__all__ = ["dataset", "Dataset", "from_manifest", "ingest", "compat", "__version__"]
