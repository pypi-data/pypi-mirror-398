"""Image compositing module for creating alternating row/column composites."""

from PIL import Image
import numpy as np
from math import lcm
from typing import Literal, List, Optional


def create_solid_image(color: str, width: int, height: int) -> np.ndarray:
    """
    Create a solid color image array.
    
    Args:
        color: 'white' or 'black'
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        RGB image array filled with the solid color
        
    Raises:
        ValueError: If color is not 'white' or 'black'
    """
    if color.lower() not in ('white', 'black'):
        raise ValueError(f"Color must be 'white' or 'black', got '{color}'")
    
    color_value = 255 if color.lower() == 'white' else 0
    return np.full((height, width, 3), color_value, dtype=np.uint8)


def tile_image(image_array: np.ndarray, target_height: int, target_width: int) -> np.ndarray:
    """
    Tile an image to match target dimensions.
    
    Args:
        image_array: The image array to tile
        target_height: Target height in pixels
        target_width: Target width in pixels
        
    Returns:
        Tiled image array with exact target dimensions
    """
    current_height, current_width = image_array.shape[:2]
    
    # Calculate how many times to tile in each direction
    tiles_y = (target_height + current_height - 1) // current_height
    tiles_x = (target_width + current_width - 1) // current_width
    
    # Tile the image
    if len(image_array.shape) == 3:
        tiled = np.tile(image_array, (tiles_y, tiles_x, 1))
    else:
        tiled = np.tile(image_array, (tiles_y, tiles_x))
    
    # Crop to exact target dimensions
    return tiled[:target_height, :target_width]


# Define a maximum size for input images
MAX_IMAGE_SIZE = (2000, 2000)  # (width, height)

def compute_target_dimension(sizes: List[int], mode: Literal['max', 'lcm']) -> int:
    """
    Compute the target dimension for tiling.

    Args:
        sizes: List of image dimensions along one axis.
        mode: 'max' for maximum, 'lcm' for least common multiple.

    Returns:
        Target dimension as an integer.
    """
    if mode == 'max':
        return max(sizes)
    elif mode == 'lcm':
        result = sizes[0]
        for size in sizes[1:]:
            result = lcm(result, size)
        return result
    else:
        raise ValueError(f"Tiling mode must be 'max' or 'lcm', got '{mode}'")

def validate_image_size(image: Image.Image) -> None:
    """
    Validate that the image does not exceed the maximum allowed size.

    Args:
        image: PIL Image object to validate.

    Raises:
        ValueError: If the image exceeds the maximum size.
    """
    if image.width > MAX_IMAGE_SIZE[0] or image.height > MAX_IMAGE_SIZE[1]:
        raise ValueError(
            f"Image size {image.width}x{image.height} exceeds the maximum allowed size of {MAX_IMAGE_SIZE[0]}x{MAX_IMAGE_SIZE[1]} pixels."
        )


def validate_and_load_images(
    image_paths: List[str],
    tiling_mode: Literal['max', 'lcm'] = 'max',
    interleave_mode: Literal['rows', 'columns'] = 'rows'
) -> List[np.ndarray]:
    """
    Load and validate multiple images (supports 'white'/'black'), then tile to match.

    - Accepts file paths and the strings 'white' or 'black' for solid colors.
    - Enforces per-image maximum size (2000x2000) for file-based images.
    - Requires at least one real image to define target dimensions.
    - Supports two tiling modes:
      - 'max': tile all to the maximum dimension (existing behavior)
      - 'lcm': tile to the least common multiple of dimensions in the interleave direction

    Args:
        image_paths: List of image file paths or 'white'/'black'.
        tiling_mode: 'max' or 'lcm' for how to compute target dimensions.
        interleave_mode: 'rows' or 'columns' to determine which dimension to compute LCM on.

    Returns:
        List of image arrays with matching dimensions.

    Raises:
        ValueError: If any file image exceeds max size, if no real image is provided,
                   or if computed LCM target exceeds MAX_IMAGE_SIZE.
    """
    real_images: List[np.ndarray] = []
    widths: List[int] = []
    heights: List[int] = []

    # First pass: load real images and collect dimensions
    for path in image_paths:
        if isinstance(path, str) and path.lower() in ("white", "black"):
            continue
        img = Image.open(path)
        validate_image_size(img)
        img = img.convert("RGB")
        arr = np.array(img)
        real_images.append(arr)
        widths.append(img.width)
        heights.append(img.height)

    if not real_images:
        raise ValueError("At least one input must be a real image file (not all 'white'/'black').")

    # Compute target dimensions based on tiling mode
    # In 'lcm' mode we now tile both axes to the least common multiple
    # (this ensures consistent tiling in both directions).
    if tiling_mode == 'lcm':
        target_height = compute_target_dimension(heights, 'lcm')
        target_width = compute_target_dimension(widths, 'lcm')
    else:  # max mode
        target_height = max(heights)
        target_width = max(widths)

    # Validate computed target does not exceed MAX_IMAGE_SIZE
    if target_width > MAX_IMAGE_SIZE[0] or target_height > MAX_IMAGE_SIZE[1]:
        raise ValueError(
            f"Computed target size {target_width}x{target_height} exceeds the maximum allowed size of "
            f"{MAX_IMAGE_SIZE[0]}x{MAX_IMAGE_SIZE[1]} pixels. Try using --tile-mode max or smaller images."
        )

    # Build final list following original order, creating solids where requested
    result_images: List[np.ndarray] = []
    real_iter = iter(real_images)
    for path in image_paths:
        if isinstance(path, str) and path.lower() in ("white", "black"):
            result_images.append(create_solid_image(path, target_width, target_height))
        else:
            # Next real image (tile if smaller than target)
            arr = next(real_iter)
            if arr.shape[0] != target_height or arr.shape[1] != target_width:
                arr = tile_image(arr, target_height, target_width)
            result_images.append(arr)

    return result_images


def composite_rows(image1_path: str, image2_path: str, output_path: str, tiling_mode: Literal['max', 'lcm'] = 'max') -> None:
    """
    Create a composite image by interleaving rows from two images.
    
    Output structure:
    - Row 0: from image1 row 0
    - Row 1: from image2 row 0
    - Row 2: from image1 row 1
    - Row 3: from image2 row 1
    - etc.
    
    The output image height will be 2x the input height (or N times if N images use LCM tiling).
    
    Args:
        image1_path: Path to the first input image
        image2_path: Path to the second input image
        output_path: Path to save the output composite image
        tiling_mode: 'max' (default) or 'lcm' for tiling strategy
    """
    images = validate_and_load_images([image1_path, image2_path], tiling_mode=tiling_mode, interleave_mode='rows')
    img1_array, img2_array = images[0], images[1]
    
    height, width = img1_array.shape[:2]
    
    # Create output array with 2x height (interleaved rows)
    if len(img1_array.shape) == 3:
        output = np.zeros((height * 2, width, img1_array.shape[2]), dtype=img1_array.dtype)
    else:
        output = np.zeros((height * 2, width), dtype=img1_array.dtype)
    
    # Interleave rows starting from the bottom of each source image using
    # per-image pointers so repeated rows consume subsequent rows upward.
    pointers = [height - 1, height - 1]
    out_idx = 0
    for _ in range(height):
        for img_i, img in enumerate((img1_array, img2_array)):
            if out_idx < output.shape[0]:
                src_r = pointers[img_i] % height
                output[out_idx] = img[src_r]
                pointers[img_i] = (pointers[img_i] - 1) % height
                out_idx += 1

    # Final vertical reflection (flip top/bottom) as the last operation
    output = output[::-1]

    # Save the result
    result_image = Image.fromarray(output)
    result_image.save(output_path)


def composite_columns(image1_path: str, image2_path: str, output_path: str, tiling_mode: Literal['max', 'lcm'] = 'max') -> None:
    """
    Create a composite image by interleaving columns from two images.
    
    Output structure:
    - Column 0: from image1 column 0
    - Column 1: from image2 column 0
    - Column 2: from image1 column 1
    - Column 3: from image2 column 1
    - etc.
    
    The output image width will be 2x the input width (or N times if N images use LCM tiling).
    
    Args:
        image1_path: Path to the first input image
        image2_path: Path to the second input image
        output_path: Path to save the output composite image
        tiling_mode: 'max' (default) or 'lcm' for tiling strategy
    """
    images = validate_and_load_images([image1_path, image2_path], tiling_mode=tiling_mode, interleave_mode='columns')
    img1_array, img2_array = images[0], images[1]
    
    height, width = img1_array.shape[:2]
    
    # Create output array with 2x width (interleaved columns)
    if len(img1_array.shape) == 3:
        output = np.zeros((height, width * 2, img1_array.shape[2]), dtype=img1_array.dtype)
    else:
        output = np.zeros((height, width * 2), dtype=img1_array.dtype)
    
    # Interleave columns: odd columns from img1, even columns from img2
    output[:, ::2] = img1_array   # Columns 0, 2, 4, ... from image1
    output[:, 1::2] = img2_array  # Columns 1, 3, 5, ... from image2
    
    # Save the result
    result_image = Image.fromarray(output)
    result_image.save(output_path)


def composite(
    image1_path: str, 
    image2_path: str, 
    output_path: str, 
    mode: Literal['rows', 'columns'] = 'rows',
    tiling_mode: Literal['max', 'lcm'] = 'max'
) -> None:
    """
    Create a composite image by alternating rows or columns from two images.
    
    Args:
        image1_path: Path to the first input image
        image2_path: Path to the second input image
        output_path: Path to save the output composite image
        mode: 'rows' to alternate rows, 'columns' to alternate columns
        tiling_mode: 'max' (default) or 'lcm' for tiling strategy
        
    Raises:
        ValueError: If mode is not 'rows' or 'columns', or if images don't match
    """
    if mode not in ('rows', 'columns'):
        raise ValueError(f"Mode must be 'rows' or 'columns', got '{mode}'")
    
    if mode == 'rows':
        composite_rows(image1_path, image2_path, output_path, tiling_mode=tiling_mode)
    else:
        composite_columns(image1_path, image2_path, output_path, tiling_mode=tiling_mode)


def interlace_rows(image1_path: str, image2_path: str, output_path: str, tiling_mode: Literal['max', 'lcm'] = 'max') -> None:
    """
    Create a same-size interlaced image by taking alternating rows from two images.

    Behavior:
    - Output has the same height/width as the (tiled) input images
    - Output rows at even indices come from `image1`'s corresponding even rows
    - Output rows at odd indices come from `image2`'s corresponding odd rows

    Args:
        image1_path: Path to the first input image
        image2_path: Path to the second input image
        output_path: Path to save the output interlaced image
        tiling_mode: 'max' (default) or 'lcm' for tiling strategy
    """
    images = validate_and_load_images([image1_path, image2_path], tiling_mode=tiling_mode, interleave_mode='rows')
    img1_array, img2_array = images[0], images[1]

    height, width = img1_array.shape[:2]

    # Create output array with same shape
    if len(img1_array.shape) == 3:
        output = np.zeros((height, width, img1_array.shape[2]), dtype=img1_array.dtype)
    else:
        output = np.zeros((height, width), dtype=img1_array.dtype)

    # Interlace rows in-place using corresponding row indices
    output[::2] = img1_array[::2]
    output[1::2] = img2_array[1::2]

    result_image = Image.fromarray(output)
    result_image.save(output_path)


def interlace_columns(image1_path: str, image2_path: str, output_path: str, tiling_mode: Literal['max', 'lcm'] = 'max') -> None:
    """
    Create a same-size interlaced image by taking alternating columns from two images.

    Behavior:
    - Output has the same height/width as the (tiled) input images
    - Output columns at even indices come from `image1`'s corresponding even columns
    - Output columns at odd indices come from `image2`'s corresponding odd columns
    
    Args:
        image1_path: Path to the first input image
        image2_path: Path to the second input image
        output_path: Path to save the output interlaced image
        tiling_mode: 'max' (default) or 'lcm' for tiling strategy
    """
    images = validate_and_load_images([image1_path, image2_path], tiling_mode=tiling_mode, interleave_mode='columns')
    img1_array, img2_array = images[0], images[1]

    height, width = img1_array.shape[:2]

    # Create output array with same shape
    if len(img1_array.shape) == 3:
        output = np.zeros((height, width, img1_array.shape[2]), dtype=img1_array.dtype)
    else:
        output = np.zeros((height, width), dtype=img1_array.dtype)

    # Interlace columns in-place using corresponding column indices
    output[:, ::2] = img1_array[:, ::2]
    output[:, 1::2] = img2_array[:, 1::2]

    result_image = Image.fromarray(output)
    result_image.save(output_path)


def interlace(
    image1_path: str, 
    image2_path: str, 
    output_path: str, 
    mode: Literal['rows', 'columns'] = 'rows',
    tiling_mode: Literal['max', 'lcm'] = 'max'
) -> None:
    """
    Wrapper to call interlace_rows or interlace_columns based on `mode`.
    """
    if mode not in ('rows', 'columns'):
        raise ValueError(f"Mode must be 'rows' or 'columns', got '{mode}'")

    if mode == 'rows':
        interlace_rows(image1_path, image2_path, output_path, tiling_mode=tiling_mode)
    else:
        interlace_columns(image1_path, image2_path, output_path, tiling_mode=tiling_mode)


def composite_n_images(image_paths: List[str], output_path: str, mode: Literal['rows', 'columns'] = 'rows', tiling_mode: Literal['max', 'lcm'] = 'max', stride: Optional[List[int]] = None) -> None:
    """
    Create a composite image by interleaving rows or columns from multiple images.

    Args:
        image_paths: List of input image paths (up to 6).
        output_path: Path to save the output composite image.
        mode: 'rows' to alternate rows, 'columns' to alternate columns.
        tiling_mode: 'max' (default) or 'lcm' for tiling strategy.
        stride: List of integers specifying how many rows/columns to take from each image.
                e.g., [1, 2, 1] takes 1 row from img1, 2 from img2, 1 from img3, then repeats.
                Defaults to [1, 1, ...] (one row/column per image).

    Raises:
        ValueError: If mode is not 'rows' or 'columns', or if more than 6 images are provided.
    """
    if len(image_paths) > 6:
        raise ValueError("A maximum of 6 images can be interleaved.")

    if mode not in ('rows', 'columns'):
        raise ValueError(f"Mode must be 'rows' or 'columns', got '{mode}'")

    # Load and validate images
    images = validate_and_load_images(image_paths, tiling_mode=tiling_mode, interleave_mode=mode)

    # Default stride: 1 row/column per image
    if stride is None:
        stride = [1] * len(images)
    
    # Validate stride
    if len(stride) != len(images):
        raise ValueError(f"Stride length ({len(stride)}) must match number of images ({len(images)})")
    if any(s < 1 for s in stride):
        raise ValueError("All stride values must be at least 1")

    # Determine output dimensions
    height, width = images[0].shape[:2]
    stride_sum = sum(stride)
    
    if mode == 'rows':
        output_shape = (height * stride_sum, width, 3)
    else:
        output_shape = (height, width * stride_sum, 3)

    # Create output array
    output = np.zeros(output_shape, dtype=images[0].dtype)

    # Interleave rows or columns using stride pattern.
    # Initialize per-image pointers to start from bottom for rows (height-1)
    # and from rightmost for columns (width-1). Decrement pointers so we
    # move upward/leftward through each source image.
    if mode == 'rows':
        pointers = [height - 1] * len(images)
        out_idx = 0
        for _ in range(height):
            for img_i, (img, count) in enumerate(zip(images, stride)):
                for _ in range(count):
                    if out_idx < output_shape[0]:
                        src_r = pointers[img_i] % height
                        output[out_idx] = img[src_r]
                        pointers[img_i] = (pointers[img_i] - 1) % height
                        out_idx += 1
    else:  # columns
        pointers = [width - 1] * len(images)
        out_idx = 0
        for _ in range(width):
            for img_i, (img, count) in enumerate(zip(images, stride)):
                for _ in range(count):
                    if out_idx < output_shape[1]:
                        src_c = pointers[img_i] % width
                        output[:, out_idx] = img[:, src_c]
                        pointers[img_i] = (pointers[img_i] - 1) % width
                        out_idx += 1

    # For rows-mode, apply final vertical reflection (flip top/bottom) as the last operation
    if mode == 'rows':
        output = output[::-1]

    # Save the result
    result_image = Image.fromarray(output)
    result_image.save(output_path)
