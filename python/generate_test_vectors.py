import numpy as np
import os

DATA_WIDTH = 16
COEFF_SHIFT = 15   # COEFF_WIDTH - 1
NUM_SAMPLES = 200
FS = 8000.0        # Hz, arbitrary sample rate for the test signal

DATA_MIN, DATA_MAX = -(2**(DATA_WIDTH-1)), 2**(DATA_WIDTH-1) - 1

def load_coeffs():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "q_coeffs.npy")
    if not os.path.exists(path):
        raise SystemExit("Run generate_coeffs.py first to create q_coeffs.npy")
    return np.load(path)

def make_stimulus(n):
    t = np.arange(n) / FS
    # Low-frequency tone (should pass) + high-frequency tone (should be attenuated)
    sig = 0.4 * np.sin(2 * np.pi * 300 * t) + 0.4 * np.sin(2 * np.pi * 3000 * t)
    # Small step partway through, to see settling behaviour
    sig[n // 2:] += 0.15
    quantized = np.round(sig * (2**(DATA_WIDTH-1) - 1)).astype(np.int64)
    return np.clip(quantized, DATA_MIN, DATA_MAX)

def saturate(v):
    return int(np.clip(v, DATA_MIN, DATA_MAX))

def golden_model(x, coeffs):
    """Bit-exact emulation of the VHDL direct-form FIR (see fir_filter.vhd)."""
    num_taps = len(coeffs)
    shift_reg = np.zeros(num_taps, dtype=np.int64)  # shift_reg(0..N-1) 
    y = np.zeros(len(x), dtype=np.int64)

    for n in range(len(x)):
        taps_now = np.zeros(num_taps, dtype=np.int64)
        taps_now[0] = x[n]
        taps_now[1:] = shift_reg[:num_taps - 1]

        acc = int(np.sum(taps_now.astype(np.int64) * coeffs.astype(np.int64)))
        rescaled = acc >> COEFF_SHIFT   
        y[n] = saturate(rescaled)

        shift_reg = taps_now

    return y

def main():
    coeffs = load_coeffs()
    x = make_stimulus(NUM_SAMPLES)
    y = golden_model(x, coeffs)

    here = os.path.dirname(__file__)
    data_dir = os.path.join(here, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    with open(os.path.join(data_dir, "stimulus.txt"), "w") as f:
        f.write("\n".join(str(v) for v in x) + "\n")

    with open(os.path.join(data_dir, "expected_output.txt"), "w") as f:
        f.write("\n".join(str(v) for v in y) + "\n")

    print(f"Wrote {len(x)} samples to data/stimulus.txt and data/expected_output.txt")
    print(f"Input range:  [{x.min()}, {x.max()}]")
    print(f"Output range: [{y.min()}, {y.max()}]")

if __name__ == "__main__":
    main()
