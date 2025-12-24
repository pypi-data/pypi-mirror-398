"""
Discrete Fourier - Discrete Fourier functions
=============================================

Author: Ricardo Marcelo Alvarez
Date: 2025-12-19
"""

from typing import Union
import numpy

class DiscreteFourier():
    """
    DiscreteFourier
    ===============
    
    A class for computing Discrete Fourier Series coefficients and reconstructing
    signals from those coefficients. This implementation calculates Fourier series
    representation of discrete data and provides methods for evaluating the series
    and its derivatives at any point.
    
    The class uses the real Fourier series representation:
        f(t) = a_0 + Σ[a_k * cos(2πkt/N) + b_k * sin(2πkt/N)]
    
    where N is the number of data points and k ranges from 1 to N/2.
    """
    def __init__(self):
        """
        Initialize DiscreteFourier instance.
        
        Note: All methods are class methods, so instantiation is not required.
        """

    @classmethod
    def calculate_fourier_coefs(cls, data_in):
        """
        calculate_fourier_coefs
        =======================

        Calculate Fourier series coefficients from discrete data.
        
        Computes the real Fourier series coefficients (a_k, b_k) for the input data
        using the discrete Fourier series formulas. The data is automatically adjusted
        to have an even number of points if necessary.
        
        Parameters
        ----------
        data_in : list or array-like
            Input data sequence. If the length is odd, the first element is removed
            to ensure an even number of points.
        
        Returns
        -------
        tuple of (numpy.ndarray, numpy.ndarray)
            A tuple containing:
            - a_k: Cosine coefficients array, where a_k[0] is the mean (DC component)
            - b_k: Sine coefficients array, where b_k[0] is always 0
            
            Both arrays have length (N/2 + 1) where N is the number of data points.
        
        Notes
        -----
        The coefficients are computed using:
            a_0 = mean(data)
            a_k = (2/N) * Σ[data[i] * cos(2πki/N)] for k = 1..N/2
            b_k = (2/N) * Σ[data[i] * sin(2πki/N)] for k = 1..N/2-1
            b_N/2 = 0
        
        Examples
        --------
        >>> data = [1.0, 2.0, 3.0, 4.0]
        >>> a_k, b_k = DiscreteFourier.calculate_fourier_coefs(data)
        >>> print(a_k[0])  # Mean value
        2.5
        """

        result = None

        if (len(data_in) % 2) == 0:
            data = numpy.array(data_in)
        else:
            data = numpy.array(data_in[1:])

        n_t = len(data)
        k_t = int(round(n_t / 2))

        t = 1 + numpy.arange(0, n_t)
        k = 1 + numpy.arange(0, k_t)

        rad_const = (2 * numpy.pi) / n_t
        rad = rad_const * numpy.outer(k, t)

        cos_terms = numpy.cos(rad)
        sin_terms = numpy.sin(rad)

        a_k = numpy.sum(data * cos_terms, axis=1)
        b_k = numpy.sum(data * sin_terms, axis=1)

        a_k *= (2 / n_t)
        b_k *= (2 / n_t)

        a_k[k_t-1] /= 2
        b_k[k_t-1] = 0

        a_k = numpy.insert(a_k, 0, numpy.mean(data))
        b_k = numpy.insert(b_k, 0, 0)

        result = (a_k, b_k)

        return result

    @classmethod
    def calculate_fourier_value(cls, fourier_coefs, t):
        """
        calculate_fourier_value
        =======================

        Calculate the Fourier series value at a specific position.
        
        Reconstructs the signal value at position t using the Fourier coefficients.
        This method evaluates the Fourier series representation at any point,
        including positions beyond the original data range (extrapolation).
        
        Parameters
        ----------
        fourier_coefs : tuple of (numpy.ndarray, numpy.ndarray)
            Tuple of (a_k, b_k) coefficients from calculate_fourier_coefs()
        t : int or float
            Position at which to evaluate the Fourier series. Can be any real number,
            but the series is periodic with period N (the original data length).
        
        Returns
        -------
        float
            The reconstructed value at position t
        
        Notes
        -----
        The value is computed using:
            f(t) = a_0 + Σ[a_k * cos(2πkt/N) + b_k * sin(2πkt/N)]
        
        Due to the periodic nature of Fourier series, f(t) = f(t + N) = f(t + 2N) = ...
        
        Examples
        --------
        Calculate the first derivative of the Fourier series at a specific position.
        
        Computes the rate of change (slope) of the reconstructed signal at position t
        by differentiating the Fourier series term by term.
        
        Parameters
        ----------
        fourier_coefs : tuple of (numpy.ndarray, numpy.ndarray)
            Tuple of (a_k, b_k) coefficients from calculate_fourier_coefs()
        t : int or float
            Position at which to evaluate the derivative
        
        Returns
        -------
        float
            The first derivative value at position t (df/dt)
        
        Notes
        -----
        The derivative is computed using:
            f'(t) = Σ[k * (2π/N) * (-a_k * sin(2πkt/N) + b_k * cos(2πkt/N))]
        
        The derivative is useful for:
        - Detecting local maxima/minima (where f'(t) = 0)
        - Identifying trend direction (positive = increasing, negative = decreasing)
        - Calculating velocity from position data
        
        Calculate the second derivative of the Fourier series at a specific position.
        
        Computes the rate of change of the slope (curvature or acceleration) of the
        reconstructed signal at position t by differentiating the Fourier series twice.
        
        Parameters
        ----------
        fourier_coefs : tuple of (numpy.ndarray, numpy.ndarray)
            Tuple of (a_k, b_k) coefficients from calculate_fourier_coefs()
        t : int or float
            Position at which to evaluate the second derivative
        
        Returns
        -------
        float
            The second derivative value at position t (d²f/dt²)
        
        Notes
        -----
        The second derivative is computed using:
            f''(t) = Σ[-k² * (2π/N)² * (a_k * cos(2πkt/N) + b_k * sin(2πkt/N))]
        
        The second derivative is useful for:
        - Identifying inflection points (where f''(t) = 0)
        - Detecting concavity (positive = concave up, negative = concave down)
        - Calculating acceleration from position data
        - Finding local extrema (combined with first derivative)
        
        Examples
        --------
        >>> data = [1.0, 2.0, 3.0, 4.0]
        >>> coefs = DiscreteFourier.calculate_fourier_coefs(data)
        >>> second_deriv = DiscreteFourier.calculate_fourier_double_derivative_value(coefs, 2)
        >>> # Negative value indicates concave down (peak), positive indicates concave up (valley)
        >>> data = [1.0, 2.0, 3.0, 4.0]
        >>> coefs = DiscreteFourier.calculate_fourier_coefs(data)
        >>> derivative = DiscreteFourier.calculate_fourier_derivative_value(coefs, 2)
        >>> # Positive value indicates increasing trendate_fourier_coefs(data)
        >>> value_at_1 = DiscreteFourier.calculate_fourier_value(coefs, 1)
        >>> # value_at_1 should be close to data[0] = 1.0
        """
        result = 0

        a_k = fourier_coefs[0]
        b_k = fourier_coefs[1]

        result = a_k[0]

        a_k = a_k[1:]
        b_k = b_k[1:]

        k_len = len(a_k)
        n_len = k_len * 2

        k = numpy.arange(1, k_len + 1)
        rad_const = (2 * numpy.pi) / n_len
        rad = rad_const * k
        numpy_result = a_k * numpy.cos(rad * t) + b_k * numpy.sin(rad * t)

        result = result + numpy.sum(numpy_result)

        return result

    @classmethod
    def calculate_fourier_derivative_value(cls, fourier_coefs, t):
        """
        calculate_fourier_derivative_value
        ==================================
        """
        result = 0

        a_k = fourier_coefs[0]
        b_k = fourier_coefs[1]

        a_k = a_k[1:]
        b_k = b_k[1:]

        k_len = len(a_k)
        n_len = k_len * 2

        k = numpy.arange(1, k_len + 1)
        rad_const = (2 * numpy.pi) / n_len
        rad = rad_const * k
        a = (-1) * a_k * numpy.sin(rad * t)
        b =  b_k * numpy.cos(rad * t)
        numpy_result = (a + b) * rad
        result = numpy.sum(numpy_result)

        return result

    @classmethod
    def calculate_fourier_double_derivative_value(cls, fourier_coefs, t):
        """
        calculate_fourier_double_derivative_value
        =========================================
        """
        result = 0

        a_k = fourier_coefs[0]
        b_k = fourier_coefs[1]

        a_k = a_k[1:]
        b_k = b_k[1:]

        k_len = len(a_k)
        n_len = k_len * 2

        k = numpy.arange(1, k_len + 1)
        rad_const = (2 * numpy.pi) / n_len
        rad = rad_const * k
        a = (-1) * a_k * numpy.cos(rad * t)
        b =  (-1) * b_k * numpy.sin(rad * t)
        numpy_result = (a + b) * numpy.square(rad)
        result = numpy.sum(numpy_result)

        return result

    @classmethod
    def find_dominant_period(cls,
                             data_in: Union[list, numpy.ndarray] = None,
                             fourier_coefs: tuple = None):
        """
        Find the dominant period in the data using Fourier coefficient magnitudes.
        
        Identifies the frequency component with the largest magnitude, which
        represents the most prominent cyclical pattern in the data.
        
        Parameters
        ----------
        data_in : list or array-like, optional
            Input data sequence. Either data_in or fourier_coefs must be provided.
        fourier_coefs : tuple of (numpy.ndarray, numpy.ndarray), optional
            Pre-calculated (a_k, b_k) coefficients. Either data_in or fourier_coefs
            must be provided.
        
        Returns
        -------
        dict
            Dictionary containing:
            - 'period' (float): Dominant period in data points (N/k)
            - 'k' (int): Frequency index with highest magnitude
            - 'magnitude' (float): Magnitude of the dominant component
            - 'data_length' (int): Original data length N
        
        Notes
        -----
        - The magnitude of component k is: sqrt(a_k² + b_k²)
        - Period = N/k, where N is the data length
        - Maximum detectable period is N (k=1, the fundamental frequency)
        - Minimum detectable period is 2 (k=N/2, the Nyquist frequency)
        - To detect periods longer than N, you need more data
        
        The DC component (k=0, representing the mean) is excluded from analysis.
        
        Examples
        --------
        >>> data = [1, 2, 3, 4, 3, 2, 1, 2, 3, 4, 3, 2]
        >>> result = DiscreteFourier.find_dominant_period(data)
        >>> print(f"Dominant period: {result['period']:.2f} points")
        >>> print(f"This pattern repeats every {result['period']:.1f} data points")
        """
        if fourier_coefs is None:
            if data_in is None:
                raise ValueError("Either data_in or fourier_coefs must be provided")
            fourier_coefs = cls.calculate_fourier_coefs(data_in)
            n_len = len(data_in) if len(data_in) % 2 == 0 else len(data_in) - 1
        else:
            a_k = fourier_coefs[0]
            k_len = len(a_k) - 1
            n_len = k_len * 2

        a_k = fourier_coefs[0]
        b_k = fourier_coefs[1]

        # Calculate magnitudes (skip a_0, the DC component)
        magnitudes = numpy.sqrt(a_k[1:]**2 + b_k[1:]**2)

        # Find the k with maximum magnitude
        dominant_idx = numpy.argmax(magnitudes)
        dominant_k = dominant_idx + 1  # +1 because we skipped k=0

        # Calculate period: N/k
        dominant_period = n_len / dominant_k
        dominant_magnitude = magnitudes[dominant_idx]

        return {
            'period': round(float(dominant_period), 4),
            'k': round(float(dominant_k), 4),
            'magnitude': round(float(dominant_magnitude), 8),
            'data_length': n_len
        }

    @classmethod
    def find_top_periods(cls,
                         data_in: Union[list, numpy.ndarray] = None,
                         fourier_coefs: tuple = None,
                         n_periods: int = 3):
        """
        Find the top N dominant periods in the data.
        
        Identifies multiple frequency components ranked by magnitude, revealing
        the most significant cyclical patterns in the data.
        
        Parameters
        ----------
        data_in : Union[list, numpy.ndarray], optional
            Input data sequence. Either data_in or fourier_coefs must be provided.
        fourier_coefs : tuple of (numpy.ndarray, numpy.ndarray), optional
            Pre-calculated (a_k, b_k) coefficients. Either data_in or fourier_coefs
            must be provided.
        n_periods : int, default=3
            Number of top periods to return
        
        Returns
        -------
        list of dict
            List of dictionaries, sorted by magnitude (highest first), each containing:
            - 'period' (float): Period in data points (N/k)
            - 'k' (int): Frequency index
            - 'magnitude' (float): Magnitude of this component
            - 'percent' (float): Percentage of total magnitude
        
        Notes
        -----
        The percentage shows the relative importance of each frequency component.
        A high percentage (>50%) indicates a very dominant periodic pattern.
        Multiple similar percentages suggest the signal has multiple important cycles.
        
        Examples
        --------
        >>> data = numpy.sin(numpy.linspace(0, 4*numpy.pi, 100))
        >>> top_periods = DiscreteFourier.find_top_periods(data, n_periods=5)
        >>> for i, p in enumerate(top_periods, 1):
        ...     print(f"{i}. Period: {p['period']:.1f}, "
        ...           f"k={p['k']}, {p['percent']:.1f}% of signal")
        """
        if fourier_coefs is None:
            if data_in is None:
                raise ValueError("Either data_in or fourier_coefs must be provided")
            fourier_coefs = cls.calculate_fourier_coefs(data_in)
            n_len = len(data_in) if len(data_in) % 2 == 0 else len(data_in) - 1
        else:
            a_k = fourier_coefs[0]
            k_len = len(a_k) - 1
            n_len = k_len * 2

        a_k = fourier_coefs[0]
        b_k = fourier_coefs[1]

        # Calculate magnitudes (skip a_0, the DC component)
        magnitudes = numpy.sqrt(a_k[1:]**2 + b_k[1:]**2)

        # Get indices of top N magnitudes
        n_periods = min(n_periods, len(magnitudes))
        top_indices = numpy.argsort(magnitudes)[::-1][:n_periods]

        # Calculate total magnitude for percentages
        total_magnitude = magnitudes.sum()

        results = []
        for idx in top_indices:
            k = idx + 1  # +1 because we skipped k=0
            period = n_len / k
            magnitude = magnitudes[idx]
            percent = 100 * magnitude / total_magnitude if total_magnitude > 0 else 0

            results.append({
                'k': round(float(k), 4),
                'period': round(float(period), 4),
                'magnitude': round(float(magnitude), 8),
                'percent': round(float(percent), 4)
            })

        return results

    @classmethod
    def validate_period(cls,
                        data_in: Union[list, numpy.ndarray],
                        period: float,
                        window_size: int = None,
                        method: str = 'all'):
        """
        Validate if a detected period actually repeats in the data.
        
        Compares the last window of data with an earlier window separated by one period
        to verify if the pattern truly repeats. This helps distinguish real periodicity
        from mathematical artifacts.
        
        Parameters
        ----------
        data_in : list or array-like
            Input data sequence to validate
        period : float
            Period to validate (in data points). Can be fractional.
        window_size : int, optional
            Size of the comparison window. If None, uses min(period/2, 50)
        method : str, default='all'
            Validation method to use:
            - 'correlation': Pearson correlation coefficient
            - 'rmse': Root Mean Square Error (normalized)
            - 'cosine': Cosine similarity
            - 'all': Returns all metrics (recommended)
        
        Returns
        -------
        dict
            Dictionary containing validation metrics:
            - 'valid' (bool): True if period appears valid (correlation > 0.5)
            - 'confidence' (float): Overall confidence score (0-1)
            - 'correlation' (float): Pearson correlation (-1 to 1)
            - 'rmse' (float): Normalized RMSE (0 to 1, lower is better)
            - 'cosine_similarity' (float): Cosine similarity (0 to 1)
            - 'period' (float): The period being validated
            - 'window_size' (int): Size of comparison window used
            
        Notes
        -----
        The validation compares:
            - Recent window: data[-window_size:]
            - Previous cycle: data[-(period+window_size):-period]
        
        For reliable validation:
            - Need at least 2 complete periods in data
            - Larger window_size gives more robust results
            - Correlation > 0.7 indicates strong periodicity
            - Correlation < 0.3 suggests period is not real
        
        Examples
        --------
        >>> # Validate dominant period
        >>> data = numpy.sin(numpy.linspace(0, 4*numpy.pi, 100))
        >>> dominant = DiscreteFourier.find_dominant_period(data)
        >>> validation = DiscreteFourier.validate_period(data, dominant['period'])
        >>> print(f"Confidence: {validation['confidence']:.2f}")
        >>> print(f"Correlation: {validation['correlation']:.2f}")
        """
        data = numpy.array(data_in)
        period_int = int(round(period))

        # Default window size: use half the period or 50, whichever is smaller
        if window_size is None:
            window_size = min(max(period_int // 2, 10), 50)

        # Ensure we have enough data
        required_len = period_int + window_size
        if len(data) < required_len:
            return {
                'valid': False,
                'confidence': 0.0,
                'correlation': 0.0,
                'rmse': 1.0,
                'cosine_similarity': 0.0,
                'period': period,
                'window_size': window_size,
                'error': f'Insufficient data: need {required_len}, have {len(data)}'
            }

        # Extract windows for comparison
        recent_window = data[-window_size:]
        previous_cycle = data[-(period_int + window_size):-period_int]

        # Ensure both windows have the same size
        min_len = min(len(recent_window), len(previous_cycle))
        recent_window = recent_window[:min_len]
        previous_cycle = previous_cycle[:min_len]

        # Calculate correlation
        if numpy.std(recent_window) == 0 or numpy.std(previous_cycle) == 0:
            correlation = 0.0
        else:
            correlation = numpy.corrcoef(recent_window, previous_cycle)[0, 1]

        # Calculate normalized RMSE
        rmse = numpy.sqrt(numpy.mean((recent_window - previous_cycle)**2))
        data_range = numpy.std(data)
        normalized_rmse = rmse / data_range if data_range > 0 else 1.0
        normalized_rmse = min(normalized_rmse, 1.0)  # Cap at 1.0

        # Calculate cosine similarity
        dot_product = numpy.dot(recent_window, previous_cycle)
        norm_recent = numpy.linalg.norm(recent_window)
        norm_previous = numpy.linalg.norm(previous_cycle)

        if norm_recent == 0 or norm_previous == 0:
            cosine_similarity = 0.0
        else:
            cosine_similarity = dot_product / (norm_recent * norm_previous)

        # Calculate overall confidence score
        # Weight: correlation 50%, cosine 30%, (1-rmse) 20%
        confidence = (
            0.5 * max(correlation, 0) +
            0.3 * max(cosine_similarity, 0) +
            0.2 * (1 - normalized_rmse)
        )
        confidence = max(0.0, min(1.0, confidence))

        # Determine if valid (correlation > 0.5 or confidence > 0.6)
        valid = correlation > 0.5 or confidence > 0.6

        result = {
            'valid': bool(valid),
            'confidence': round(float(confidence), 8),
            'correlation': round(float(correlation), 8),
            'rmse': round(float(normalized_rmse), 8),
            'cosine_similarity': round(float(cosine_similarity), 8),
            'period': round(float(period), 8),
            'window_size': int(window_size)
        }

        if method == 'correlation':
            return correlation
        elif method == 'rmse':
            return normalized_rmse
        elif method == 'cosine':
            return cosine_similarity
        else:  # method == 'all'
            return result
