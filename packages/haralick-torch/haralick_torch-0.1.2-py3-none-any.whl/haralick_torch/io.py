import torch
import numpy as np
from osgeo import gdal

def read_tiff_as_tensor(path, band_idx=8, device='cuda'):
    ds = gdal.Open(path)
    band = ds.GetRasterBand(band_idx)
    arr = band.ReadAsArray().astype(np.float32)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-10)
    return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).to(device), ds

def normalize_to_uint16(array):
    vmin, vmax = array.min(), array.max()
    if vmax - vmin > 0:
        scaled = (array - vmin) / (vmax - vmin)
    else:
        scaled = np.zeros_like(array)
    return (scaled * 65535).astype(np.uint16)

def save_tiff(array, ref_ds, path, description=None):
    driver = gdal.GetDriverByName('GTiff')
    H, W = array.shape[-2], array.shape[-1]
    out_ds = driver.Create(path, W, H, 1, gdal.GDT_UInt16,
                           options=['COMPRESS=DEFLATE', 'PREDICTOR=2', 'ZLEVEL=4', 'TILED=YES'])
    out_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    out_ds.SetProjection(ref_ds.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(normalize_to_uint16(array))
    if description:
        out_ds.GetRasterBand(1).SetDescription(description)
    out_ds = None
