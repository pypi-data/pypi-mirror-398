import torch
from .haralick import haralick_batch

def process_in_tiles(img, tile_size, window_size, levels):
    _, _, H, W = img.shape
    dummy = haralick_batch(img[:, :, :tile_size, :tile_size], window_size, levels)
    results = {k: torch.zeros((H, W), dtype=torch.float32) for k in dummy}

    for i in range(0, H, tile_size):
        for j in range(0, W, tile_size):
            tile = img[:, :, i:i+tile_size, j:j+tile_size]
            feats = haralick_batch(tile, window_size, levels)
            for k, v in feats.items():
                results[k][i:i+v.shape[0], j:j+v.shape[1]] = v.cpu()
            torch.cuda.empty_cache()

    return results
