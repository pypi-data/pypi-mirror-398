"""
This graph is intended for the preCICE logical-checker https://github.com/precice-forschungsprojekt/config-checker.

You can find documentation under README.md, docs/Nodes.md and docs/Edges.md.

This graph was developed by Simon Wazynski, Alexander Hutter and Orlando Ackermann as part of https://github.com/precice-forschungsprojekt.
"""

from __future__ import annotations

from enum import Enum


class MappingMethod(Enum):
    NEAREST_NEIGHBOR = "nearest-neighbor"
    NEAREST_PROJECTION = "nearest-projection"
    NEAREST_NEIGHBOR_GRADIENT = "nearest-neighbor-gradient"
    LINEAR_CELL_INTERPOLATION = "linear-cell-interpolation"
    RBF_GLOBAL_ITERATIVE = "rbf-global-iterative"
    RBF_GLOBAL_DIRECT = "rbf-global-direct"
    RBF_PUM_DIRECT = "rbf-pum-direct"
    RBF = "rbf"
    AXIAL_GEOMETRIC_MULTISCALE = "axial-geometric-multiscale"
    RADIAL_GEOMETRIC_MULTISCALE = "radial-geometric-multiscale"


class MappingConstraint(Enum):
    CONSERVATIVE = "conservative"
    CONSISTENT = "consistent"
    SCALED_CONSISTENT_SURFACE = "scaled-consistent-surface"
    SCALED_CONSISTENT_VOLUME = "scaled-consistent-volume"


class M2NType(Enum):
    SOCKETS = "sockets"
    MPI = "mpi"
    MPI_MULTIPLE_PORTS = "mpi-multiple-ports"


class Direction(Enum):
    READ = "read"
    WRITE = "write"


class DataType(Enum):
    SCALAR = "scalar"
    VECTOR = "vector"


class TimingType(Enum):
    WRITE_MAPPING_POST = "write-mapping-post"
    READ_MAPPING_POST = "read-mapping-post"


class CouplingSchemeType(Enum):
    SERIAL_EXPLICIT = "serial-explicit"
    PARALLEL_EXPLICIT = "parallel-explicit"
    SERIAL_IMPLICIT = "serial-implicit"
    PARALLEL_IMPLICIT = "parallel-implicit"
    # This enum does not include coupling-scheme:multi, since it is modeled with a different node type


class ActionType(Enum):
    MULTIPLY_BY_AREA = "multiply-by-area"
    DIVIDE_BY_AREA = "divide-by-area"
    SUMMATION = "summation"
    PYTHON = "python"
    RECORDER = "recorder"


class ExportFormat(Enum):
    VTK = "vtk"
    VTU = "vtu"
    VTP = "vtp"
    CSV = "csv"


class AccelerationType(Enum):
    AITKEN = "aitken"
    IQN_ILS = "IQN-ILS"
    IQN_IMVJ = "IQN-IMVJ"
    CONSTANT = "constant"


class ConvergenceMeasureType(Enum):
    ABSOLUTE = "absolute"
    ABSOLUTE_OR_RELATIVE = "absolute-or-relative"
    RELATIVE = "relative"
    RESIDUAL_RELATIVE = "residual-relative"


class MappingExecutorType(Enum):
    CPU = "cpu"
    CUDA = "cuda"
    OPENMP = "openmp"
    HIP = "hip"


class PreconditionerType(Enum):
    CONSTANT = "constant"
    VALUE = "value"
    RESIDUAL = "residual"
    RESIDUAL_SUM = "residual-sum"


class AccelerationFilterType(Enum):
    QR1 = "QR1"
    QR1ABSOLUTE = "QR1-absolute"
    QR2 = "QR2"
    QR3 = "QR3"


class MappingBasisFunctionType(Enum):
    COMPACT_POLYNOMIAL_C0 = "compact-polynomial-c0"
    COMPACT_POLYNOMIAL_C2 = "compact-polynomial-c2"
    COMPACT_POLYNOMIAL_C4 = "compact-polynomial-c4"
    COMPACT_POLYNOMIAL_C6 = "compact-polynomial-c6"
    COMPACT_POLYNOMIAL_C8 = "compact-polynomial-c8"
    COMPACT_TPS_C2 = "compact-tps-c2"
    MULTIQUADRICS = "multiquadrics"
    INVERSE_MULTIQUADRICS = "inverse-multiquadrics"
    GAUSSIAN = "gaussian"
    THIN_PLATE_SPLINE = "thin-plate-spline"
    VOLUME_SPLINE = "volume-spline"


class MappingMultiscaleType(Enum):
    SPREAD = "spread"
    COLLECT = "collect"


class MappingMultiscaleAxis(Enum):
    X = "x"
    Y = "y"
    Z = "z"


class MappingPolynomialType(Enum):
    SEPARATE = "separate"
    ON = "on"
    OFF = "off"
