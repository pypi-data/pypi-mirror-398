"""
cornea.py

This module provides the SDK interface for Cornea functions.

Cornea is a component of the Telekinesis project. Use this module to access and interact with Cornea-related features programmatically.

Functions:
    (Add function documentation here as you implement them.)

Example:
    import cornea
    # Use cornea functions here

"""

from loguru import logger
import numpy as np
from typing import Dict, Any, Optional, Union, List, Tuple

from telekinesis import datatypes
from cornea import color, contour, graph, refinement, region, superpixel, threshold, tracking, deep


# Color Segmentation Functions
def segment_using_rgb(
    image: np.ndarray,
    lower_bound: Tuple[int, int, int] = (0, 0, 0),
    upper_bound: Tuple[int, int, int] = (255, 255, 255),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs RGB color space segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        lower_bound: Lower bound for RGB range (R, G, B). Default: (0, 0, 0).
        upper_bound: Upper bound for RGB range (R, G, B). Default: (255, 255, 255).
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    rgb_segmentation = color.RGBSegmentation(
        lower_bound=lower_bound,
        upper_bound=upper_bound
    )
    result = rgb_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_rgb successfully")
    return result


def segment_using_hsv(
    image: np.ndarray,
    lower_bound: Tuple[int, int, int] = (0, 0, 0),
    upper_bound: Tuple[int, int, int] = (180, 255, 255),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs HSV color space segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        lower_bound: Lower bound for HSV range (H: 0-180, S: 0-255, V: 0-255). Default: (0, 0, 0).
        upper_bound: Upper bound for HSV range (H: 0-180, S: 0-255, V: 0-255). Default: (180, 255, 255).
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    hsv_segmentation = color.HSVSegmentation(
        lower_bound=lower_bound,
        upper_bound=upper_bound
    )
    result = hsv_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_hsv successfully")
    return result


def segment_using_lab(
    image: np.ndarray,
    lower_bound: Tuple[int, int, int] = (0, 0, 0),
    upper_bound: Tuple[int, int, int] = (255, 255, 255),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs LAB color space segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        lower_bound: Lower bound for LAB range. Default: (0, 0, 0).
        upper_bound: Upper bound for LAB range. Default: (255, 255, 255).
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    lab_segmentation = color.LABSegmentation(
        lower_bound=lower_bound,
        upper_bound=upper_bound
    )
    result = lab_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_lab successfully")
    return result


def segment_using_ycrcb(
    image: np.ndarray,
    lower_bound: Tuple[int, int, int] = (0, 133, 77),
    upper_bound: Tuple[int, int, int] = (255, 173, 127),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs YCrCb color space segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        lower_bound: Lower bound for YCrCb range. Default: (0, 133, 77).
        upper_bound: Upper bound for YCrCb range. Default: (255, 173, 127).
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    ycrcb_segmentation = color.YCrCbSegmentation(
        lower_bound=lower_bound,
        upper_bound=upper_bound
    )
    result = ycrcb_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_ycrcb successfully")
    return result


def segment_using_gray(
    image: np.ndarray,
    lower_bound: datatypes.Int = datatypes.Int(50),
    upper_bound: datatypes.Int = datatypes.Int(200),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs grayscale intensity segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        lower_bound: Lower bound for grayscale intensity. Default: 50.
        upper_bound: Upper bound for grayscale intensity. Default: 200.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(lower_bound, datatypes.Int):
        raise TypeError(
            f"lower_bound must be an Int object, class received: {type(lower_bound).__name__}"
        )
    if not isinstance(upper_bound, datatypes.Int):
        raise TypeError(
            f"upper_bound must be an Int object, class received: {type(upper_bound).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    gray_segmentation = color.GraySegmentation(
        lower_bound=lower_bound.value,
        upper_bound=upper_bound.value
    )
    result = gray_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_gray successfully")
    return result


# Contour Segmentation Functions
def segment_using_chan_vese(
    image: np.ndarray,
    contour_smoothness: datatypes.Float = datatypes.Float(0.25),
    foreground_weight: datatypes.Float = datatypes.Float(1),
    background_weight: datatypes.Float = datatypes.Float(1),
    convergence_tolerance: datatypes.Float = datatypes.Float(1e-3),
    max_iterations: datatypes.Int = datatypes.Int(200),
    time_step: datatypes.Float = datatypes.Float(0.5),
    initialization_method: datatypes.String = datatypes.String("checkerboard"),
    return_full_output: datatypes.Bool = datatypes.Bool(True),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs Chan-Vese segmentation on a grayscale image.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        contour_smoothness: Length term weight. Default: 0.25.
        foreground_weight: Weight for inside region. Default: 1.
        background_weight: Weight for outside region. Default: 1.
        convergence_tolerance: Tolerance for the stopping criterion. Default: 1e-3.
        max_iterations: Maximum number of iterations. Default: 200.
        time_step: Time step for level set updates. Default: 0.5.
        initialization_method: Initial level set shape. Default: "checkerboard".
        return_full_output: If True, returns the final level set as well. Default: True.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(contour_smoothness, datatypes.Float):
        raise TypeError(
            f"contour_smoothness must be a Float object, class received: {type(contour_smoothness).__name__}"
        )
    if not isinstance(foreground_weight, datatypes.Float):
        raise TypeError(
            f"foreground_weight must be a Float object, class received: {type(foreground_weight).__name__}"
        )
    if not isinstance(background_weight, datatypes.Float):
        raise TypeError(
            f"background_weight must be a Float object, class received: {type(background_weight).__name__}"
        )
    if not isinstance(convergence_tolerance, datatypes.Float):
        raise TypeError(
            f"convergence_tolerance must be a Float object, class received: {type(convergence_tolerance).__name__}"
        )
    if not isinstance(max_iterations, datatypes.Int):
        raise TypeError(
            f"max_iterations must be an Int object, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(time_step, datatypes.Float):
        raise TypeError(
            f"time_step must be a Float object, class received: {type(time_step).__name__}"
        )
    if not isinstance(initialization_method, datatypes.String):
        raise TypeError(
            f"initialization_method must be a String object, class received: {type(initialization_method).__name__}"
        )
    if not isinstance(return_full_output, datatypes.Bool):
        raise TypeError(
            f"return_full_output must be a Bool object, class received: {type(return_full_output).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    chan_vese_segmentation = contour.ChanVeseSegmentation(
        contour_smoothness=contour_smoothness.value,
        foreground_weight=foreground_weight.value,
        background_weight=background_weight.value,
        convergence_tolerance=convergence_tolerance.value,
        max_iterations=max_iterations.value,
        time_step=time_step.value,
        initialization_method=initialization_method.value,
        return_full_output=return_full_output.value
    )
    result = chan_vese_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_chan_vese successfully")
    return result


def segment_using_contour(
    image: np.ndarray,
    min_area: datatypes.Float = datatypes.Float(100.0),
    max_area: datatypes.Float = datatypes.Float(5000.0),
    contour_retrieval_mode: datatypes.String = datatypes.String("retr tree"),
    contour_approximation_method: datatypes.String = datatypes.String("chain approximation none"),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs contour-based segmentation based on area thresholds.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        min_area: Minimum contour area. Default: 100.0.
        max_area: Maximum contour area. Default: 5000.0.
        contour_retrieval_mode: Contour retrieval mode. Default: "retr tree".
        contour_approximation_method: Contour approximation method. Default: "chain approximation none".
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_area, datatypes.Float):
        raise TypeError(
            f"min_area must be a Float object, class received: {type(min_area).__name__}"
        )
    if not isinstance(max_area, datatypes.Float):
        raise TypeError(
            f"max_area must be a Float object, class received: {type(max_area).__name__}"
        )
    if not isinstance(contour_retrieval_mode, datatypes.String):
        raise TypeError(
            f"contour_retrieval_mode must be a String object, class received: {type(contour_retrieval_mode).__name__}"
        )
    if not isinstance(contour_approximation_method, datatypes.String):
        raise TypeError(
            f"contour_approximation_method must be a String object, class received: {type(contour_approximation_method).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    contour_segmentation = contour.ContourSegmentation(
        min_area=min_area.value,
        max_area=max_area.value,
        contour_retrieval_mode=contour_retrieval_mode.value,
        contour_approximation_method=contour_approximation_method.value
    )
    result = contour_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_contour successfully")
    return result


# Region Segmentation Functions
def segment_using_flood_fill(
    image: np.ndarray,
    seed_point: Tuple[int, int] = (0, 0),
    tolerance: datatypes.Int = datatypes.Int(10),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs flood fill segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        seed_point: Starting point for flood fill (x, y). Default: (0, 0).
        tolerance: Color tolerance for flood fill. Default: 10.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(tolerance, datatypes.Int):
        raise TypeError(
            f"tolerance must be an Int object, class received: {type(tolerance).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    flood_fill_segmentation = region.FloodFillSegmentation(
        seed_point=seed_point,
        tolerance=tolerance.value
    )
    result = flood_fill_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_flood_fill successfully")
    return result


def segment_using_label(
    image: np.ndarray,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs label-based segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    label_segmentation = region.LabelSegmentation()
    result = label_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_label successfully")
    return result


def segment_using_watershed(
    image: np.ndarray,
    markers: np.ndarray,
    connectivity: datatypes.Int = datatypes.Int(1),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs watershed segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        markers: Marker image for watershed segmentation.
        connectivity: Connectivity for watershed. Default: 1.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(connectivity, datatypes.Int):
        raise TypeError(
            f"connectivity must be an Int object, class received: {type(connectivity).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    watershed_segmentation = region.WatershedSegmentation(
        markers=markers,
        connectivity=connectivity.value
    )
    result = watershed_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_watershed successfully")
    return result


def segment_using_focus_region(
    image: np.ndarray,
    blur_kernel_size: datatypes.Int = datatypes.Int(10),
    threshold: datatypes.Int = datatypes.Int(1),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Segments the in-focus regions of an image.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        blur_kernel_size: Kernel size for blur operation. Default: 10.
        threshold: Threshold for focus detection. Default: 1.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(blur_kernel_size, datatypes.Int):
        raise TypeError(
            f"blur_kernel_size must be an Int object, class received: {type(blur_kernel_size).__name__}"
        )
    if not isinstance(threshold, datatypes.Int):
        raise TypeError(
            f"threshold must be an Int object, class received: {type(threshold).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    focus_region_segmentation = region.FocusRegionSegmentation(
        blur_kernel_size=blur_kernel_size.value,
        threshold=threshold.value
    )
    result = focus_region_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_focus_region successfully")
    return result


def segment_using_morphological_gac(
    image: np.ndarray,
    num_iterations: datatypes.Int = datatypes.Int(230),
    init_level_set: datatypes.String = datatypes.String('checkerboard'),
    balloon: datatypes.Int = datatypes.Int(0),
    threshold: datatypes.Float = datatypes.Float(0.69),
    smoothing: datatypes.Int = datatypes.Int(1),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs morphological geodesic active contour segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        num_iterations: Number of iterations. Default: 230.
        init_level_set: Initial level set shape. Default: 'checkerboard'.
        balloon: Balloon force. Default: 0.
        threshold: Threshold value. Default: 0.69.
        smoothing: Smoothing parameter. Default: 1.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(num_iterations, datatypes.Int):
        raise TypeError(
            f"num_iterations must be an Int object, class received: {type(num_iterations).__name__}"
        )
    if not isinstance(init_level_set, datatypes.String):
        raise TypeError(
            f"init_level_set must be a String object, class received: {type(init_level_set).__name__}"
        )
    if not isinstance(balloon, datatypes.Int):
        raise TypeError(
            f"balloon must be an Int object, class received: {type(balloon).__name__}"
        )
    if not isinstance(threshold, datatypes.Float):
        raise TypeError(
            f"threshold must be a Float object, class received: {type(threshold).__name__}"
        )
    if not isinstance(smoothing, datatypes.Int):
        raise TypeError(
            f"smoothing must be an Int object, class received: {type(smoothing).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    morphological_gac = region.MorphologicalGAC(
        num_iterations=num_iterations.value,
        init_level_set=init_level_set.value,
        balloon=balloon.value,
        threshold=threshold.value,
        smoothing=smoothing.value
    )
    result = morphological_gac.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_morphological_gac successfully")
    return result


# Threshold Segmentation Functions
def segment_using_otsu_threshold(
    image: np.ndarray,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs Otsu threshold segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    otsu_threshold_segmentation = threshold.OtsuThresholdSegmentation()
    result = otsu_threshold_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_otsu_threshold successfully")
    return result


def segment_using_local_threshold(
    image: np.ndarray,
    block_size: datatypes.Int = datatypes.Int(35),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs local threshold segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        block_size: Block size for local threshold. Default: 35.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(block_size, datatypes.Int):
        raise TypeError(
            f"block_size must be an Int object, class received: {type(block_size).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    local_threshold_segmentation = threshold.LocalThresholdSegmentation(
        block_size=block_size.value
    )
    result = local_threshold_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_local_threshold successfully")
    return result


def segment_using_yen_threshold(
    image: np.ndarray,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs Yen threshold segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    yen_threshold_segmentation = threshold.YenThresholdSegmentation()
    result = yen_threshold_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_yen_threshold successfully")
    return result


def segment_using_threshold(
    image: np.ndarray,
    min_value: datatypes.Int = datatypes.Int(127),
    max_value: datatypes.Int = datatypes.Int(255),
    threshold_type: datatypes.String = datatypes.String('binary'),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs basic threshold segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        min_value: Minimum threshold value. Default: 127.
        max_value: Maximum threshold value. Default: 255.
        threshold_type: Type of threshold. Default: 'binary'.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_value, datatypes.Int):
        raise TypeError(
            f"min_value must be an Int object, class received: {type(min_value).__name__}"
        )
    if not isinstance(max_value, datatypes.Int):
        raise TypeError(
            f"max_value must be an Int object, class received: {type(max_value).__name__}"
        )
    if not isinstance(threshold_type, datatypes.String):
        raise TypeError(
            f"threshold_type must be a String object, class received: {type(threshold_type).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    threshold_segmentation = threshold.ThresholdSegmentation(
        min_value=min_value.value,
        max_value=max_value.value,
        threshold_type=threshold_type.value
    )
    result = threshold_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_threshold successfully")
    return result


def segment_using_adaptive_threshold(
    image: np.ndarray,
    max_value: datatypes.Int = datatypes.Int(255),
    adaptive_method: datatypes.String = datatypes.String("gaussian constant"),
    threshold_type: datatypes.String = datatypes.String('binary'),
    block_size: datatypes.Int = datatypes.Int(11),
    offset_constant: datatypes.Int = datatypes.Int(2),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs adaptive threshold segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        max_value: Maximum value for threshold. Default: 255.
        adaptive_method: Adaptive method. Default: "gaussian constant".
        threshold_type: Type of threshold. Default: 'binary'.
        block_size: Block size for adaptive threshold. Default: 11.
        offset_constant: Offset constant. Default: 2.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(max_value, datatypes.Int):
        raise TypeError(
            f"max_value must be an Int object, class received: {type(max_value).__name__}"
        )
    if not isinstance(adaptive_method, datatypes.String):
        raise TypeError(
            f"adaptive_method must be a String object, class received: {type(adaptive_method).__name__}"
        )
    if not isinstance(threshold_type, datatypes.String):
        raise TypeError(
            f"threshold_type must be a String object, class received: {type(threshold_type).__name__}"
        )
    if not isinstance(block_size, datatypes.Int):
        raise TypeError(
            f"block_size must be an Int object, class received: {type(block_size).__name__}"
        )
    if not isinstance(offset_constant, datatypes.Int):
        raise TypeError(
            f"offset_constant must be an Int object, class received: {type(offset_constant).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    adaptive_threshold_segmentation = threshold.AdaptiveThresholdSegmentation(
        max_value=max_value.value,
        adaptive_method=adaptive_method.value,
        threshold_type=threshold_type.value,
        block_size=block_size.value,
        offset_constant=offset_constant.value
    )
    result = adaptive_threshold_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_adaptive_threshold successfully")
    return result


def segment_using_laplacian_threshold(
    image: np.ndarray,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs Laplacian threshold segmentation.

    Args:
        image: Input image (H, W) or (H, W, 3) as numpy array.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    laplacian_threshold_segmentation = threshold.LaplacianThresholdSegmentation()
    result = laplacian_threshold_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_laplacian_threshold successfully")
    return result


# Superpixel Segmentation Functions
def segment_using_felzenszwalb(
    image: np.ndarray,
    scale: datatypes.Int = datatypes.Int(100),
    sigma: datatypes.Float = datatypes.Float(0.5),
    min_size: datatypes.Int = datatypes.Int(50),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs Felzenszwalb segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        scale: Scale parameter. Default: 100.
        sigma: Sigma parameter. Default: 0.5.
        min_size: Minimum segment size. Default: 50.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(scale, datatypes.Int):
        raise TypeError(
            f"scale must be an Int object, class received: {type(scale).__name__}"
        )
    if not isinstance(sigma, datatypes.Float):
        raise TypeError(
            f"sigma must be a Float object, class received: {type(sigma).__name__}"
        )
    if not isinstance(min_size, datatypes.Int):
        raise TypeError(
            f"min_size must be an Int object, class received: {type(min_size).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    felzenszwalb_segmentation = superpixel.FelzenszwalbSegmentation(
        scale=scale.value,
        sigma=sigma.value,
        min_size=min_size.value
    )
    result = felzenszwalb_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_felzenszwalb successfully")
    return result


def segment_using_slic_superpixel(
    image: np.ndarray,
    num_segments: datatypes.Int = datatypes.Int(100),
    compactness: datatypes.Float = datatypes.Float(10.0),
    max_iterations: datatypes.Int = datatypes.Int(10),
    sigma: datatypes.Float = datatypes.Float(0),
    spacing: Optional[Tuple[int, int]] = None,
    convert_to_lab: Optional[datatypes.Bool] = None,
    enforce_connectivity: datatypes.Bool = datatypes.Bool(True),
    min_size_factor: datatypes.Float = datatypes.Float(0.5),
    max_size_factor: datatypes.Float = datatypes.Float(3),
    use_slic_zero: datatypes.Bool = datatypes.Bool(False),
    start_label: datatypes.Int = datatypes.Int(1),
    mask: Optional[np.ndarray] = None,
    channel_axis: datatypes.Int = datatypes.Int(-1),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs SLIC superpixel segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        num_segments: Number of segments. Default: 100.
        compactness: Compactness parameter. Default: 10.0.
        max_iterations: Maximum iterations. Default: 10.
        sigma: Sigma for Gaussian smoothing. Default: 0.
        spacing: Spacing between pixels. Default: None.
        convert_to_lab: Whether to convert to LAB color space. Default: None.
        enforce_connectivity: Whether to enforce connectivity. Default: True.
        min_size_factor: Minimum size factor. Default: 0.5.
        max_size_factor: Maximum size factor. Default: 3.
        use_slic_zero: Whether to use SLIC zero. Default: False.
        start_label: Starting label. Default: 1.
        mask: Optional mask. Default: None.
        channel_axis: Channel axis. Default: -1.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(num_segments, datatypes.Int):
        raise TypeError(
            f"num_segments must be an Int object, class received: {type(num_segments).__name__}"
        )
    if not isinstance(compactness, datatypes.Float):
        raise TypeError(
            f"compactness must be a Float object, class received: {type(compactness).__name__}"
        )
    if not isinstance(max_iterations, datatypes.Int):
        raise TypeError(
            f"max_iterations must be an Int object, class received: {type(max_iterations).__name__}"
        )
    if not isinstance(sigma, datatypes.Float):
        raise TypeError(
            f"sigma must be a Float object, class received: {type(sigma).__name__}"
        )
    if convert_to_lab is not None and not isinstance(convert_to_lab, datatypes.Bool):
        raise TypeError(
            f"convert_to_lab must be a Bool object or None, class received: {type(convert_to_lab).__name__}"
        )
    if not isinstance(enforce_connectivity, datatypes.Bool):
        raise TypeError(
            f"enforce_connectivity must be a Bool object, class received: {type(enforce_connectivity).__name__}"
        )
    if not isinstance(min_size_factor, datatypes.Float):
        raise TypeError(
            f"min_size_factor must be a Float object, class received: {type(min_size_factor).__name__}"
        )
    if not isinstance(max_size_factor, datatypes.Float):
        raise TypeError(
            f"max_size_factor must be a Float object, class received: {type(max_size_factor).__name__}"
        )
    if not isinstance(use_slic_zero, datatypes.Bool):
        raise TypeError(
            f"use_slic_zero must be a Bool object, class received: {type(use_slic_zero).__name__}"
        )
    if not isinstance(start_label, datatypes.Int):
        raise TypeError(
            f"start_label must be an Int object, class received: {type(start_label).__name__}"
        )
    if not isinstance(channel_axis, datatypes.Int):
        raise TypeError(
            f"channel_axis must be an Int object, class received: {type(channel_axis).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    slic_superpixel_segmentation = superpixel.SLICSuperpixelSegmentation(
        num_segments=num_segments.value,
        compactness=compactness.value,
        max_iterations=max_iterations.value,
        sigma=sigma.value,
        spacing=spacing,
        convert_to_lab=convert_to_lab.value if convert_to_lab is not None else None,
        enforce_connectivity=enforce_connectivity.value,
        min_size_factor=min_size_factor.value,
        max_size_factor=max_size_factor.value,
        use_slic_zero=use_slic_zero.value,
        start_label=start_label.value,
        mask=mask,
        channel_axis=channel_axis.value
    )
    result = slic_superpixel_segmentation.execute(image, mask=mask, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_slic_superpixel successfully")
    return result


# Superpixel Filter Functions
def filter_label_area(
    image: np.ndarray,
    labels: np.ndarray,
    min_area: datatypes.Int = datatypes.Int(20),
    max_area: datatypes.Int = datatypes.Int(1000),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Filters superpixels based on area.

    Args:
        image: Input image (H, W, 3) as numpy array.
        labels: Label image.
        min_area: Minimum area. Default: 20.
        max_area: Maximum area. Default: 1000.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing filtered results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_area, datatypes.Int):
        raise TypeError(
            f"min_area must be an Int object, class received: {type(min_area).__name__}"
        )
    if not isinstance(max_area, datatypes.Int):
        raise TypeError(
            f"max_area must be an Int object, class received: {type(max_area).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    label_area_filter = superpixel.LabelAreaFilter(
        min_area=min_area.value,
        max_area=max_area.value
    )
    result = label_area_filter.execute(image, labels, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called filter_label_area successfully")
    return result


def filter_label_color(
    image: np.ndarray,
    labels: np.ndarray,
    min_color: datatypes.Float = datatypes.Float(0.0),
    max_color: datatypes.Float = datatypes.Float(255.0),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Filters superpixels based on color.

    Args:
        image: Input image (H, W, 3) as numpy array.
        labels: Label image.
        min_color: Minimum color value. Default: 0.0.
        max_color: Maximum color value. Default: 255.0.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing filtered results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(min_color, datatypes.Float):
        raise TypeError(
            f"min_color must be a Float object, class received: {type(min_color).__name__}"
        )
    if not isinstance(max_color, datatypes.Float):
        raise TypeError(
            f"max_color must be a Float object, class received: {type(max_color).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    label_color_filter = superpixel.LabelColorFilter(
        min_color=min_color.value,
        max_color=max_color.value
    )
    result = label_color_filter.execute(image, labels, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called filter_label_color successfully")
    return result


def filter_label_mask(
    image: np.ndarray,
    labels: np.ndarray,
    mask: np.ndarray,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Filters superpixels based on a mask.

    Args:
        image: Input image (H, W, 3) as numpy array.
        labels: Label image.
        mask: Mask image.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing filtered results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    label_mask_filter = superpixel.LabelMaskFilter()
    result = label_mask_filter.execute(image, labels, mask, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called filter_label_mask successfully")
    return result


# Graph Functions
def generate_rag_using_similarity(
    image: np.ndarray,
    labels: np.ndarray,
    mode: datatypes.String = datatypes.String('similarity'),
    connectivity: datatypes.Int = datatypes.Int(2),
    sigma: datatypes.Float = datatypes.Float(1.0),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Generates a region adjacency graph.

    Args:
        image: Input image (H, W, 3) as numpy array.
        labels: Label image.
        mode: RAG generation mode. Default: 'similarity'.
        connectivity: Connectivity parameter. Default: 2.
        sigma: Sigma parameter. Default: 1.0.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing RAG generation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(mode, datatypes.String):
        raise TypeError(
            f"mode must be a String object, class received: {type(mode).__name__}"
        )
    if not isinstance(connectivity, datatypes.Int):
        raise TypeError(
            f"connectivity must be an Int object, class received: {type(connectivity).__name__}"
        )
    if not isinstance(sigma, datatypes.Float):
        raise TypeError(
            f"sigma must be a Float object, class received: {type(sigma).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    rag_generation = graph.RAGGeneration(
        mode=mode.value,
        connectivity=connectivity.value,
        sigma=sigma.value
    )
    result = rag_generation.execute(image, labels=labels, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called generate_rag_using_similarity successfully")
    return result


def segment_using_grab_cut(
    image: np.ndarray,
    num_iterations: datatypes.Int = datatypes.Int(5),
    initial_bbox: Optional[Tuple[int, int, int, int]] = None,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs GrabCut segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        num_iterations: Number of iterations. Default: 5.
        initial_bbox: Initial bounding box (x, y, w, h). Default: None.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(num_iterations, datatypes.Int):
        raise TypeError(
            f"num_iterations must be an Int object, class received: {type(num_iterations).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    grab_cut_segmentation = graph.GrabCutSegmentation(
        num_iterations=num_iterations.value,
        initial_bbox=initial_bbox
    )
    result = grab_cut_segmentation.execute(image, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_grab_cut successfully")
    return result


def segment_using_normalized_cut(
    image: np.ndarray,
    graph_obj: Any,
    segments: np.ndarray,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
) -> Dict[str, Any]:
    """
    Performs normalized cut segmentation.

    Args:
        image: Input image (H, W, 3) as numpy array.
        graph_obj: Graph object.
        segments: Segment image.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    
    normalized_cut_segmentation = graph.NormalizedCutSegmentation()
    result = normalized_cut_segmentation.execute(image, graph=graph_obj, segments=segments, image_id=image_id.value, file_name=file_name.value)
    logger.success("Called segment_using_normalized_cut successfully")
    return result


# Refinement Functions
def refine_using_crf(
    image: np.ndarray,
    mask: np.ndarray,
    ground_truth_probability: datatypes.Float = datatypes.Float(0.65),
    num_iterations: datatypes.Int = datatypes.Int(20),
    spatial_sigma_gaussian: Tuple[int, int] = (3, 3),
    spatial_sigma_bilateral: Tuple[int, int] = (50, 50),
    color_sigma_bilateral: Tuple[int, int, int] = (13, 13, 13),
    gaussian_pairwise_weight: datatypes.Int = datatypes.Int(3),
    bilateral_pairwise_weight: datatypes.Int = datatypes.Int(10),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Refines a segmentation mask using CRF.

    Args:
        image: Input image (H, W, 3) as numpy array.
        mask: Input mask to refine.
        ground_truth_probability: Ground truth probability. Default: 0.65.
        num_iterations: Number of iterations. Default: 20.
        spatial_sigma_gaussian: Spatial sigma for Gaussian. Default: (3, 3).
        spatial_sigma_bilateral: Spatial sigma for bilateral. Default: (50, 50).
        color_sigma_bilateral: Color sigma for bilateral. Default: (13, 13, 13).
        gaussian_pairwise_weight: Gaussian pairwise weight. Default: 3.
        bilateral_pairwise_weight: Bilateral pairwise weight. Default: 10.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing refined results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(ground_truth_probability, datatypes.Float):
        raise TypeError(
            f"ground_truth_probability must be a Float object, class received: {type(ground_truth_probability).__name__}"
        )
    if not isinstance(num_iterations, datatypes.Int):
        raise TypeError(
            f"num_iterations must be an Int object, class received: {type(num_iterations).__name__}"
        )
    if not isinstance(gaussian_pairwise_weight, datatypes.Int):
        raise TypeError(
            f"gaussian_pairwise_weight must be an Int object, class received: {type(gaussian_pairwise_weight).__name__}"
        )
    if not isinstance(bilateral_pairwise_weight, datatypes.Int):
        raise TypeError(
            f"bilateral_pairwise_weight must be an Int object, class received: {type(bilateral_pairwise_weight).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    crf_refiner = refinement.CRFRefiner(
        ground_truth_probability=ground_truth_probability.value,
        num_iterations=num_iterations.value,
        spatial_sigma_gaussian=spatial_sigma_gaussian,
        spatial_sigma_bilateral=spatial_sigma_bilateral,
        color_sigma_bilateral=color_sigma_bilateral,
        gaussian_pairwise_weight=gaussian_pairwise_weight.value,
        bilateral_pairwise_weight=bilateral_pairwise_weight.value
    )
    result = crf_refiner.execute(image, mask, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called refine_using_crf successfully")
    return result


def refine_using_component_connecting(
    mask: np.ndarray,
    connectivity: datatypes.Int = datatypes.Int(8),
    connected_components_type: datatypes.String = datatypes.String("stat_area"),
    min_area: datatypes.Int = datatypes.Int(0),
    max_area: datatypes.Int = datatypes.Int(10000),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Refines a segmentation mask by connecting components.

    Args:
        mask: Input mask to refine.
        connectivity: Connectivity parameter. Default: 8.
        connected_components_type: Type of connected components. Default: "stat_area".
        min_area: Minimum area. Default: 0.
        max_area: Maximum area. Default: 10000.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing refined results in COCO panoptic format.
    """
    if not isinstance(mask, np.ndarray):
        raise TypeError(
            f"mask must be a numpy array, class received: {type(mask).__name__}"
        )
    if not isinstance(connectivity, datatypes.Int):
        raise TypeError(
            f"connectivity must be an Int object, class received: {type(connectivity).__name__}"
        )
    if not isinstance(connected_components_type, datatypes.String):
        raise TypeError(
            f"connected_components_type must be a String object, class received: {type(connected_components_type).__name__}"
        )
    if not isinstance(min_area, datatypes.Int):
        raise TypeError(
            f"min_area must be an Int object, class received: {type(min_area).__name__}"
        )
    if not isinstance(max_area, datatypes.Int):
        raise TypeError(
            f"max_area must be an Int object, class received: {type(max_area).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    component_connecting_refiner = refinement.ComponentConnectingRefiner(
        connectivity=connectivity.value,
        connected_components_type=connected_components_type.value,
        min_area=min_area.value,
        max_area=max_area.value
    )
    result = component_connecting_refiner.execute(mask, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called refine_using_component_connecting successfully")
    return result


# Tracking Functions
def track_using_xmem(
    image: np.ndarray,
    mask: np.ndarray,
    pretrained_model_name_or_path: datatypes.String = datatypes.String("path/to/xmem_model.pth"),
    frame_interval_in_memory: datatypes.Int = datatypes.Int(5),
    deep_update_interval_in_memory: datatypes.Int = datatypes.Int(5),
    enable_long_term: datatypes.Bool = datatypes.Bool(False),
    enable_long_term_count_usage: datatypes.Bool = datatypes.Bool(False),
    min_mid_term_frames: datatypes.Int = datatypes.Int(5),
    max_mid_term_frames: datatypes.Int = datatypes.Int(10),
    num_prototypes: datatypes.Int = datatypes.Int(128),
    max_long_term_elements: datatypes.Int = datatypes.Int(10000),
    top_k: datatypes.Int = datatypes.Int(30),
    enable_mixed_precision: datatypes.Bool = datatypes.Bool(True),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Tracks a mask using XMem.

    Args:
        image: Input image (H, W, 3) as numpy array.
        mask: Input mask to track.
        pretrained_model_name_or_path: Path to pretrained model. Default: "path/to/xmem_model.pth".
        frame_interval_in_memory: Frame interval in memory. Default: 5.
        deep_update_interval_in_memory: Deep update interval in memory. Default: 5.
        enable_long_term: Enable long term memory. Default: False.
        enable_long_term_count_usage: Enable long term count usage. Default: False.
        min_mid_term_frames: Minimum mid term frames. Default: 5.
        max_mid_term_frames: Maximum mid term frames. Default: 10.
        num_prototypes: Number of prototypes. Default: 128.
        max_long_term_elements: Maximum long term elements. Default: 10000.
        top_k: Top k value. Default: 30.
        enable_mixed_precision: Enable mixed precision. Default: True.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing tracking results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(pretrained_model_name_or_path, datatypes.String):
        raise TypeError(
            f"pretrained_model_name_or_path must be a String object, class received: {type(pretrained_model_name_or_path).__name__}"
        )
    if not isinstance(frame_interval_in_memory, datatypes.Int):
        raise TypeError(
            f"frame_interval_in_memory must be an Int object, class received: {type(frame_interval_in_memory).__name__}"
        )
    if not isinstance(deep_update_interval_in_memory, datatypes.Int):
        raise TypeError(
            f"deep_update_interval_in_memory must be an Int object, class received: {type(deep_update_interval_in_memory).__name__}"
        )
    if not isinstance(enable_long_term, datatypes.Bool):
        raise TypeError(
            f"enable_long_term must be a Bool object, class received: {type(enable_long_term).__name__}"
        )
    if not isinstance(enable_long_term_count_usage, datatypes.Bool):
        raise TypeError(
            f"enable_long_term_count_usage must be a Bool object, class received: {type(enable_long_term_count_usage).__name__}"
        )
    if not isinstance(min_mid_term_frames, datatypes.Int):
        raise TypeError(
            f"min_mid_term_frames must be an Int object, class received: {type(min_mid_term_frames).__name__}"
        )
    if not isinstance(max_mid_term_frames, datatypes.Int):
        raise TypeError(
            f"max_mid_term_frames must be an Int object, class received: {type(max_mid_term_frames).__name__}"
        )
    if not isinstance(num_prototypes, datatypes.Int):
        raise TypeError(
            f"num_prototypes must be an Int object, class received: {type(num_prototypes).__name__}"
        )
    if not isinstance(max_long_term_elements, datatypes.Int):
        raise TypeError(
            f"max_long_term_elements must be an Int object, class received: {type(max_long_term_elements).__name__}"
        )
    if not isinstance(top_k, datatypes.Int):
        raise TypeError(
            f"top_k must be an Int object, class received: {type(top_k).__name__}"
        )
    if not isinstance(enable_mixed_precision, datatypes.Bool):
        raise TypeError(
            f"enable_mixed_precision must be a Bool object, class received: {type(enable_mixed_precision).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    mask_xmem_tracker = tracking.MaskXmemTracker(
        pretrained_model_name_or_path=pretrained_model_name_or_path.value,
        frame_interval_in_memory=frame_interval_in_memory.value,
        deep_update_interval_in_memory=deep_update_interval_in_memory.value,
        enable_long_term=enable_long_term.value,
        enable_long_term_count_usage=enable_long_term_count_usage.value,
        min_mid_term_frames=min_mid_term_frames.value,
        max_mid_term_frames=max_mid_term_frames.value,
        num_prototypes=num_prototypes.value,
        max_long_term_elements=max_long_term_elements.value,
        top_k=top_k.value,
        enable_mixed_precision=enable_mixed_precision.value
    )
    result = mask_xmem_tracker.execute(image, mask=mask, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called track_using_xmem successfully")
    return result


def track_using_sam2(
    image: np.ndarray,
    mask: np.ndarray,
    pretrained_model_name_or_path: datatypes.String = datatypes.String("path/to/sam2_model.pt"),
    model_config_filepath: datatypes.String = datatypes.String("path/to/sam2_config.yaml"),
    num_clicks: datatypes.Int = datatypes.Int(5),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Tracks a mask using SAM2.

    Args:
        image: Input image (H, W, 3) as numpy array.
        mask: Input mask to track.
        pretrained_model_name_or_path: Path to pretrained model. Default: "path/to/sam2_model.pt".
        model_config_filepath: Path to model config. Default: "path/to/sam2_config.yaml".
        num_clicks: Number of clicks. Default: 5.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing tracking results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(pretrained_model_name_or_path, datatypes.String):
        raise TypeError(
            f"pretrained_model_name_or_path must be a String object, class received: {type(pretrained_model_name_or_path).__name__}"
        )
    if not isinstance(model_config_filepath, datatypes.String):
        raise TypeError(
            f"model_config_filepath must be a String object, class received: {type(model_config_filepath).__name__}"
        )
    if not isinstance(num_clicks, datatypes.Int):
        raise TypeError(
            f"num_clicks must be an Int object, class received: {type(num_clicks).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    mask_sam2_tracker = tracking.MaskSAM2Tracker(
        pretrained_model_name_or_path=pretrained_model_name_or_path.value,
        model_config_filepath=model_config_filepath.value,
        num_clicks=num_clicks.value
    )
    result = mask_sam2_tracker.execute(image, mask=mask, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called track_using_sam2 successfully")
    return result


# Deep Learning Functions
def segment_using_foreground_birefnet(
    image: np.ndarray,
    pretrained_model_name_or_path: datatypes.String = datatypes.String("zhengpeng7/BiRefNet"),
    image_into_model_height: datatypes.Int = datatypes.Int(1024),
    image_into_model_width: datatypes.Int = datatypes.Int(1024),
    pixel_value_threshold: datatypes.Int = datatypes.Int(0),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Segments the foreground using BiRefNet.

    Args:
        image: Input image (H, W, 3) as numpy array.
        pretrained_model_name_or_path: Path to pretrained model. Default: "zhengpeng7/BiRefNet".
        image_into_model_height: Image height for model. Default: 1024.
        image_into_model_width: Image width for model. Default: 1024.
        pixel_value_threshold: Pixel value threshold. Default: 0.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(pretrained_model_name_or_path, datatypes.String):
        raise TypeError(
            f"pretrained_model_name_or_path must be a String object, class received: {type(pretrained_model_name_or_path).__name__}"
        )
    if not isinstance(image_into_model_height, datatypes.Int):
        raise TypeError(
            f"image_into_model_height must be an Int object, class received: {type(image_into_model_height).__name__}"
        )
    if not isinstance(image_into_model_width, datatypes.Int):
        raise TypeError(
            f"image_into_model_width must be an Int object, class received: {type(image_into_model_width).__name__}"
        )
    if not isinstance(pixel_value_threshold, datatypes.Int):
        raise TypeError(
            f"pixel_value_threshold must be an Int object, class received: {type(pixel_value_threshold).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    foreground_birefnet_segmentor = deep.ForegroundBiRefNetSegmentor(
        pretrained_model_name_or_path=pretrained_model_name_or_path.value,
        image_into_model_height=image_into_model_height.value,
        image_into_model_width=image_into_model_width.value,
        pixel_value_threshold=pixel_value_threshold.value
    )
    result = foreground_birefnet_segmentor.execute(image, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called segment_using_foreground_birefnet successfully")
    return result


def segment_using_deep_learning(
    image: np.ndarray,
    model_filepath: datatypes.String = datatypes.String("path/to/model.ts"),
    score_threshold: datatypes.Float = datatypes.Float(0.5),
    classes_of_interest: Optional[Union[int, List[int]]] = None,
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Performs image segmentation using a deep learning model.

    Args:
        image: Input image (H, W, 3) as numpy array.
        model_filepath: Path to model file. Default: "path/to/model.ts".
        score_threshold: Score threshold. Default: 0.5.
        classes_of_interest: Classes of interest. Default: None.
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(model_filepath, datatypes.String):
        raise TypeError(
            f"model_filepath must be a String object, class received: {type(model_filepath).__name__}"
        )
    if not isinstance(score_threshold, datatypes.Float):
        raise TypeError(
            f"score_threshold must be a Float object, class received: {type(score_threshold).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    image_deep_learning_segmentor = deep.ImageDeepLearningSegmentor(
        model_filepath=model_filepath.value,
        score_threshold=score_threshold.value,
        classes_of_interest=classes_of_interest
    )
    result = image_deep_learning_segmentor.execute(image, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called segment_using_deep_learning successfully")
    return result


def segment_using_sam(
    image: np.ndarray,
    bboxes: List[List[int]],
    model_name: datatypes.String = datatypes.String("facebook/sam-vit-base"),
    image_id: datatypes.Int = datatypes.Int(0),
    file_name: datatypes.String = datatypes.String(""),
    return_coco: datatypes.Bool = datatypes.Bool(True),
) -> Dict[str, Any]:
    """
    Performs segmentation using SAM (Segment Anything Model).

    Args:
        image: Input image (H, W, 3) as numpy array.
        bboxes: List of bounding boxes [[x1, y1, x2, y2], ...].
        model_name: Model name. Default: "facebook/sam-vit-base".
        image_id: Image identifier for COCO format. Default: 0.
        file_name: Source image filename. Default: "".
        return_coco: Whether to return COCO format. Default: True.

    Returns:
        Dictionary containing segmentation results in COCO panoptic format.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(
            f"image must be a numpy array, class received: {type(image).__name__}"
        )
    if not isinstance(model_name, datatypes.String):
        raise TypeError(
            f"model_name must be a String object, class received: {type(model_name).__name__}"
        )
    if not isinstance(image_id, datatypes.Int):
        raise TypeError(
            f"image_id must be an Int object, class received: {type(image_id).__name__}"
        )
    if not isinstance(file_name, datatypes.String):
        raise TypeError(
            f"file_name must be a String object, class received: {type(file_name).__name__}"
        )
    if not isinstance(return_coco, datatypes.Bool):
        raise TypeError(
            f"return_coco must be a Bool object, class received: {type(return_coco).__name__}"
        )
    
    sam_segmentor = deep.SAMSegmentor(
        model_name=model_name.value
    )
    result = sam_segmentor.execute(image, bboxes=bboxes, image_id=image_id.value, file_name=file_name.value, return_coco=return_coco.value)
    logger.success("Called segment_using_sam successfully")
    return result

