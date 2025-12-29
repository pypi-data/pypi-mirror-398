"""
pupil.py

This module provides the SDK interface for Pupil functions.

Pupil is a component of the Telekinesis project. Use this module to access and interact with Pupil-related features programmatically.

Functions:
    (Add function documentation here as you implement them.)

Example:
    import pupil
    # Use pupil functions here

"""

from loguru import logger
import numpy as np
from datatypes import datatypes


# Filter Functions
def filter_using_bilateral(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(9),
    spatial_sensitivity: datatypes.Float = datatypes.Float(75.0),
    color_sensitivity: datatypes.Float = datatypes.Float(75.0),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies a bilateral filter to reduce noise while preserving edges.

    Bilateral filtering is effective for noise reduction while maintaining edge sharpness.
    It considers both spatial proximity and color similarity.

    Args:
        image: The input image to filter. Should be a numpy array (H, W) or (H, W, C).
        kernel_size: The size of the kernel for spatial filtering. Must be odd. Increasing
            increases the spatial smoothing area but is slower. Decreasing is faster but
            less effective at smoothing. Typical range: 3-15. Use 3-5 for small images,
            5-9 for medium, 9-15 for large. Default: 9.
        spatial_sensitivity: The spatial standard deviation in pixels. Increasing makes
            the filter consider pixels farther away, creating more smoothing. Decreasing
            focuses on nearby pixels only. Typical range: 10.0-150.0. Use 10.0-50.0 for
            fine details, 50.0-100.0 for balanced, 100.0-150.0 for strong smoothing.
            Default: 75.0.
        color_sensitivity: The color/intensity standard deviation. Increasing allows
            larger color differences to be smoothed, merging more regions. Decreasing
            preserves more color boundaries. Typical range: 10.0-150.0. Use 10.0-50.0
            for strict color preservation, 50.0-100.0 for balanced, 100.0-150.0 for
            more color blending. Default: 75.0.
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". "default" uses the library's default. Set using
            `datatypes.String("mode_name")`. Default: "default".

    Returns:
        A numpy array containing the filtered image with the same shape as input.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(spatial_sensitivity, datatypes.Float):
        raise TypeError(
            f"spatial_sensitivity must be a Float object, class received: {type(spatial_sensitivity).__name__}"
        )
    if not isinstance(color_sensitivity, datatypes.Float):
        raise TypeError(
            f"color_sensitivity must be a Float object, class received: {type(color_sensitivity).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_bilateral successfully")


def filter_using_blur(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(15),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies a simple box blur filter to an image.

    Box blur is a basic smoothing operation that averages pixel values within a kernel.
    Fast but can blur edges.

    Args:
        image: The input image to filter. Should be a numpy array (H, W) or (H, W, C).
        kernel_size: The size of the blur kernel. Must be odd. Increasing creates more
            blur but is slower. Decreasing is faster but less blur. Typical range: 3-31.
            Use 3-7 for light blur, 7-15 for moderate, 15-31 for heavy blur.
            Default: 15.
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". Set using `datatypes.String("mode_name")`.
            Default: "default".

    Returns:
        A numpy array containing the blurred image with the same shape as input.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_blur successfully")


def filter_using_box(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
    normalize_kernel: datatypes.Bool = datatypes.Bool(True),
    output_depth: datatypes.String = datatypes.String("64bit"),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies a normalized box filter with configurable depth and normalization.

    Box filter performs normalized averaging within a kernel region. Useful for basic
    smoothing operations.

    Args:
        image: The input image to filter. Should be a numpy array (H, W) or (H, W, C).
        kernel_size: The size of the box kernel. Must be odd. Increasing creates larger
            averaging area. Typical range: 3-15. Default: 5.
        normalize_kernel: Whether to normalize the kernel so the sum equals 1. When True,
            preserves average brightness. When False, may brighten or darken the image.
            Set using `datatypes.Bool(True)` or `datatypes.Bool(False)`.
            Default: True.
        output_depth: The output bit depth. Options: "8bit", "16bit", "32bit", "64bit".
            Higher depth preserves more precision but uses more memory. Set using
            `datatypes.String("depth")`. Default: "64bit".
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". Set using `datatypes.String("mode_name")`.
            Default: "default".

    Returns:
        A numpy array containing the filtered image with the same shape as input.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(normalize_kernel, datatypes.Bool):
        raise TypeError(
            f"normalize_kernel must be a Bool object, class received: {type(normalize_kernel).__name__}"
        )
    if not isinstance(output_depth, datatypes.String):
        raise TypeError(
            f"output_depth must be a String object, class received: {type(output_depth).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_box successfully")


def filter_using_gaussian_blur(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(15),
    standard_deviation_x: datatypes.Float = datatypes.Float(3.0),
    standard_deviation_y: datatypes.Float = datatypes.Float(3.0),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies Gaussian blur for smooth noise reduction.

    Gaussian blur uses a Gaussian kernel for weighted averaging, providing natural-looking
    blur with better edge preservation than simple blur.

    Args:
        image: The input image to filter. Should be a numpy array (H, W) or (H, W, C).
        kernel_size: The size of the Gaussian kernel. Must be odd. Increasing creates
            more blur. Typical range: 3-31. Use 3-7 for light blur, 7-15 for moderate,
            15-31 for heavy blur. Default: 15.
        standard_deviation_x: The standard deviation in the X direction. Increasing creates
            more horizontal blur. When 0, computed from kernel_size. Typical range: 0.0-10.0.
            Use 0.0 for auto, 1.0-3.0 for light, 3.0-7.0 for moderate, 7.0-10.0 for heavy.
            Default: 3.0.
        standard_deviation_y: The standard deviation in the Y direction. Increasing creates
            more vertical blur. When 0, computed from kernel_size. Typical range: 0.0-10.0.
            Use 0.0 for auto, 1.0-3.0 for light, 3.0-7.0 for moderate, 7.0-10.0 for heavy.
            Default: 3.0.
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". Set using `datatypes.String("mode_name")`.
            Default: "default".

    Returns:
        A numpy array containing the blurred image with the same shape as input.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(standard_deviation_x, datatypes.Float):
        raise TypeError(
            f"standard_deviation_x must be a Float object, class received: {type(standard_deviation_x).__name__}"
        )
    if not isinstance(standard_deviation_y, datatypes.Float):
        raise TypeError(
            f"standard_deviation_y must be a Float object, class received: {type(standard_deviation_y).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_gaussian_blur successfully")


def filter_using_median_blur(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
) -> np.ndarray:
    """
    Applies median blur to reduce salt-and-pepper noise.

    Median blur replaces each pixel with the median of its neighborhood, effectively
    removing impulse noise while preserving edges.

    Args:
        image: The input image to filter. Should be a numpy array (H, W) or (H, W, C).
        kernel_size: The size of the median filter kernel. Must be odd. Increasing removes
            larger noise spots but may blur fine details. Typical range: 3-15. Use 3-5
            for small noise, 5-9 for moderate, 9-15 for heavy noise. Default: 5.

    Returns:
        A numpy array containing the filtered image with the same shape as input.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )

    logger.success("Called filter_using_median_blur successfully")


def filter_using_laplacian(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(3),
    scale: datatypes.Float = datatypes.Float(1.0),
    output_offset: datatypes.Float = datatypes.Float(0.0),
    output_depth: datatypes.String = datatypes.String("64bit"),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies Laplacian filter for edge detection using second derivatives.

    Laplacian operator detects edges by finding regions where the second derivative is
    zero or changes sign.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the Laplacian kernel. Must be 1, 3, 5, or 7. Larger
            kernels detect larger edges. Typical values: 1, 3, 5, 7. Default: 3.
        scale: The scale factor for the computed Laplacian values. Increasing amplifies
            edge responses. Typical range: 0.1-10.0. Use 0.1-1.0 for subtle edges,
            1.0-5.0 for normal, 5.0-10.0 for strong. Default: 1.0.
        output_offset: The offset added to the output. Useful for visualization.
            Typical range: -128.0 to 128.0. Default: 0.0.
        output_depth: The output bit depth. Options: "8bit", "16bit", "32bit", "64bit".
            Set using `datatypes.String("depth")`. Default: "64bit".
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". Set using `datatypes.String("mode_name")`.
            Default: "default".

    Returns:
        A numpy array containing the edge-detected image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(scale, datatypes.Float):
        raise TypeError(
            f"scale must be a Float object, class received: {type(scale).__name__}"
        )
    if not isinstance(output_offset, datatypes.Float):
        raise TypeError(
            f"output_offset must be a Float object, class received: {type(output_offset).__name__}"
        )
    if not isinstance(output_depth, datatypes.String):
        raise TypeError(
            f"output_depth must be a String object, class received: {type(output_depth).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_laplacian successfully")


def filter_using_sobel(
    image: np.ndarray,
    derivative_order_x: datatypes.Int = datatypes.Int(1),
    derivative_order_y: datatypes.Int = datatypes.Int(1),
    kernel_size: datatypes.Int = datatypes.Int(3),
    scale: datatypes.Float = datatypes.Float(1.0),
    output_offset: datatypes.Float = datatypes.Float(0.0),
    output_depth: datatypes.String = datatypes.String("64bit"),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies Sobel filter for directional edge detection.

    Sobel operator computes gradients in X and Y directions, useful for detecting edges
    and their orientation.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W).
        derivative_order_x: The order of the derivative in X direction. 0 means no
            derivative, 1 means first derivative (edge detection), 2 means second
            derivative. Typical values: 0, 1, 2. Default: 1.
        derivative_order_y: The order of the derivative in Y direction. Typical values:
            0, 1, 2. Default: 1.
        kernel_size: The size of the Sobel kernel. Must be 1, 3, 5, 7, or 9. Larger
            kernels detect larger edges. Typical values: 1, 3, 5, 7, 9. Default: 3.
        scale: The scale factor for the computed derivative values. Increasing amplifies
            edge responses. Typical range: 0.1-10.0. Default: 1.0.
        output_offset: The offset added to the output. Typical range: -128.0 to 128.0.
            Default: 0.0.
        output_depth: The output bit depth. Options: "8bit", "16bit", "32bit", "64bit".
            Set using `datatypes.String("depth")`. Default: "64bit".
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". Set using `datatypes.String("mode_name")`.
            Default: "default".

    Returns:
        A numpy array containing the edge-detected image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(derivative_order_x, datatypes.Int):
        raise TypeError(
            f"derivative_order_x must be an Int object, class received: {type(derivative_order_x).__name__}"
        )
    if not isinstance(derivative_order_y, datatypes.Int):
        raise TypeError(
            f"derivative_order_y must be an Int object, class received: {type(derivative_order_y).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(scale, datatypes.Float):
        raise TypeError(
            f"scale must be a Float object, class received: {type(scale).__name__}"
        )
    if not isinstance(output_offset, datatypes.Float):
        raise TypeError(
            f"output_offset must be a Float object, class received: {type(output_offset).__name__}"
        )
    if not isinstance(output_depth, datatypes.String):
        raise TypeError(
            f"output_depth must be a String object, class received: {type(output_depth).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_sobel successfully")


def filter_using_scharr(
    image: np.ndarray,
    derivative_order_x: datatypes.Int = datatypes.Int(1),
    derivative_order_y: datatypes.Int = datatypes.Int(0),
    scale: datatypes.Float = datatypes.Float(1.0),
    output_offset: datatypes.Float = datatypes.Float(0.0),
    output_depth: datatypes.String = datatypes.String("64bit"),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies Scharr filter for improved edge detection accuracy.

    Scharr operator is similar to Sobel but with better rotation invariance and more
    accurate gradient estimation.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W).
        derivative_order_x: The order of the derivative in X direction. Typical values:
            0, 1. Default: 1.
        derivative_order_y: The order of the derivative in Y direction. Typical values:
            0, 1. Default: 0.
        scale: The scale factor for the computed derivative values. Typical range:
            0.1-10.0. Default: 1.0.
        output_offset: The offset added to the output. Typical range: -128.0 to 128.0.
            Default: 0.0.
        output_depth: The output bit depth. Options: "8bit", "16bit", "32bit", "64bit".
            Set using `datatypes.String("depth")`. Default: "64bit".
        border_mode: The border handling mode. Options: "default", "constant", "replicate",
            "reflect", "wrap". Set using `datatypes.String("mode_name")`.
            Default: "default".

    Returns:
        A numpy array containing the edge-detected image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(derivative_order_x, datatypes.Int):
        raise TypeError(
            f"derivative_order_x must be an Int object, class received: {type(derivative_order_x).__name__}"
        )
    if not isinstance(derivative_order_y, datatypes.Int):
        raise TypeError(
            f"derivative_order_y must be an Int object, class received: {type(derivative_order_y).__name__}"
        )
    if not isinstance(scale, datatypes.Float):
        raise TypeError(
            f"scale must be a Float object, class received: {type(scale).__name__}"
        )
    if not isinstance(output_offset, datatypes.Float):
        raise TypeError(
            f"output_offset must be a Float object, class received: {type(output_offset).__name__}"
        )
    if not isinstance(output_depth, datatypes.String):
        raise TypeError(
            f"output_depth must be a String object, class received: {type(output_depth).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called filter_using_scharr successfully")


def filter_using_gabor(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(21),
    gaussian_width: datatypes.Float = datatypes.Float(5.0),
    orientation_angle: datatypes.Float = datatypes.Float(0.0),
    wavelength: datatypes.Float = datatypes.Float(10.0),
    aspect_ratio: datatypes.Float = datatypes.Float(0.5),
    phase_shift: datatypes.Float = datatypes.Float(0.0),
) -> np.ndarray:
    """
    Applies Gabor filter for texture analysis and feature detection.

    Gabor filters are useful for detecting oriented features and textures at specific
    scales and orientations.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the Gabor kernel. Must be odd. Increasing captures
            larger features. Typical range: 5-51. Use 5-15 for fine textures, 15-31
            for medium, 31-51 for coarse. Default: 21.
        gaussian_width: The standard deviation of the Gaussian envelope. Increasing
            creates a wider filter. Typical range: 1.0-20.0. Default: 5.0.
        orientation_angle: The orientation of the filter in degrees. 0° is horizontal,
            90° is vertical. Typical range: 0.0-180.0. Default: 0.0.
        wavelength: The wavelength of the sinusoidal component. Decreasing detects
            finer features. Typical range: 2.0-50.0. Default: 10.0.
        aspect_ratio: The aspect ratio of the filter (width/height). 1.0 is circular,
            <1.0 is elongated. Typical range: 0.1-1.0. Default: 0.5.
        phase_shift: The phase offset of the sinusoidal component in degrees.
            Typical range: 0.0-360.0. Default: 0.0.

    Returns:
        A numpy array containing the filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(gaussian_width, datatypes.Float):
        raise TypeError(
            f"gaussian_width must be a Float object, class received: {type(gaussian_width).__name__}"
        )
    if not isinstance(orientation_angle, datatypes.Float):
        raise TypeError(
            f"orientation_angle must be a Float object, class received: {type(orientation_angle).__name__}"
        )
    if not isinstance(wavelength, datatypes.Float):
        raise TypeError(
            f"wavelength must be a Float object, class received: {type(wavelength).__name__}"
        )
    if not isinstance(aspect_ratio, datatypes.Float):
        raise TypeError(
            f"aspect_ratio must be a Float object, class received: {type(aspect_ratio).__name__}"
        )
    if not isinstance(phase_shift, datatypes.Float):
        raise TypeError(
            f"phase_shift must be a Float object, class received: {type(phase_shift).__name__}"
        )

    logger.success("Called filter_using_gabor successfully")


def filter_using_frangi(
    image: np.ndarray,
    min_structure_size: datatypes.Int = datatypes.Int(1),
    max_structure_size: datatypes.Int = datatypes.Int(10),
    structure_step_size: datatypes.Int = datatypes.Int(2),
    alpha: datatypes.Float = datatypes.Float(0.5),
    beta: datatypes.Float = datatypes.Float(0.5),
    gamma: datatypes.Float | None = None,
    detect_black_ridges: datatypes.Bool = datatypes.Bool(True),
    ridge_padding_mode: datatypes.String = datatypes.String("reflect"),
    padding_value: datatypes.Float = datatypes.Float(0.0),
) -> np.ndarray:
    """
    Applies Frangi vesselness filter to enhance tubular structures.

    Frangi filter is designed to detect vessel-like structures in medical images,
    fingerprints, and other images with elongated features.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W)
            normalized to 0-1 range.
        min_structure_size: The minimum scale (sigma) for structure detection.
            Typical range: 1-5. Default: 1.
        max_structure_size: The maximum scale (sigma) for structure detection.
            Typical range: 5-20. Default: 10.
        structure_step_size: The step size between scales. Smaller steps provide
            finer scale resolution but are slower. Typical range: 1-5. Default: 2.
        alpha: The weight for the blobness measure. Increasing emphasizes blob-like
            structures. Typical range: 0.1-2.0. Default: 0.5.
        beta: The weight for the second-order structureness. Increasing emphasizes
            tubular structures. Typical range: 0.1-2.0. Default: 0.5.
        gamma: The weight for the background suppression. If None, computed automatically.
            Typical range: 0.1-2.0. Default: None.
        detect_black_ridges: Whether to detect dark ridges (vessels) instead of bright.
            Set using `datatypes.Bool(True)` or `datatypes.Bool(False)`.
            Default: True.
        ridge_padding_mode: The padding mode for ridge detection. Options: "reflect",
            "constant", "edge", "symmetric", "wrap". Set using `datatypes.String("mode")`.
            Default: "reflect".
        padding_value: The value used for constant padding mode. Typical range: 0.0-1.0.
            Default: 0.0.

    Returns:
        A numpy array containing the vesselness-filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_structure_size, datatypes.Int):
        raise TypeError(
            f"min_structure_size must be an Int object, class received: {type(min_structure_size).__name__}"
        )
    if not isinstance(max_structure_size, datatypes.Int):
        raise TypeError(
            f"max_structure_size must be an Int object, class received: {type(max_structure_size).__name__}"
        )
    if not isinstance(structure_step_size, datatypes.Int):
        raise TypeError(
            f"structure_step_size must be an Int object, class received: {type(structure_step_size).__name__}"
        )
    if not isinstance(alpha, datatypes.Float):
        raise TypeError(
            f"alpha must be a Float object, class received: {type(alpha).__name__}"
        )
    if not isinstance(beta, datatypes.Float):
        raise TypeError(
            f"beta must be a Float object, class received: {type(beta).__name__}"
        )
    if gamma is not None and not isinstance(gamma, datatypes.Float):
        raise TypeError(
            f"gamma must be a Float object or None, class received: {type(gamma).__name__}"
        )
    if not isinstance(detect_black_ridges, datatypes.Bool):
        raise TypeError(
            f"detect_black_ridges must be a Bool object, class received: {type(detect_black_ridges).__name__}"
        )
    if not isinstance(ridge_padding_mode, datatypes.String):
        raise TypeError(
            f"ridge_padding_mode must be a String object, class received: {type(ridge_padding_mode).__name__}"
        )
    if not isinstance(padding_value, datatypes.Float):
        raise TypeError(
            f"padding_value must be a Float object, class received: {type(padding_value).__name__}"
        )

    logger.success("Called filter_using_frangi successfully")


def filter_using_hessian(
    image: np.ndarray,
    scale_start: datatypes.Int = datatypes.Int(1),
    scale_end: datatypes.Int = datatypes.Int(10),
    scale_step: datatypes.Int = datatypes.Int(2),
    detect_black_ridges: datatypes.Bool = datatypes.Bool(True),
    mode: datatypes.String = datatypes.String("reflect"),
    constant_value: datatypes.Float = datatypes.Float(0.0),
) -> np.ndarray:
    """
    Applies Hessian-based vesselness filter for tubular structure detection.

    Hessian filter uses eigenvalue analysis to detect vessel-like structures, similar
    to Frangi but with different vesselness measure.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W)
            normalized to 0-1 range.
        scale_start: The starting scale (sigma) for multi-scale detection.
            Typical range: 1-5. Default: 1.
        scale_end: The ending scale (sigma) for multi-scale detection.
            Typical range: 5-20. Default: 10.
        scale_step: The step size between scales. Typical range: 1-5. Default: 2.
        detect_black_ridges: Whether to detect dark ridges instead of bright.
            Set using `datatypes.Bool(True)` or `datatypes.Bool(False)`.
            Default: True.
        mode: The padding mode. Options: "reflect", "constant", "edge", "symmetric",
            "wrap". Set using `datatypes.String("mode")`. Default: "reflect".
        constant_value: The value used for constant padding mode. Typical range:
            0.0-1.0. Default: 0.0.

    Returns:
        A numpy array containing the vesselness-filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(scale_start, datatypes.Int):
        raise TypeError(
            f"scale_start must be an Int object, class received: {type(scale_start).__name__}"
        )
    if not isinstance(scale_end, datatypes.Int):
        raise TypeError(
            f"scale_end must be an Int object, class received: {type(scale_end).__name__}"
        )
    if not isinstance(scale_step, datatypes.Int):
        raise TypeError(
            f"scale_step must be an Int object, class received: {type(scale_step).__name__}"
        )
    if not isinstance(detect_black_ridges, datatypes.Bool):
        raise TypeError(
            f"detect_black_ridges must be a Bool object, class received: {type(detect_black_ridges).__name__}"
        )
    if not isinstance(mode, datatypes.String):
        raise TypeError(
            f"mode must be a String object, class received: {type(mode).__name__}"
        )
    if not isinstance(constant_value, datatypes.Float):
        raise TypeError(
            f"constant_value must be a Float object, class received: {type(constant_value).__name__}"
        )

    logger.success("Called filter_using_hessian successfully")


def filter_using_sato(
    image: np.ndarray,
    min_structure_size: datatypes.Int = datatypes.Int(1),
    max_structure_size: datatypes.Int = datatypes.Int(10),
    structure_step_size: datatypes.Int = datatypes.Int(2),
    detect_black_ridges: datatypes.Bool = datatypes.Bool(True),
    ridge_padding_mode: datatypes.String = datatypes.String("reflect"),
    padding_value: datatypes.Float = datatypes.Float(0.0),
) -> np.ndarray:
    """
    Applies Sato filter for multi-scale ridge detection.

    Sato filter is designed to detect ridges and valleys at multiple scales, useful
    for detecting fine structures like vessels or fibers.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W)
            normalized to 0-1 range.
        min_structure_size: The minimum scale (sigma) for structure detection.
            Typical range: 1-5. Default: 1.
        max_structure_size: The maximum scale (sigma) for structure detection.
            Typical range: 5-20. Default: 10.
        structure_step_size: The step size between scales. Typical range: 1-5.
            Default: 2.
        detect_black_ridges: Whether to detect dark ridges instead of bright.
            Set using `datatypes.Bool(True)` or `datatypes.Bool(False)`.
            Default: True.
        ridge_padding_mode: The padding mode. Options: "reflect", "constant", "edge",
            "symmetric", "wrap". Set using `datatypes.String("mode")`.
            Default: "reflect".
        padding_value: The value used for constant padding mode. Typical range:
            0.0-1.0. Default: 0.0.

    Returns:
        A numpy array containing the ridge-filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_structure_size, datatypes.Int):
        raise TypeError(
            f"min_structure_size must be an Int object, class received: {type(min_structure_size).__name__}"
        )
    if not isinstance(max_structure_size, datatypes.Int):
        raise TypeError(
            f"max_structure_size must be an Int object, class received: {type(max_structure_size).__name__}"
        )
    if not isinstance(structure_step_size, datatypes.Int):
        raise TypeError(
            f"structure_step_size must be an Int object, class received: {type(structure_step_size).__name__}"
        )
    if not isinstance(detect_black_ridges, datatypes.Bool):
        raise TypeError(
            f"detect_black_ridges must be a Bool object, class received: {type(detect_black_ridges).__name__}"
        )
    if not isinstance(ridge_padding_mode, datatypes.String):
        raise TypeError(
            f"ridge_padding_mode must be a String object, class received: {type(ridge_padding_mode).__name__}"
        )
    if not isinstance(padding_value, datatypes.Float):
        raise TypeError(
            f"padding_value must be a Float object, class received: {type(padding_value).__name__}"
        )

    logger.success("Called filter_using_sato successfully")


def filter_using_meijering(
    image: np.ndarray,
    min_structure_size: datatypes.Int = datatypes.Int(1),
    max_structure_size: datatypes.Int = datatypes.Int(10),
    structure_step_size: datatypes.Int = datatypes.Int(2),
    detect_black_ridges: datatypes.Bool = datatypes.Bool(True),
    ridge_padding_mode: datatypes.String = datatypes.String("reflect"),
    padding_value: datatypes.Float = datatypes.Float(0.0),
) -> np.ndarray:
    """
    Applies Meijering filter for neurite detection.

    Meijering filter is optimized for detecting neurites and similar branching
    structures in biomedical images.

    Args:
        image: The input image to filter. Should be a grayscale numpy array (H, W)
            normalized to 0-1 range.
        min_structure_size: The minimum scale (sigma) for structure detection.
            Typical range: 1-5. Default: 1.
        max_structure_size: The maximum scale (sigma) for structure detection.
            Typical range: 5-20. Default: 10.
        structure_step_size: The step size between scales. Typical range: 1-5.
            Default: 2.
        detect_black_ridges: Whether to detect dark ridges instead of bright.
            Set using `datatypes.Bool(True)` or `datatypes.Bool(False)`.
            Default: True.
        ridge_padding_mode: The padding mode. Options: "reflect", "constant", "edge",
            "symmetric", "wrap". Set using `datatypes.String("mode")`.
            Default: "reflect".
        padding_value: The value used for constant padding mode. Typical range:
            0.0-1.0. Default: 0.0.

    Returns:
        A numpy array containing the neurite-filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_structure_size, datatypes.Int):
        raise TypeError(
            f"min_structure_size must be an Int object, class received: {type(min_structure_size).__name__}"
        )
    if not isinstance(max_structure_size, datatypes.Int):
        raise TypeError(
            f"max_structure_size must be an Int object, class received: {type(max_structure_size).__name__}"
        )
    if not isinstance(structure_step_size, datatypes.Int):
        raise TypeError(
            f"structure_step_size must be an Int object, class received: {type(structure_step_size).__name__}"
        )
    if not isinstance(detect_black_ridges, datatypes.Bool):
        raise TypeError(
            f"detect_black_ridges must be a Bool object, class received: {type(detect_black_ridges).__name__}"
        )
    if not isinstance(ridge_padding_mode, datatypes.String):
        raise TypeError(
            f"ridge_padding_mode must be a String object, class received: {type(ridge_padding_mode).__name__}"
        )
    if not isinstance(padding_value, datatypes.Float):
        raise TypeError(
            f"padding_value must be a Float object, class received: {type(padding_value).__name__}"
        )

    logger.success("Called filter_using_meijering successfully")


# Morphology Functions
def morphology_using_erosion(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies erosion to shrink bright regions and remove small noise.

    Erosion removes pixels from object boundaries, useful for removing small bright
    spots and shrinking objects.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing removes larger
            features but may shrink objects more. Typical range: 3-15. Default: 5.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times erosion is applied. Increasing applies more
            erosion. Typical range: 1-10. Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the eroded image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_erosion successfully")


def morphology_using_dilation(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies dilation to expand bright regions and fill holes.

    Dilation adds pixels to object boundaries, useful for filling gaps and expanding
    objects.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing expands objects
            more. Typical range: 3-15. Default: 5.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times dilation is applied. Increasing applies more
            dilation. Typical range: 1-10. Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the dilated image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_dilation successfully")


def morphology_using_closing(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies morphological closing (dilation followed by erosion).

    Closing fills small holes and gaps, useful for connecting nearby components
    while preserving overall shape.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing fills larger
            holes. Typical range: 3-15. Default: 5.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times closing is applied. Typical range: 1-10.
            Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the closed image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_closing successfully")


def morphology_using_opening(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies morphological opening (erosion followed by dilation).

    Opening removes small bright spots and thin connections, useful for noise removal
    while preserving object size.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing removes larger
            features. Typical range: 3-15. Default: 5.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times opening is applied. Typical range: 1-10.
            Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the opened image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_opening successfully")


def morphology_using_gradient(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(5),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies morphological gradient for edge detection.

    Morphological gradient highlights boundaries by computing the difference between
    dilation and erosion.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing detects thicker
            edges. Typical range: 3-15. Default: 5.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times gradient is applied. Typical range: 1-5.
            Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the gradient image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_gradient successfully")


def morphology_using_tophat(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(15),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies top-hat transform to extract small bright features.

    Top-hat finds bright features smaller than the structuring element, useful for
    detecting small objects or enhancing details.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing extracts larger
            features. Typical range: 5-31. Default: 15.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times tophat is applied. Typical range: 1-5.
            Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the tophat-filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_tophat successfully")


def morphology_using_blackhat(
    image: np.ndarray,
    kernel_size: datatypes.Int = datatypes.Int(15),
    kernel_shape: datatypes.String = datatypes.String("ellipse"),
    iterations: datatypes.Int = datatypes.Int(1),
    border_mode: datatypes.String = datatypes.String("default"),
) -> np.ndarray:
    """
    Applies black-hat transform to extract small dark features.

    Black-hat finds dark features smaller than the structuring element, useful for
    detecting small holes or dark details.

    Args:
        image: The input image to process. Should be a grayscale numpy array (H, W).
        kernel_size: The size of the structuring element. Increasing extracts larger
            features. Typical range: 5-31. Default: 15.
        kernel_shape: The shape of the structuring element. Options: "ellipse",
            "rectangle", "cross". Set using `datatypes.String("shape")`.
            Default: "ellipse".
        iterations: The number of times blackhat is applied. Typical range: 1-5.
            Default: 1.
        border_mode: The border handling mode. Options: "default", "constant",
            "replicate", "reflect", "wrap". Set using `datatypes.String("mode")`.
            Default: "default".

    Returns:
        A numpy array containing the blackhat-filtered image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(kernel_size, datatypes.Int):
        raise TypeError(
            f"kernel_size must be an Int object, class received: {type(kernel_size).__name__}"
        )
    if not isinstance(kernel_shape, datatypes.String):
        raise TypeError(
            f"kernel_shape must be a String object, class received: {type(kernel_shape).__name__}"
        )
    if not isinstance(iterations, datatypes.Int):
        raise TypeError(
            f"iterations must be an Int object, class received: {type(iterations).__name__}"
        )
    if not isinstance(border_mode, datatypes.String):
        raise TypeError(
            f"border_mode must be a String object, class received: {type(border_mode).__name__}"
        )

    logger.success("Called morphology_using_blackhat successfully")


def morphology_using_thinning(
    image: np.ndarray,
    thinning_method: datatypes.String = datatypes.String("thinning_zhangsuen"),
) -> np.ndarray:
    """
    Applies skeletonization (thinning) to binary images.

    Thinning reduces binary objects to their skeletons, useful for shape analysis
    and feature extraction.

    Args:
        image: The input binary image to process. Should be a grayscale numpy array
            (H, W) with values 0 and 255.
        thinning_method: The thinning algorithm to use. Options: "thinning_zhangsuen",
            "thinning_guohall". Set using `datatypes.String("method")`.
            Default: "thinning_zhangsuen".

    Returns:
        A numpy array containing the skeletonized image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(thinning_method, datatypes.String):
        raise TypeError(
            f"thinning_method must be a String object, class received: {type(thinning_method).__name__}"
        )

    logger.success("Called morphology_using_thinning successfully")


# Transform Functions
def transform_using_pyramid_down(
    image: np.ndarray,
    scale_factor: datatypes.Float = datatypes.Float(0.5),
) -> np.ndarray:
    """
    Downsamples an image using Gaussian pyramid.

    Pyramid down reduces image resolution, useful for multi-scale analysis and
    efficient processing.

    Args:
        image: The input image to downsample. Should be a numpy array (H, W) or
            (H, W, C).
        scale_factor: The scale factor for downsampling. Must be between 0 and 1.
            Decreasing creates smaller output. Typical range: 0.1-0.9. Use 0.5 for
            half size, 0.25 for quarter size. Default: 0.5.

    Returns:
        A numpy array containing the downsampled image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(scale_factor, datatypes.Float):
        raise TypeError(
            f"scale_factor must be a Float object, class received: {type(scale_factor).__name__}"
        )

    logger.success("Called transform_using_pyramid_down successfully")


def transform_using_pyramid_up(
    image: np.ndarray,
    scale_factor: datatypes.Float = datatypes.Float(2.0),
) -> np.ndarray:
    """
    Upsamples an image using Gaussian pyramid.

    Pyramid up increases image resolution, useful for image enlargement and
    multi-scale reconstruction.

    Args:
        image: The input image to upsample. Should be a numpy array (H, W) or
            (H, W, C).
        scale_factor: The scale factor for upsampling. Must be greater than 1.
            Increasing creates larger output. Typical range: 1.1-4.0. Use 2.0 for
            double size, 4.0 for quadruple size. Default: 2.0.

    Returns:
        A numpy array containing the upsampled image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(scale_factor, datatypes.Float):
        raise TypeError(
            f"scale_factor must be a Float object, class received: {type(scale_factor).__name__}"
        )

    logger.success("Called transform_using_pyramid_up successfully")


def transform_using_resize(
    image: np.ndarray,
    scale_factor: datatypes.Float | None = None,
    width: datatypes.Int | None = None,
    height: datatypes.Int | None = None,
    interpolation_method: datatypes.String = datatypes.String("linear"),
) -> np.ndarray:
    """
    Resizes an image to specified dimensions or scale factor.

    Image resizing changes image dimensions while maintaining or adjusting aspect
    ratio, useful for preprocessing and display.

    Args:
        image: The input image to resize. Should be a numpy array (H, W) or (H, W, C).
        scale_factor: The scale factor for resizing. If provided, both width and height
            are scaled by this factor. When None, width and height must be specified.
            Typical range: 0.1-10.0. Default: None.
        width: The target width in pixels. When None, computed from scale_factor or
            maintains aspect ratio. Typical range: 1-10000. Default: None.
        height: The target height in pixels. When None, computed from scale_factor or
            maintains aspect ratio. Typical range: 1-10000. Default: None.
        interpolation_method: The interpolation method. Options: "linear", "nearest",
            "cubic", "area", "lanczos". Set using `datatypes.String("method")`.
            Default: "linear".

    Returns:
        A numpy array containing the resized image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if scale_factor is not None and not isinstance(scale_factor, datatypes.Float):
        raise TypeError(
            f"scale_factor must be a Float object or None, class received: {type(scale_factor).__name__}"
        )
    if width is not None and not isinstance(width, datatypes.Int):
        raise TypeError(
            f"width must be an Int object or None, class received: {type(width).__name__}"
        )
    if height is not None and not isinstance(height, datatypes.Int):
        raise TypeError(
            f"height must be an Int object or None, class received: {type(height).__name__}"
        )
    if not isinstance(interpolation_method, datatypes.String):
        raise TypeError(
            f"interpolation_method must be a String object, class received: {type(interpolation_method).__name__}"
        )

    logger.success("Called transform_using_resize successfully")


def transform_using_rotate(
    image: np.ndarray,
    angle_in_deg: datatypes.Float,
    interpolation_method: datatypes.String = datatypes.String("linear"),
) -> np.ndarray:
    """
    Rotates an image by a specified angle.

    Image rotation is useful for orientation correction and data augmentation.

    Args:
        image: The input image to rotate. Should be a numpy array (H, W) or (H, W, C).
        angle_in_deg: The rotation angle in degrees. Positive values rotate clockwise,
            negative counter-clockwise. Typical range: -360.0 to 360.0. Default: 0.0.
        interpolation_method: The interpolation method. Options: "linear", "nearest",
            "cubic". Set using `datatypes.String("method")`. Default: "linear".

    Returns:
        A numpy array containing the rotated image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(angle_in_deg, datatypes.Float):
        raise TypeError(
            f"angle_in_deg must be a Float object, class received: {type(angle_in_deg).__name__}"
        )
    if not isinstance(interpolation_method, datatypes.String):
        raise TypeError(
            f"interpolation_method must be a String object, class received: {type(interpolation_method).__name__}"
        )

    logger.success("Called transform_using_rotate successfully")


def transform_using_split_channels(
    image: np.ndarray,
) -> list[np.ndarray]:
    """
    Splits a multi-channel image into separate channels.

    Channel splitting is useful for processing individual color channels or extracting
    specific components.

    Args:
        image: The input multi-channel image. Should be a numpy array (H, W, C) where
            C is the number of channels (typically 3 for RGB/BGR).

    Returns:
        A list of numpy arrays, one for each channel, each with shape (H, W).
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )

    logger.success("Called transform_using_split_channels successfully")


def transform_using_merge_channels(
    channel_1: np.ndarray,
    channel_2: np.ndarray,
    channel_3: np.ndarray,
) -> np.ndarray:
    """
    Merges separate channels into a multi-channel image.

    Channel merging combines individual grayscale images into a multi-channel color
    image.

    Args:
        channel_1: The first channel. Should be a grayscale numpy array (H, W).
        channel_2: The second channel. Should be a grayscale numpy array (H, W).
        channel_3: The third channel. Should be a grayscale numpy array (H, W).

    Returns:
        A numpy array containing the merged image with shape (H, W, 3).
    """
    if not isinstance(channel_1, np.ndarray):
        raise TypeError(
            f"channel_1 must be a numpy array, class received: {type(channel_1).__name__}"
        )
    if not isinstance(channel_2, np.ndarray):
        raise TypeError(
            f"channel_2 must be a numpy array, class received: {type(channel_2).__name__}"
        )
    if not isinstance(channel_3, np.ndarray):
        raise TypeError(
            f"channel_3 must be a numpy array, class received: {type(channel_3).__name__}"
        )

    logger.success("Called transform_using_merge_channels successfully")


def transform_using_single_box_crop(
    image: np.ndarray,
    bounding_box: list[int],
    retain_coordinates: datatypes.Bool = datatypes.Bool(False),
) -> tuple[np.ndarray, np.ndarray]:
    """
    Crops an image using a single bounding box in (x, y, width, height) format.

    Single box cropping extracts a rectangular region from an image, optionally
    retaining original coordinates in a black canvas.

    Args:
        image: The input image to crop. Should be a numpy array (H, W) or (H, W, C).
        bounding_box: The bounding box as [x, y, width, height] where (x, y) is the
            top-left corner. x and y are pixel coordinates, width and height are the
            dimensions of the crop region. Typical range: x, y: 0 to image_width/height,
            width, height: 1 to image_width/height.
        retain_coordinates: Whether to retain original coordinates by placing the
            cropped region in a black canvas of the same size as the original image.
            When True, the output image has the same size as input. When False, the
            output is just the cropped region. Set using `datatypes.Bool(True)` or
            `datatypes.Bool(False)`. Default: False.

    Returns:
        A tuple containing:
        - A numpy array containing the cropped image.
        - A numpy array containing the contour/region information.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(bounding_box, list):
        raise TypeError(
            f"bounding_box must be a list, class received: {type(bounding_box).__name__}"
        )
    if len(bounding_box) != 4:
        raise ValueError(
            f"bounding_box must have 4 elements [x, y, width, height], got {len(bounding_box)}"
        )
    if not isinstance(retain_coordinates, datatypes.Bool):
        raise TypeError(
            f"retain_coordinates must be a Bool object, class received: {type(retain_coordinates).__name__}"
        )

    logger.success("Called transform_using_single_box_crop successfully")


def transform_using_box_crop(
    image: np.ndarray,
    bounding_boxes: np.ndarray,
    retain_coordinates: datatypes.Bool = datatypes.Bool(False),
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """
    Crops multiple bounding boxes from an image.

    Box cropper handles multiple regions simultaneously, useful for batch processing
    or multi-object extraction.

    Args:
        image: The input image to crop. Should be a numpy array (H, W) or (H, W, C).
        bounding_boxes: An array of bounding boxes, each as [x, y, width, height].
            Shape should be (N, 4) where N is the number of boxes. Each box is
            [x, y, width, height] where (x, y) is the top-left corner.
        retain_coordinates: Whether to retain original coordinates by placing each
            cropped region in a black canvas of the same size as the original image.
            When True, output images have the same size as input. When False, outputs
            are just the cropped regions. Set using `datatypes.Bool(True)` or
            `datatypes.Bool(False)`. Default: False.

    Returns:
        A tuple containing:
        - A list of numpy arrays, each containing a cropped image.
        - A list of numpy arrays, each containing contour/region information.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(bounding_boxes, np.ndarray):
        raise TypeError(
            f"bounding_boxes must be a numpy array, class received: {type(bounding_boxes).__name__}"
        )
    if bounding_boxes.shape[1] != 4:
        raise ValueError(
            f"bounding_boxes must have shape (N, 4), got {bounding_boxes.shape}"
        )
    if not isinstance(retain_coordinates, datatypes.Bool):
        raise TypeError(
            f"retain_coordinates must be a Bool object, class received: {type(retain_coordinates).__name__}"
        )

    logger.success("Called transform_using_box_crop successfully")


def transform_using_polygon_crop(
    image: np.ndarray,
    polygon_vertices: list[tuple[int, int]],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Crops an image using a polygon mask defined by vertices.

    Polygon cropping allows for non-rectangular regions, useful for irregular
    shapes or region-of-interest extraction.

    Args:
        image: The input image to crop. Should be a numpy array (H, W) or (H, W, C).
        polygon_vertices: A list of (x, y) tuples defining the polygon vertices.
            The polygon is formed by connecting these vertices in order. Each vertex
            is a tuple of pixel coordinates. Minimum 3 vertices required for a valid
            polygon. Vertices should be within image bounds for best results.

    Returns:
        A tuple containing:
        - A numpy array containing the cropped image (masked region).
        - A numpy array containing the contour/region information.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(polygon_vertices, list):
        raise TypeError(
            f"polygon_vertices must be a list, class received: {type(polygon_vertices).__name__}"
        )
    if len(polygon_vertices) < 3:
        raise ValueError(
            f"polygon_vertices must have at least 3 vertices, got {len(polygon_vertices)}"
        )
    for vertex in polygon_vertices:
        if not isinstance(vertex, tuple) or len(vertex) != 2:
            raise ValueError(
                f"Each vertex must be a tuple of (x, y), got {vertex}"
            )

    logger.success("Called transform_using_polygon_crop successfully")


def transform_using_circle_center_alignment_resize(
    source_image: np.ndarray,
    target_image: np.ndarray,
    pred_mask_min_distance: datatypes.Int = datatypes.Int(200),
    pred_mask_max_diameter: datatypes.Int = datatypes.Int(250),
    pred_mask_min_diameter: datatypes.Int = datatypes.Int(150),
    pred_param1: datatypes.Int = datatypes.Int(50),
    pred_param2: datatypes.Int = datatypes.Int(30),
    template_mask_diameter: datatypes.Int = datatypes.Int(200),
    template_mask_max_diameter: datatypes.Int = datatypes.Int(250),
    template_mask_min_diameter: datatypes.Int = datatypes.Int(150),
    template_param1: datatypes.Int = datatypes.Int(50),
    template_param2: datatypes.Int = datatypes.Int(30),
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """
    Resizes and center-aligns two binary masks based on detected circular regions.

    Uses Hough Circle Transform to detect circles, then aligns and scales the source
    mask to match the template mask's circle size and center.

    Args:
        source_image: The source binary mask to align. Should be a grayscale numpy
            array (H, W) with values 0 and 255.
        target_image: The target/template binary mask to match. Should be a grayscale
            numpy array (H, W) with values 0 and 255.
        pred_mask_min_distance: Minimum distance between circle centers in the source
            mask. Increasing reduces false detections but may miss close circles.
            Typical range: 50-500. Default: 200.
        pred_mask_max_diameter: Maximum diameter of circles to detect in source mask.
            Typical range: 50-1000. Default: 250.
        pred_mask_min_diameter: Minimum diameter of circles to detect in source mask.
            Typical range: 10-500. Default: 150.
        pred_param1: Upper threshold for edge detection in source mask. Typical range:
            10-200. Default: 50.
        pred_param2: Accumulator threshold for circle detection in source mask.
            Lower values detect more circles but may include false positives. Typical
            range: 10-100. Default: 30.
        template_mask_diameter: Expected diameter of circles in target mask. Typical
            range: 50-1000. Default: 200.
        template_mask_max_diameter: Maximum diameter of circles to detect in target
            mask. Typical range: 50-1000. Default: 250.
        template_mask_min_diameter: Minimum diameter of circles to detect in target
            mask. Typical range: 10-500. Default: 150.
        template_param1: Upper threshold for edge detection in target mask. Typical
            range: 10-200. Default: 50.
        template_param2: Accumulator threshold for circle detection in target mask.
            Typical range: 10-100. Default: 30.

    Returns:
        A tuple containing:
        - The aligned source image (numpy array) or None if alignment failed.
        - The aligned target image (numpy array) or None if alignment failed.
    """
    if not isinstance(source_image, np.ndarray):
        raise TypeError(
            f"source_image must be a numpy array, class received: {type(source_image).__name__}"
        )
    if not isinstance(target_image, np.ndarray):
        raise TypeError(
            f"target_image must be a numpy array, class received: {type(target_image).__name__}"
        )
    if not isinstance(pred_mask_min_distance, datatypes.Int):
        raise TypeError(
            f"pred_mask_min_distance must be an Int object, class received: {type(pred_mask_min_distance).__name__}"
        )
    if not isinstance(pred_mask_max_diameter, datatypes.Int):
        raise TypeError(
            f"pred_mask_max_diameter must be an Int object, class received: {type(pred_mask_max_diameter).__name__}"
        )
    if not isinstance(pred_mask_min_diameter, datatypes.Int):
        raise TypeError(
            f"pred_mask_min_diameter must be an Int object, class received: {type(pred_mask_min_diameter).__name__}"
        )
    if not isinstance(pred_param1, datatypes.Int):
        raise TypeError(
            f"pred_param1 must be an Int object, class received: {type(pred_param1).__name__}"
        )
    if not isinstance(pred_param2, datatypes.Int):
        raise TypeError(
            f"pred_param2 must be an Int object, class received: {type(pred_param2).__name__}"
        )
    if not isinstance(template_mask_diameter, datatypes.Int):
        raise TypeError(
            f"template_mask_diameter must be an Int object, class received: {type(template_mask_diameter).__name__}"
        )
    if not isinstance(template_mask_max_diameter, datatypes.Int):
        raise TypeError(
            f"template_mask_max_diameter must be an Int object, class received: {type(template_mask_max_diameter).__name__}"
        )
    if not isinstance(template_mask_min_diameter, datatypes.Int):
        raise TypeError(
            f"template_mask_min_diameter must be an Int object, class received: {type(template_mask_min_diameter).__name__}"
        )
    if not isinstance(template_param1, datatypes.Int):
        raise TypeError(
            f"template_param1 must be an Int object, class received: {type(template_param1).__name__}"
        )
    if not isinstance(template_param2, datatypes.Int):
        raise TypeError(
            f"template_param2 must be an Int object, class received: {type(template_param2).__name__}"
        )

    logger.success("Called transform_using_circle_center_alignment_resize successfully")


def transform_using_resize_with_reference_image(
    image: np.ndarray,
    reference_image: np.ndarray,
    pad_color: tuple[int, int, int] | None = None,
) -> np.ndarray:
    """
    Resizes an image to match reference image dimensions while preserving aspect ratio.

    Pads the resized image with a specified color to fill the target size. Useful
    for batch processing where all images need the same dimensions.

    Args:
        image: The input image to resize. Should be a numpy array (H, W) or (H, W, C).
        reference_image: The reference image whose dimensions to match. Should be a
            numpy array (H, W) or (H, W, C). The output will have the same dimensions
            as this image.
        pad_color: The RGB color tuple (R, G, B) for padding. When None, uses black
            (0, 0, 0). Each value should be 0-255. Typical values: (0, 0, 0) for
            black, (128, 128, 128) for gray, (255, 255, 255) for white.
            Default: None (black).

    Returns:
        A numpy array containing the resized and padded image with the same
        dimensions as the reference image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(reference_image, np.ndarray):
        raise TypeError(
            f"reference_image must be a numpy array, class received: {type(reference_image).__name__}"
        )
    if pad_color is not None:
        if not isinstance(pad_color, tuple) or len(pad_color) != 3:
            raise ValueError(
                f"pad_color must be a tuple of (R, G, B), got {pad_color}"
            )
        for val in pad_color:
            if not isinstance(val, int) or val < 0 or val > 255:
                raise ValueError(
                    f"pad_color values must be integers 0-255, got {pad_color}"
                )

    logger.success("Called transform_using_resize_with_reference_image successfully")


# Color Functions
def color_using_convert_space(
    image: np.ndarray,
    source_color_space: datatypes.String,
    target_color_space: datatypes.String,
) -> np.ndarray:
    """
    Converts an image between different color spaces.

    Color space conversion is useful for various image processing tasks, such as
    using HSV for color-based segmentation.

    Args:
        image: The input image to convert. Should be a numpy array (H, W, C).
        source_color_space: The source color space. Options: "BGR", "RGB", "HSV",
            "LAB", "XYZ", "GRAY". Set using `datatypes.String("space")`.
        target_color_space: The target color space. Options: "BGR", "RGB", "HSV",
            "LAB", "XYZ", "GRAY". Set using `datatypes.String("space")`.

    Returns:
        A numpy array containing the converted image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(source_color_space, datatypes.String):
        raise TypeError(
            f"source_color_space must be a String object, class received: {type(source_color_space).__name__}"
        )
    if not isinstance(target_color_space, datatypes.String):
        raise TypeError(
            f"target_color_space must be a String object, class received: {type(target_color_space).__name__}"
        )

    logger.success("Called color_using_convert_space successfully")


def color_using_normalize_intensity(
    image: np.ndarray,
    alpha: datatypes.Float = datatypes.Float(0.0),
    beta: datatypes.Float = datatypes.Float(255.0),
    normalization_method: datatypes.String = datatypes.String("minmax"),
    output_depth: datatypes.String = datatypes.String("8bit"),
) -> np.ndarray:
    """
    Normalizes image pixel intensities to a specified range.

    Normalization adjusts pixel values to a desired range, useful for preprocessing
    and contrast enhancement.

    Args:
        image: The input image to normalize. Should be a numpy array (H, W) or
            (H, W, C).
        alpha: The lower bound of the output range. Increasing shifts the output
            range upward. Typical range: 0.0-255.0. Default: 0.0.
        beta: The upper bound of the output range. Increasing expands the output
            range. Typical range: 0.0-255.0. Default: 255.0.
        normalization_method: The normalization method. Options: "minmax", "norm",
            "scale". Set using `datatypes.String("method")`. Default: "minmax".
        output_depth: The output bit depth. Options: "8bit", "16bit", "32bit",
            "64bit". Set using `datatypes.String("depth")`. Default: "8bit".

    Returns:
        A numpy array containing the normalized image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(alpha, datatypes.Float):
        raise TypeError(
            f"alpha must be a Float object, class received: {type(alpha).__name__}"
        )
    if not isinstance(beta, datatypes.Float):
        raise TypeError(
            f"beta must be a Float object, class received: {type(beta).__name__}"
        )
    if not isinstance(normalization_method, datatypes.String):
        raise TypeError(
            f"normalization_method must be a String object, class received: {type(normalization_method).__name__}"
        )
    if not isinstance(output_depth, datatypes.String):
        raise TypeError(
            f"output_depth must be a String object, class received: {type(output_depth).__name__}"
        )

    logger.success("Called color_using_normalize_intensity successfully")


def color_using_create_solid(
    image: np.ndarray,
    color: datatypes.String = datatypes.String("red"),
) -> np.ndarray:
    """
    Generates a solid color image matching input dimensions.

    Solid color image generation is useful for creating masks, backgrounds, or test
    images of specific colors.

    Args:
        image: The input image to match dimensions. Should be a numpy array (H, W)
            or (H, W, C).
        color: The color name. Options: "red", "green", "blue", "white", "black",
            "gray". Set using `datatypes.String("color")`. Default: "red".

    Returns:
        A numpy array containing the solid color image with the same shape as input.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(color, datatypes.String):
        raise TypeError(
            f"color must be a String object, class received: {type(color).__name__}"
        )

    logger.success("Called color_using_create_solid successfully")


def color_using_clahe(
    image: np.ndarray,
    clip_limit: datatypes.Float = datatypes.Float(2.0),
    tile_grid_size: datatypes.Int = datatypes.Int(8),
    color_space: datatypes.String = datatypes.String("gray"),
) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization.

    CLAHE enhances local contrast adaptively, preventing over-amplification of noise
    in uniform regions.

    Args:
        image: The input image to process. Should be a numpy array (H, W) or
            (H, W, C).
        clip_limit: The contrast limiting threshold. Increasing allows more contrast
            enhancement but may amplify noise. Typical range: 1.0-8.0. Use 1.0-2.0
            for subtle enhancement, 2.0-4.0 for moderate, 4.0-8.0 for strong.
            Default: 2.0.
        tile_grid_size: The size of the grid for adaptive processing. Increasing
            processes larger regions but may lose local detail. Typical range: 2-16.
            Use 2-4 for fine detail, 4-8 for balanced, 8-16 for coarse. Default: 8.
        color_space: The color space to process. Options: "gray", "rgb", "lab".
            Set using `datatypes.String("space")`. Default: "gray".

    Returns:
        A numpy array containing the CLAHE-enhanced image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(clip_limit, datatypes.Float):
        raise TypeError(
            f"clip_limit must be a Float object, class received: {type(clip_limit).__name__}"
        )
    if not isinstance(tile_grid_size, datatypes.Int):
        raise TypeError(
            f"tile_grid_size must be an Int object, class received: {type(tile_grid_size).__name__}"
        )
    if not isinstance(color_space, datatypes.String):
        raise TypeError(
            f"color_space must be a String object, class received: {type(color_space).__name__}"
        )

    logger.success("Called color_using_clahe successfully")


def color_using_gamma_correction(
    image: np.ndarray,
    gamma: datatypes.Float = datatypes.Float(1.0),
) -> np.ndarray:
    """
    Applies gamma correction for brightness adjustment.

    Gamma correction adjusts image brightness non-linearly, useful for display
    calibration and contrast enhancement.

    Args:
        image: The input image to process. Should be a numpy array (H, W) or
            (H, W, C).
        gamma: The gamma value. Values < 1.0 brighten the image, values > 1.0 darken.
            Typical range: 0.1-3.0. Use 0.1-0.5 for brightening, 0.5-1.5 for
            balanced, 1.5-3.0 for darkening. Default: 1.0.

    Returns:
        A numpy array containing the gamma-corrected image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(gamma, datatypes.Float):
        raise TypeError(
            f"gamma must be a Float object, class received: {type(gamma).__name__}"
        )

    logger.success("Called color_using_gamma_correction successfully")


def color_using_white_balance(
    image: np.ndarray,
) -> np.ndarray:
    """
    Applies white balance correction to adjust color temperature.

    White balance removes color casts caused by lighting conditions, making images
    appear more natural.

    Args:
        image: The input image to process. Should be a numpy array (H, W, C) with
            color channels.

    Returns:
        A numpy array containing the white-balanced image.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )

    logger.success("Called color_using_white_balance successfully")


# IO Functions
def load_image(
    filepath: datatypes.String,
) -> np.ndarray:
    """
    Loads an image from a file path.

    Image loading is the basic input operation for image processing pipelines.

    Args:
        filepath: The file path to the image file. Can be absolute or relative path.
            Supports common formats: JPEG, PNG, BMP, TIFF, etc. Set using
            `datatypes.String("path/to/image.jpg")`.

    Returns:
        A numpy array containing the loaded image.
    """
    if not isinstance(filepath, datatypes.String):
        raise TypeError(
            f"filepath must be a String object, class received: {type(filepath).__name__}"
        )

    logger.success("Called load_image successfully")


def save_image(
    image: np.ndarray,
    filepath: datatypes.String,
) -> None:
    """
    Writes an image to a file path.

    Image writing saves processed images to disk for later use or analysis.

    Args:
        image: The image to save. Should be a numpy array (H, W) or (H, W, C).
        filepath: The file path where to save the image. Can be absolute or relative
            path. The file format is determined by the extension. Set using
            `datatypes.String("path/to/output.jpg")`.

    Returns:
        None
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(filepath, datatypes.String):
        raise TypeError(
            f"filepath must be a String object, class received: {type(filepath).__name__}"
        )

    logger.success("Called save_image successfully")

