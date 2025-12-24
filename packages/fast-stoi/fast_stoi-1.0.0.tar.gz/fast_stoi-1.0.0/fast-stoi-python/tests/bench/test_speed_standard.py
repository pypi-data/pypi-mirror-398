import numpy as np


def test_pystoi_reference(benchmark):
    from pystoi import stoi

    sr = 8_000
    seconds = 3
    size = seconds * sr
    x = np.random.randn(size).astype(np.float32)
    y = np.random.randn(size).astype(np.float32)
    benchmark(stoi, x, y, sr, False)


def test_torch_stoi_reference(benchmark):
    from torch_stoi import NegSTOILoss
    from torchaudio import torch

    stoi = NegSTOILoss(8_000)

    sr = 8_000
    seconds = 3
    size = seconds * sr
    x = torch.randn(size)
    y = torch.randn(size)
    benchmark(stoi, x, y)


def test_ours(benchmark):
    from fast_stoi import stoi

    sr = 8_000
    seconds = 3
    size = seconds * sr
    x = np.random.randn(size).astype(np.float32)
    y = np.random.randn(size).astype(np.float32)
    benchmark(stoi, x, y, sr, False)


def test_pystoi_reference_batched(benchmark):
    from pystoi import stoi

    sr = 8_000
    seconds = 3
    size = seconds * sr
    batch_size = 16
    x = np.random.randn(batch_size, size).astype(np.float32)
    y = np.random.randn(batch_size, size).astype(np.float32)

    def batched_stoi(x, y, sr, extended):
        for x, y in zip(x, y):
            stoi(x, y, sr, extended)

    benchmark(batched_stoi, x, y, sr, False)


def test_torch_stoi_reference_batched(benchmark):
    from torch_stoi import NegSTOILoss
    from torchaudio import torch

    stoi = NegSTOILoss(8_000)

    sr = 8_000
    seconds = 3
    size = seconds * sr
    batch_size = 16
    x = torch.randn(batch_size, size)
    y = torch.randn(batch_size, size)
    benchmark(stoi, x, y)


def test_ours_batched(benchmark):
    from fast_stoi import stoi

    sr = 8_000
    seconds = 3
    batch_size = 16
    size = seconds * sr
    x = np.random.randn(batch_size, size).astype(np.float32)
    y = np.random.randn(batch_size, size).astype(np.float32)
    benchmark(stoi, x, y, sr, False)
