"""ImageFolder ingestor - ImageNet-style directory trees.

Handles datasets structured as:
    images/
        class_a/
            img001.jpg
            img002.jpg
        class_b/
            img003.jpg

Or flat directories:
    images/
        img001.jpg
        img002.jpg
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from warpdatasets.ingest.base import (
    Ingestor,
    IngestPlan,
    ArtifactSpec,
    BindingSpec,
    MediaType,
    IdStrategy,
    LabelStrategy,
    compute_id,
    compute_label,
)


# Common image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


@dataclass
class PairSpec:
    """Specification for a paired artifact (masks, annotations, etc.)."""

    name: str
    source_dir: Path
    pattern: str  # e.g., "{id}.npy" or "{id}_mask.png"
    media_type: MediaType = "file"
    optional: bool = True  # Allow missing pairs


@dataclass
class ImageFolderIngestor(Ingestor):
    """Ingest ImageNet-style directory structures.

    Example usage:
        ingestor = ImageFolderIngestor(
            images_dir=Path("train_images"),
            labels="from-parent",
            pairs=[
                PairSpec("masks", Path("train_masks"), "{id}.npy"),
            ],
        )
        plan = ingestor.plan()
        ingestor.run("local/my_dataset")
    """

    images_dir: Path
    labels: LabelStrategy = "from-parent"
    id_strategy: IdStrategy = "stem"
    pairs: list[PairSpec] = field(default_factory=list)
    extensions: set[str] = field(default_factory=lambda: IMAGE_EXTENSIONS.copy())
    recursive: bool = True

    @property
    def name(self) -> str:
        return "imagefolder"

    def _find_images(self) -> list[Path]:
        """Find all image files in the source directory."""
        images = []
        if self.recursive:
            for ext in self.extensions:
                images.extend(self.images_dir.rglob(f"*{ext}"))
                images.extend(self.images_dir.rglob(f"*{ext.upper()}"))
        else:
            for ext in self.extensions:
                images.extend(self.images_dir.glob(f"*{ext}"))
                images.extend(self.images_dir.glob(f"*{ext.upper()}"))
        return sorted(set(images))

    def _resolve_pair(self, pair: PairSpec, img_id: str) -> str | None:
        """Resolve a paired file path.

        Args:
            pair: Pair specification
            img_id: Image ID to match

        Returns:
            Relative path to paired file, or None if not found
        """
        # Replace {id} placeholder in pattern
        filename = pair.pattern.replace("{id}", img_id)
        full_path = pair.source_dir / filename

        if full_path.exists():
            return filename
        elif pair.optional:
            return None
        else:
            raise FileNotFoundError(f"Required pair not found: {full_path}")

    def plan(self) -> IngestPlan:
        """Scan images and produce an ingest plan."""
        images = self._find_images()

        if not images:
            raise ValueError(f"No images found in {self.images_dir}")

        rows = []
        for img_path in images:
            img_id = compute_id(img_path, self.images_dir, self.id_strategy)
            label = compute_label(img_path, self.images_dir, self.labels)

            # Compute relative path for image ref
            rel_path = img_path.relative_to(self.images_dir)

            row: dict[str, Any] = {
                "id": img_id,
                "image_ref": str(rel_path),
            }

            if label is not None:
                row["label"] = label

            # Resolve pairs
            for pair in self.pairs:
                col_name = f"{pair.name}_ref"
                row[col_name] = self._resolve_pair(pair, img_id)

            rows.append(row)

        # Build artifact specs
        artifacts = [
            ArtifactSpec(
                name="images",
                source_dir=self.images_dir,
                media_type="image",
            )
        ]
        for pair in self.pairs:
            artifacts.append(ArtifactSpec(
                name=pair.name,
                source_dir=pair.source_dir,
                media_type=pair.media_type,
            ))

        # Build binding specs
        bindings = [
            BindingSpec(
                table="main",
                column="image_ref",
                artifact="images",
                media_type="image",
                ref_type="file_path",
            )
        ]
        for pair in self.pairs:
            bindings.append(BindingSpec(
                table="main",
                column=f"{pair.name}_ref",
                artifact=pair.name,
                media_type=pair.media_type,
                ref_type="file_path",
            ))

        return IngestPlan(
            table_data=rows,
            artifacts=artifacts,
            bindings=bindings,
            meta={
                "ingestor": self.name,
                "source_dir": str(self.images_dir),
                "labels": self.labels,
                "id_strategy": self.id_strategy,
            },
        )


def imagefolder(
    dataset_id: str,
    images_dir: str | Path,
    *,
    labels: LabelStrategy = "from-parent",
    id_strategy: IdStrategy = "stem",
    pairs: dict[str, tuple[str | Path, str]] | None = None,
    media_types: dict[str, MediaType] | None = None,
    extensions: set[str] | None = None,
    recursive: bool = True,
    workspace_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    progress: bool = True,
    dry_run: bool = False,
) -> IngestPlan | Path:
    """Ingest an ImageNet-style directory as a warpdatasets dataset.

    Args:
        dataset_id: Target dataset ID (e.g., "local/scientific_forgery")
        images_dir: Path to images directory
        labels: Label strategy ("from-parent" or "none")
        id_strategy: ID strategy ("stem", "relative", or "hash")
        pairs: Dict of name -> (dir, pattern) for paired files
            e.g., {"masks": ("train_masks", "{id}.npy")}
        media_types: Dict of artifact name -> media type
            e.g., {"masks": "file"}
        extensions: Set of valid image extensions (default: common image types)
        recursive: Search subdirectories
        workspace_root: Workspace root directory
        output_dir: Where to write parquet
        progress: Show progress output
        dry_run: Only return plan without executing

    Returns:
        IngestPlan if dry_run=True, else Path to manifest

    Example:
        >>> import warpdatasets as wd
        >>> wd.ingest.imagefolder(
        ...     "local/scientific_forgery",
        ...     images_dir="~/data/train_images",
        ...     labels="from-parent",
        ...     pairs={"masks": ("~/data/train_masks", "{id}.npy")},
        ... )
    """
    images_dir = Path(images_dir).expanduser().resolve()

    # Build pair specs
    pair_specs = []
    if pairs:
        media_types = media_types or {}
        for name, (pair_dir, pattern) in pairs.items():
            pair_specs.append(PairSpec(
                name=name,
                source_dir=Path(pair_dir).expanduser().resolve(),
                pattern=pattern,
                media_type=media_types.get(name, "file"),
            ))

    ingestor = ImageFolderIngestor(
        images_dir=images_dir,
        labels=labels,
        id_strategy=id_strategy,
        pairs=pair_specs,
        extensions=extensions or IMAGE_EXTENSIONS.copy(),
        recursive=recursive,
    )

    plan = ingestor.plan()

    if dry_run:
        return plan

    return ingestor.run(
        dataset_id=dataset_id,
        output_dir=Path(output_dir).expanduser() if output_dir else None,
        workspace_root=Path(workspace_root).expanduser() if workspace_root else None,
        progress=progress,
    )
