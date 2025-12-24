"""Tests for ref laziness (I3.5: refs are lazy and cheap).

Tests that creating/transporting refs does not eagerly download bytes.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest


class TestFileRefLaziness:
    """Tests that FileRef does not fetch on construction."""

    def test_fileref_does_not_fetch_on_construct(self):
        """FileRef construction must not trigger any resolver calls."""
        from warpdatasets.refs.base import FileRef

        # Create a mock resolver that tracks calls
        mock_resolver = MagicMock()

        # Create a FileRef
        ref = FileRef(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            resolver=mock_resolver,
        )

        # Resolver should not have been called
        mock_resolver.open.assert_not_called()
        mock_resolver.read_bytes.assert_not_called()

    def test_read_bytes_calls_resolver(self):
        """read_bytes() should call the resolver."""
        from warpdatasets.refs.base import FileRef

        mock_resolver = MagicMock()
        mock_resolver.read_bytes.return_value = b"test data"

        ref = FileRef(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            resolver=mock_resolver,
        )

        # Now call read_bytes
        data = ref.read_bytes()

        # Resolver should have been called
        mock_resolver.read_bytes.assert_called_once_with(
            "raw_images", "images/test.jpg", max_bytes=None
        )
        assert data == b"test data"

    def test_open_calls_resolver(self):
        """open() should call the resolver."""
        from io import BytesIO

        from warpdatasets.refs.base import FileRef

        mock_resolver = MagicMock()
        mock_resolver.open.return_value = BytesIO(b"test data")

        ref = FileRef(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            resolver=mock_resolver,
        )

        # Now call open
        stream = ref.open()

        # Resolver should have been called
        mock_resolver.open.assert_called_once_with("raw_images", "images/test.jpg")
        assert stream.read() == b"test data"

    def test_repr_does_not_fetch(self):
        """__repr__ must not trigger resolver calls."""
        from warpdatasets.refs.base import FileRef

        mock_resolver = MagicMock()

        ref = FileRef(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            resolver=mock_resolver,
        )

        # Call repr
        repr_str = repr(ref)

        # Resolver should not have been called
        mock_resolver.open.assert_not_called()
        mock_resolver.read_bytes.assert_not_called()

        # repr should contain useful info
        assert "images/test.jpg" in repr_str
        assert "FileRef" in repr_str

    def test_info_does_not_fetch(self):
        """info() should not fetch bytes."""
        from warpdatasets.refs.base import FileRef

        mock_resolver = MagicMock()

        ref = FileRef(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            resolver=mock_resolver,
        )

        # Call info
        info = ref.info()

        # Resolver should not have been called (for bytes)
        mock_resolver.open.assert_not_called()
        mock_resolver.read_bytes.assert_not_called()

        # info should contain ref details
        assert info["artifact"] == "raw_images"
        assert info["ref"] == "images/test.jpg"


class TestImageRefLaziness:
    """Tests that ImageRef does not fetch on construction."""

    def test_imageref_does_not_fetch_on_construct(self):
        """ImageRef construction must not trigger any resolver calls."""
        from warpdatasets.refs.image import ImageRef

        mock_resolver = MagicMock()

        ref = ImageRef(
            artifact_name="raw_images",
            ref_value="images/test.jpg",
            resolver=mock_resolver,
        )

        # Resolver should not have been called
        mock_resolver.open.assert_not_called()
        mock_resolver.read_bytes.assert_not_called()

    def test_as_pil_calls_resolver(self):
        """as_pil() should call the resolver."""
        pytest.importorskip("PIL")
        from io import BytesIO

        from PIL import Image

        from warpdatasets.refs.image import ImageRef

        # Create a tiny valid PNG
        img = Image.new("RGB", (2, 2), color="red")
        buf = BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        mock_resolver = MagicMock()
        mock_resolver.read_bytes.return_value = png_bytes

        ref = ImageRef(
            artifact_name="raw_images",
            ref_value="images/test.png",
            resolver=mock_resolver,
        )

        # Now call as_pil
        pil_img = ref.as_pil()

        # Resolver should have been called
        mock_resolver.read_bytes.assert_called_once()
        assert pil_img.size == (2, 2)


class TestAudioRefLaziness:
    """Tests that AudioRef does not fetch on construction."""

    def test_audioref_does_not_fetch_on_construct(self):
        """AudioRef construction must not trigger any resolver calls."""
        from warpdatasets.refs.audio import AudioRef

        mock_resolver = MagicMock()

        ref = AudioRef(
            artifact_name="raw_audio",
            ref_value="audio/test.wav",
            resolver=mock_resolver,
        )

        # Resolver should not have been called
        mock_resolver.open.assert_not_called()
        mock_resolver.read_bytes.assert_not_called()
