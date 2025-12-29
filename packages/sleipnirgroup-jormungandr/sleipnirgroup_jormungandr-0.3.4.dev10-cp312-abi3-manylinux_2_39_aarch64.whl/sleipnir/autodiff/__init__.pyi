from collections.abc import Callable, Iterator, Sequence
import enum
from typing import Annotated, overload

import numpy
from numpy.typing import NDArray
import scipy

import _sleipnir.optimization


class ExpressionType(enum.Enum):
    """
    Expression type.

    Used for autodiff caching.
    """

    NONE = 0
    """There is no expression."""

    CONSTANT = 1
    """The expression is a constant."""

    LINEAR = 2
    """The expression is composed of linear and lower-order operators."""

    QUADRATIC = 3
    """The expression is composed of quadratic and lower-order operators."""

    NONLINEAR = 4
    """The expression is composed of nonlinear and lower-order operators."""

class Variable:
    """
    An autodiff variable pointing to an expression node.

    Template parameter ``Scalar_``:
        Scalar type.
    """

    @overload
    def __init__(self) -> None:
        """Constructs a linear Variable with a value of zero."""

    @overload
    def __init__(self, value: float) -> None:
        """Constructs an empty Variable."""

    def set_value(self, value: float) -> None:
        """
        Sets Variable's internal value.

        Parameter ``value``:
            The value of the Variable.
        """

    def value(self) -> float:
        """
        Returns the value of this variable.

        Returns:
            The value of this variable.
        """

    def type(self) -> ExpressionType:
        """
        Returns the type of this expression (constant, linear, quadratic, or
        nonlinear).

        Returns:
            The type of this expression.
        """

    @overload
    def __mul__(self, rhs: Variable) -> Variable: ...

    @overload
    def __mul__(self, rhs: float) -> Variable: ...

    @overload
    def __mul__(self, rhs: int) -> Variable: ...

    @overload
    def __imul__(self, rhs: Variable) -> Variable:
        """
        Variable-Variable compound multiplication operator.

        Parameter ``rhs``:
            Operator right-hand side.

        Returns:
            Result of multiplication.
        """

    @overload
    def __imul__(self, rhs: float) -> Variable: ...

    @overload
    def __imul__(self, rhs: int) -> Variable: ...

    @overload
    def __truediv__(self, rhs: Variable) -> Variable: ...

    @overload
    def __truediv__(self, rhs: float) -> Variable: ...

    @overload
    def __truediv__(self, rhs: int) -> Variable: ...

    @overload
    def __itruediv__(self, rhs: Variable) -> Variable:
        """
        Variable-Variable compound division operator.

        Parameter ``rhs``:
            Operator right-hand side.

        Returns:
            Result of division.
        """

    @overload
    def __itruediv__(self, rhs: float) -> Variable: ...

    @overload
    def __itruediv__(self, rhs: int) -> Variable: ...

    @overload
    def __add__(self, rhs: Variable) -> Variable: ...

    @overload
    def __add__(self, rhs: float) -> Variable: ...

    @overload
    def __add__(self, rhs: int) -> Variable: ...

    @overload
    def __iadd__(self, rhs: Variable) -> Variable:
        """
        Variable-Variable compound addition operator.

        Parameter ``rhs``:
            Operator right-hand side.

        Returns:
            Result of addition.
        """

    @overload
    def __iadd__(self, rhs: float) -> Variable: ...

    @overload
    def __iadd__(self, rhs: int) -> Variable: ...

    @overload
    def __sub__(self, rhs: Variable) -> Variable: ...

    @overload
    def __sub__(self, rhs: float) -> Variable: ...

    @overload
    def __sub__(self, rhs: int) -> Variable: ...

    @overload
    def __isub__(self, rhs: Variable) -> Variable:
        """
        Variable-Variable compound subtraction operator.

        Parameter ``rhs``:
            Operator right-hand side.

        Returns:
            Result of subtraction.
        """

    @overload
    def __isub__(self, rhs: float) -> Variable: ...

    @overload
    def __isub__(self, rhs: int) -> Variable: ...

    @overload
    def __rmul__(self, lhs: float) -> Variable: ...

    @overload
    def __rmul__(self, lhs: int) -> Variable: ...

    @overload
    def __rtruediv__(self, lhs: float) -> Variable: ...

    @overload
    def __rtruediv__(self, lhs: int) -> Variable: ...

    @overload
    def __radd__(self, lhs: float) -> Variable: ...

    @overload
    def __radd__(self, lhs: int) -> Variable: ...

    @overload
    def __rsub__(self, lhs: float) -> Variable: ...

    @overload
    def __rsub__(self, lhs: int) -> Variable: ...

    def __pow__(self, power: int) -> Variable: ...

    def __neg__(self) -> Variable: ...

    def __pos__(self) -> Variable: ...

    @overload
    def __eq__(self, rhs: Variable) -> _sleipnir.optimization.EqualityConstraints:
        """
        Equality operator that returns an equality constraint for two
        Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __eq__(self, rhs: float) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, lhs: float) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: int) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, lhs: int) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __lt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, lhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, lhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, lhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, lhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, lhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, lhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, lhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, lhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

class VariableMatrix:
    """
    A matrix of autodiff variables.

    Template parameter ``Scalar_``:
        Scalar type.
    """

    @overload
    def __init__(self) -> None:
        """Constructs an empty VariableMatrix."""

    @overload
    def __init__(self, rows: int) -> None:
        """
        Constructs a zero-initialized VariableMatrix column vector with the
        given rows.

        Parameter ``rows``:
            The number of matrix rows.
        """

    @overload
    def __init__(self, rows: int, cols: int) -> None:
        """
        Constructs a zero-initialized VariableMatrix with the given
        dimensions.

        Parameter ``rows``:
            The number of matrix rows.

        Parameter ``cols``:
            The number of matrix columns.
        """

    @overload
    def __init__(self, list: Sequence[Sequence[Variable]]) -> None:
        """
        Constructs a scalar VariableMatrix from a nested list of Variables.

        Parameter ``list``:
            The nested list of Variables.
        """

    @overload
    def __init__(self, list: Sequence[Sequence[float]]) -> None:
        """
        Constructs a scalar VariableMatrix from a nested list of scalars.

        This overload is for Python bindings only.

        Parameter ``list``:
            The nested list of Variables.
        """

    @overload
    def __init__(self, values: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None:
        """
        Constructs a VariableMatrix from an Eigen matrix.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def __init__(self, values: Annotated[NDArray[numpy.float32], dict(shape=(None, None))]) -> None:
        """
        Constructs a VariableMatrix from an Eigen matrix.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def __init__(self, variable: Variable) -> None:
        """
        Constructs a scalar VariableMatrix from a Variable.

        Parameter ``variable``:
            Variable.
        """

    @overload
    def __init__(self, values: VariableBlock) -> None:
        """
        Constructs a VariableMatrix from a VariableBlock.

        Parameter ``values``:
            VariableBlock of values.
        """

    @overload
    def __init__(self, arg: VariableBlock, /) -> None: ...

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None:
        """
        Sets the VariableMatrix's internal values.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.float32], dict(shape=(None, None))]) -> None: ...

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.int64], dict(shape=(None, None))]) -> None: ...

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.int32], dict(shape=(None, None))]) -> None: ...

    @overload
    def __setitem__(self, row: int, value: Variable) -> Variable: ...

    @overload
    def __setitem__(self, slices: tuple, value: object) -> None: ...

    @overload
    def __getitem__(self, row: int) -> Variable:
        """
        Returns the element at the given index.

        Parameter ``index``:
            The index.

        Returns:
            The element at the given index.
        """

    @overload
    def __getitem__(self, slices: tuple) -> object:
        """
        Returns the element at the given row and column.

        Parameter ``row``:
            The row.

        Parameter ``col``:
            The column.

        Returns:
            The element at the given row and column.
        """

    def row(self, row: int) -> VariableBlock:
        """
        Returns a row slice of the variable matrix.

        Parameter ``row``:
            The row to slice.

        Returns:
            A row slice of the variable matrix.
        """

    def col(self, col: int) -> VariableBlock:
        """
        Returns a column slice of the variable matrix.

        Parameter ``col``:
            The column to slice.

        Returns:
            A column slice of the variable matrix.
        """

    @overload
    def __mul__(self, rhs: VariableMatrix) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: float) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: int) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: Variable) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: float) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: int) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: Variable) -> VariableMatrix: ...

    @overload
    def __matmul__(self, rhs: VariableMatrix) -> VariableMatrix: ...

    @overload
    def __matmul__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __matmul__(self, rhs: VariableMatrix) -> VariableMatrix: ...

    @overload
    def __matmul__(self, rhs: VariableBlock) -> VariableMatrix: ...

    def __array_ufunc__(self, ufunc: object, method: str, *inputs, **kwargs) -> object: ...

    @overload
    def __add__(self, rhs: VariableMatrix) -> VariableMatrix: ...

    @overload
    def __add__(self, rhs: float) -> Variable: ...

    @overload
    def __add__(self, rhs: int) -> Variable: ...

    @overload
    def __add__(self, rhs: Variable) -> Variable: ...

    @overload
    def __add__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __add__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    @overload
    def __sub__(self, rhs: VariableMatrix) -> VariableMatrix: ...

    @overload
    def __sub__(self, rhs: float) -> Variable: ...

    @overload
    def __sub__(self, rhs: int) -> Variable: ...

    @overload
    def __sub__(self, rhs: Variable) -> Variable: ...

    @overload
    def __sub__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __sub__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    def __neg__(self) -> VariableMatrix: ...

    @overload
    def __truediv__(self, rhs: float) -> VariableMatrix: ...

    @overload
    def __truediv__(self, rhs: int) -> VariableMatrix: ...

    @overload
    def __truediv__(self, rhs: Variable) -> VariableMatrix: ...

    @overload
    def __itruediv__(self, rhs: float) -> VariableMatrix: ...

    @overload
    def __itruediv__(self, rhs: int) -> VariableMatrix: ...

    @overload
    def __itruediv__(self, rhs: Variable) -> VariableMatrix: ...

    @overload
    def __radd__(self, lhs: float) -> Variable: ...

    @overload
    def __radd__(self, lhs: int) -> Variable: ...

    @overload
    def __radd__(self, lhs: Variable) -> Variable: ...

    @overload
    def __radd__(self, lhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __radd__(self, lhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    @overload
    def __rsub__(self, lhs: float) -> Variable: ...

    @overload
    def __rsub__(self, lhs: int) -> Variable: ...

    @overload
    def __rsub__(self, lhs: Variable) -> Variable: ...

    @overload
    def __rsub__(self, lhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __rsub__(self, lhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    def __pow__(self, power: int) -> VariableMatrix: ...

    @property
    def T(self) -> VariableMatrix:
        """
        Returns the transpose of the variable matrix.

        Returns:
            The transpose of the variable matrix.
        """

    def rows(self) -> int:
        """
        Returns the number of rows in the matrix.

        Returns:
            The number of rows in the matrix.
        """

    def cols(self) -> int:
        """
        Returns the number of columns in the matrix.

        Returns:
            The number of columns in the matrix.
        """

    @property
    def shape(self) -> tuple: ...

    @overload
    def value(self, row: int, col: int) -> float:
        """
        Returns an element of the variable matrix.

        Parameter ``row``:
            The row of the element to return.

        Parameter ``col``:
            The column of the element to return.

        Returns:
            An element of the variable matrix.
        """

    @overload
    def value(self, index: int) -> float:
        """
        Returns an element of the variable matrix.

        Parameter ``index``:
            The index of the element to return.

        Returns:
            An element of the variable matrix.
        """

    @overload
    def value(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """
        Returns the contents of the variable matrix.

        Returns:
            The contents of the variable matrix.
        """

    def cwise_map(self, func: Callable[[Variable], Variable]) -> VariableMatrix:
        """
        Transforms the matrix coefficient-wise with an unary operator.

        Parameter ``unary_op``:
            The unary operator to use for the transform operation.

        Returns:
            Result of the unary operator.
        """

    @staticmethod
    def zero(rows: int, cols: int) -> VariableMatrix:
        """
        Returns a variable matrix filled with zeroes.

        Parameter ``rows``:
            The number of matrix rows.

        Parameter ``cols``:
            The number of matrix columns.

        Returns:
            A variable matrix filled with zeroes.
        """

    @staticmethod
    def ones(rows: int, cols: int) -> VariableMatrix:
        """
        Returns a variable matrix filled with ones.

        Parameter ``rows``:
            The number of matrix rows.

        Parameter ``cols``:
            The number of matrix columns.

        Returns:
            A variable matrix filled with ones.
        """

    @overload
    def __eq__(self, rhs: VariableMatrix) -> _sleipnir.optimization.EqualityConstraints:
        """
        Equality operator that returns an equality constraint for two
        Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __eq__(self, rhs: float) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: float) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: int) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: int) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: Variable) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: Variable) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: VariableBlock) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __lt__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    def __len__(self) -> int:
        """
        Returns the number of rows in the matrix.

        Returns:
            The number of rows in the matrix.
        """

    def __iter__(self) -> Iterator[Variable]: ...

class VariableBlock:
    """
    A submatrix of autodiff variables with reference semantics.

    Template parameter ``Mat``:
        The type of the matrix whose storage this class points to.
    """

    @overload
    def set_value(self, value: float) -> None:
        """
        Assigns a scalar to the block.

        This only works for blocks with one row and one column.

        Parameter ``value``:
            Value to assign.
        """

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None:
        """
        Sets block's internal values.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.float32], dict(shape=(None, None))]) -> None:
        """
        Sets block's internal values.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.int64], dict(shape=(None, None))]) -> None:
        """
        Sets block's internal values.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def set_value(self, values: Annotated[NDArray[numpy.int32], dict(shape=(None, None))]) -> None:
        """
        Sets block's internal values.

        Parameter ``values``:
            Eigen matrix of values.
        """

    @overload
    def __setitem__(self, row: int, value: Variable) -> Variable: ...

    @overload
    def __setitem__(self, slices: tuple, value: object) -> None: ...

    @overload
    def __getitem__(self, row: int) -> Variable:
        """
        Returns a scalar subblock at the given index.

        Parameter ``index``:
            The scalar subblock's index.

        Returns:
            A scalar subblock at the given index.
        """

    @overload
    def __getitem__(self, slices: tuple) -> object:
        """
        Returns a scalar subblock at the given row and column.

        Parameter ``row``:
            The scalar subblock's row.

        Parameter ``col``:
            The scalar subblock's column.

        Returns:
            A scalar subblock at the given row and column.
        """

    def row(self, row: int) -> VariableBlock:
        """
        Returns a row slice of the variable matrix.

        Parameter ``row``:
            The row to slice.

        Returns:
            A row slice of the variable matrix.
        """

    def col(self, col: int) -> VariableBlock:
        """
        Returns a column slice of the variable matrix.

        Parameter ``col``:
            The column to slice.

        Returns:
            A column slice of the variable matrix.
        """

    def __array_ufunc__(self, ufunc: object, method: str, *inputs, **kwargs) -> object: ...

    @overload
    def __add__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __add__(self, rhs: float) -> Variable: ...

    @overload
    def __add__(self, rhs: int) -> Variable: ...

    @overload
    def __add__(self, rhs: Variable) -> Variable: ...

    @overload
    def __add__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    @overload
    def __sub__(self, rhs: VariableBlock) -> VariableMatrix: ...

    @overload
    def __sub__(self, rhs: float) -> Variable: ...

    @overload
    def __sub__(self, rhs: int) -> Variable: ...

    @overload
    def __sub__(self, rhs: Variable) -> Variable: ...

    @overload
    def __sub__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    def __neg__(self) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: float) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: int) -> VariableMatrix: ...

    @overload
    def __mul__(self, rhs: Variable) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: float) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: int) -> VariableMatrix: ...

    @overload
    def __rmul__(self, lhs: Variable) -> VariableMatrix: ...

    @overload
    def __truediv__(self, rhs: float) -> VariableMatrix: ...

    @overload
    def __truediv__(self, rhs: int) -> VariableMatrix: ...

    @overload
    def __truediv__(self, rhs: Variable) -> VariableMatrix: ...

    @overload
    def __itruediv__(self, rhs: float) -> VariableBlock: ...

    @overload
    def __itruediv__(self, rhs: int) -> VariableBlock: ...

    @overload
    def __itruediv__(self, rhs: Variable) -> VariableBlock: ...

    @overload
    def __radd__(self, lhs: float) -> Variable: ...

    @overload
    def __radd__(self, lhs: int) -> Variable: ...

    @overload
    def __radd__(self, lhs: Variable) -> Variable: ...

    @overload
    def __radd__(self, lhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    @overload
    def __rsub__(self, lhs: float) -> Variable: ...

    @overload
    def __rsub__(self, lhs: int) -> Variable: ...

    @overload
    def __rsub__(self, lhs: Variable) -> Variable: ...

    @overload
    def __rsub__(self, lhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> VariableMatrix: ...

    def __pow__(self, power: int) -> VariableMatrix: ...

    @property
    def T(self) -> VariableMatrix:
        """
        Returns the transpose of the variable matrix.

        Returns:
            The transpose of the variable matrix.
        """

    def rows(self) -> int:
        """
        Returns the number of rows in the matrix.

        Returns:
            The number of rows in the matrix.
        """

    def cols(self) -> int:
        """
        Returns the number of columns in the matrix.

        Returns:
            The number of columns in the matrix.
        """

    @property
    def shape(self) -> tuple: ...

    @overload
    def value(self, row: int, col: int) -> float:
        """
        Returns an element of the variable matrix.

        Parameter ``row``:
            The row of the element to return.

        Parameter ``col``:
            The column of the element to return.

        Returns:
            An element of the variable matrix.
        """

    @overload
    def value(self, index: int) -> float:
        """
        Returns an element of the variable block.

        Parameter ``index``:
            The index of the element to return.

        Returns:
            An element of the variable block.
        """

    @overload
    def value(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None, None), order='F')]:
        """
        Returns the contents of the variable matrix.

        Returns:
            The contents of the variable matrix.
        """

    def cwise_map(self, func: Callable[[Variable], Variable]) -> VariableMatrix:
        """
        Transforms the matrix coefficient-wise with an unary operator.

        Parameter ``unary_op``:
            The unary operator to use for the transform operation.

        Returns:
            Result of the unary operator.
        """

    @overload
    def __eq__(self, rhs: VariableBlock) -> _sleipnir.optimization.EqualityConstraints:
        """
        Equality operator that returns an equality constraint for two
        Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __eq__(self, rhs: float) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: float) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: int) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: int) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: Variable) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: Variable) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: VariableMatrix) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __eq__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.EqualityConstraints: ...

    @overload
    def __lt__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __lt__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __le__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __gt__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than comparison operator that returns an inequality constraint
        for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: VariableBlock) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: float) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: int) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Variable) -> _sleipnir.optimization.InequalityConstraints:
        """
        Less-than-or-equal-to comparison operator that returns an inequality
        constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: VariableMatrix) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    @overload
    def __ge__(self, rhs: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> _sleipnir.optimization.InequalityConstraints:
        """
        Greater-than-or-equal-to comparison operator that returns an
        inequality constraint for two Variables.

        Parameter ``lhs``:
            Left-hand side.

        Parameter ``rhs``:
            Left-hand side.
        """

    def __len__(self) -> int:
        """
        Returns the number of rows in the matrix.

        Returns:
            The number of rows in the matrix.
        """

    def __iter__(self) -> Iterator[Variable]: ...

class Gradient:
    """
    This class calculates the gradient of a variable with respect to a
    vector of variables.

    The gradient is only recomputed if the variable expression is
    quadratic or higher order.

    Template parameter ``Scalar``:
        Scalar type.
    """

    @overload
    def __init__(self, variable: Variable, wrt: Variable) -> None:
        """
        Constructs a Gradient object.

        Parameter ``variable``:
            Variable of which to compute the gradient.

        Parameter ``wrt``:
            Variable with respect to which to compute the gradient.
        """

    @overload
    def __init__(self, variable: Variable, wrt: VariableMatrix) -> None: ...

    def get(self) -> VariableMatrix:
        """
        Returns the gradient as a VariableMatrix.

        This is useful when constructing optimization problems with
        derivatives in them.

        Returns:
            The gradient as a VariableMatrix.
        """

    def value(self) -> scipy.sparse.csc_matrix[float]:
        """
        Evaluates the gradient at wrt's value.

        Returns:
            The gradient at wrt's value.
        """

class Hessian:
    """
    This class calculates the Hessian of a variable with respect to a
    vector of variables.

    The gradient tree is cached so subsequent Hessian calculations are
    faster, and the Hessian is only recomputed if the variable expression
    is nonlinear.

    Template parameter ``Scalar``:
        Scalar type.

    Template parameter ``UpLo``:
        Which part of the Hessian to compute (Lower or Lower | Upper).
    """

    @overload
    def __init__(self, variable: Variable, wrt: Variable) -> None:
        """
        Constructs a Hessian object.

        Parameter ``variable``:
            Variable of which to compute the Hessian.

        Parameter ``wrt``:
            Variable with respect to which to compute the Hessian.
        """

    @overload
    def __init__(self, variable: Variable, wrt: VariableMatrix) -> None: ...

    def get(self) -> VariableMatrix:
        """
        Returns the Hessian as a VariableMatrix.

        This is useful when constructing optimization problems with
        derivatives in them.

        Returns:
            The Hessian as a VariableMatrix.
        """

    def value(self) -> scipy.sparse.csc_matrix[float]:
        """
        Evaluates the Hessian at wrt's value.

        Returns:
            The Hessian at wrt's value.
        """

class Jacobian:
    """
    This class calculates the Jacobian of a vector of variables with
    respect to a vector of variables.

    The Jacobian is only recomputed if the variable expression is
    quadratic or higher order.

    Template parameter ``Scalar``:
        Scalar type.
    """

    @overload
    def __init__(self, variable: Variable, wrt: Variable) -> None:
        """
        Constructs a Jacobian object.

        Parameter ``variable``:
            Variable of which to compute the Jacobian.

        Parameter ``wrt``:
            Variable with respect to which to compute the Jacobian.
        """

    @overload
    def __init__(self, variable: Variable, wrt: VariableMatrix) -> None: ...

    @overload
    def __init__(self, variables: VariableMatrix, wrt: VariableMatrix) -> None: ...

    def get(self) -> VariableMatrix:
        """
        Returns the Jacobian as a VariableMatrix.

        This is useful when constructing optimization problems with
        derivatives in them.

        Returns:
            The Jacobian as a VariableMatrix.
        """

    def value(self) -> scipy.sparse.csc_matrix[float]:
        """
        Evaluates the Jacobian at wrt's value.

        Returns:
            The Jacobian at wrt's value.
        """

@overload
def abs(x: float) -> Variable:
    """
    abs() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def abs(x: Variable) -> Variable: ...

@overload
def acos(x: float) -> Variable:
    """
    acos() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def acos(x: Variable) -> Variable: ...

@overload
def asin(x: float) -> Variable:
    """
    asin() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def asin(x: Variable) -> Variable: ...

@overload
def atan(x: float) -> Variable:
    """
    atan() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def atan(x: Variable) -> Variable: ...

@overload
def atan2(y: float, x: float) -> Variable:
    """
    atan2() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``y``:
        The y argument.

    Parameter ``x``:
        The x argument.
    """

@overload
def atan2(y: float, x: Variable) -> Variable: ...

@overload
def atan2(y: Variable, x: float) -> Variable: ...

@overload
def atan2(y: Variable, x: Variable) -> Variable: ...

@overload
def cbrt(x: float) -> Variable:
    """
    cbrt() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def cbrt(x: Variable) -> Variable: ...

@overload
def cos(x: float) -> Variable:
    """
    cos() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def cos(x: Variable) -> Variable: ...

@overload
def cosh(x: float) -> Variable:
    """
    cosh() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def cosh(x: Variable) -> Variable: ...

@overload
def erf(x: float) -> Variable:
    """
    erf() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def erf(x: Variable) -> Variable: ...

@overload
def exp(x: float) -> Variable:
    """
    exp() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def exp(x: Variable) -> Variable: ...

@overload
def hypot(x: float, y: float) -> Variable:
    """
    hypot() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The x argument.

    Parameter ``y``:
        The y argument.
    """

@overload
def hypot(x: float, y: Variable) -> Variable: ...

@overload
def hypot(x: Variable, y: float) -> Variable: ...

@overload
def hypot(x: Variable, y: Variable) -> Variable: ...

@overload
def hypot(x: float, y: float, z: float) -> Variable: ...

@overload
def hypot(x: float, y: float, z: Variable) -> Variable: ...

@overload
def hypot(x: float, y: Variable, z: float) -> Variable: ...

@overload
def hypot(x: float, y: Variable, z: Variable) -> Variable: ...

@overload
def hypot(x: Variable, y: float, z: float) -> Variable: ...

@overload
def hypot(x: Variable, y: float, z: Variable) -> Variable: ...

@overload
def hypot(x: Variable, y: Variable, z: float) -> Variable: ...

@overload
def hypot(x: Variable, y: Variable, z: Variable) -> Variable: ...

@overload
def log(x: float) -> Variable:
    """
    log() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def log(x: Variable) -> Variable: ...

@overload
def log10(x: float) -> Variable:
    """
    log10() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def log10(x: Variable) -> Variable: ...

@overload
def pow(base: float, power: float) -> Variable:
    """
    pow() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``base``:
        The base.

    Parameter ``power``:
        The power.
    """

@overload
def pow(base: float, power: Variable) -> Variable: ...

@overload
def pow(base: Variable, power: float) -> Variable: ...

@overload
def pow(base: Variable, power: Variable) -> Variable: ...

@overload
def sign(x: float) -> Variable:
    """
    sign() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def sign(x: Variable) -> Variable: ...

@overload
def sin(x: float) -> Variable:
    """
    sin() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def sin(x: Variable) -> Variable: ...

@overload
def sinh(x: float) -> Variable:
    """
    sinh() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def sinh(x: Variable) -> Variable: ...

@overload
def sqrt(x: float) -> Variable:
    """
    sqrt() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def sqrt(x: Variable) -> Variable: ...

@overload
def tan(x: float) -> Variable:
    """
    tan() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def tan(x: Variable) -> Variable: ...

@overload
def tanh(x: float) -> Variable:
    """
    tanh() for Variables.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``x``:
        The argument.
    """

@overload
def tanh(x: Variable) -> Variable: ...

def cwise_reduce(lhs: VariableMatrix, rhs: VariableMatrix, func: Callable[[Variable, Variable], Variable]) -> VariableMatrix:
    """
    Applies a coefficient-wise reduce operation to two matrices.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``lhs``:
        The left-hand side of the binary operator.

    Parameter ``rhs``:
        The right-hand side of the binary operator.

    Parameter ``binary_op``:
        The binary operator to use for the reduce operation.
    """

def block(list: Sequence[Sequence[VariableMatrix]]) -> VariableMatrix:
    """
    Assemble a VariableMatrix from a nested list of blocks.

    Each row's blocks must have the same height, and the assembled block
    rows must have the same width. For example, for the block matrix [[A,
    B], [C]] to be constructible, the number of rows in A and B must
    match, and the number of columns in [A, B] and [C] must match.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``list``:
        The nested list of blocks.
    """

def solve(A: VariableMatrix, B: VariableMatrix) -> VariableMatrix:
    """
    Solves the VariableMatrix equation AX = B for X.

    Template parameter ``Scalar``:
        Scalar type.

    Parameter ``A``:
        The left-hand side.

    Parameter ``B``:
        The right-hand side.

    Returns:
        The solution X.
    """
