import torch

def precompute_matrices(levels, device):
    I, J = torch.meshgrid(
        torch.arange(levels, device=device),
        torch.arange(levels, device=device),
        indexing='ij'
    )
    return I.unsqueeze(0), J.unsqueeze(0), (I - J).abs().unsqueeze(0)


def haralick_batch(
    img,
    window_size,
    levels,
    PRECOMP_I,
    PRECOMP_J,
    PRECOMP_DIFF
):
    B, C, H, W = img.shape

    patches = torch.nn.functional.unfold(
        img, kernel_size=window_size, padding=window_size // 2
    )
    patches = patches.squeeze(0).T
    patches = torch.clamp((patches * (levels - 1)).long(), 0, levels - 1)

    left = patches[:, :-1]
    right = patches[:, 1:]
    codes = left * levels + right

    glcm = torch.zeros(
        (codes.shape[0], levels * levels),
        device=img.device
    )
    glcm.scatter_add_(1, codes, torch.ones_like(codes, dtype=torch.float32))
    glcm = glcm.view(-1, levels, levels)

    glcm = glcm + glcm.transpose(1, 2)
    glcm = glcm / (glcm.sum(dim=(1, 2), keepdim=True) + 1e-10)

    I = PRECOMP_I
    J = PRECOMP_J
    D = PRECOMP_DIFF

    mean_i = (glcm * I).sum(dim=(1, 2))
    mean_j = (glcm * J).sum(dim=(1, 2))
    std_i = torch.sqrt(((I - mean_i[:, None, None]) ** 2 * glcm).sum(dim=(1, 2)))
    std_j = torch.sqrt(((J - mean_j[:, None, None]) ** 2 * glcm).sum(dim=(1, 2)))

    sum_mean = ((I + J) * glcm).sum(dim=(1, 2))
    sum_variance = ((I + J - sum_mean[:, None, None]) ** 2 * glcm).sum(dim=(1, 2))

    features = {
        'Angular Second Moment': (glcm ** 2).sum(dim=(1, 2)),
        'Contrast': ((I - J) ** 2 * glcm).sum(dim=(1, 2)),
        'Correlation': (
            (I * J * glcm).sum(dim=(1, 2)) - mean_i * mean_j
        ) / (std_i * std_j + 1e-10),
        'Sum of Squares: Variance': ((I - mean_i[:, None, None]) ** 2 * glcm).sum(dim=(1, 2)),
        'Inverse Difference Moment': (glcm / (1 + (I - J).abs())).sum(dim=(1, 2)),
        'Sum Average': ((I + J) * glcm).sum(dim=(1, 2)),
        'Sum Variance': sum_variance,
        'Sum Entropy': -(glcm.sum(dim=2) * torch.log(glcm.sum(dim=2) + 1e-10)).sum(dim=1),
        'Entropy': -(glcm * torch.log(glcm + 1e-10)).sum(dim=(1, 2)),
        'Difference Variance': (((D - (D * glcm).sum(dim=(1, 2), keepdim=True)) ** 2) * glcm).sum(dim=(1, 2)),
        'Difference Entropy': -(glcm.sum(dim=1) * torch.log(glcm.sum(dim=1) + 1e-10)).sum(dim=1),
    }

    px = glcm.sum(dim=2)
    py = glcm.sum(dim=1)
    hx = -(px * torch.log(px + 1e-10)).sum(dim=1)
    hy = -(py * torch.log(py + 1e-10)).sum(dim=1)
    hxy = features['Entropy']
    hxy1 = -(glcm * torch.log(px[:, :, None] * py[:, None, :] + 1e-10)).sum(dim=(1, 2))
    hxy2 = -(px[:, :, None] * py[:, None, :] * torch.log(px[:, :, None] * py[:, None, :] + 1e-10)).sum(dim=(1, 2))

    features['Information Measure of Correlation 1'] = (hxy - hxy1) / (torch.max(hx, hy) + 1e-10)
    features['Information Measure of Correlation 2'] = torch.sqrt(1 - torch.exp(-2 * (hxy2 - hxy)))

    for k in features:
        features[k] = features[k].reshape(H, W)

    return features
