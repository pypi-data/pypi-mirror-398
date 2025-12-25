import argparse
import torch

from .io import read_nir_tensor, write_haralick_geotiff, write_pca_geotiff
from .core import precompute_matrices
from .tiles import process_in_tiles
from .pca import pca_3_components

FEATURE_NAMES = [
    'Angular Second Moment', 'Contrast', 'Correlation',
    'Sum of Squares: Variance', 'Inverse Difference Moment',
    'Sum Average', 'Sum Variance', 'Sum Entropy',
    'Entropy', 'Difference Variance', 'Difference Entropy',
    'Information Measure of Correlation 1',
    'Information Measure of Correlation 2'
]

def main():
    parser = argparse.ArgumentParser("haralick-torch")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-texture", required=True)
    parser.add_argument("--out-pca", required=True)
    parser.add_argument("--nir-idx", type=int, default=8)
    parser.add_argument("--window", type=int, default=7)
    parser.add_argument("--levels", type=int, default=128)
    parser.add_argument("--tile", type=int, default=64)

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    img, ds = read_nir_tensor(args.input, args.nir_idx, device)
    img = torch.nn.functional.pad(img, (3, 3, 3, 3), mode="reflect")

    I, J, D = precompute_matrices(args.levels, device)

    textures = process_in_tiles(
        img, args.tile, args.window, args.levels, I, J, D
    )

    write_haralick_geotiff(
        args.out_texture, textures, FEATURE_NAMES, ds
    )

    pca = pca_3_components(
        [textures[n] for n in FEATURE_NAMES],
        device
    ).reshape(3, *textures[FEATURE_NAMES[0]].shape)

    write_pca_geotiff(args.out_pca, pca.cpu().numpy(), ds)
