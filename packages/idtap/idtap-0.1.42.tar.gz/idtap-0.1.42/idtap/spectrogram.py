"""Spectrogram data access and visualization for IDTAP audio recordings."""

from __future__ import annotations

import gzip
import numpy as np
from typing import Optional, Tuple, Dict, Any, List, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .client import SwaraClient
    from .classes.piece import Piece
    from PIL import Image
    from matplotlib.figure import Figure
    from matplotlib.axes import Axes
    from matplotlib.image import AxesImage


# Supported matplotlib colormaps (matches web app functionality)
SUPPORTED_COLORMAPS = [
    # Perceptually uniform
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'turbo',
    # Sequential
    'Blues', 'Greens', 'Reds', 'Oranges', 'Purples', 'Greys',
    'BuGn', 'BuPu', 'GnBu', 'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'RdPu',
    'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd',
    # Diverging
    'RdBu', 'BrBG', 'PRGn', 'PiYG', 'PuOr', 'RdGy', 'RdYlBu', 'RdYlGn', 'Spectral',
    # Cyclical
    'rainbow', 'hsv',
    # Temperature
    'cool', 'warm', 'coolwarm'
]


class SpectrogramData:
    """Constant-Q spectrogram data for IDTAP audio recordings.

    This class provides access to the same high-quality constant-Q transform
    spectrograms used in the IDTAP web application, with tools for visualization,
    manipulation, and integration with matplotlib-based research workflows.

    Attributes:
        audio_id: IDTAP audio recording ID
        freq_range: Tuple of (min_hz, max_hz) for the frequency range
        bins_per_octave: Number of frequency bins per octave
    """

    # Constants matching web app implementation
    DEFAULT_FREQ_RANGE = (75.0, 2400.0)  # Hz
    DEFAULT_BINS_PER_OCTAVE = 72
    DEFAULT_TIME_RESOLUTION = 0.015080  # seconds per frame (fallback when DB unavailable)

    def __init__(self, data: np.ndarray, audio_id: str,
                 freq_range: Tuple[float, float] = DEFAULT_FREQ_RANGE,
                 bins_per_octave: int = DEFAULT_BINS_PER_OCTAVE,
                 time_resolution: Optional[float] = None):
        """Initialize SpectrogramData with raw data.

        Args:
            data: Raw uint8 spectrogram array [freq_bins, time_frames]
            audio_id: Audio recording ID
            freq_range: Frequency range (min_hz, max_hz)
            bins_per_octave: Number of frequency bins per octave
            time_resolution: Time resolution in seconds per frame (optional)
                           If None, uses DEFAULT_TIME_RESOLUTION fallback
        """
        if not isinstance(data, np.ndarray):
            raise TypeError(f"data must be numpy array, got {type(data)}")
        if data.dtype != np.uint8:
            raise TypeError(f"data must be uint8 array, got {data.dtype}")
        if data.ndim != 2:
            raise ValueError(f"data must be 2D array, got {data.ndim}D")

        self._data = data
        self.audio_id = audio_id
        self.freq_range = freq_range
        self.bins_per_octave = bins_per_octave
        self._time_resolution = time_resolution if time_resolution is not None else self.DEFAULT_TIME_RESOLUTION

    @classmethod
    def from_audio_id(cls, audio_id: str, client: Optional['SwaraClient'] = None) -> 'SpectrogramData':
        """Download and load spectrogram data from audio ID.

        Fetches compressed spectrogram data from https://swara.studio/spec_data/{audio_id}/
        and calculates accurate time_resolution from the audio recording duration in the database.

        Args:
            audio_id: IDTAP audio recording ID
            client: Optional SwaraClient instance (creates one if not provided)

        Returns:
            SpectrogramData instance with accurate time_resolution

        Raises:
            requests.HTTPError: If spectrogram data doesn't exist or download fails
        """
        # Create client if not provided
        if client is None:
            from .client import SwaraClient
            client = SwaraClient()

        # Download compressed data and metadata
        compressed_data = client.download_spectrogram_data(audio_id)
        metadata = client.download_spectrogram_metadata(audio_id)

        # Decompress data
        decompressed = gzip.decompress(compressed_data)

        # Reshape to numpy array
        shape = tuple(metadata['shape'])  # [freq_bins, time_frames]
        data = np.frombuffer(decompressed, dtype=np.uint8).reshape(shape)

        # Flip frequency axis so row 0 = lowest frequency (matches freq_bins ordering)
        # Server data has row 0 = highest frequency, but we want row 0 = lowest
        data = np.flipud(data)

        # Get exact audio duration from recording database
        time_resolution = None
        try:
            recording = client.get_audio_recording(audio_id)
            audio_duration = recording['duration']
            time_frames = shape[1]
            time_resolution = audio_duration / time_frames
        except Exception:
            # Fallback to DEFAULT_TIME_RESOLUTION if recording not found
            # This will be handled by __init__
            pass

        return cls(data, audio_id, time_resolution=time_resolution)

    @classmethod
    def from_piece(cls, piece: 'Piece', client: Optional['SwaraClient'] = None) -> Optional['SpectrogramData']:
        """Load spectrogram data from a Piece object.

        Args:
            piece: Piece object with audio_id attribute
            client: Optional SwaraClient instance

        Returns:
            SpectrogramData instance, or None if piece has no audio_id
        """
        if not hasattr(piece, 'audio_id') or piece.audio_id is None:
            return None
        return cls.from_audio_id(piece.audio_id, client)

    def apply_intensity(self, power: float = 1.0) -> np.ndarray:
        """Apply power-law intensity transformation (matches web app behavior).

        This transformation enhances visual contrast in the spectrogram.
        Formula: output = (input^power / 255^power) * 255

        Args:
            power: Exponent for power transform (1.0-5.0)
                  1.0 = linear (no change)
                  >1.0 = increased contrast

        Returns:
            Transformed uint8 array with same shape as input

        Raises:
            ValueError: If power is outside valid range [1.0, 5.0]
        """
        if not 1.0 <= power <= 5.0:
            raise ValueError(f"Power must be between 1.0 and 5.0, got {power}")

        if power == 1.0:
            return self._data.copy()

        # Vectorized power transform
        # Convert to float for precision, apply transform, convert back
        data_float = self._data.astype(np.float32)
        transformed = np.power(data_float / 255.0, power) * 255.0
        return np.clip(transformed, 0, 255).astype(np.uint8)

    def apply_colormap(self, data: Optional[np.ndarray] = None,
                      cmap: str = 'viridis') -> np.ndarray:
        """Apply matplotlib colormap to spectrogram data.

        Args:
            data: Input spectrogram data (if None, uses self._data)
            cmap: Matplotlib colormap name (see SUPPORTED_COLORMAPS)

        Returns:
            RGB array of shape [height, width, 3] with uint8 values

        Raises:
            ValueError: If colormap name is not recognized
        """
        import matplotlib.pyplot as plt

        if data is None:
            data = self._data

        # Get matplotlib colormap
        try:
            colormap = plt.get_cmap(cmap)
        except ValueError:
            raise ValueError(
                f"Unknown colormap: '{cmap}'. "
                f"See SUPPORTED_COLORMAPS for valid options."
            )

        # Apply colormap (handles normalization automatically)
        # Returns RGBA array, we take only RGB channels
        colored = colormap(data / 255.0)  # Normalize to [0, 1]
        rgb = (colored[:, :, :3] * 255).astype(np.uint8)

        return rgb

    def crop_frequency(self, min_hz: Optional[float] = None,
                      max_hz: Optional[float] = None) -> 'SpectrogramData':
        """Crop spectrogram to a specific frequency range.

        Args:
            min_hz: Minimum frequency (Hz), defaults to original min
            max_hz: Maximum frequency (Hz), defaults to original max

        Returns:
            New SpectrogramData instance with cropped data
        """
        if min_hz is None:
            min_hz = self.freq_range[0]
        if max_hz is None:
            max_hz = self.freq_range[1]

        # Calculate bin indices for frequency range
        freq_bins = self.freq_bins

        # Find closest bin indices
        min_idx = np.searchsorted(freq_bins, min_hz)
        max_idx = np.searchsorted(freq_bins, max_hz)

        # Ensure valid range
        min_idx = max(0, min_idx)
        max_idx = min(len(freq_bins), max_idx)

        # Crop data
        cropped_data = self._data[min_idx:max_idx, :]

        # Create new instance with updated frequency range
        return SpectrogramData(
            cropped_data,
            self.audio_id,
            freq_range=(freq_bins[min_idx], freq_bins[max_idx - 1] if max_idx > min_idx else freq_bins[min_idx]),
            bins_per_octave=self.bins_per_octave,
            time_resolution=self._time_resolution
        )

    def crop_time(self, start_time: Optional[float] = None,
                 end_time: Optional[float] = None) -> 'SpectrogramData':
        """Crop spectrogram to a specific time range.

        Args:
            start_time: Start time in seconds (defaults to 0)
            end_time: End time in seconds (defaults to duration)

        Returns:
            New SpectrogramData instance with cropped data
        """
        if start_time is None:
            start_time = 0.0
        if end_time is None:
            end_time = self.duration

        # Convert times to frame indices
        start_frame = int(start_time / self.time_resolution)
        end_frame = int(end_time / self.time_resolution)

        # Ensure valid range
        start_frame = max(0, start_frame)
        end_frame = min(self.shape[1], end_frame)

        # Crop data
        cropped_data = self._data[:, start_frame:end_frame]

        return SpectrogramData(
            cropped_data,
            self.audio_id,
            freq_range=self.freq_range,
            bins_per_octave=self.bins_per_octave,
            time_resolution=self._time_resolution
        )

    def get_extent(self) -> List[float]:
        """Get matplotlib extent for this spectrogram.

        Returns:
            [left, right, bottom, top] = [0, duration, min_freq, max_freq]
            This is the format matplotlib imshow() expects for extent parameter.
        """
        return [0, self.duration, self.freq_range[0], self.freq_range[1]]

    def get_plot_data(self, power: float = 1.0,
                     apply_cmap: bool = False,
                     cmap: str = 'viridis') -> Tuple[np.ndarray, List[float]]:
        """Get processed spectrogram data and extent for matplotlib plotting.

        Use this when you need direct control over the plotting process,
        or when you want to manipulate the data before plotting.

        Args:
            power: Intensity power transform (1.0-5.0)
            apply_cmap: If True, returns RGB array; if False, returns grayscale uint8
            cmap: Colormap name (only used if apply_cmap=True)

        Returns:
            Tuple of (data, extent):
                - data: Processed spectrogram array
                       If apply_cmap=False: uint8 array [freq_bins, time_frames]
                       If apply_cmap=True: RGB uint8 array [freq_bins, time_frames, 3]
                - extent: [left, right, bottom, top] for matplotlib imshow()

        Example:
            >>> # Low-level control
            >>> data, extent = spec.get_plot_data(power=2.5)
            >>> fig, ax = plt.subplots()
            >>> im = ax.imshow(data, extent=extent, aspect='auto',
            ...                origin='lower', cmap='magma')
        """
        # Apply intensity transform
        transformed = self.apply_intensity(power)

        # Optionally apply colormap
        if apply_cmap:
            data = self.apply_colormap(transformed, cmap)
        else:
            data = transformed

        # Get extent
        extent = self.get_extent()

        return data, extent

    def plot_on_axis(self, ax: 'Axes',
                    power: float = 1.0,
                    cmap: str = 'viridis',
                    alpha: float = 1.0,
                    zorder: int = 0,
                    log_freq: bool = True,
                    **imshow_kwargs) -> 'AxesImage':
        """Plot spectrogram on an existing matplotlib axis (for overlays).

        This is the primary method for using spectrograms as underlays in
        custom matplotlib visualizations.

        Args:
            ax: Matplotlib axis to plot on
            power: Intensity power transform (1.0-5.0)
            cmap: Matplotlib colormap name
            alpha: Transparency (0.0-1.0), useful for subtle underlays
            zorder: Drawing order (0 = background, higher = foreground)
            log_freq: Whether to use logarithmic frequency scale (default: True)
            **imshow_kwargs: Additional arguments passed to ax.imshow()

        Returns:
            AxesImage object (useful for adding colorbars)

        Example:
            >>> fig, ax = plt.subplots(figsize=(12, 6))
            >>> im = spec.plot_on_axis(ax, power=2.0, cmap='viridis', alpha=0.7)
            >>> ax.plot(times, pitch_contour, 'r-', linewidth=2)  # Overlay pitch
            >>> ax.set_xlabel('Time (s)')
            >>> ax.set_ylabel('Frequency (Hz)')
            >>> plt.colorbar(im, ax=ax, label='Intensity')
        """
        # Get processed data and extent
        data, extent = self.get_plot_data(power=power, apply_cmap=False)

        # Plot on provided axis
        im = ax.imshow(
            data,
            extent=extent,
            aspect='auto',
            origin='lower',
            cmap=cmap,
            alpha=alpha,
            zorder=zorder,
            **imshow_kwargs
        )

        # Set log scale for frequency axis (CQT is log-spaced)
        if log_freq:
            ax.set_yscale('log')
            # Set reasonable y-axis limits
            ax.set_ylim(self.freq_range[0], self.freq_range[1])

        return im

    def to_image(self, width: Optional[int] = None,
                height: Optional[int] = None,
                power: float = 1.0,
                cmap: str = 'viridis',
                interpolation: str = 'bilinear') -> 'Image':
        """Generate PIL Image with full processing pipeline.

        Args:
            width: Output width in pixels (default: original width)
            height: Output height in pixels (default: original height)
            power: Intensity power transform (1.0-5.0)
            cmap: Matplotlib colormap name
            interpolation: Resampling method ('bilinear', 'nearest', 'lanczos', etc.)
                          See PIL.Image.Resampling for all options

        Returns:
            PIL Image in RGB mode
        """
        from PIL import Image

        # Apply intensity transform
        transformed = self.apply_intensity(power)

        # Apply colormap
        rgb = self.apply_colormap(transformed, cmap)

        # Create PIL Image
        img = Image.fromarray(rgb, mode='RGB')

        # Resize if requested
        if width or height:
            # Determine final size
            orig_height, orig_width = rgb.shape[:2]

            if width and height:
                new_size = (width, height)
            elif width:
                # Keep aspect ratio
                ratio = width / orig_width
                new_size = (width, int(orig_height * ratio))
            else:  # height only
                ratio = height / orig_height
                new_size = (int(orig_width * ratio), height)

            # Map interpolation string to PIL constant
            from PIL import Image as PILImage
            resample_map = {
                'nearest': PILImage.Resampling.NEAREST,
                'bilinear': PILImage.Resampling.BILINEAR,
                'bicubic': PILImage.Resampling.BICUBIC,
                'lanczos': PILImage.Resampling.LANCZOS,
            }
            resample = resample_map.get(interpolation.lower(), PILImage.Resampling.BILINEAR)

            img = img.resize(new_size, resample=resample)

        return img

    def to_matplotlib(self, figsize: Tuple[float, float] = (12, 6),
                     power: float = 1.0,
                     cmap: str = 'viridis',
                     show_colorbar: bool = True,
                     show_axes: bool = True,
                     log_freq: bool = True) -> 'Figure':
        """Generate standalone matplotlib Figure for publication.

        Use this for quick visualization. For overlays and custom plots,
        use plot_on_axis() instead.

        Args:
            figsize: Figure size (width, height) in inches
            power: Intensity power transform (1.0-5.0)
            cmap: Matplotlib colormap name
            show_colorbar: Whether to show colorbar
            show_axes: Whether to show frequency/time axis labels
            log_freq: Whether to use logarithmic frequency scale (default: True)

        Returns:
            Matplotlib Figure object
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        # Use plot_on_axis internally
        im = self.plot_on_axis(ax, power=power, cmap=cmap, log_freq=log_freq)

        if show_axes:
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Frequency (Hz)')
        else:
            ax.axis('off')

        if show_colorbar:
            plt.colorbar(im, ax=ax, label='Intensity')

        return fig

    def save(self, filepath: str, width: Optional[int] = None,
            height: Optional[int] = None, power: float = 1.0,
            cmap: str = 'viridis', format: Optional[str] = None,
            **kwargs):
        """Save spectrogram as image file.

        Args:
            filepath: Output file path
            width: Output width in pixels (default: original)
            height: Output height in pixels (default: original)
            power: Intensity power transform (1.0-5.0)
            cmap: Matplotlib colormap name
            format: Image format ('png', 'jpg', 'webp', etc.)
                   Auto-detected from filepath extension if not provided
            **kwargs: Additional arguments passed to PIL Image.save()
        """
        img = self.to_image(width, height, power, cmap)

        # Auto-detect format from extension if not provided
        if format is None:
            suffix = Path(filepath).suffix
            if suffix:
                format = suffix[1:]  # Remove leading dot

        img.save(filepath, format=format, **kwargs)

    @property
    def shape(self) -> Tuple[int, int]:
        """Data shape: (frequency_bins, time_frames)."""
        return self._data.shape

    @property
    def duration(self) -> float:
        """Audio duration in seconds (estimated from time frames)."""
        return self.shape[1] * self.time_resolution

    @property
    def time_resolution(self) -> float:
        """Time resolution in seconds per frame.

        Calculated from audio recording duration in database (when available).
        Falls back to DEFAULT_TIME_RESOLUTION if recording metadata unavailable.

        Note: Spectrograms always cover the full audio recording, even when
        the associated Piece transcribes only an excerpt.
        """
        return self._time_resolution

    @property
    def freq_bins(self) -> np.ndarray:
        """Array of frequency values (Hz) for each bin.

        Calculated from bins_per_octave and freq_range using log spacing.
        """
        n_bins = self.shape[0]

        # Calculate frequencies using constant-Q log spacing
        # freq = min_freq * 2^(bin / bins_per_octave)
        min_freq = self.freq_range[0]
        bin_indices = np.arange(n_bins)
        frequencies = min_freq * np.power(2, bin_indices / self.bins_per_octave)

        return frequencies
