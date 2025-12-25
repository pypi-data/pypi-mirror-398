"""
imuBias submodule
"""
from __future__ import annotations
import numpy
import numpy.typing
import typing
__all__: list[str] = ['ConstantBias']
class ConstantBias:
    @staticmethod
    def Identity() -> ConstantBias:
        """
        identity for group operation
        """
    def __add__(self, arg0: ConstantBias) -> ConstantBias:
        ...
    def __getstate__(self) -> tuple:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, biasAcc: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 1]"], biasGyro: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 1]"]) -> None:
        ...
    def __neg__(self) -> ConstantBias:
        ...
    def __repr__(self, s: str = '') -> str:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    def __sub__(self, arg0: ConstantBias) -> ConstantBias:
        ...
    def accelerometer(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
        get accelerometer bias
        """
    def correctAccelerometer(self, measurement: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
        Correct an accelerometer measurement using this bias model, and optionally compute Jacobians.
        """
    def correctGyroscope(self, measurement: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
        Correct a gyroscope measurement using this bias model, and optionally compute Jacobians.
        """
    def deserialize(self, serialized: str) -> None:
        ...
    def equals(self, expected: ConstantBias, tol: typing.SupportsFloat) -> bool:
        """
        equality up to tolerance
        """
    def gyroscope(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
        get gyroscope bias
        """
    def localCoordinates(self, b: ConstantBias) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 1]"]:
        ...
    def print(self, s: str = '') -> None:
        """
        print with optional string
        """
    def retract(self, v: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 1]"]) -> ConstantBias:
        """
        The retract function.
        """
    def serialize(self) -> str:
        ...
    def vector(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 1]"]:
        """
        return the accelerometer and gyro biases in a single vector
        """
