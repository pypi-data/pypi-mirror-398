import argparse
import torch
import os

from .io import read_tiff_as_tensor
from .tiling import process_in_tiles
from .utils import save_as_tif

def main():
    parser = argparse.ArgumentParser("Haralick textures with PyTorch + GDAL")
    parser.add_argument("image", help="Input GeoTIFF")
    parser.add_argument("--out", default="outputs")
    parser.add_argument("--tile", type=int, default=128)
    parser.add_argument("--window", type=int, default=15)
    parser.add_argument("--levels", type=int, default=64)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(args.out, exist_ok=True)

    img, ref = read_tiff_as_tensor(args.image, device)
    textures = process_in_tiles(img, args.tile, args.window, args.levels)

    for name, tensor in textures.items():
        save_as_tif(tensor.numpy(), ref, f"{args.out}/{name}.tif")
