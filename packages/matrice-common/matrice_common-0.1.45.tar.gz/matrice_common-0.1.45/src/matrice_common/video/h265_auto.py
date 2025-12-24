"""
Platform-aware H.265 encoder/decoder that automatically selects the best implementation.

Usage:
    from matrice_common.video.h265_auto import H265FrameEncoder, H265FrameDecoder

The module will automatically use:
- Persistent subprocess implementation on Linux (high performance)
- Per-frame subprocess implementation on Windows (reliable)
"""
import platform
import logging

logger = logging.getLogger(__name__)

# Detect platform
IS_LINUX = platform.system() == 'Linux'

if IS_LINUX:
    try:
        from .h265_processor_linux import (
            H265PersistentFrameEncoder as H265FrameEncoder,
            H265PersistentFrameDecoder as H265FrameDecoder
        )
        logger.info("Using Linux-optimized persistent subprocess H.265 encoder/decoder")
    except ImportError as e:
        logger.warning(f"Failed to import Linux-optimized version: {e}, falling back to standard")
        from .h265_processor import H265FrameEncoder, H265FrameDecoder
else:
    # Windows or other platforms - use reliable per-frame implementation
    from .h265_processor import H265FrameEncoder, H265FrameDecoder
    logger.info(f"Using per-frame H.265 encoder/decoder (platform: {platform.system()})")


__all__ = ['H265FrameEncoder', 'H265FrameDecoder']
