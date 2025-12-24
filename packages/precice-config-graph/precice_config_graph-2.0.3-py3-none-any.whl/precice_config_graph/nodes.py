"""
This graph is intended for the preCICE logical-checker https://github.com/precice-forschungsprojekt/config-checker.

You can find documentation under README.md, docs/Nodes.md and docs/Edges.md.

This graph was developed by Simon Wazynski, Alexander Hutter and Orlando Ackermann as part of https://github.com/precice-forschungsprojekt.
"""

from __future__ import annotations

from . import enums as e


class ParticipantNode:
    def __init__(
            self,
            name: str,
            write_data: list[WriteDataNode] = None,
            read_data: list[ReadDataNode] = None,
            receive_meshes: list[ReceiveMeshNode] = None,
            provide_meshes: list[MeshNode] = None,
            mappings: list[MappingNode] = None,
            exports: list[ExportNode] = None,
            actions: list[ActionNode] = None,
            watchpoints: list[WatchPointNode] = None,
            watch_integrals: list[WatchIntegralNode] = None,
            line: int = None,
    ):
        self.name = name

        if write_data is None:
            self.write_data = []
        else:
            self.write_data = write_data

        if read_data is None:
            self.read_data = []
        else:
            self.read_data = read_data

        if receive_meshes is None:
            self.receive_meshes = []
        else:
            self.receive_meshes = receive_meshes

        if provide_meshes is None:
            self.provide_meshes = []
        else:
            self.provide_meshes = provide_meshes

        if mappings is None:
            self.mappings = []
        else:
            self.mappings = mappings

        if exports is None:
            self.exports = []
        else:
            self.exports = exports

        if actions is None:
            self.actions = []
        else:
            self.actions = actions

        if watchpoints is None:
            self.watchpoints = []
        else:
            self.watchpoints = watchpoints

        if watch_integrals is None:
            self.watch_integrals = []
        else:
            self.watch_integrals = watch_integrals

        self.line = line

    def to_xml(self):
        xml_str: str = f"<participant name=\"{self.name}\">\n"
        for provide_mesh in self.provide_meshes:
            xml_str += f"  <provide-mesh name=\"{provide_mesh.name}\" />\n"
        for receive_mesh in self.receive_meshes:
            xml_str += f"  {receive_mesh.to_xml()}\n"
        for write_data in self.write_data:
            xml_str += f"  {write_data.to_xml()}\n"
        for read_data in self.read_data:
            xml_str += f"  {read_data.to_xml()}\n"
        for mapping in self.mappings:
            xml_str += f"  {mapping.to_xml()}\n"

        for action in self.actions:
            xml_str += f"  {action.to_xml()}\n"
        for export in self.exports:
            xml_str += f"  {export.to_xml()}\n"
        for watchpoint in self.watchpoints:
            xml_str += f"  {watchpoint.to_xml()}\n"
        for watch_integral in self.watch_integrals:
            xml_str += f"  {watch_integral.to_xml()}\n"

        xml_str += f"</participant>\n"
        return xml_str


class MeshNode:
    def __init__(self, name: str, use_data: list[DataNode] = None, line: int = None, dimensions: int = 3):
        self.name = name

        if use_data is None:
            self.use_data = []
        else:
            self.use_data = use_data
        self.dimensions = dimensions
        self.line = line

    def to_xml(self):
        xml_str: str = f"<mesh name=\"{self.name}\" dimensions=\"{self.dimensions}\">\n"
        for data in self.use_data:
            xml_str += f"  <use-data name=\"{data.name}\" />\n"
        xml_str += f"</mesh>\n"
        return xml_str


class ReceiveMeshNode:
    def __init__(
            self,
            participant: ParticipantNode,
            mesh: MeshNode,
            from_participant: ParticipantNode,
            api_access: bool,
            line: int = None,
    ):
        self.participant = participant
        self.mesh = mesh
        self.from_participant = from_participant
        self.api_access = api_access
        self.line = line

    def to_xml(self):
        api_access_str: str = "api-access=\"true\" " if self.api_access else ""
        xml_str: str = f"<receive-mesh name=\"{self.mesh.name}\" from=\"{self.from_participant.name}\" {api_access_str}/>"
        return xml_str


class CouplingSchemeNode:
    def __init__(
            self,
            type: e.CouplingSchemeType,
            first_participant: ParticipantNode,
            second_participant: ParticipantNode,
            exchanges: list[ExchangeNode] = None,
            acceleration: AccelerationNode = None,
            convergence_measures: list[ConvergenceMeasureNode] = None,
            line: int = None,
            max_time_windows: int = 10,
            time_window_size: float = 1e-1,
    ):
        self.type = type
        self.first_participant = first_participant
        self.second_participant = second_participant

        if exchanges is None:
            self.exchanges = []
        else:
            self.exchanges = exchanges

        self.acceleration = acceleration

        if convergence_measures is None:
            self.convergence_measures = []
        else:
            self.convergence_measures = convergence_measures

        self.line = line
        self.max_time_windows = max_time_windows
        self.time_window_size = time_window_size

    def to_xml(self):
        xml_str: str = f"<coupling-scheme:{self.type.value}>\n"
        xml_str += f"  <participants first=\"{self.first_participant.name}\" second=\"{self.second_participant.name}\" />\n"
        xml_str += f"  <max-time-windows value=\"{self.max_time_windows}\" />\n"
        xml_str += f"  <time-window-size value=\"{self.time_window_size}\" />\n"
        for exchange in self.exchanges:
            xml_str += f"  {exchange.to_xml()}\n"
        if self.acceleration is not None:
            xml_str += f"  {self.acceleration.to_xml()}\n"
        for convergence in self.convergence_measures:
            xml_str += f"  {convergence.to_xml()}\n"
        xml_str += f"</coupling-scheme:{self.type.value}>\n"
        return xml_str


class MultiCouplingSchemeNode:
    def __init__(
            self,
            control_participant: ParticipantNode,
            participants: list[ParticipantNode] = None,
            exchanges: list[ExchangeNode] = None,
            acceleration: AccelerationNode = None,
            convergence_measures: list[ConvergenceMeasureNode] = None,
            max_time_windows: int = 10,
            time_window_size: float = 1e-1,
            line: int = None,
    ):
        self.control_participant = control_participant

        if participants is None:
            self.participants = []
        else:
            self.participants = participants

        if exchanges is None:
            self.exchanges = []
        else:
            self.exchanges = exchanges

        self.acceleration = acceleration

        if convergence_measures is None:
            self.convergence_measures = []
        else:
            self.convergence_measures = convergence_measures

        self.max_time_windows = max_time_windows
        self.time_window_size = time_window_size
        self.line = line

    def to_xml(self):
        xml_str: str = f"<coupling-scheme:multi>\n"
        xml_str += f"  <max-time-windows value=\"{self.max_time_windows}\" />\n"
        xml_str += f"  <time-window-size value=\"{self.time_window_size}\" />\n"
        for participant in self.participants:
            if participant == self.control_participant:
                xml_str += f"  <participant name=\"{participant.name}\" control=\"yes\" />\n"
            else:
                xml_str += f"  <participant name=\"{participant.name}\" />\n"
        for exchange in self.exchanges:
            xml_str += f"  {exchange.to_xml()}\n"
        if self.acceleration is not None:
            xml_str += f"  {self.acceleration.to_xml()}\n"
        for convergence in self.convergence_measures:
            xml_str += f"  {convergence.to_xml()}\n"

        xml_str += f"</coupling-scheme:multi>\n"
        return xml_str


class DataNode:
    def __init__(self, name: str, data_type: e.DataType, line: int = None):
        self.name = name
        self.data_type = data_type
        self.line = line

    def to_xml(self) -> str:
        return f"<data:{self.data_type.value} name=\"{self.name}\" />"


class MappingNode:
    def __init__(
            self,
            parent_participant: ParticipantNode,
            direction: e.Direction,
            just_in_time: bool,
            method: e.MappingMethod,
            constraint: e.MappingConstraint,
            from_mesh: MeshNode | None = None,
            to_mesh: MeshNode | None = None,
            polynomial: e.MappingPolynomialType = e.MappingPolynomialType.SEPARATE,
            x_dead: bool = False,
            y_dead: bool = False,
            z_dead: bool = False,
            solver_rtol: float = 1e-9,
            vertices_per_cluster: int = 50,
            relative_overlap: float = 0.15,
            project_to_input: bool = True,
            multiscale_type: e.MappingMultiscaleType = e.MappingMultiscaleType.COLLECT,
            multiscale_axis: e.MappingMultiscaleAxis = e.MappingMultiscaleAxis.X,
            multiscale_radius: float = 1,
            basisfunction: MappingBasisFunctionNode = None,
            executor: MappingExecutorNode = None,
            line: int = None,
    ):
        self.parent_participant = parent_participant
        self.direction = direction
        self.just_in_time = just_in_time
        self.method = method
        self.constraint = constraint
        self.from_mesh = from_mesh
        self.to_mesh = to_mesh

        self.polynomial = polynomial
        self.x_dead = x_dead
        self.y_dead = y_dead
        self.z_dead = z_dead
        self.solver_rtol = solver_rtol
        self.vertices_per_cluster = vertices_per_cluster
        self.relative_overlap = relative_overlap
        self.project_to_input = project_to_input
        self.multiscale_type = multiscale_type
        self.multiscale_axis = multiscale_axis
        self.multiscale_radius = multiscale_radius
        if basisfunction is None:
            self.basisfunction = MappingBasisFunctionNode(mapping=self,
                                                          type=e.MappingBasisFunctionType.COMPACT_POLYNOMIAL_C0)
        else:
            self.basisfunction = basisfunction
        if executor is None:
            self.executor = MappingExecutorNode(mapping=self, type=e.MappingExecutorType.CPU)
        else:
            self.executor = executor

        self.line = line

    def to_xml(self) -> str:
        # General tags
        xml_str: str = f"<mapping:{self.method.value}\n"
        xml_str += f"  direction=\"{self.direction.value}\"\n"
        # For a just-in-time mapping, either "from" or "to" is not specified
        xml_str += f"  from=\"{self.from_mesh.name}\"\n" if self.from_mesh else ""
        xml_str += f"  to=\"{self.to_mesh.name}\"\n" if self.to_mesh else ""
        xml_str += f"  constraint=\"{self.constraint.value}\"\n"
        # Specialized tags
        if self.method in [e.MappingMethod.RBF, e.MappingMethod.RBF_GLOBAL_DIRECT,
                           e.MappingMethod.RBF_GLOBAL_ITERATIVE]:
            xml_str += f"  x-dead=\"{self.x_dead}\"\n"
            xml_str += f"  y-dead=\"{self.y_dead}\"\n"
            xml_str += f"  z-dead=\"{self.z_dead}\"\n"
        if self.method in [e.MappingMethod.RBF_GLOBAL_DIRECT, e.MappingMethod.RBF_GLOBAL_ITERATIVE,
                           e.MappingMethod.RBF_PUM_DIRECT]:
            xml_str += f"  polynomial=\"{self.polynomial.value}\"\n"
        if self.method == e.MappingMethod.RBF_PUM_DIRECT:
            xml_str += f"  vertices-per-cluster=\"{self.vertices_per_cluster}\"\n"
            xml_str += f"  relative-overlap=\"{self.relative_overlap}\"\n"
            xml_str += f"  project-to-input=\"{self.project_to_input}\"\n"
        if self.method in [e.MappingMethod.AXIAL_GEOMETRIC_MULTISCALE, e.MappingMethod.RADIAL_GEOMETRIC_MULTISCALE]:
            xml_str += f"  multiscale-type=\"{self.multiscale_type.value}\"\n"
            xml_str += f"  multiscale-axis=\"{self.multiscale_axis.value}\"\n"
            xml_str += f"  multiscale-radius=\"{self.multiscale_radius}\"\n"
        # Specialized subelements
        if self.method in [e.MappingMethod.RBF_GLOBAL_ITERATIVE, e.MappingMethod.RBF_GLOBAL_DIRECT,
                           e.MappingMethod.RBF_PUM_DIRECT, e.MappingMethod.RBF]:
            xml_str += f"/>\n"  # close opening element brace
            xml_str += f"  {self.executor.to_xml()}\n"
            xml_str += f"  {self.basisfunction.to_xml()}\n"
            xml_str += f"<mapping:{self.method.value}/>"
        else:
            xml_str += f"/>"
        return xml_str


class WriteDataNode:
    def __init__(
            self,
            participant: ParticipantNode,
            data: DataNode,
            mesh: MeshNode,
            line: int = None,
    ):
        self.participant = participant
        self.data = data
        self.mesh = mesh
        self.line = line

    def to_xml(self) -> str:
        xml_str: str = f"<write-data name=\"{self.data.name}\" mesh=\"{self.mesh.name}\" />"
        return xml_str


class ReadDataNode:
    def __init__(
            self,
            participant: ParticipantNode,
            data: DataNode,
            mesh: MeshNode,
            line: int = None,
    ):
        self.participant = participant
        self.data = data
        self.mesh = mesh
        self.line = line

    def to_xml(self) -> str:
        xml_str: str = f"<read-data name=\"{self.data.name}\" mesh=\"{self.mesh.name}\" />"
        return xml_str


class ExchangeNode:
    def __init__(
            self,
            coupling_scheme: CouplingSchemeNode | MultiCouplingSchemeNode,
            data: DataNode,
            mesh: MeshNode,
            from_participant: ParticipantNode,
            to_participant: ParticipantNode,
            line: int = None,
    ):
        self.coupling_scheme = coupling_scheme
        self.data = data
        self.mesh = mesh
        self.from_participant = from_participant
        self.to_participant = to_participant
        self.line = line

    def to_xml(self) -> str:
        xml_str: str = (f"  <exchange data=\"{self.data.name}\" mesh=\"{self.mesh.name}\" "
                        f"from=\"{self.from_participant.name}\" to=\"{self.to_participant.name}\" />")
        return xml_str


class ExportNode:
    def __init__(
            self, participant: ParticipantNode, format: e.ExportFormat, line: int = None, directory: str = "."
    ):
        self.participant = participant
        self.format = format
        self.line = line
        self.directory = directory

    def to_xml(self) -> str:
        xml_str: str = f"<export:{self.format.value} directory=\"{self.directory}\" />"
        return xml_str


class ActionNode:
    def __init__(
            self,
            participant: ParticipantNode,
            type: e.ActionType,
            mesh: MeshNode,
            timing: e.TimingType,
            target_data: DataNode | None = None,
            source_data: list[DataNode] = None,
            python_module_name: str = "",
            line: int = None,
    ):
        self.participant = participant
        self.type = type
        self.mesh = mesh
        self.timing = timing
        self.target_data = target_data

        if source_data is None:
            self.source_data = []
        else:
            self.source_data = source_data

        self.python_module_name = python_module_name

        self.line = line

    def to_xml(self) -> str:
        xml_str: str = f"<action:{self.type.value} mesh=\"{self.mesh.name}\" timing={self.timing.value}>\n"
        if self.type != e.ActionType.RECORDER and self.target_data is not None:
            xml_str += f"  <target-data name=\"{self.target_data.name}\" />\n"
        if self.type == e.ActionType.PYTHON:
            xml_str += f"  <module name=\"{self.python_module_name}\" />\n"
        for source_data in self.source_data:
            xml_str += f"  <source-data name=\"{source_data.name}\" />\n"
        xml_str += f"</action:{self.type.value}>\n"
        return xml_str


class WatchPointNode:
    def __init__(
            self, name: str, participant: ParticipantNode, mesh: MeshNode, line: int = None,
            coordinate: list[float] = None
    ):
        self.name = name
        self.participant = participant
        self.mesh = mesh
        if coordinate is None:
            self.coordinate = [0] * self.mesh.dimensions  # create a 2-d or 3-d coordinate
        elif len(coordinate) != self.mesh.dimensions:
            self.coordinate = [0] * self.mesh.dimensions  # create a 2-d or 3-d coordinate
        else:
            self.coordinate = coordinate
        self.line = line

    def to_xml(self) -> str:
        coordinate = ";".join(map(str, self.coordinate))  # Coordinate of the form 0;1;2 ...
        xml_str: str = f"<watch-point name=\"{self.name}\" mesh=\"{self.mesh.name}\" coordinate=\"{coordinate}\" />"
        return xml_str


class WatchIntegralNode:
    def __init__(
            self, name: str, participant: ParticipantNode, mesh: MeshNode, scale_with_connectivity: bool = False,
            line: int = None
    ):
        self.name = name
        self.participant = participant
        self.mesh = mesh
        self.scale_with_connectivity = scale_with_connectivity
        self.line = line

    def to_xml(self) -> str:
        xml_str: str = f"<watch-integral name=\"{self.name}\" mesh=\"{self.mesh.name}\" scale-with-connectivity=\"{self.scale_with_connectivity}\" />"
        return xml_str


class M2NNode:
    def __init__(
            self,
            type: e.M2NType,
            acceptor: ParticipantNode,
            connector: ParticipantNode,
            directory: str = ".",
            line: int = None,
    ):
        self.type = type
        self.acceptor = acceptor
        self.connector = connector
        self.directory = directory
        self.line = line

    def to_xml(self) -> str:
        return f"<m2n:{self.type.value} acceptor=\"{self.acceptor.name}\" connector=\"{self.connector.name}\" directory=\"{self.directory}\"/>\n"


class AccelerationDataNode:
    def __init__(
            self,
            acceleration: AccelerationNode,
            data: DataNode,
            mesh: MeshNode,
            line: int = None,
    ):
        self.acceleration = acceleration
        self.data = data
        self.mesh = mesh
        self.line = line

    def to_xml(self) -> str:
        xml_str: str = f"<data name=\"{self.data.name}\" mesh=\"{self.mesh.name}\" />"
        return xml_str


class AccelerationNode:
    def __init__(
            self,
            coupling_scheme: CouplingSchemeNode | MultiCouplingSchemeNode,
            type: e.AccelerationType,
            data: list[AccelerationDataNode] = None,
            preconditioner: PreconditionerNode = None,
            filter: AccelerationFilterNode = None,
            line: int = None,
    ):
        self.coupling_scheme = coupling_scheme
        self.type = type

        if data is None:
            self.data = []
        else:
            self.data = data

        self.preconditioner = preconditioner
        self.filter = filter

        self.line = line

    def to_xml(self) -> str:
        xml_str: str = f"<acceleration:{self.type.value}>\n"
        if self.type == e.AccelerationType.CONSTANT:
            xml_str += f"  <relaxation value=\"1\" />\n"
        for accelerated_data in self.data:
            xml_str += f"  {accelerated_data.to_xml()}\n"
        if self.preconditioner is not None:
            xml_str += f"  {self.preconditioner.to_xml()}\n"
        if self.filter is not None:
            xml_str += f"  {self.filter.to_xml()}"
        xml_str += f"</acceleration:{self.type.value}>"
        return xml_str


class ConvergenceMeasureNode:
    def __init__(
            self,
            coupling_scheme: CouplingSchemeNode | MultiCouplingSchemeNode,
            type: e.ConvergenceMeasureType,
            data: DataNode,
            mesh: MeshNode,
            line: int = None,
            limit: float = 0.1,  # functions as absolute and residual limit (they cannot appear together)
            rel_limit: float = 0.1,
    ):
        self.type = type
        self.coupling_scheme = coupling_scheme
        self.data = data
        self.mesh = mesh
        self.line = line
        self.limit = limit
        self.rel_limit = rel_limit

    def to_xml(self) -> str:
        limit_str: str = ""
        if self.type == e.ConvergenceMeasureType.ABSOLUTE:
            limit_str = f"limit=\"{self.limit}\" "
        elif self.type == e.ConvergenceMeasureType.RELATIVE:
            limit_str = f"limit=\"{self.rel_limit}\" "
        elif self.type == e.ConvergenceMeasureType.ABSOLUTE_OR_RELATIVE:
            limit_str = f"abs-limit=\"{self.limit}\" rel-limit=\"{self.rel_limit}\" "
        elif self.type == e.ConvergenceMeasureType.RESIDUAL_RELATIVE:
            limit_str = f"limit=\"{self.limit}\" "
        xml_str: str = f"<{self.type.value}-convergence-measure data=\"{self.data.name}\" mesh=\"{self.mesh.name}\" {limit_str}/>"
        return xml_str


class PreconditionerNode:
    def __init__(
            self,
            type: e.PreconditionerType,
            acceleration: AccelerationNode,
            freeze_after: int = -1,
            update_on_threshold: bool = True
    ):
        self.type = type
        self.acceleration = acceleration
        self.freeze_after = freeze_after
        self.update_on_threshold = update_on_threshold

    def to_xml(self) -> str:
        threshold_str: str = ""
        if self.acceleration.type != e.AccelerationType.AITKEN:
            threshold_str = f"update-on-threshold=\"{self.update_on_threshold}\" "

        xml_str: str = f"<preconditioner type=\"{self.type.value}\" freeze-after=\"{self.freeze_after}\" {threshold_str}/>"
        return xml_str


class AccelerationFilterNode:
    def __init__(
            self,
            acceleration: AccelerationNode,
            type: e.AccelerationFilterType = e.AccelerationFilterType.QR3,
            limit: float = 1e-16,
    ):
        self.acceleration = acceleration
        self.type = type
        self.limit = limit

    def to_xml(self) -> str:
        xml_str: str = f"<filter type=\"{self.type.value}\" limit=\"{self.limit}\" />"
        return xml_str


class MappingBasisFunctionNode:
    def __init__(
            self,
            type: e.MappingBasisFunctionType,
            mapping: MappingNode,
            support_radius: float = 0.5,
            shape_parameter: float = 1,
    ):
        self.type = type
        self.mapping = mapping
        self.support_radius = support_radius
        self.shape_parameter = shape_parameter

    def to_xml(self) -> str:
        support_radius: str = ""
        if self.type in [e.MappingBasisFunctionType.COMPACT_POLYNOMIAL_C0,
                         e.MappingBasisFunctionType.COMPACT_POLYNOMIAL_C2,
                         e.MappingBasisFunctionType.COMPACT_POLYNOMIAL_C4,
                         e.MappingBasisFunctionType.COMPACT_POLYNOMIAL_C6,
                         e.MappingBasisFunctionType.COMPACT_POLYNOMIAL_C8,
                         e.MappingBasisFunctionType.COMPACT_TPS_C2,
                         e.MappingBasisFunctionType.GAUSSIAN,
                         ]:
            support_radius += f"support-radius=\"{self.support_radius}\" "
        shape_parameter_str: str = ""
        if self.type in [e.MappingBasisFunctionType.MULTIQUADRICS,
                         e.MappingBasisFunctionType.INVERSE_MULTIQUADRICS,
                         e.MappingBasisFunctionType.GAUSSIAN]:
            shape_parameter_str = f"shape-parameter=\"{self.shape_parameter}\" "
        xml_str: str = f"<basis-function:{self.type.value} {shape_parameter_str}{support_radius}/>"
        return xml_str


class MappingExecutorNode:
    def __init__(self, type: e.MappingExecutorType, mapping: MappingNode, gpu_device_id: int = 0, n_threads: int = 0):
        self.type = type
        self.mapping = mapping
        self.gpu_device_id = gpu_device_id
        self.n_threads = n_threads

    def to_xml(self) -> str:
        gpu_device_id_str: str = ""
        if self.type in [e.MappingExecutorType.CUDA, e.MappingExecutorType.HIP]:
            gpu_device_id_str += f"gpu-device-id=\"{self.gpu_device_id}\" "
        n_threads_str: str = ""
        if self.type == e.MappingExecutorType.OPENMP:
            n_threads_str += f"n-threads=\"{self.n_threads}\" "
        xml_str: str = f"<executor:{self.type.value} {n_threads_str}{gpu_device_id_str}/>"
        return xml_str
