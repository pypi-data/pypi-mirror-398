"""AudioRef - typed reference for audio files.

Provides lazy, remote-first audio access (minimal in Phase 3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from warpdatasets.refs.base import FileRef

if TYPE_CHECKING:
    import numpy as np


class AudioRef(FileRef):
    """A resolvable reference to an audio file.

    Extends FileRef with audio-specific methods (minimal in Phase 3).
    """

    def as_array(self) -> tuple["np.ndarray", int]:
        """Load the audio as a numpy array.

        Returns:
            Tuple of (samples array, sample_rate).

        Raises:
            ImportError: If soundfile is not installed.
        """
        try:
            import soundfile as sf
        except ImportError:
            raise ImportError(
                "soundfile is required for as_array(). "
                "Install with: pip install soundfile"
            )

        from io import BytesIO

        data = self.read_bytes()
        samples, sample_rate = sf.read(BytesIO(data))
        return samples, sample_rate
