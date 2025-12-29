from collections.abc import Callable, Sequence
import datetime
import enum
from typing import Annotated, overload

import numpy
from numpy.typing import NDArray
import scipy

import _sleipnir.autodiff


class EqualityConstraints:
    """
    A vector of equality constraints of the form cₑ(x) = 0.

    Template parameter ``Scalar``:
        Scalar type.
    """

    def __init__(self, equality_constraints: Sequence[EqualityConstraints]) -> None:
        """
        Concatenates multiple equality constraints.

        This overload is for Python bindings only.

        Parameter ``equality_constraints``:
            The list of EqualityConstraints to concatenate.
        """

    def __bool__(self) -> bool:
        """Implicit conversion operator to bool."""

class InequalityConstraints:
    """
    A vector of inequality constraints of the form cᵢ(x) ≥ 0.

    Template parameter ``Scalar``:
        Scalar type.
    """

    def __init__(self, inequality_constraints: Sequence[InequalityConstraints]) -> None:
        """
        Concatenates multiple inequality constraints.

        This overload is for Python bindings only.

        Parameter ``inequality_constraints``:
            The list of InequalityConstraints to concatenate.
        """

    def __bool__(self) -> bool:
        """Implicit conversion operator to bool."""

@overload
def bounds(l: float, x: _sleipnir.autodiff.Variable, u: float) -> InequalityConstraints:
    """
    Helper function for creating bound constraints.

    Parameter ``l``:
        Lower bound.

    Parameter ``x``:
        Variable to bound.

    Parameter ``u``:
        Upper bound.
    """

@overload
def bounds(l: float, x: _sleipnir.autodiff.Variable, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableMatrix, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableMatrix, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableBlock, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableBlock, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: float, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.Variable, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.Variable, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableMatrix, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableMatrix, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableBlock, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableBlock, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: int, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.Variable, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.Variable, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableMatrix, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableMatrix, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableBlock, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableBlock, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.Variable, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.Variable, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.Variable, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableMatrix, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableMatrix, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableBlock, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableBlock, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableMatrix, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.Variable, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.Variable, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.Variable, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableMatrix, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableMatrix, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableMatrix, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableBlock, u: float) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableBlock, u: int) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.Variable) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableMatrix) -> InequalityConstraints: ...

@overload
def bounds(l: _sleipnir.autodiff.VariableBlock, x: _sleipnir.autodiff.VariableBlock, u: _sleipnir.autodiff.VariableBlock) -> InequalityConstraints: ...

class ExitStatus(enum.Enum):
    """Solver exit status. Negative values indicate failure."""

    SUCCESS = 0
    """Solved the problem to the desired tolerance."""

    CALLBACK_REQUESTED_STOP = 1
    """
    The solver returned its solution so far after the user requested a
    stop.
    """

    TOO_FEW_DOFS = -1
    """The solver determined the problem to be overconstrained and gave up."""

    LOCALLY_INFEASIBLE = -2
    """
    The solver determined the problem to be locally infeasible and gave
    up.
    """

    GLOBALLY_INFEASIBLE = -3
    """
    The problem setup frontend determined the problem to have an empty
    feasible region.
    """

    FACTORIZATION_FAILED = -4
    """The linear system factorization failed."""

    LINE_SEARCH_FAILED = -5
    """
    The backtracking line search failed, and the problem isn't locally
    infeasible.
    """

    NONFINITE_INITIAL_COST_OR_CONSTRAINTS = -6
    """
    The solver encountered nonfinite initial cost or constraints and gave
    up.
    """

    DIVERGING_ITERATES = -7
    """
    The solver encountered diverging primal iterates xₖ and/or sₖ and gave
    up.
    """

    MAX_ITERATIONS_EXCEEDED = -8
    """
    The solver returned its solution so far after exceeding the maximum
    number of iterations.
    """

    TIMEOUT = -9
    """
    The solver returned its solution so far after exceeding the maximum
    elapsed wall clock time.
    """

class IterationInfo:
    """
    Solver iteration information exposed to an iteration callback.

    Template parameter ``Scalar``:
        Scalar type.
    """

    @property
    def iteration(self) -> int:
        """The solver iteration."""

    @property
    def x(self) -> Annotated[NDArray[numpy.float64], dict(shape=(None,), order='C')]:
        """The decision variables."""

    @property
    def g(self) -> scipy.sparse.csc_matrix[float]:
        """The gradient of the cost function."""

    @property
    def H(self) -> scipy.sparse.csc_matrix[float]:
        """The Hessian of the Lagrangian."""

    @property
    def A_e(self) -> scipy.sparse.csc_matrix[float]:
        """The equality constraint Jacobian."""

    @property
    def A_i(self) -> scipy.sparse.csc_matrix[float]:
        """The inequality constraint Jacobian."""

class Problem:
    """
    This class allows the user to pose a constrained nonlinear
    optimization problem in natural mathematical notation and solve it.

    This class supports problems of the form:

    ```
    minₓ f(x)
    subject to cₑ(x) = 0
               cᵢ(x) ≥ 0
    ```

    where f(x) is the scalar cost function, x is the vector of decision
    variables (variables the solver can tweak to minimize the cost
    function), cᵢ(x) are the inequality constraints, and cₑ(x) are the
    equality constraints. Constraints are equations or inequalities of the
    decision variables that constrain what values the solver is allowed to
    use when searching for an optimal solution.

    The nice thing about this class is users don't have to put their
    system in the form shown above manually; they can write it in natural
    mathematical form and it'll be converted for them.

    Template parameter ``Scalar``:
        Scalar type.
    """

    def __init__(self) -> None:
        """Construct the optimization problem."""

    @overload
    def decision_variable(self) -> _sleipnir.autodiff.Variable:
        """
        Create a decision variable in the optimization problem.

        Returns:
            A decision variable in the optimization problem.
        """

    @overload
    def decision_variable(self, rows: int, cols: int = 1) -> _sleipnir.autodiff.VariableMatrix:
        """
        Create a matrix of decision variables in the optimization problem.

        Parameter ``rows``:
            Number of matrix rows.

        Parameter ``cols``:
            Number of matrix columns.

        Returns:
            A matrix of decision variables in the optimization problem.
        """

    def symmetric_decision_variable(self, rows: int) -> _sleipnir.autodiff.VariableMatrix:
        """
        Create a symmetric matrix of decision variables in the optimization
        problem.

        Variable instances are reused across the diagonal, which helps reduce
        problem dimensionality.

        Parameter ``rows``:
            Number of matrix rows.

        Returns:
            A symmetric matrix of decision varaibles in the optimization
            problem.
        """

    @overload
    def minimize(self, cost: _sleipnir.autodiff.Variable) -> None:
        """
        Tells the solver to minimize the output of the given cost function.

        Note that this is optional. If only constraints are specified, the
        solver will find the closest solution to the initial conditions that's
        in the feasible set.

        Parameter ``cost``:
            The cost function to minimize.
        """

    @overload
    def minimize(self, cost: _sleipnir.autodiff.VariableMatrix) -> None: ...

    @overload
    def minimize(self, cost: float) -> None: ...

    @overload
    def maximize(self, objective: _sleipnir.autodiff.Variable) -> None:
        """
        Tells the solver to maximize the output of the given objective
        function.

        Note that this is optional. If only constraints are specified, the
        solver will find the closest solution to the initial conditions that's
        in the feasible set.

        Parameter ``objective``:
            The objective function to maximize.
        """

    @overload
    def maximize(self, objective: _sleipnir.autodiff.VariableMatrix) -> None: ...

    @overload
    def maximize(self, objective: float) -> None: ...

    @overload
    def subject_to(self, constraint: EqualityConstraints) -> None:
        """
        Tells the solver to solve the problem while satisfying the given
        equality constraint.

        Parameter ``constraint``:
            The constraint to satisfy.
        """

    @overload
    def subject_to(self, constraint: InequalityConstraints) -> None:
        """
        Tells the solver to solve the problem while satisfying the given
        inequality constraint.

        Parameter ``constraint``:
            The constraint to satisfy.
        """

    def cost_function_type(self) -> _sleipnir.autodiff.ExpressionType:
        """
        Returns the cost function's type.

        Returns:
            The cost function's type.
        """

    def equality_constraint_type(self) -> _sleipnir.autodiff.ExpressionType:
        """
        Returns the type of the highest order equality constraint.

        Returns:
            The type of the highest order equality constraint.
        """

    def inequality_constraint_type(self) -> _sleipnir.autodiff.ExpressionType:
        """
        Returns the type of the highest order inequality constraint.

        Returns:
            The type of the highest order inequality constraint.
        """

    def solve(self, **kwargs) -> ExitStatus:
        """
        Solve the optimization problem. The solution will be stored in the
        original variables used to construct the problem.

        Parameter ``tolerance``:
            The solver will stop once the error is below this tolerance.
            (default: 1e-8)

        Parameter ``max_iterations``:
            The maximum number of solver iterations before returning a solution.
            (default: 5000)

        Parameter ``timeout``:
            The maximum elapsed wall clock time before returning a solution.
            (default: infinity)

        Parameter ``feasible_ipm``:
            Enables the feasible interior-point method. When the inequality
            constraints are all feasible, step sizes are reduced when necessary to
            prevent them becoming infeasible again. This is useful when parts of the
            problem are ill-conditioned in infeasible regions (e.g., square root of a
            negative value). This can slow or prevent progress toward a solution
            though, so only enable it if necessary.
            (default: False)

        Parameter ``diagnostics``:
            Enables diagnostic prints.

            <table>
              <tr>
                <th>Heading</th>
                <th>Description</th>
              </tr>
              <tr>
                <td>iter</td>
                <td>Iteration number</td>
              </tr>
              <tr>
                <td>type</td>
                <td>Iteration type (normal, accepted second-order correction, rejected second-order correction)</td>
              </tr>
              <tr>
                <td>time (ms)</td>
                <td>Duration of iteration in milliseconds</td>
              </tr>
              <tr>
                <td>error</td>
                <td>Error estimate</td>
              </tr>
              <tr>
                <td>cost</td>
                <td>Cost function value at current iterate</td>
              </tr>
              <tr>
                <td>infeas.</td>
                <td>Constraint infeasibility at current iterate</td>
              </tr>
              <tr>
                <td>complement.</td>
                <td>Complementary slackness at current iterate (sᵀz)</td>
              </tr>
              <tr>
                <td>μ</td>
                <td>Barrier parameter</td>
              </tr>
              <tr>
                <td>reg</td>
                <td>Iteration matrix regularization</td>
              </tr>
              <tr>
                <td>primal α</td>
                <td>Primal step size</td>
              </tr>
              <tr>
                <td>dual α</td>
                <td>Dual step size</td>
              </tr>
              <tr>
                <td>↩</td>
                <td>Number of line search backtracks</td>
              </tr>
            </table>
            (default: False)

        Parameter ``spy``:
            Enables writing sparsity patterns of H, Aₑ, and Aᵢ to files named H.spy,
            A_e.spy, and A_i.spy respectively during solve. Use tools/spy.py to plot them.
            (default: False)
        """

    def add_callback(self, callback: Callable[[IterationInfo], bool]) -> None:
        """
        Adds a callback to be called at the beginning of each solver
        iteration.

        The callback for this overload should return bool.

        Parameter ``callback``:
            The callback. Returning true from the callback causes the solver
            to exit early with the solution it has so far.
        """

    def clear_callbacks(self) -> None:
        """Clears the registered callbacks."""

class DynamicsType(enum.Enum):
    """Enum describing a type of system dynamics constraints."""

    EXPLICIT_ODE = 0
    """The dynamics are a function in the form dx/dt = f(t, x, u)."""

    DISCRETE = 1
    """The dynamics are a function in the form xₖ₊₁ = f(t, xₖ, uₖ)."""

class TimestepMethod(enum.Enum):
    """Enum describing the type of system timestep."""

    FIXED = 0
    """The timestep is a fixed constant."""

    VARIABLE = 1
    """The timesteps are allowed to vary as independent decision variables."""

    VARIABLE_SINGLE = 2
    """
    The timesteps are equal length but allowed to vary as a single
    decision variable.
    """

class TranscriptionMethod(enum.Enum):
    """Enum describing an OCP transcription method."""

    DIRECT_TRANSCRIPTION = 0
    """
    Each state is a decision variable constrained to the integrated
    dynamics of the previous state.
    """

    DIRECT_COLLOCATION = 1
    """
    The trajectory is modeled as a series of cubic polynomials where the
    centerpoint slope is constrained.
    """

    SINGLE_SHOOTING = 2
    """
    States depend explicitly as a function of all previous states and all
    previous inputs.
    """

class OCP(Problem):
    """
    This class allows the user to pose and solve a constrained optimal
    control problem (OCP) in a variety of ways.

    The system is transcripted by one of three methods (direct
    transcription, direct collocation, or single-shooting) and additional
    constraints can be added.

    In direct transcription, each state is a decision variable constrained
    to the integrated dynamics of the previous state. In direct
    collocation, the trajectory is modeled as a series of cubic
    polynomials where the centerpoint slope is constrained. In single-
    shooting, states depend explicitly as a function of all previous
    states and all previous inputs.

    Explicit ODEs are integrated using RK4.

    For explicit ODEs, the function must be in the form dx/dt = f(t, x,
    u). For discrete state transition functions, the function must be in
    the form xₖ₊₁ = f(t, xₖ, uₖ).

    Direct collocation requires an explicit ODE. Direct transcription and
    single-shooting can use either an ODE or state transition function.

    https://underactuated.mit.edu/trajopt.html goes into more detail on
    each transcription method.

    Template parameter ``Scalar``:
        Scalar type.
    """

    def __init__(self, num_states: int, num_inputs: int, dt: datetime.timedelta | float, num_steps: int, dynamics: Callable[[_sleipnir.autodiff.VariableMatrix, _sleipnir.autodiff.VariableMatrix], _sleipnir.autodiff.VariableMatrix], dynamics_type: DynamicsType = DynamicsType.EXPLICIT_ODE, timestep_method: TimestepMethod = TimestepMethod.FIXED, transcription_method: TranscriptionMethod = TranscriptionMethod.DIRECT_TRANSCRIPTION) -> None:
        """
        Build an optimization problem using a system evolution function
        (explicit ODE or discrete state transition function).

        Parameter ``num_states``:
            The number of system states.

        Parameter ``num_inputs``:
            The number of system inputs.

        Parameter ``dt``:
            The timestep for fixed-step integration.

        Parameter ``num_steps``:
            The number of control points.

        Parameter ``dynamics``:
            Function representing an explicit or implicit ODE, or a discrete
            state transition function.

        * Explicit: dx/dt = f(x, u, *)

        * Implicit: f([x dx/dt]', u, *) = 0

        * State transition: xₖ₊₁ = f(xₖ, uₖ)

        Parameter ``dynamics_type``:
            The type of system evolution function.

        Parameter ``timestep_method``:
            The timestep method.

        Parameter ``transcription_method``:
            The transcription method.
        """

    @overload
    def constrain_initial_state(self, initial_state: float) -> None:
        """
        Utility function to constrain the initial state.

        Parameter ``initial_state``:
            the initial state to constrain to.
        """

    @overload
    def constrain_initial_state(self, initial_state: int) -> None: ...

    @overload
    def constrain_initial_state(self, initial_state: _sleipnir.autodiff.Variable) -> None: ...

    @overload
    def constrain_initial_state(self, initial_state: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None: ...

    @overload
    def constrain_initial_state(self, initial_state: _sleipnir.autodiff.VariableMatrix) -> None: ...

    @overload
    def constrain_final_state(self, final_state: float) -> None:
        """
        Utility function to constrain the final state.

        Parameter ``final_state``:
            the final state to constrain to.
        """

    @overload
    def constrain_final_state(self, final_state: int) -> None: ...

    @overload
    def constrain_final_state(self, final_state: _sleipnir.autodiff.Variable) -> None: ...

    @overload
    def constrain_final_state(self, final_state: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None: ...

    @overload
    def constrain_final_state(self, final_state: _sleipnir.autodiff.VariableMatrix) -> None: ...

    def for_each_step(self, callback: Callable[[_sleipnir.autodiff.VariableMatrix, _sleipnir.autodiff.VariableMatrix], None]) -> None:
        """
        Set the constraint evaluation function. This function is called
        `num_steps+1` times, with the corresponding state and input
        VariableMatrices.

        Parameter ``callback``:
            The callback f(x, u) where x is the state and u is the input
            vector.
        """

    @overload
    def set_lower_input_bound(self, lower_bound: float) -> None:
        """
        Convenience function to set a lower bound on the input.

        Parameter ``lower_bound``:
            The lower bound that inputs must always be above. Must be shaped
            (num_inputs)x1.
        """

    @overload
    def set_lower_input_bound(self, lower_bound: int) -> None: ...

    @overload
    def set_lower_input_bound(self, lower_bound: _sleipnir.autodiff.Variable) -> None: ...

    @overload
    def set_lower_input_bound(self, lower_bound: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None: ...

    @overload
    def set_lower_input_bound(self, lower_bound: _sleipnir.autodiff.VariableMatrix) -> None: ...

    @overload
    def set_upper_input_bound(self, upper_bound: float) -> None:
        """
        Convenience function to set an upper bound on the input.

        Parameter ``upper_bound``:
            The upper bound that inputs must always be below. Must be shaped
            (num_inputs)x1.
        """

    @overload
    def set_upper_input_bound(self, upper_bound: int) -> None: ...

    @overload
    def set_upper_input_bound(self, upper_bound: _sleipnir.autodiff.Variable) -> None: ...

    @overload
    def set_upper_input_bound(self, upper_bound: Annotated[NDArray[numpy.float64], dict(shape=(None, None))]) -> None: ...

    @overload
    def set_upper_input_bound(self, upper_bound: _sleipnir.autodiff.VariableMatrix) -> None: ...

    def set_min_timestep(self, min_timestep: datetime.timedelta | float) -> None:
        """
        Convenience function to set a lower bound on the timestep.

        Parameter ``min_timestep``:
            The minimum timestep.
        """

    def set_max_timestep(self, max_timestep: datetime.timedelta | float) -> None:
        """
        Convenience function to set an upper bound on the timestep.

        Parameter ``max_timestep``:
            The maximum timestep.
        """

    def X(self) -> _sleipnir.autodiff.VariableMatrix:
        """
        Get the state variables. After the problem is solved, this will
        contain the optimized trajectory.

        Shaped (num_states)x(num_steps+1).

        Returns:
            The state variable matrix.
        """

    def U(self) -> _sleipnir.autodiff.VariableMatrix:
        """
        Get the input variables. After the problem is solved, this will
        contain the inputs corresponding to the optimized trajectory.

        Shaped (num_inputs)x(num_steps+1), although the last input step is
        unused in the trajectory.

        Returns:
            The input variable matrix.
        """

    def dt(self) -> _sleipnir.autodiff.VariableMatrix:
        """
        Get the timestep variables. After the problem is solved, this will
        contain the timesteps corresponding to the optimized trajectory.

        Shaped 1x(num_steps+1), although the last timestep is unused in the
        trajectory.

        Returns:
            The timestep variable matrix.
        """

    def initial_state(self) -> _sleipnir.autodiff.VariableMatrix:
        """
        Convenience function to get the initial state in the trajectory.

        Returns:
            The initial state of the trajectory.
        """

    def final_state(self) -> _sleipnir.autodiff.VariableMatrix:
        """
        Convenience function to get the final state in the trajectory.

        Returns:
            The final state of the trajectory.
        """
