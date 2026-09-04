# 16-Tap FIR Digital Filter — VHDL + Python Golden Model

A fixed-point, direct-form FIR (Finite Impulse Response) low-pass filter
implemented in synthesizable VHDL, verified against a bit-exact Python
model, with a self-checking testbench.

## What this is

A digital FIR filter smooths or shapes a stream of samples by computing a
weighted sum of the current sample and a window of past samples:

```
y[n] = sum_{i=0}^{N-1} h[i] * x[n-i]
```

This project designs a 16-tap low-pass filter (cutoff at 0.2 × Nyquist,
Hamming window) using `scipy.signal.firwin`, quantizes the coefficients
to **Q15 fixed-point** (16-bit signed integers, so `1.0` is represented as
`32768`), and implements the filter as a fully-parallel, single-cycle
direct-form structure in VHDL — the standard architecture used before
moving to a resource-shared or systolic implementation on real FPGA
hardware.

**Why this project:** it's a compact, self-contained demonstration of
moving a signal-processing design (Python/NumPy/SciPy) into synthesizable
hardware (VHDL), including the fixed-point quantization and saturation
arithmetic that a purely algorithmic DSP background usually skips.

## Repository structure

```
fir_filter_project/
├── rtl/
│   └── fir_filter.vhd          # synthesizable FIR filter (the design)
├── tb/
│   └── fir_filter_tb.vhd       # self-checking testbench
├── python/
│   ├── generate_coeffs.py      # designs + quantizes the filter coefficients
│   └── generate_test_vectors.py# generates stimulus + bit-exact expected output
├── data/
│   ├── stimulus.txt            # input samples fed to the testbench
│   └── expected_output.txt     # golden-model output, compared against the DUT
└── README.md
```

## How the pieces fit together

1. **`generate_coeffs.py`** designs the filter in floating point with
   SciPy, quantizes each coefficient to Q15, and prints a VHDL constant
   table (already pasted into `fir_filter.vhd`).
2. **`generate_test_vectors.py`** builds a test signal (a low-frequency
   tone that should pass, a high-frequency tone that should be
   attenuated, and a step), then re-implements the *exact* fixed-point
   arithmetic the VHDL will do — 40-bit MAC, arithmetic right-shift by
   15, saturate to 16 bits — in Python, to produce a bit-exact expected
   output.
3. **`fir_filter.vhd`** is the RTL: a shift register of past samples, one
   multiply-accumulate per tap per cycle, then rescale/saturate.
   One clock cycle of latency from `valid_in` to `valid_out`.
4. **`fir_filter_tb.vhd`** reads `stimulus.txt`, drives the DUT one
   sample per cycle, and compares every output against
   `expected_output.txt`, reporting a pass/fail count.

## Running the simulation

This needs a VHDL-2008 simulator such as **GHDL** (free, open source) or
ModelSim/Questa/Vivado's `xsim`. I could not run a simulator in the
sandbox this was written in, so **run and check this yourself** before
relying on it — the RTL and the Python golden model were written to
match arithmetically, but they haven't been simulated end-to-end.

With GHDL:

```bash
cd fir_filter_project
ghdl -a --std=08 rtl/fir_filter.vhd
ghdl -a --std=08 tb/fir_filter_tb.vhd
ghdl -e --std=08 fir_filter_tb
ghdl -r --std=08 fir_filter_tb --wave=wave.ghw
```

You should see a report line like:

```
FIR filter testbench complete: 200 passed, 0 failed
RESULT: PASS
```

If you get mismatches, the two most likely causes are (a) a simulator
that treats `shift_right` on `signed` as a logical rather than
arithmetic shift — check your tool's `numeric_std` implementation — or
(b) an off-by-one in file line counts if you regenerate `data/*.txt`
with a different `NUM_SAMPLES`.

To regenerate the coefficients or test vectors (e.g. with more taps or
a different cutoff):

```bash
cd python
python3 generate_coeffs.py            # re-run, then paste the printed
                                       # table into rtl/fir_filter.vhd
python3 generate_test_vectors.py      # regenerates data/*.txt
```

Requires `numpy` and `scipy` (`pip install numpy scipy`).

## Design parameters

| Parameter      | Value                                  |
|----------------|-----------------------------------------|
| Taps           | 16                                      |
| Filter type    | Low-pass, Hamming window                |
| Cutoff         | 0.2 × Nyquist                           |
| Coefficient format | Q15 (16-bit signed)                 |
| Data width     | 16-bit signed                           |
| Accumulator    | 40-bit signed                           |
| Latency        | 1 clock cycle                           |
| Throughput     | 1 sample / clock cycle                  |

## Possible extensions

- Swap the fully-parallel MAC array for a single shared multiplier
  (time-multiplexed across taps) to compare resource usage on a target
  FPGA.
- Add an AXI-Stream wrapper (`s_axis`/`m_axis`) so it drops into a
  Vivado block design.
- Synthesize for a real device (e.g. Basys3/Nexys A7) and report
  utilization/timing from the tool's reports.
- Extend `generate_coeffs.py` to support band-pass/high-pass designs and
  parameterize the testbench to sweep cutoff frequencies.
