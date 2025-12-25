import numpy as np
from osgeo import gdal

def contrast_stretch(arr):
    p2, p98 = np.percentile(arr, (2, 98))
    return np.clip((arr - p2) / (p98 - p2 + 1e-10), 0, 1)

def save_as_tif(array, ref_ds, path):
    driver = gdal.GetDriverByName("GTiff")
    H, W = array.shape
    out = driver.Create(path, W, H, 1, gdal.GDT_Byte)
    out.SetGeoTransform(ref_ds.GetGeoTransform())
    out.SetProjection(ref_ds.GetProjection())

    arr_255 = (contrast_stretch(array) * 255).astype(np.uint8)
    out.GetRasterBand(1).WriteArray(arr_255)
    out.FlushCache()
