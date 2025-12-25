from numpy.typing import NDArray
from typing import Optional

def uniform_signal_linear_interp(
    signal: NDArray, x: NDArray, left: Optional[float], right: Optional[float]
) -> NDArray: ...
def uniform_signal_linear_vertical_interp_2d(signal: NDArray, x: float) -> NDArray: ...
def uniform_signal_cubic_interp(
    signal: NDArray, x: NDArray, left: Optional[float], right: Optional[float]
) -> NDArray: ...
