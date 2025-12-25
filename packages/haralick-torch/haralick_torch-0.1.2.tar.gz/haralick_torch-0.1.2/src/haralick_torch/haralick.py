import torch

# Precomputados para eficiência
PRECOMP_I = None
PRECOMP_J = None
PRECOMP_DIFF = None

def _init_precomp(levels=128, device='cuda'):
    global PRECOMP_I, PRECOMP_J, PRECOMP_DIFF
    I, J = torch.meshgrid(torch.arange(levels, device=device),
                          torch.arange(levels, device=device),
                          indexing='ij')
    PRECOMP_I = I.unsqueeze(0)
    PRECOMP_J = J.unsqueeze(0)
    PRECOMP_DIFF = (I - J).abs().unsqueeze(0)

def haralick_batch(img, window_size=7, levels=128):
    if PRECOMP_I is None:
        _init_precomp(levels, img.device)

    B, C, H, W = img.shape
    patches = torch.nn.functional.unfold(img, kernel_size=window_size, padding=window_size//2)
    patches = patches.squeeze(0).T
    patches = torch.clamp((patches * (levels - 1)).long(), 0, levels - 1)

    left = patches[:, :-1]
    right = patches[:, 1:]
    codes = left * levels + right
    glcm = torch.zeros((codes.shape[0], levels * levels), device=img.device)
    codes = torch.clamp(codes, 0, levels*levels-1)
    glcm.scatter_add_(1, codes, torch.ones_like(codes, dtype=torch.float32))
    glcm = glcm.view(-1, levels, levels)
    glcm = glcm + glcm.transpose(1,2)
    glcm = glcm / (glcm.sum(dim=(1,2), keepdim=True) + 1e-10)

    I = PRECOMP_I
    J = PRECOMP_J
    diff = PRECOMP_DIFF

    mean_i = (glcm * I).sum(dim=(1,2))
    mean_j = (glcm * J).sum(dim=(1,2))
    std_i = torch.sqrt(((I - mean_i[:,None,None])**2 * glcm).sum(dim=(1,2)))
    std_j = torch.sqrt(((J - mean_j[:,None,None])**2 * glcm).sum(dim=(1,2)))
    sum_mean = ((I+J)*glcm).sum(dim=(1,2))
    sum_variance = ((I+J-sum_mean[:,None,None])**2 * glcm).sum(dim=(1,2))

    # Features Haralick principais
    features = {
        'Angular Second Moment': (glcm**2).sum(dim=(1,2)),
        'Contrast': ((I-J)**2 * glcm).sum(dim=(1,2)),
        'Correlation': ((I*J*glcm).sum(dim=(1,2)) - mean_i*mean_j)/(std_i*std_j + 1e-10),
        'Sum of Squares: Variance': ((I - mean_i[:,None,None])**2 * glcm).sum(dim=(1,2)),
        'Inverse Difference Moment': (glcm / (1 + (I-J).abs())).sum(dim=(1,2)),
        'Sum Average': ((I+J)*glcm).sum(dim=(1,2)),
        'Sum Variance': sum_variance,
        'Sum Entropy': -(glcm.sum(dim=2) * torch.log(glcm.sum(dim=2) + 1e-10)).sum(dim=1),
        'Entropy': -(glcm*torch.log(glcm+1e-10)).sum(dim=(1,2)),
        'Difference Variance': (((diff - (diff*glcm).sum(dim=(1,2),keepdim=True))**2)*glcm).sum(dim=(1,2)),
        'Difference Entropy': -(glcm.sum(dim=1)*torch.log(glcm.sum(dim=1)+1e-10)).sum(dim=1),
        # Informação de correlação
        'Information Measure of Correlation 1': ((-(glcm*torch.log((glcm.sum(dim=2)[:,:,None]*glcm.sum(dim=1)[:,None,:])+1e-10))).sum(dim=(1,2))),
        'Information Measure of Correlation 2': torch.sqrt(1 - torch.exp(-2*((-(glcm.sum(dim=2)[:,:,None]*glcm.sum(dim=1)[:,None,:]*torch.log(glcm.sum(dim=2)[:,:,None]*glcm.sum(dim=1)[:,None,:]+1e-10))).sum(dim=(1,2)) - (-(glcm*torch.log(glcm+1e-10))).sum(dim=(1,2)))))
    }

    # Redimensionar para HxW
    for k in features:
        features[k] = features[k].reshape(H, W)

    return features

def process_in_tiles(img, tile_size=64, window_size=7, levels=128):
    pad = window_size // 2
    _,_,H_pad,W_pad = img.shape
    H = H_pad - 2*pad
    W = W_pad - 2*pad

    dummy = haralick_batch(img[:,:,:tile_size,:tile_size], window_size, levels)
    results = {k: torch.zeros((H,W), dtype=torch.float32, device='cpu') for k in dummy.keys()}

    for i in range(0,H,tile_size):
        for j in range(0,W,tile_size):
            i0,i1 = i, min(i+tile_size+2*pad,H_pad)
            j0,j1 = j, min(j+tile_size+2*pad,W_pad)
            tile = img[:,:,i0:i1,j0:j1]
            with torch.no_grad():
                feats = haralick_batch(tile, window_size, levels)
            si,sj = pad,pad
            ei = si + min(tile_size,H-i)
            ej = sj + min(tile_size,W-j)
            for k,v in feats.items():
                results[k][i:i+(ei-si), j:j+(ej-sj)] = v[si:ei,sj:ej].cpu()
            del tile, feats
            torch.cuda.empty_cache()
    return results

def extract_haralick(img_tensor, tile_size=64, window_size=7, levels=128):
    return process_in_tiles(img_tensor, tile_size, window_size, levels)
