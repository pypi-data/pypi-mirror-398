# Discrete Fourier

A Python library for computing Discrete Fourier Series coefficients and reconstructing signals from discrete data. This implementation provides efficient methods for Fourier analysis, signal reconstruction, and derivative calculations.

## Features

- **Fourier Coefficient Calculation**: Compute real Fourier series coefficients (a_k, b_k) from discrete data
- **Signal Reconstruction**: Evaluate the Fourier series at any position (interpolation and extrapolation)
- **First Derivative**: Calculate the rate of change of the reconstructed signal
- **Second Derivative**: Compute the curvature/acceleration of the signal
- **NumPy-based**: Efficient vectorized computations for fast performance

## Why Not Just Use NumPy FFT?

While NumPy and SciPy provide excellent FFT implementations, this library offers distinct advantages for working with **real Fourier series**:

### **Real Coefficients vs Complex Numbers**

**NumPy FFT:**
```python
import numpy as np

fft_result = np.fft.fft(data)
# Returns: [c0, c1, c2, ...] - complex numbers
# Example: [(2.5+0j), (1.2+0.8j), (-0.5-1.2j), ...]
# Requires understanding of complex arithmetic
```

**This Library:**
```python
from discrete_fourier import DiscreteFourier

coefs = DiscreteFourier.calculate_fourier_coefs(data)
# Returns: (a_k, b_k) - separate real arrays
# a_k: [2.5, 1.2, -0.5, ...]  (cosine coefficients)
# b_k: [0.0, 0.8, -1.2, ...]  (sine coefficients)
# More interpretable, no complex numbers needed
```

### **Point Evaluation**

**NumPy FFT:**
```python
# To evaluate at a single point, you must:
# 1. Compute full inverse FFT
reconstructed = np.fft.ifft(fft_result).real
value_at_50 = reconstructed[50]  # Only works for original indices

# 2. For arbitrary positions (like t=50.5), need custom interpolation
```

**This Library:**
```python
# Evaluate at any position directly
value = DiscreteFourier.calculate_fourier_value(coefs, 50.5)
# Works for any t, including beyond original data range
```

### **Analytical Derivatives**

**NumPy FFT:**
```python
# No built-in derivative calculation
# Must write custom code to differentiate Fourier series
# Requires understanding of complex derivative formulas
```

**This Library:**
```python
# Built-in analytical derivatives
first_deriv = DiscreteFourier.calculate_fourier_derivative_value(coefs, t)
second_deriv = DiscreteFourier.calculate_fourier_double_derivative_value(coefs, t)
# Ready to use for trend analysis, extrema detection, etc.
```

### **Comparison Table**

| Feature | NumPy/SciPy FFT | discrete_fourier |
|---------|----------------|------------------|
| Coefficient format | Complex numbers | Real (a_k, b_k) |
| Learning curve | Requires complex math | Simple real arithmetic |
| Point evaluation | Reconstruct full signal | Direct evaluation at any t |
| Derivatives | Manual implementation | Built-in 1st & 2nd derivatives |
| Extrapolation | Not straightforward | Natural (periodic) |
| Use case | General FFT operations | Real Fourier series focus |

### **When to Use This Library**

✅ **Use discrete_fourier when:**
- Working with real-valued signals (not complex)
- Need to evaluate series at arbitrary positions
- Require derivative calculations
- Want interpretable cosine/sine coefficients
- Teaching or learning Fourier series concepts
- Prefer simple API over FFT theory

❌ **Use NumPy/SciPy FFT when:**
- Need full FFT/IFFT transformations
- Working with complex signals
- Require 2D/3D transforms
- Need specialized FFT algorithms (Bluestein, Rader, etc.)
- Performance critical applications with large datasets

## Installation

```bash
pip install discrete_fourier
```

## Quick Start

```python
from discrete_fourier import DiscreteFourier

# Sample data
data = [1.0, 2.5, 4.0, 3.5, 2.0, 1.5]

# Calculate Fourier coefficients
coefs = DiscreteFourier.calculate_fourier_coefs(data)

# Reconstruct values at original positions
for i in range(len(data)):
    value = DiscreteFourier.calculate_fourier_value(coefs, i + 1)
    print(f"Position {i+1}: Original={data[i]:.2f}, Reconstructed={value:.2f}")

# Predict future values (extrapolation)
future_value = DiscreteFourier.calculate_fourier_value(coefs, len(data) + 1)
print(f"Next value: {future_value:.2f}")

# Calculate derivatives
derivative = DiscreteFourier.calculate_fourier_derivative_value(coefs, 3)
second_deriv = DiscreteFourier.calculate_fourier_double_derivative_value(coefs, 3)
print(f"At position 3: f'={derivative:.2f}, f''={second_deriv:.2f}")
```

## API Reference

### `DiscreteFourier.calculate_fourier_coefs(data_in)`

Calculate Fourier series coefficients from discrete data.

**Parameters:**
- `data_in` (list or array-like): Input data sequence

**Returns:**
- `tuple`: (a_k, b_k) where:
  - `a_k`: Cosine coefficients (a_k[0] is the mean)
  - `b_k`: Sine coefficients (b_k[0] is always 0)

**Notes:**
- If input has odd length, the first element is removed to ensure even length
- Uses real Fourier series representation: `f(t) = a_0 + Σ[a_k*cos(2πkt/N) + b_k*sin(2πkt/N)]`

### `DiscreteFourier.calculate_fourier_value(fourier_coefs, t)`

Reconstruct the signal value at position t.

**Parameters:**
- `fourier_coefs` (tuple): (a_k, b_k) from `calculate_fourier_coefs()`
- `t` (int or float): Position to evaluate (can be beyond original data range)

**Returns:**
- `float`: Reconstructed value at position t

**Notes:**
- Due to periodicity: f(t) = f(t + N) where N is the original data length
- Can be used for interpolation (within data range) or extrapolation (beyond data range)

### `DiscreteFourier.calculate_fourier_derivative_value(fourier_coefs, t)`

Calculate the first derivative (slope) at position t.

**Parameters:**
- `fourier_coefs` (tuple): (a_k, b_k) from `calculate_fourier_coefs()`
- `t` (int or float): Position to evaluate

**Returns:**
- `float`: First derivative df/dt at position t

**Use cases:**
- Trend detection (positive = increasing, negative = decreasing)
- Finding local maxima/minima (where f'(t) = 0)
- Velocity calculation from position data

### `DiscreteFourier.calculate_fourier_double_derivative_value(fourier_coefs, t)`

Calculate the second derivative (curvature) at position t.

**Parameters:**
- `fourier_coefs` (tuple): (a_k, b_k) from `calculate_fourier_coefs()`
- `t` (int or float): Position to evaluate

**Returns:**
- `float`: Second derivative d²f/dt² at position t

**Use cases:**
- Concavity detection (positive = concave up, negative = concave down)
- Finding inflection points (where f''(t) = 0)
- Acceleration calculation from position data

## Mathematical Background

The Discrete Fourier Series represents a periodic signal as a sum of sinusoids:

```
f(t) = a₀ + Σ[aₖ·cos(2πkt/N) + bₖ·sin(2πkt/N)]
```

Where:
- N is the number of data points
- k ranges from 1 to N/2
- a₀ is the mean (DC component)

The coefficients are computed using:

```
a₀ = mean(data)
aₖ = (2/N)·Σ[data[i]·cos(2πki/N)]  for k = 1..N/2
bₖ = (2/N)·Σ[data[i]·sin(2πki/N)]  for k = 1..N/2-1
```

## Use Cases

- **Signal Processing**: Analyze periodic signals and extract frequency components
- **Time Series Analysis**: Smooth noisy data and identify cyclical patterns
- **Data Interpolation**: Fill missing values in periodic sequences
- **Trend Analysis**: Calculate derivatives to detect trends and turning points
- **Financial Analysis**: Model cyclical patterns in market data
- **Scientific Computing**: Represent periodic phenomena mathematically
- **Education**: Teaching Fourier series with clear, interpretable real coefficients
- **Physics**: Modeling oscillatory systems (springs, pendulums, waves)
- **Economics**: Analyzing seasonal patterns and business cycles

## Limitations

- **Periodicity Assumption**: Fourier series assumes the signal is periodic. Extrapolation beyond the original data will repeat the pattern.
- **Even Length**: Input data is adjusted to even length (first element removed if odd).
- **Discontinuities**: Sharp jumps in data may cause Gibbs phenomenon (ringing artifacts).

## Example: Complete Workflow

```python
import numpy as np
from discrete_fourier import DiscreteFourier

# Create sample data (sine wave with noise)
N = 100
t = np.linspace(0, 4*np.pi, N)
data = np.sin(t) + 0.1 * np.random.randn(N)

# Step 1: Calculate Fourier coefficients
coefs = DiscreteFourier.calculate_fourier_coefs(data.tolist())

# Step 2: Reconstruct the smoothed signal
reconstructed = [
    DiscreteFourier.calculate_fourier_value(coefs, i+1) 
    for i in range(N)
]

# Step 3: Find local maxima (where derivative changes from + to -)
derivatives = [
    DiscreteFourier.calculate_fourier_derivative_value(coefs, i+1)
    for i in range(N)
]

# Step 4: Predict next 10 values
predictions = [
    DiscreteFourier.calculate_fourier_value(coefs, N + i + 1)
    for i in range(10)
]

print(f"Predicted next values: {predictions}")
```

## Requirements

- Python 3.8+
- NumPy

## License

See LICENSE file for details.

## Author

Ricardo Marcelo Alvarez  
Date: 2025-12-19

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
