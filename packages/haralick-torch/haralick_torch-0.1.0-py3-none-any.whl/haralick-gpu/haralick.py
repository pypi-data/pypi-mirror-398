import torch

def haralick_batch(img, window_size=7, levels=8):
    B, C, H, W = img.shape
    patches = torch.nn.functional.unfold(img, kernel_size=window_size, padding=window_size // 2)
    patches = patches.squeeze(0).T
    patches = torch.clamp((patches * (levels - 1)).long(), 0, levels - 1)

    left = patches[:, :-1]
    right = patches[:, 1:]
    N = patches.shape[0]
    glcm = torch.zeros((N, levels, levels), dtype=torch.float32, device=img.device)

    for i in range(levels):
        for j in range(levels):
            mask = (left == i) & (right == j)
            glcm[:, i, j] = mask.sum(dim=1)

    glcm = glcm + glcm.transpose(1, 2)
    glcm = glcm / (glcm.sum(dim=(1, 2), keepdim=True) + 1e-10)

    I, J = torch.meshgrid(
        torch.arange(levels, device=glcm.device),
        torch.arange(levels, device=glcm.device),
        indexing="ij"
    )
    I = I.unsqueeze(0)
    J = J.unsqueeze(0)

    mean_i = (glcm * I).sum(dim=(1, 2))
    mean_j = (glcm * J).sum(dim=(1, 2))
    std_i = torch.sqrt(((I - mean_i[:, None, None]) ** 2 * glcm).sum(dim=(1, 2)))
    std_j = torch.sqrt(((J - mean_j[:, None, None]) ** 2 * glcm).sum(dim=(1, 2)))
    sum_mean = ((I + J) * glcm).sum(dim=(1, 2))
    sum_variance = ((I + J - sum_mean[:, None, None]) ** 2 * glcm).sum(dim=(1, 2))
    difference = (I - J).abs()

    features = {
        "energy": (glcm ** 2).sum(dim=(1, 2)),
        "contrast": ((I - J) ** 2 * glcm).sum(dim=(1, 2)),
        "homogeneity": (glcm / (1 + (I - J).abs())).sum(dim=(1, 2)),
        "entropy": -(glcm * torch.log(glcm + 1e-10)).sum(dim=(1, 2)),
        "correlation": ((I * J * glcm).sum(dim=(1, 2)) - mean_i * mean_j) / (std_i * std_j + 1e-10),
        "sum_average": ((I + J) * glcm).sum(dim=(1, 2)),
        "sum_variance": sum_variance,
        "sum_entropy": -(glcm.sum(dim=2) * torch.log(glcm.sum(dim=2) + 1e-10)).sum(dim=1),
        "difference_entropy": -(glcm.sum(dim=1) * torch.log(glcm.sum(dim=1) + 1e-10)).sum(dim=1),
        "difference_variance": (((difference - (difference * glcm).sum(dim=(1, 2), keepdim=True)) ** 2) * glcm).sum(dim=(1, 2)),
        "cluster_shade": (((I + J - mean_i[:, None, None] - mean_j[:, None, None]) ** 3) * glcm).sum(dim=(1, 2)),
        "cluster_prominence": (((I + J - mean_i[:, None, None] - mean_j[:, None, None]) ** 4) * glcm).sum(dim=(1, 2)),
        "max_probability": glcm.amax(dim=(1, 2)),
    }

    for k, v in features.items():
        features[k] = v.reshape(H, W)

    return features
