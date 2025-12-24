import numpy as np
from pystoi import stoi as theirs

from fast_stoi import stoi as ours


def test_standard():
    np.random.seed(42)
    values = []
    srs = [8_000, 16_000, 32_000]
    seconds = 3
    for sr in srs:
        for _ in range(100):
            x = np.random.randn(sr * seconds)
            y = np.random.randn(sr * seconds)
            values.append(abs(theirs(x, y, fs_sig=sr) - ours(x, y, fs_sig=sr)))

    assert np.array(values).max() < 1e-7


def test_extended():
    np.random.seed(42)
    values = []
    srs = [8_000, 16_000, 32_000]
    seconds = 3
    for sr in srs:
        for _ in range(100):
            x = np.random.randn(sr * seconds)
            y = np.random.randn(sr * seconds)
            values.append(
                abs(
                    theirs(x, y, fs_sig=sr, extended=True)
                    - ours(x, y, fs_sig=sr, extended=True)
                )
            )

    assert np.array(values).max() < 1e-7
