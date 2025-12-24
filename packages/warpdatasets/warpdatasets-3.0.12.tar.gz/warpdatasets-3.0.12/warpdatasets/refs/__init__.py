"""Typed reference objects for raw data access.

Provides FileRef, ImageRef, AudioRef for lazy, remote-first raw data access.
"""

from warpdatasets.refs.base import FileRef
from warpdatasets.refs.image import ImageRef
from warpdatasets.refs.audio import AudioRef
from warpdatasets.refs.factory import create_ref

__all__ = ["FileRef", "ImageRef", "AudioRef", "create_ref"]
