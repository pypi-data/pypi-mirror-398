"""Tests for ref factory (choosing ref class based on binding kind).

Tests that the factory correctly selects FileRef/ImageRef/AudioRef
based on media_type in bindings.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestRefFactorySelection:
    """Tests for ref class selection based on media_type."""

    def test_media_type_image_returns_imageref(self):
        """media_type='image' should return ImageRef."""
        from warpdatasets.refs.factory import create_ref
        from warpdatasets.refs.image import ImageRef

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            media_type="image",
            resolver=mock_resolver,
        )

        assert isinstance(ref, ImageRef)

    def test_media_type_audio_returns_audioref(self):
        """media_type='audio' should return AudioRef."""
        from warpdatasets.refs.audio import AudioRef
        from warpdatasets.refs.factory import create_ref

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_audio",
            ref_value="audio/test.wav",
            media_type="audio",
            resolver=mock_resolver,
        )

        assert isinstance(ref, AudioRef)

    def test_media_type_file_returns_fileref(self):
        """media_type='file' should return FileRef (not subclass)."""
        from warpdatasets.refs.base import FileRef
        from warpdatasets.refs.factory import create_ref
        from warpdatasets.refs.image import ImageRef

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_data",
            ref_value="data/test.bin",
            media_type="file",
            resolver=mock_resolver,
        )

        assert isinstance(ref, FileRef)
        assert not isinstance(ref, ImageRef)

    def test_unknown_media_type_returns_fileref(self):
        """Unknown media_type should fall back to FileRef."""
        from warpdatasets.refs.base import FileRef
        from warpdatasets.refs.factory import create_ref

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_data",
            ref_value="data/test.bin",
            media_type="unknown",
            resolver=mock_resolver,
        )

        assert isinstance(ref, FileRef)

    def test_none_value_returns_none(self):
        """None ref_value should return None."""
        from warpdatasets.refs.factory import create_ref

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_images",
            ref_value=None,
            media_type="image",
            resolver=mock_resolver,
        )

        assert ref is None

    def test_empty_string_returns_none(self):
        """Empty string ref_value should return None."""
        from warpdatasets.refs.factory import create_ref

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_images",
            ref_value="",
            media_type="image",
            resolver=mock_resolver,
        )

        assert ref is None


class TestRefFactoryPreservesInfo:
    """Tests that factory preserves ref info correctly."""

    def test_imageref_preserves_artifact_name(self):
        """ImageRef should preserve artifact name."""
        from warpdatasets.refs.factory import create_ref

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            media_type="image",
            resolver=mock_resolver,
        )

        assert ref.artifact_name == "raw_images"
        assert ref.ref_value == "images/test.jpg"

    def test_audioref_preserves_artifact_name(self):
        """AudioRef should preserve artifact name."""
        from warpdatasets.refs.factory import create_ref

        mock_resolver = MagicMock()

        ref = create_ref(
            artifact_name="raw_audio",
            ref_value="audio/test.wav",
            media_type="audio",
            resolver=mock_resolver,
        )

        assert ref.artifact_name == "raw_audio"
        assert ref.ref_value == "audio/test.wav"
