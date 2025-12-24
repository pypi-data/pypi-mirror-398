"""WarpDatasets v3 - Remote-first dataset library for ML training."""

from warpdatasets.api.dataset import Dataset, dataset
from warpdatasets import ingest

__version__ = "3.0.4"
__all__ = ["dataset", "Dataset", "ingest", "__version__"]
