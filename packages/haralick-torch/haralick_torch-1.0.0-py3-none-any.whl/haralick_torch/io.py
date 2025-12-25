import numpy as np
import torch
from osgeo import gdal

gdal.UseExceptions()

def read_nir_tensor(path, nir_idx, device):
    ds = gdal.Open(path)
    band = ds.GetRasterBand(nir_idx)
    arr = band.ReadAsArray().astype(np.float32)

    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-10)

    tensor = (
        torch.from_numpy(arr)
        .unsqueeze(0)
        .unsqueeze(0)
        .to(device)
    )

    return tensor, ds

def normalize_to_uint16(array):
    vmin, vmax = array.min(), array.max()
    if vmax - vmin > 0:
        scaled = (array - vmin) / (vmax - vmin)
    else:
        scaled = np.zeros_like(array)
    return (scaled * 65535).astype(np.uint16)

def write_pca_geotiff(
    out_path,
    pca_array,
    ref_ds
):
    driver = gdal.GetDriverByName("GTiff")

    rows = ref_ds.RasterYSize
    cols = ref_ds.RasterXSize

    out_ds = driver.Create(
        out_path,
        cols,
        rows,
        3,
        gdal.GDT_UInt16,
        options=[
            "COMPRESS=DEFLATE",
            "PREDICTOR=2",
            "INTERLEAVE=BAND",
            "ZLEVEL=4",
            "TILED=YES"
        ]
    )

    out_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    out_ds.SetProjection(ref_ds.GetProjection())

    for i in range(3):
        out_ds.GetRasterBand(i + 1).WriteArray(
            normalize_to_uint16(pca_array[i])
        )
        out_ds.GetRasterBand(i + 1).SetDescription(f"PCA Component {i + 1}")
        out_ds.GetRasterBand(i + 1).SetNoDataValue(0)

    out_ds = None

def write_haralick_geotiff(
    out_path,
    textures,
    feature_names,
    ref_ds
):
    driver = gdal.GetDriverByName("GTiff")

    rows = ref_ds.RasterYSize
    cols = ref_ds.RasterXSize

    out_ds = driver.Create(
        out_path,
        cols,
        rows,
        len(feature_names),
        gdal.GDT_UInt16,
        options=[
            "COMPRESS=DEFLATE",
            "PREDICTOR=2",
            "ZLEVEL=4",
            "TILED=YES"
        ]
    )

    out_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    out_ds.SetProjection(ref_ds.GetProjection())

    for i, name in enumerate(feature_names, 1):
        out_ds.GetRasterBand(i).WriteArray(
            normalize_to_uint16(textures[name].numpy())
        )
        out_ds.GetRasterBand(i).SetDescription(name)
        out_ds.GetRasterBand(i).SetNoDataValue(0)

    out_ds = None
