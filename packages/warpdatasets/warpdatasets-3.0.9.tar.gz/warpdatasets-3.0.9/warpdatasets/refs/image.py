"""ImageRef - typed reference for image files.

Provides lazy, remote-first image access with optional PIL/numpy conversion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from warpdatasets.refs.base import FileRef

if TYPE_CHECKING:
    import numpy as np
    from PIL import Image as PILImage


class ImageRef(FileRef):
    """A resolvable reference to an image file.

    Extends FileRef with image-specific methods like as_pil() and as_numpy().
    """

    def as_pil(self) -> "PILImage.Image":
        """Load the image as a PIL Image.

        Returns:
            PIL Image object.

        Raises:
            ImportError: If Pillow is not installed.
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError(
                "Pillow is required for as_pil(). Install with: pip install Pillow"
            )

        from io import BytesIO

        data = self.read_bytes()
        return Image.open(BytesIO(data))

    def as_numpy(self) -> "np.ndarray":
        """Load the image as a numpy array.

        Returns:
            Numpy array with shape (H, W, C) or (H, W).

        Raises:
            ImportError: If Pillow or numpy is not installed.
        """
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "numpy is required for as_numpy(). Install with: pip install numpy"
            )

        img = self.as_pil()
        return np.array(img)
