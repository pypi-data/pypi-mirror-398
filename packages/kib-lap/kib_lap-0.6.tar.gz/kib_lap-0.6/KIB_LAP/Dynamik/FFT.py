import numpy as np

class FFTAnalyzer:
    def __init__(self, t: np.ndarray, y: np.ndarray, window: str = None):
        """
        Parameters
        ----------
        t : np.ndarray
            Time array (must be uniformly spaced).
        y : np.ndarray
            Signal array, same length as t.
        window : str or None
            If not None, must be one of np’s window functions, e.g. 'hann','hamming','blackman'.
        """

        # sampling
        dt = t[1] - t[0]
        if not np.allclose(np.diff(t), dt, rtol=1e-5, atol=1e-8):
            raise ValueError("t must be uniformly spaced")
        self.fs = 1.0 / dt
        self.N  = len(t)
        self._t = t
        self._y = y
        # window
        if window is not None:
            try:
                win = getattr(np, window)(self.N)
            except AttributeError:
                raise ValueError(f"Unknown window '{window}'")
        else:
            win = np.ones(self.N)
        self._y_win = y * win

        # placeholders
        self.freqs    = None
        self.amp      = None
        self.phase    = None
        self._computed = False

    def compute(self):
        """Compute the one-sided FFT, filling freqs, amp, phase."""
        # full FFT
        Y = np.fft.rfft(self._y_win)
        # frequencies
        self.freqs = np.fft.rfftfreq(self.N, d=1/self.fs)
        # amplitude correction (accounting for window & symmetry)
        # multiply by 2/N (except DC and Nyquist if present)
        A = np.abs(Y) * 2.0 / self.N
        A[0] /= 2.0
        if self.N % 2 == 0:  # Nyquist freq at end
            A[-1] /= 2.0
        self.amp   = A
        # phase
        self.phase = np.angle(Y)
        self._computed = True
        return self.freqs, self.amp, self.phase

    def plot(self, ax=None, xlim=None):
        """
        Quick plot of amplitude spectrum. 
        Returns (fig, ax).

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes to plot into. Wenn None, wird ein neues Figure/Axes‐Paar erzeugt.
        xlim : tuple of float (xmin, xmax), optional
            Frequenzbereich in Hz für die x‐Achse.
        """
        import matplotlib.pyplot as plt
        if not self._computed:
            self.compute()
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        ax.plot(self.freqs, self.amp)
        ax.set_xlabel("Frequency [Hz]")
        ax.set_ylabel("Amplitude")
        ax.grid(True)

        if xlim is not None:
            ax.set_xlim(xlim)

        return fig, ax

