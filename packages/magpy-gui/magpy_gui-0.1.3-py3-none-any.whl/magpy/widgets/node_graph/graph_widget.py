"""
NodeGraphWidget - Interactive canvas for node-based pipeline editing.

Provides pan, zoom, node placement, and wire drawing functionality.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Callable
from uuid import UUID

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QWheelEvent, QMouseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
)

from .node import Node, NodeDefinition, NodePort, PortType
from .connection import Connection


class NodeGraphScene(QGraphicsScene):
    """Scene for the node graph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor("#1e1e1e"))

        # Grid settings
        self.grid_size = 20
        self.grid_color = QColor("#2a2a2a")

    def drawBackground(self, painter: QPainter, rect):
        """Draw grid background."""
        super().drawBackground(painter, rect)

        # Draw grid
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        lines = []
        x = left
        while x < rect.right():
            lines.append((QPointF(x, rect.top()), QPointF(x, rect.bottom())))
            x += self.grid_size

        y = top
        while y < rect.bottom():
            lines.append((QPointF(rect.left(), y), QPointF(rect.right(), y)))
            y += self.grid_size

        painter.setPen(QPen(self.grid_color, 0.5))
        for start, end in lines:
            painter.drawLine(start, end)


class NodeGraphWidget(QGraphicsView):
    """Interactive node graph editor widget."""

    # Signals
    node_added = pyqtSignal(Node)
    node_removed = pyqtSignal(Node)
    node_selected = pyqtSignal(Node)
    connection_added = pyqtSignal(Connection)
    connection_removed = pyqtSignal(Connection)
    graph_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create scene
        self._scene = NodeGraphScene(self)
        self._scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.setScene(self._scene)

        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # State
        self._nodes: Dict[UUID, Node] = {}
        self._connections: List[Connection] = []
        self._node_definitions: Dict[str, NodeDefinition] = {}

        # Interaction state
        self._is_panning = False
        self._pan_start = QPointF()
        self._creating_connection: Optional[Connection] = None
        self._connection_start_port: Optional[NodePort] = None

        # Zoom settings
        self._zoom = 1.0
        self._zoom_min = 0.2
        self._zoom_max = 3.0
        self._zoom_step = 0.1

        # Callbacks
        self.on_node_double_clicked: Optional[Callable[[Node], None]] = None

    def register_node_definition(self, definition: NodeDefinition):
        """Register a node type definition."""
        self._node_definitions[definition.node_type] = definition

    def get_node_definition(self, node_type: str) -> Optional[NodeDefinition]:
        """Get a node definition by type."""
        return self._node_definitions.get(node_type)

    def add_node(
        self,
        node_type: str,
        position: Optional[QPointF] = None,
        node_id: Optional[UUID] = None,
    ) -> Optional[Node]:
        """Add a node to the graph."""
        definition = self._node_definitions.get(node_type)
        if not definition:
            return None

        node = Node(definition, node_id)
        if position:
            node.setPos(position)
        else:
            # Place in center of view
            center = self.mapToScene(self.viewport().rect().center())
            node.setPos(center)

        node.on_double_clicked = self._on_node_double_clicked

        self._scene.addItem(node)
        self._nodes[node.node_id] = node

        self.node_added.emit(node)
        self.graph_changed.emit()

        return node

    def remove_node(self, node: Node):
        """Remove a node and its connections from the graph."""
        # Remove all connections to this node
        connections_to_remove = []
        for port in node.input_ports + node.output_ports:
            connections_to_remove.extend(port.connections)

        for conn in connections_to_remove:
            self.remove_connection(conn)

        # Remove node
        self._scene.removeItem(node)
        del self._nodes[node.node_id]

        self.node_removed.emit(node)
        self.graph_changed.emit()

    def get_node(self, node_id: UUID) -> Optional[Node]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_nodes(self) -> List[Node]:
        """Get all nodes."""
        return list(self._nodes.values())

    def add_connection(
        self,
        source_node: Node,
        source_port_name: str,
        target_node: Node,
        target_port_name: str,
    ) -> Optional[Connection]:
        """Add a connection between two ports."""
        source_port = source_node.get_port(source_port_name, PortType.OUTPUT)
        target_port = target_node.get_port(target_port_name, PortType.INPUT)

        if not source_port or not target_port:
            return None

        # Check if connection already exists
        for existing in self._connections:
            if (existing.source_port == source_port and
                existing.target_port == target_port):
                return existing

        connection = Connection(source_port, target_port)
        self._scene.addItem(connection)
        self._connections.append(connection)

        self.connection_added.emit(connection)
        self.graph_changed.emit()

        return connection

    def remove_connection(self, connection: Connection):
        """Remove a connection."""
        if connection in self._connections:
            self._connections.remove(connection)
            connection.remove()

            self.connection_removed.emit(connection)
            self.graph_changed.emit()

    def get_connections(self) -> List[Connection]:
        """Get all connections."""
        return self._connections.copy()

    def clear(self):
        """Clear all nodes and connections."""
        for conn in self._connections.copy():
            self.remove_connection(conn)

        for node in list(self._nodes.values()):
            self.remove_node(node)

        self.graph_changed.emit()

    def _on_node_double_clicked(self, node: Node):
        """Handle node double click."""
        if self.on_node_double_clicked:
            self.on_node_double_clicked(node)

    # =========================================================================
    # Mouse Interaction
    # =========================================================================

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Start panning
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on a port
            scene_pos = self.mapToScene(event.position().toPoint())
            items = self._scene.items(scene_pos)

            for item in items:
                if isinstance(item, NodePort):
                    # Start creating connection
                    self._start_connection(item, scene_pos)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move."""
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            return

        if self._creating_connection:
            # Update connection end point
            scene_pos = self.mapToScene(event.position().toPoint())
            self._creating_connection.set_temp_end(scene_pos)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.MiddleButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if event.button() == Qt.MouseButton.LeftButton and self._creating_connection:
            # Try to complete connection
            scene_pos = self.mapToScene(event.position().toPoint())
            self._finish_connection(scene_pos)
            return

        super().mouseReleaseEvent(event)

        # Emit selection signal
        selected = self._scene.selectedItems()
        for item in selected:
            if isinstance(item, Node):
                self.node_selected.emit(item)
                break

    def _start_connection(self, port: NodePort, scene_pos: QPointF):
        """Start creating a new connection from a port."""
        self._connection_start_port = port

        # Create temporary connection
        if port.port_type == PortType.OUTPUT:
            self._creating_connection = Connection(source_port=port)
        else:
            self._creating_connection = Connection(target_port=port)

        self._creating_connection.set_temp_end(scene_pos)
        self._scene.addItem(self._creating_connection)

    def _finish_connection(self, scene_pos: QPointF):
        """Finish creating a connection."""
        if not self._creating_connection or not self._connection_start_port:
            return

        # Find port under cursor
        items = self._scene.items(scene_pos)
        target_port = None

        for item in items:
            if isinstance(item, NodePort) and item != self._connection_start_port:
                # Check port compatibility
                if item.port_type != self._connection_start_port.port_type:
                    # Different types, valid connection
                    if item.parent_node != self._connection_start_port.parent_node:
                        # Different nodes, valid connection
                        target_port = item
                        break

        # Remove temporary connection
        self._scene.removeItem(self._creating_connection)

        if target_port:
            # Create actual connection
            if self._connection_start_port.port_type == PortType.OUTPUT:
                source_port = self._connection_start_port
                dest_port = target_port
            else:
                source_port = target_port
                dest_port = self._connection_start_port

            connection = Connection(source_port, dest_port)
            self._scene.addItem(connection)
            self._connections.append(connection)

            self.connection_added.emit(connection)
            self.graph_changed.emit()

        self._creating_connection = None
        self._connection_start_port = None

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()

        if delta > 0:
            factor = 1 + self._zoom_step
        else:
            factor = 1 - self._zoom_step

        new_zoom = self._zoom * factor
        if self._zoom_min <= new_zoom <= self._zoom_max:
            self._zoom = new_zoom
            self.scale(factor, factor)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press."""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Delete selected items
            selected = self._scene.selectedItems()
            for item in selected:
                if isinstance(item, Connection):
                    self.remove_connection(item)
                elif isinstance(item, Node):
                    self.remove_node(item)
            return

        if event.key() == Qt.Key.Key_Home:
            # Reset view
            self.resetTransform()
            self._zoom = 1.0
            self.centerOn(0, 0)
            return

        super().keyPressEvent(event)

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict:
        """Serialize the graph to a dictionary."""
        nodes = [node.to_dict() for node in self._nodes.values()]
        connections = [conn.to_dict() for conn in self._connections if conn.is_complete]

        return {
            "nodes": nodes,
            "connections": connections,
        }

    def from_dict(self, data: dict):
        """Load the graph from a dictionary."""
        self.clear()

        # Create nodes
        node_map: Dict[str, Node] = {}
        for node_data in data.get("nodes", []):
            node_type = node_data.get("type")
            node_id = UUID(node_data["id"])
            position = QPointF(node_data.get("x", 0), node_data.get("y", 0))

            node = self.add_node(node_type, position, node_id)
            if node:
                node.parameters.update(node_data.get("parameters", {}))
                node_map[str(node_id)] = node

        # Create connections
        for conn_data in data.get("connections", []):
            source_node_id = conn_data.get("source_node")
            target_node_id = conn_data.get("target_node")

            if source_node_id and target_node_id:
                source_node = node_map.get(source_node_id)
                target_node = node_map.get(target_node_id)

                if source_node and target_node:
                    self.add_connection(
                        source_node,
                        conn_data.get("source_port", ""),
                        target_node,
                        conn_data.get("target_port", ""),
                    )

    def reset_node_states(self):
        """Reset all node execution states."""
        for node in self._nodes.values():
            node.reset_state()
