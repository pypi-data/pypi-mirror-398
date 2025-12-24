"""
Node - Visual node representation for pipeline steps.

Each node represents a workflow action with input/output ports
and configurable parameters. Generic interface for future bioamla integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID, uuid4

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QFontMetrics,
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QStyleOptionGraphicsItem,
    QWidget,
    QGraphicsSceneMouseEvent,
)


class PortType(Enum):
    """Type of node port."""
    INPUT = auto()
    OUTPUT = auto()


@dataclass
class PortDefinition:
    """Definition of a port on a node."""
    name: str
    port_type: PortType
    data_type: str = "any"
    required: bool = True
    description: str = ""


@dataclass
class ParameterDefinition:
    """Definition of a node parameter."""
    name: str
    param_type: str  # "string", "int", "float", "bool", "choice", "file", "dir"
    label: str = ""
    default: Any = None
    description: str = ""
    choices: List[str] = field(default_factory=list)  # For "choice" type
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class NodeDefinition:
    """Definition of a node type."""
    node_type: str  # Unique identifier e.g., "audio.resample"
    name: str  # Display name
    description: str
    category: str
    color: str  # Hex color for node header
    inputs: List[PortDefinition] = field(default_factory=list)
    outputs: List[PortDefinition] = field(default_factory=list)
    parameters: List[ParameterDefinition] = field(default_factory=list)


class NodePort(QGraphicsEllipseItem):
    """Visual representation of a node port (input or output)."""

    PORT_RADIUS = 6

    def __init__(
        self,
        port_def: PortDefinition,
        parent_node: "Node",
    ):
        super().__init__(
            -self.PORT_RADIUS, -self.PORT_RADIUS,
            self.PORT_RADIUS * 2, self.PORT_RADIUS * 2,
            parent_node
        )
        self.port_def = port_def
        self.parent_node = parent_node
        self.connections: List = []  # List of Connection objects

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)

        # Appearance
        self._normal_brush = QBrush(QColor("#6c6c6c"))
        self._hover_brush = QBrush(QColor("#00d4aa"))
        self._connected_brush = QBrush(QColor("#4a9eff"))

        self.setBrush(self._normal_brush)
        self.setPen(QPen(QColor("#1e1e1e"), 2))

        tooltip = port_def.name
        if port_def.description:
            tooltip += f"\n{port_def.description}"
        self.setToolTip(tooltip)

    @property
    def port_type(self) -> PortType:
        return self.port_def.port_type

    @property
    def is_connected(self) -> bool:
        return len(self.connections) > 0

    def add_connection(self, connection):
        if connection not in self.connections:
            self.connections.append(connection)
        self._update_appearance()

    def remove_connection(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)
        self._update_appearance()

    def _update_appearance(self):
        if self.is_connected:
            self.setBrush(self._connected_brush)
        else:
            self.setBrush(self._normal_brush)

    def hoverEnterEvent(self, event):
        self.setBrush(self._hover_brush)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._update_appearance()
        super().hoverLeaveEvent(event)

    def center_scene_pos(self) -> QPointF:
        """Get the center position in scene coordinates."""
        return self.scenePos()


class Node(QGraphicsRectItem):
    """Visual representation of a pipeline node."""

    # Node dimensions
    MIN_WIDTH = 180
    HEADER_HEIGHT = 28
    PORT_SPACING = 24
    PORT_MARGIN = 12
    PADDING = 10
    CORNER_RADIUS = 8

    def __init__(
        self,
        definition: NodeDefinition,
        node_id: Optional[UUID] = None,
    ):
        super().__init__()
        self.definition = definition
        self.node_id = node_id or uuid4()
        self.parameters: Dict[str, Any] = {}

        # Initialize parameters with defaults
        for param_def in definition.parameters:
            self.parameters[param_def.name] = param_def.default

        # Create ports
        self.input_ports: List[NodePort] = []
        self.output_ports: List[NodePort] = []

        self._create_ports()
        self._calculate_size()
        self._setup_appearance()

        # Make node movable and selectable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        # Execution state
        self._is_running = False
        self._is_completed = False
        self._is_failed = False

        # Callbacks
        self.on_position_changed: Optional[Callable[["Node"], None]] = None
        self.on_double_clicked: Optional[Callable[["Node"], None]] = None

    def _create_ports(self):
        """Create input and output port widgets."""
        for port_def in self.definition.inputs:
            port = NodePort(port_def, self)
            self.input_ports.append(port)

        for port_def in self.definition.outputs:
            port = NodePort(port_def, self)
            self.output_ports.append(port)

    def _calculate_size(self):
        """Calculate node size based on ports and content."""
        num_ports = max(len(self.input_ports), len(self.output_ports), 1)
        content_height = num_ports * self.PORT_SPACING + self.PORT_MARGIN * 2
        height = self.HEADER_HEIGHT + content_height

        font = QFont("Segoe UI", 10)
        fm = QFontMetrics(font)
        name_width = fm.horizontalAdvance(self.definition.name)
        width = max(self.MIN_WIDTH, name_width + 40)

        self.setRect(0, 0, width, height)
        self._position_ports()

    def _position_ports(self):
        """Position ports along the sides of the node."""
        rect = self.rect()

        for i, port in enumerate(self.input_ports):
            y = self.HEADER_HEIGHT + self.PORT_MARGIN + i * self.PORT_SPACING
            port.setPos(0, y)

        for i, port in enumerate(self.output_ports):
            y = self.HEADER_HEIGHT + self.PORT_MARGIN + i * self.PORT_SPACING
            port.setPos(rect.width(), y)

    def _setup_appearance(self):
        """Setup node visual appearance."""
        self.setPen(QPen(QColor("#3c3c3c"), 1))
        self._update_appearance()

    def _update_appearance(self):
        """Update appearance based on state."""
        if self._is_failed:
            self.setBrush(QBrush(QColor("#3c1e1e")))
        elif self._is_completed:
            self.setBrush(QBrush(QColor("#1e3c1e")))
        elif self._is_running:
            self.setBrush(QBrush(QColor("#2d2d1e")))
        else:
            self.setBrush(QBrush(QColor("#2d2d2d")))

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None
    ):
        """Custom paint for rounded rectangle with header."""
        rect = self.rect()

        # Create rounded rect path
        path = QPainterPath()
        path.addRoundedRect(rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        # Draw body
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.brush())
        painter.drawPath(path)

        # Draw header
        header_path = QPainterPath()
        header_rect = QRectF(0, 0, rect.width(), self.HEADER_HEIGHT)
        header_path.addRoundedRect(header_rect, self.CORNER_RADIUS, self.CORNER_RADIUS)

        clip_rect = QRectF(
            0, self.CORNER_RADIUS,
            rect.width(), self.HEADER_HEIGHT - self.CORNER_RADIUS
        )
        header_path.addRect(clip_rect)

        painter.setBrush(QBrush(QColor(self.definition.color)))
        painter.drawPath(header_path)

        # Draw border
        if self.isSelected():
            painter.setPen(QPen(QColor("#4a9eff"), 2))
        else:
            painter.setPen(QPen(QColor("#3c3c3c"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Draw title
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(self.PADDING, 0, rect.width() - 2 * self.PADDING, self.HEADER_HEIGHT),
            Qt.AlignmentFlag.AlignVCenter,
            self.definition.name
        )

        # Draw port labels
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QPen(QColor("#cccccc")))

        for i, port in enumerate(self.input_ports):
            y = self.HEADER_HEIGHT + self.PORT_MARGIN + i * self.PORT_SPACING
            painter.drawText(
                QRectF(self.PADDING + 8, y - 8, 100, 16),
                Qt.AlignmentFlag.AlignVCenter,
                port.port_def.name
            )

        for i, port in enumerate(self.output_ports):
            y = self.HEADER_HEIGHT + self.PORT_MARGIN + i * self.PORT_SPACING
            painter.drawText(
                QRectF(rect.width() - self.PADDING - 108, y - 8, 100, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                port.port_def.name
            )

    def get_port(self, name: str, port_type: PortType) -> Optional[NodePort]:
        """Get a port by name and type."""
        ports = self.input_ports if port_type == PortType.INPUT else self.output_ports
        for port in ports:
            if port.port_def.name == name:
                return port
        return None

    def set_running(self, running: bool):
        """Set node running state."""
        self._is_running = running
        self._is_completed = False
        self._is_failed = False
        self._update_appearance()
        self.update()

    def set_completed(self, success: bool):
        """Set node completion state."""
        self._is_running = False
        self._is_completed = success
        self._is_failed = not success
        self._update_appearance()
        self.update()

    def reset_state(self):
        """Reset node execution state."""
        self._is_running = False
        self._is_completed = False
        self._is_failed = False
        self._update_appearance()
        self.update()

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.input_ports + self.output_ports:
                for conn in port.connections:
                    conn.update_path()
            if self.on_position_changed:
                self.on_position_changed(self)
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle double click to edit parameters."""
        if self.on_double_clicked:
            self.on_double_clicked(self)
        super().mouseDoubleClickEvent(event)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            "id": str(self.node_id),
            "type": self.definition.node_type,
            "name": self.definition.name,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "parameters": self.parameters.copy(),
        }
