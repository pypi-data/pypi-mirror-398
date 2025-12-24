"""Data ingestors for warpdatasets.

Provides a simple way to convert raw data (image folders, CSVs, etc.)
into warpdatasets format without writing pandas code.

Example:
    >>> import warpdatasets as wd
    >>> wd.ingest.imagefolder(
    ...     "local/scientific_forgery",
    ...     images_dir="~/data/train_images",
    ...     labels="from-parent",
    ...     pairs={"masks": ("~/data/train_masks", "{id}.npy")},
    ... )
"""

from warpdatasets.ingest.base import (
    Ingestor,
    IngestPlan,
    ArtifactSpec,
    BindingSpec,
    MediaType,
    IdStrategy,
    LabelStrategy,
    MEDIA_TYPE_MAP,
)
from warpdatasets.ingest.imagefolder import (
    ImageFolderIngestor,
    PairSpec,
    imagefolder,
)
from warpdatasets.ingest.paired import (
    PairedIngestor,
    SourceSpec,
    paired,
)
from warpdatasets.ingest.csv_files import (
    CSVFilesIngestor,
    FileColumnSpec,
    csv_files,
)

__all__ = [
    # Base
    "Ingestor",
    "IngestPlan",
    "ArtifactSpec",
    "BindingSpec",
    "MediaType",
    "IdStrategy",
    "LabelStrategy",
    "MEDIA_TYPE_MAP",
    # ImageFolder
    "ImageFolderIngestor",
    "PairSpec",
    "imagefolder",
    # Paired
    "PairedIngestor",
    "SourceSpec",
    "paired",
    # CSV+Files
    "CSVFilesIngestor",
    "FileColumnSpec",
    "csv_files",
]
