# haralick-torch

GPU-accelerated Haralick texture extraction for GeoTIFF images using PyTorch.

## Installation

GDAL must be installed via precompiled wheels:

https://github.com/cgohlke/geospatial-wheels/releases

```bash
pip install GDAL-3.10.1-cp310-cp310-win_amd64.whl
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install haralick-torch
```

## Usage CLI

```bash
haralick-torch image.tif --tile 256 --window 15 --levels 64 --out outputs
```

## Usage API
```bash
import torch
from haralick_torch.io import read_tiff_as_tensor
from haralick_torch.tiling import process_in_tiles
from haralick_torch.utils import save_as_tif

device = "cuda" if torch.cuda.is_available() else "cpu"

img, ref = read_tiff_as_tensor("image.tif", device)
textures = process_in_tiles(img, tile_size=256, window_size=15, levels=32)

for name, tensor in textures.items():
    save_as_tif(tensor.numpy(), ref, f"{name}.tif")
```