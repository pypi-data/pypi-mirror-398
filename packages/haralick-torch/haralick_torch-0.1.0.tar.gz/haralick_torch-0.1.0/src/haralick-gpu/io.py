import torch
import numpy as np
from osgeo import gdal

def read_tiff_as_tensor(path, device):
    ds = gdal.Open(path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype(np.float32)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-10)
    return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).to(device), ds
