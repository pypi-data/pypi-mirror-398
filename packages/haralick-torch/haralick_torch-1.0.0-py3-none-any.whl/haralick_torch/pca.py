import torch

def pca_3_components(features, device):
    X = torch.stack(features, dim=0).reshape(len(features), -1).T.to(device)
    _, _, V = torch.pca_lowrank(X, q=3)
    return (X @ V[:, :3]).T
