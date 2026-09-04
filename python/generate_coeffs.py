import numpy as np
from scipy.signal import firwin

NUM_TAPS = 16
CUTOFF_NORMALIZED = 0.2   # cutoff as a fraction of Nyquist (0 < f < 1)
Q = 15                    # Q15 fixed point -> scale factor 2^15
COEFF_WIDTH = 16

def quantize_q15(coeffs, q=Q, width=COEFF_WIDTH):
    scale = 2 ** q
    q_max = 2 ** (width - 1) - 1
    q_min = -2 ** (width - 1)
    quantized = np.round(coeffs * scale).astype(int)
    quantized = np.clip(quantized, q_min, q_max)
    return quantized

def main():
    coeffs = firwin(NUM_TAPS, CUTOFF_NORMALIZED, window="hamming")
    q_coeffs = quantize_q15(coeffs)

    print(f"-- {NUM_TAPS}-tap low-pass FIR, cutoff={CUTOFF_NORMALIZED}*Nyquist, Hamming window")
    print(f"-- Q15 fixed point (value = coeff * 32768), sum of taps ~= {q_coeffs.sum()} (/32768 = {q_coeffs.sum()/32768:.4f} DC gain)")
    print("constant COEFFS : coeff_array_t := (")
    lines = []
    for i, c in enumerate(q_coeffs):
        lines.append(f"    {i} => to_signed({c:6d}, COEFF_WIDTH)")
    print(",\n".join(lines))
    print(");")

    # Save raw arrays for the testbench-vector generator to reuse
    np.save("q_coeffs.npy", q_coeffs)
    print("\nSaved quantized coefficients to python/q_coeffs.npy")

if __name__ == "__main__":
    main()
