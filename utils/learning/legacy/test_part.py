import numpy as np
import torch

from collections import defaultdict
from utils.common.legacy.utils import save_reconstructions
from utils.data.legacy.load_data import create_data_loaders
from utils.model.unet_legacy import Unet

import sys


def log_path(args):
    log_f = open(args.exp_dir / 'val-log.txt', 'w')
    return log_f


def test(args, model, data_loader):
    model.eval()
    reconstructions = defaultdict(dict)
    inputs = defaultdict(dict)

    with torch.no_grad():
        for (input, _, _, fnames, slices) in data_loader:
            input = input.cuda(non_blocking=True)
            output = model(input)

            for i in range(output.shape[0]):
                reconstructions[fnames[i]][int(slices[i])] = output[i].cpu().numpy()
                inputs[fnames[i]][int(slices[i])] = input[i].cpu().numpy()

    for fname in reconstructions:
        reconstructions[fname] = np.stack(
            [out for _, out in sorted(reconstructions[fname].items())]
        )
    for fname in inputs:
        inputs[fname] = np.stack(
            [out for _, out in sorted(inputs[fname].items())]
        )
    return reconstructions, inputs


def forward(args):
    log_f = log_path(args)

    device = torch.device(f'cuda:{args.GPU_NUM}' if torch.cuda.is_available() else 'cpu')
    torch.cuda.set_device(device)
    print('Current cuda device ', torch.cuda.current_device())
    print('Current cuda device ', torch.cuda.current_device(), file=log_f)

    model = Unet(in_chans = args.in_chans, out_chans = args.out_chans)
    model.to(device=device)

    checkpoint = torch.load(args.exp_dir / 'best_model.pt', map_location='cpu')
    print(checkpoint['epoch'], checkpoint['best_val_loss'].item())
    print(checkpoint['epoch'], checkpoint['best_val_loss'].item(), file=log_f)
    model.load_state_dict(checkpoint['model'])

    forward_loader = create_data_loaders(data_path = args.data_path, args = args, isforward = True)
    reconstructions, inputs = test(args, model, forward_loader)
    save_reconstructions(reconstructions, args.forward_dir, inputs=inputs)

    log_f.close()