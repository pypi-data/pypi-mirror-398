from typing import Tuple, Optional
import numpy as np
from osgeo import gdal
import os
from PIL import Image


def ReadGeoTiff(file_name: str) -> Tuple[np.ndarray, Tuple[float, float, float, float, float, float], str]:
    """
    Reads a GeoTIFF file and returns the image data, geotransformation parameters, and projection information.

    Parameters:
        file_name (str): Path to the input GeoTIFF file.

    Returns:
        Tuple[np.ndarray, Tuple[float, float, float, float, float, float], str]:
        - im_data: Image data as a NumPy array.
        - im_geotrans: Geotransformation parameters (tuple of 6 floats).
        - im_proj: Projection information as a string.

    Raises:
        FileNotFoundError: If the file cannot be opened or does not exist.
    """
    dataset = gdal.Open(file_name)
    if dataset is None:
        raise FileNotFoundError(f"File {file_name} cannot be opened or does not exist.")

    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()

    return im_data, im_geotrans, im_proj


def CreateGeoTiff(
        out_raster: str,
        image: np.ndarray,
        geo_transform: Optional[Tuple[float, float, float, float, float, float]] = None,
        projection: Optional[str] = None,
        dtype: str = "float",
        compress: bool = False
) -> None:
    """
    Creates a GeoTIFF file.

    Parameters:
        out_raster (str): Path to the output GeoTIFF file.
        image (np.ndarray): Image data as a NumPy array.
        geo_transform (Tuple[float, float, float, float, float, float]): Geotransformation parameters (tuple of 6 floats).
        projection (str): Projection information in WKT format.
        dtype (str, optional): Data type, defaults to 'float'. Options: 'int16', 'int32', 'float'.
        compress (bool, optional): Whether to apply LZW lossless compression, defaults to False.

    Returns:
        None

    Raises:
        ValueError: If the image data shape is invalid.
        IOError: If the GeoTIFF file cannot be created.
    """
    gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
    dtype_mapping = {"int16": gdal.GDT_Int16, "int32": gdal.GDT_Int32, "float": gdal.GDT_Float32}
    gdal_dtype = dtype_mapping.get(dtype, gdal.GDT_Float32)

    # 获取影像维度
    shape = image.shape
    if len(shape) == 2:
        bands, rows, cols = 1, *shape
    elif len(shape) == 3:
        bands, rows, cols = shape
    else:
        raise ValueError("Invalid image data format. Expected shape (H, W) or (C, H, W).")

    # 创建数据集
    driver = gdal.GetDriverByName("GTiff")

    # 如果文件大于2GB，启用BIGTIFF（留些余量）
    estimated_size_gb = (bands * rows * cols * image.itemsize) / (1024 ** 3)
    if estimated_size_gb > 2.0:
        options = ["TILED=YES", f"COMPRESS=LZW", "BIGTIFF=YES"]
    else:
        options = ["TILED=YES", f"COMPRESS=LZW"] if compress else []

    dataset = driver.Create(out_raster, cols, rows, bands, gdal_dtype, options=options)

    if dataset is None:
        raise IOError(f"Failed to create GeoTIFF file: {out_raster}")

    # 如果提供了坐标信息，才写入
    if geo_transform is not None:
        dataset.SetGeoTransform(geo_transform)
    if projection is not None:
        dataset.SetProjection(projection)

    # 写入数据
    if bands == 1:
        dataset.GetRasterBand(1).WriteArray(image)
    else:
        for i in range(bands):
            dataset.GetRasterBand(i + 1).WriteArray(image[i])

    # 释放资源
    del dataset


def CompressGeoTiff(path: str, method: str = "LZW") -> None:
    """
       Compresses a GeoTIFF file using GDAL.

       Parameters:
           path (str): Path to the GeoTIFF file to be compressed.
           method (str, optional): Compression method, defaults to 'LZW' (lossless compression).

       Returns:
           None

       Raises:
           FileNotFoundError: If the specified file does not exist.
           IOError: If the file cannot be opened.
       """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} does not exist.")

    dataset = gdal.Open(path)
    if dataset is None:
        raise IOError(f"Failed to open file: {path}")

    driver = gdal.GetDriverByName("GTiff")
    target_path = path.replace(".tif", "_compressed.tif")

    compressed_dataset = driver.CreateCopy(target_path, dataset, strict=1, options=["TILED=YES", f"COMPRESS={method}"])
    del dataset, compressed_dataset


def CreateQuicklookImage(
        out_raster: str,
        image: np.ndarray,
        stretch_percent: float = 2.0,
        resize_scale: float = 1.0,
        channel_order: list = None
) -> None:
    """
    Save raster data as a PNG or JPG image with optional stretching, resizing,
    and channel selection using PIL.

    Input format: (C, H, W) or (H, W). Handles None/NaN values.

    Args:
        out_raster (str): Output file path. File extension determines format (.png or .jpg).
        image (np.ndarray): Input raster array, shape (C, H, W) or (H, W).
        stretch_percent (float): Percent stretch for contrast (e.g., 2.0 means 2% stretch).
        resize_scale (float): Scaling factor for output size (e.g., 0.5 means half size).
        channel_order (list): Channel selection order for multi-band images. Must be length 3.
    """

    # Validate output path
    if not isinstance(out_raster, str) or not out_raster.lower().endswith((".png", ".jpg", ".jpeg")):
        raise ValueError("Output path must be a string ending with .png, .jpg, or .jpeg")

    if not isinstance(image, np.ndarray):
        raise TypeError("Input image must be a numpy.ndarray")

    # Convert to float32 and replace invalid values with NaN
    image = np.array(image, dtype=np.float32)
    image = np.where(np.isfinite(image), image, np.nan)

    # Ensure image has proper dimensions
    if image.ndim == 2:
        image = image[np.newaxis, :, :]  # convert (H, W) -> (1, H, W)
    elif image.ndim != 3:
        raise ValueError("Input image must have shape (H, W) or (C, H, W)")

    C, H, W = image.shape

    # Single-band grayscale case
    if C == 1:
        band = image[0]
        valid = band[~np.isnan(band)]
        if valid.size == 0:
            raise ValueError("Single-band image contains only NaN/None values")

        low = np.percentile(valid, stretch_percent)
        high = np.percentile(valid, 100 - stretch_percent)

        if high <= low:
            raise ValueError("Invalid stretch range: high <= low")

        band = (band - low) / (high - low)
        band = np.clip(band, 0, 1)
        band[np.isnan(band)] = 0
        band = (band * 255).astype(np.uint8)

        pil_img = Image.fromarray(band, mode="L")

    # Multi-band RGB case
    else:
        if channel_order is None or len(channel_order) != 3:
            raise ValueError("Multi-band image requires channel_order of length 3")

        try:
            selected = np.stack([image[i] for i in channel_order], axis=-1)  # (H, W, 3)
        except IndexError:
            raise ValueError(f"Channel indices {channel_order} are out of range for image with {C} channels")

        stretched = np.zeros_like(selected, dtype=np.float32)

        for b in range(3):
            band = selected[:, :, b]
            valid = band[~np.isnan(band)]
            if valid.size == 0:
                stretched[:, :, b] = 0
                continue

            low = np.percentile(valid, stretch_percent)
            high = np.percentile(valid, 100 - stretch_percent)

            if high <= low:
                stretched[:, :, b] = 0
                continue

            norm = (band - low) / (high - low)
            norm = np.clip(norm, 0, 1)
            norm[np.isnan(norm)] = 0
            stretched[:, :, b] = norm

        stretched = (stretched * 255).astype(np.uint8)
        pil_img = Image.fromarray(stretched, mode="RGB")

    # Resize if needed
    if resize_scale != 1.0:
        if resize_scale <= 0:
            raise ValueError("resize_scale must be > 0")
        new_w = int(pil_img.width * resize_scale)
        new_h = int(pil_img.height * resize_scale)
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    pil_img.save(out_raster)
    # print(f"Image saved successfully: {out_raster}, size={pil_img.size}, mode={pil_img.mode}")
