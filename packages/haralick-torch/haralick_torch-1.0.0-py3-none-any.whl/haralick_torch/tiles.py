import torch
from .core import haralick_batch

def process_in_tiles(
    img, tile_size, window_size, levels,
    PRECOMP_I, PRECOMP_J, PRECOMP_DIFF
):
    pad = window_size // 2
    _, _, H_pad, W_pad = img.shape
    H = H_pad - 2 * pad
    W = W_pad - 2 * pad

    dummy = haralick_batch(
        img[:, :, :tile_size, :tile_size],
        window_size, levels,
        PRECOMP_I, PRECOMP_J, PRECOMP_DIFF
    )

    results = {
        k: torch.zeros((H, W), device='cpu')
        for k in dummy
    }

    for i in range(0, H, tile_size):
        for j in range(0, W, tile_size):

            tile = img[:, :, i:i+tile_size+2*pad, j:j+tile_size+2*pad]

            with torch.no_grad():
                feats = haralick_batch(
                    tile, window_size, levels,
                    PRECOMP_I, PRECOMP_J, PRECOMP_DIFF
                )

            for k in feats:
                results[k][i:i+tile_size, j:j+tile_size] = \
                    feats[k][pad:pad+tile_size, pad:pad+tile_size].cpu()

            torch.cuda.empty_cache()

    return results
