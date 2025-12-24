"""
Discrete Fourier - Discrete Fourier functions
=============================================

Author: Ricardo Marcelo Alvarez
Date: 2025-12-19
"""

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
