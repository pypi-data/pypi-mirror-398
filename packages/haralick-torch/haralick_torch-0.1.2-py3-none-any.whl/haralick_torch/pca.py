import torch
import numpy as np
from .io import normalize_to_uint16

def pca_3_components(features_dict, device='cuda'):
    feature_names = list(features_dict.keys())
    H, W = features_dict[feature_names[0]].shape
    num_features = len(feature_names)

    tensor_stack = torch.stack([features_dict[name].to(device) for name in feature_names], dim=0)
    tensor_flat = tensor_stack.reshape(num_features, -1).T

    U, S, V = torch.pca_lowrank(tensor_flat, q=3)
    X_pca = tensor_flat @ V[:, :3]
    pca_features = X_pca.T.reshape(3,H,W).cpu().numpy()
    return np.array([normalize_to_uint16(pca_features[i]) for i in range(3)], dtype=np.uint16)
