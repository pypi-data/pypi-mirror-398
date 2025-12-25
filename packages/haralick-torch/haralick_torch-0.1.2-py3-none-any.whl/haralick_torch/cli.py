import os
import click
from .io import read_tiff_as_tensor, save_tiff
from .haralick import extract_haralick
from .pca import pca_3_components

# Nomes das features principais
FEATURE_NAMES = [
    'Angular Second Moment', 'Contrast', 'Correlation', 'Sum of Squares: Variance',
    'Inverse Difference Moment', 'Sum Average', 'Sum Variance', 'Sum Entropy',
    'Entropy', 'Difference Variance', 'Difference Entropy',
    'Information Measure of Correlation 1', 'Information Measure of Correlation 2'
]

@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--band", default=8, help="Índice da banda NIR no GeoTIFF (padrão: 8)")
@click.option("--tile_size", default=64, help="Tamanho do tile")
@click.option("--window_size", default=7, help="Tamanho da janela Haralick")
@click.option("--levels", default=128, help="Número de níveis de quantização")
def main(input_path, output_dir, band, tile_size, window_size, levels):
    """CLI para extrair texturas Haralick e PCA 3 componentes de um GeoTIFF"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Lendo imagem {input_path}...")
    img, ref_ds = read_tiff_as_tensor(input_path, band_idx=band)
    
    print("Extraindo Haralick features...")
    textures = extract_haralick(img, tile_size=tile_size, window_size=window_size, levels=levels)
    
    print("Salvando texturas...")
    for name in FEATURE_NAMES:
        save_tiff(textures[name], ref_ds, os.path.join(output_dir, f"{name}.tif"), description=name)
    
    print("Calculando PCA 3 componentes...")
    pca_arr = pca_3_components(textures)
    for i in range(3):
        save_tiff(pca_arr[i], ref_ds, os.path.join(output_dir, f"PCA_{i+1}.tif"), description=f"PCA {i+1}")
    
    print("Processamento concluído!")
