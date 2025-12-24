"""Tests for spectrogram data access and visualization."""

import os
import sys
import gzip
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath('.'))

from idtap.spectrogram import SpectrogramData, SUPPORTED_COLORMAPS


# Helper function to create mock spectrogram data
def create_mock_spec_data(freq_bins=368, time_frames=1000):
    """Create mock spectrogram data for testing."""
    # Create synthetic spectrogram data (uint8)
    data = np.random.randint(0, 256, size=(freq_bins, time_frames), dtype=np.uint8)
    return data


def create_mock_compressed_data(freq_bins=368, time_frames=1000):
    """Create mock compressed spectrogram data."""
    data = create_mock_spec_data(freq_bins, time_frames)
    compressed = gzip.compress(data.tobytes())
    metadata = {"shape": [freq_bins, time_frames]}
    return compressed, metadata


class TestSpectrogramDataInit:
    """Test SpectrogramData initialization."""

    def test_init_with_valid_data(self):
        """Test initialization with valid numpy array."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_audio_id")

        assert spec.audio_id == "test_audio_id"
        assert spec.shape == (368, 1000)
        assert spec.freq_range == (75.0, 2400.0)
        assert spec.bins_per_octave == 72

    def test_init_with_custom_params(self):
        """Test initialization with custom frequency range and bins."""
        data = create_mock_spec_data()
        spec = SpectrogramData(
            data, "test_id",
            freq_range=(100.0, 2000.0),
            bins_per_octave=60
        )

        assert spec.freq_range == (100.0, 2000.0)
        assert spec.bins_per_octave == 60

    def test_init_rejects_non_numpy(self):
        """Test that non-numpy array raises TypeError."""
        with pytest.raises(TypeError, match="data must be numpy array"):
            SpectrogramData([[1, 2], [3, 4]], "test_id")

    def test_init_rejects_non_uint8(self):
        """Test that non-uint8 dtype raises TypeError."""
        data = np.random.rand(100, 200).astype(np.float32)
        with pytest.raises(TypeError, match="data must be uint8 array"):
            SpectrogramData(data, "test_id")

    def test_init_rejects_non_2d(self):
        """Test that non-2D array raises ValueError."""
        data = np.random.randint(0, 256, size=(100,), dtype=np.uint8)
        with pytest.raises(ValueError, match="data must be 2D array"):
            SpectrogramData(data, "test_id")


class TestSpectrogramDataLoading:
    """Test loading spectrogram data from server."""

    @patch('idtap.client.SwaraClient')
    def test_from_audio_id_with_client(self, mock_client_class):
        """Test loading from audio_id with provided client."""
        # Setup mock client
        mock_client = Mock()
        compressed, metadata = create_mock_compressed_data()
        mock_client.download_spectrogram_data.return_value = compressed
        mock_client.download_spectrogram_metadata.return_value = metadata

        # Load spectrogram
        spec = SpectrogramData.from_audio_id("test_audio_id", mock_client)

        # Verify calls
        mock_client.download_spectrogram_data.assert_called_once_with("test_audio_id")
        mock_client.download_spectrogram_metadata.assert_called_once_with("test_audio_id")

        # Verify data
        assert spec.audio_id == "test_audio_id"
        assert spec.shape == (368, 1000)

    @patch('idtap.client.SwaraClient')
    def test_from_audio_id_creates_client(self, mock_client_class):
        """Test that from_audio_id creates client if not provided."""
        # Setup mock
        mock_client = Mock()
        compressed, metadata = create_mock_compressed_data()
        mock_client.download_spectrogram_data.return_value = compressed
        mock_client.download_spectrogram_metadata.return_value = metadata
        mock_client_class.return_value = mock_client

        # Load without providing client
        spec = SpectrogramData.from_audio_id("test_audio_id")

        # Verify client was created
        mock_client_class.assert_called_once()
        assert spec.audio_id == "test_audio_id"

    def test_from_piece_with_audio_id(self):
        """Test loading from Piece object with audio_id."""
        # Create mock piece
        mock_piece = Mock()
        mock_piece.audio_id = "piece_audio_id"

        # Create mock client
        mock_client = Mock()
        compressed, metadata = create_mock_compressed_data()
        mock_client.download_spectrogram_data.return_value = compressed
        mock_client.download_spectrogram_metadata.return_value = metadata

        # Load from piece
        spec = SpectrogramData.from_piece(mock_piece, mock_client)

        assert spec.audio_id == "piece_audio_id"

    def test_from_piece_without_audio_id(self):
        """Test from_piece returns None when no audio_id."""
        mock_piece = Mock()
        mock_piece.audio_id = None

        spec = SpectrogramData.from_piece(mock_piece)

        assert spec is None


class TestIntensityTransform:
    """Test intensity power transformation."""

    def test_apply_intensity_linear(self):
        """Test power=1.0 returns unchanged data."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        result = spec.apply_intensity(power=1.0)

        np.testing.assert_array_equal(result, data)

    def test_apply_intensity_power_transform(self):
        """Test power transform increases contrast."""
        # Create test data with known values
        data = np.array([[100, 200]], dtype=np.uint8)
        spec = SpectrogramData(data, "test_id")

        result = spec.apply_intensity(power=2.0)

        # Higher power should make dark values darker, bright values relatively brighter
        assert result[0, 0] < data[0, 0]  # 100 gets darker
        assert result.dtype == np.uint8

    def test_apply_intensity_range_validation(self):
        """Test that power outside valid range raises ValueError."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        with pytest.raises(ValueError, match="Power must be between 1.0 and 5.0"):
            spec.apply_intensity(power=0.5)

        with pytest.raises(ValueError, match="Power must be between 1.0 and 5.0"):
            spec.apply_intensity(power=6.0)

    def test_apply_intensity_preserves_shape(self):
        """Test that intensity transform preserves array shape."""
        data = create_mock_spec_data(100, 200)
        spec = SpectrogramData(data, "test_id")

        result = spec.apply_intensity(power=2.5)

        assert result.shape == data.shape


class TestColormapApplication:
    """Test colormap application."""

    def test_apply_colormap_default(self):
        """Test colormap with default viridis."""
        data = create_mock_spec_data(10, 20)
        spec = SpectrogramData(data, "test_id")

        rgb = spec.apply_colormap()

        assert rgb.shape == (10, 20, 3)
        assert rgb.dtype == np.uint8

    def test_apply_colormap_custom(self):
        """Test colormap with custom colormap name."""
        data = create_mock_spec_data(10, 20)
        spec = SpectrogramData(data, "test_id")

        rgb = spec.apply_colormap(cmap='plasma')

        assert rgb.shape == (10, 20, 3)

    def test_apply_colormap_invalid_name(self):
        """Test that invalid colormap name raises ValueError."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        with pytest.raises(ValueError, match="Unknown colormap"):
            spec.apply_colormap(cmap='nonexistent_colormap')

    def test_apply_colormap_with_custom_data(self):
        """Test applying colormap to custom data array."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        custom_data = np.ones((50, 100), dtype=np.uint8) * 128
        rgb = spec.apply_colormap(data=custom_data)

        assert rgb.shape == (50, 100, 3)


class TestCropping:
    """Test frequency and time cropping."""

    def test_crop_frequency(self):
        """Test frequency cropping."""
        data = create_mock_spec_data(368, 1000)
        spec = SpectrogramData(data, "test_id")

        # Crop to narrower frequency range
        cropped = spec.crop_frequency(min_hz=200, max_hz=800)

        # Should have fewer frequency bins
        assert cropped.shape[0] < spec.shape[0]
        assert cropped.shape[1] == spec.shape[1]  # Time unchanged
        assert cropped.freq_range[0] >= 200
        assert cropped.freq_range[1] <= 800

    def test_crop_time(self):
        """Test time cropping."""
        data = create_mock_spec_data(368, 1000)
        spec = SpectrogramData(data, "test_id")

        # Crop to 5-10 seconds
        cropped = spec.crop_time(start_time=5.0, end_time=10.0)

        # Should have fewer time frames
        assert cropped.shape[1] < spec.shape[1]
        assert cropped.shape[0] == spec.shape[0]  # Frequency unchanged

    def test_crop_chain(self):
        """Test chaining crop operations."""
        data = create_mock_spec_data(368, 1000)
        spec = SpectrogramData(data, "test_id")

        cropped = spec.crop_frequency(min_hz=200, max_hz=800).crop_time(start_time=2.0, end_time=8.0)

        assert cropped.shape[0] < spec.shape[0]
        assert cropped.shape[1] < spec.shape[1]


class TestProperties:
    """Test spectrogram properties."""

    def test_shape_property(self):
        """Test shape property."""
        data = create_mock_spec_data(100, 500)
        spec = SpectrogramData(data, "test_id")

        assert spec.shape == (100, 500)

    def test_duration_property(self):
        """Test duration calculation."""
        data = create_mock_spec_data(368, 1000)
        spec = SpectrogramData(data, "test_id")

        duration = spec.duration
        assert duration > 0
        assert isinstance(duration, float)

    def test_time_resolution_property(self):
        """Test time resolution property."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        assert spec.time_resolution > 0
        assert spec.time_resolution < 0.1  # Should be in reasonable range

    def test_freq_bins_property(self):
        """Test frequency bins calculation."""
        data = create_mock_spec_data(368, 1000)
        spec = SpectrogramData(data, "test_id")

        freq_bins = spec.freq_bins

        assert len(freq_bins) == 368
        assert freq_bins[0] == spec.freq_range[0]  # Min frequency
        # Log spacing can slightly exceed max, allow 10% tolerance
        assert freq_bins[-1] <= spec.freq_range[1] * 1.1  # Max frequency (with tolerance)
        assert all(freq_bins[i] < freq_bins[i+1] for i in range(len(freq_bins)-1))  # Monotonic


class TestMatplotlibIntegration:
    """Test matplotlib integration methods."""

    def test_get_extent(self):
        """Test get_extent returns correct format."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        extent = spec.get_extent()

        assert len(extent) == 4
        assert extent[0] == 0  # left (start time)
        assert extent[1] == spec.duration  # right (end time)
        assert extent[2] == spec.freq_range[0]  # bottom (min freq)
        assert extent[3] == spec.freq_range[1]  # top (max freq)

    def test_get_plot_data_without_colormap(self):
        """Test get_plot_data without colormap."""
        data = create_mock_spec_data(100, 200)
        spec = SpectrogramData(data, "test_id")

        plot_data, extent = spec.get_plot_data(power=2.0, apply_cmap=False)

        assert plot_data.shape == (100, 200)
        assert plot_data.dtype == np.uint8
        assert len(extent) == 4

    def test_get_plot_data_with_colormap(self):
        """Test get_plot_data with colormap applied."""
        data = create_mock_spec_data(100, 200)
        spec = SpectrogramData(data, "test_id")

        plot_data, extent = spec.get_plot_data(power=1.5, apply_cmap=True, cmap='plasma')

        assert plot_data.shape == (100, 200, 3)  # RGB
        assert plot_data.dtype == np.uint8

    @patch('matplotlib.pyplot.subplots')
    def test_plot_on_axis(self, mock_subplots):
        """Test plotting on matplotlib axis."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        # Create mock axis
        mock_ax = MagicMock()
        mock_im = MagicMock()
        mock_ax.imshow.return_value = mock_im

        # Plot on axis
        im = spec.plot_on_axis(mock_ax, power=2.0, cmap='viridis', alpha=0.7)

        # Verify imshow was called
        mock_ax.imshow.assert_called_once()
        call_kwargs = mock_ax.imshow.call_args[1]
        assert call_kwargs['cmap'] == 'viridis'
        assert call_kwargs['alpha'] == 0.7
        assert call_kwargs['origin'] == 'lower'
        assert call_kwargs['aspect'] == 'auto'


class TestImageGeneration:
    """Test image generation methods."""

    def test_to_image_basic(self):
        """Test basic image generation."""
        data = create_mock_spec_data(100, 200)
        spec = SpectrogramData(data, "test_id")

        img = spec.to_image()

        assert img.mode == 'RGB'
        assert img.size == (200, 100)  # PIL uses (width, height)

    def test_to_image_with_resize(self):
        """Test image generation with resizing."""
        data = create_mock_spec_data(100, 200)
        spec = SpectrogramData(data, "test_id")

        img = spec.to_image(width=400, height=200)

        assert img.size == (400, 200)

    def test_to_image_with_power(self):
        """Test image generation with power transform."""
        data = create_mock_spec_data(100, 200)
        spec = SpectrogramData(data, "test_id")

        img = spec.to_image(power=2.5, cmap='plasma')

        assert img.mode == 'RGB'

    @patch('matplotlib.pyplot.colorbar')
    @patch('matplotlib.pyplot.subplots')
    def test_to_matplotlib(self, mock_subplots, mock_colorbar):
        """Test matplotlib figure generation."""
        data = create_mock_spec_data()
        spec = SpectrogramData(data, "test_id")

        # Setup mocks
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_im = MagicMock()
        mock_ax.imshow.return_value = mock_im
        mock_subplots.return_value = (mock_fig, mock_ax)

        fig = spec.to_matplotlib(power=2.0, cmap='viridis', show_colorbar=True)

        # Verify figure was created
        mock_subplots.assert_called_once()
        mock_ax.imshow.assert_called_once()
        mock_colorbar.assert_called_once()

    def test_save(self, tmp_path):
        """Test saving spectrogram to file."""
        data = create_mock_spec_data(50, 100)
        spec = SpectrogramData(data, "test_id")

        filepath = tmp_path / "test_spec.png"
        spec.save(str(filepath), power=1.5, cmap='viridis')

        assert filepath.exists()


class TestConstants:
    """Test module-level constants."""

    def test_supported_colormaps(self):
        """Test that SUPPORTED_COLORMAPS list is defined."""
        assert isinstance(SUPPORTED_COLORMAPS, list)
        assert len(SUPPORTED_COLORMAPS) > 0
        assert 'viridis' in SUPPORTED_COLORMAPS
        assert 'plasma' in SUPPORTED_COLORMAPS

    def test_default_freq_range(self):
        """Test default frequency range constant."""
        assert SpectrogramData.DEFAULT_FREQ_RANGE == (75.0, 2400.0)

    def test_default_bins_per_octave(self):
        """Test default bins per octave constant."""
        assert SpectrogramData.DEFAULT_BINS_PER_OCTAVE == 72
