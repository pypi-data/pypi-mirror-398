"""
Connection - Visual wire connecting two node ports.

Represents data flow from an output port to an input port.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

if TYPE_CHECKING:
    from .node import NodePort, Node


class Connection(QGraphicsPathItem):
    """Visual wire connecting two node ports."""

    def __init__(
        self,
        source_port: Optional["NodePort"] = None,
        target_port: Optional["NodePort"] = None,
        connection_id: Optional[UUID] = None,
    ):
        super().__init__()
        self.connection_id = connection_id or uuid4()
        self._source_port = source_port
        self._target_port = target_port

        # Temporary end point for when dragging
        self._temp_end: Optional[QPointF] = None

        self.setZValue(-1)  # Draw behind nodes
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        # Appearance
        self._normal_color = QColor("#6c6c6c")
        self._hover_color = QColor("#00d4aa")
        self._selected_color = QColor("#4a9eff")
        self._current_color = self._normal_color

        self._update_pen()

        if source_port and target_port:
            self._register_with_ports()
            self.update_path()

    def _update_pen(self):
        """Update the pen based on current state."""
        pen = QPen(self._current_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)

    def _register_with_ports(self):
        """Register this connection with its ports."""
        if self._source_port:
            self._source_port.add_connection(self)
        if self._target_port:
            self._target_port.add_connection(self)

    def _unregister_from_ports(self):
        """Unregister this connection from its ports."""
        if self._source_port:
            self._source_port.remove_connection(self)
        if self._target_port:
            self._target_port.remove_connection(self)

    @property
    def source_port(self) -> Optional["NodePort"]:
        return self._source_port

    @property
    def target_port(self) -> Optional["NodePort"]:
        return self._target_port

    @property
    def source_node(self) -> Optional["Node"]:
        return self._source_port.parent_node if self._source_port else None

    @property
    def target_node(self) -> Optional["Node"]:
        return self._target_port.parent_node if self._target_port else None

    @property
    def is_complete(self) -> bool:
        """Check if connection has both endpoints."""
        return self._source_port is not None and self._target_port is not None

    def set_source(self, port: "NodePort"):
        """Set the source port."""
        if self._source_port:
            self._source_port.remove_connection(self)
        self._source_port = port
        if port:
            port.add_connection(self)
        self.update_path()

    def set_target(self, port: "NodePort"):
        """Set the target port."""
        if self._target_port:
            self._target_port.remove_connection(self)
        self._target_port = port
        if port:
            port.add_connection(self)
        self.update_path()

    def set_temp_end(self, pos: QPointF):
        """Set temporary end point for dragging."""
        self._temp_end = pos
        self.update_path()

    def clear_temp_end(self):
        """Clear temporary end point."""
        self._temp_end = None
        self.update_path()

    def update_path(self):
        """Update the bezier path between ports."""
        if not self._source_port:
            return

        start = self._source_port.center_scene_pos()

        if self._target_port:
            end = self._target_port.center_scene_pos()
        elif self._temp_end:
            end = self._temp_end
        else:
            return

        # Create bezier curve
        path = QPainterPath()
        path.moveTo(start)

        # Calculate control points for smooth curve
        dx = abs(end.x() - start.x())
        ctrl_offset = min(dx * 0.5, 100)

        ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
        ctrl2 = QPointF(end.x() - ctrl_offset, end.y())

        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Custom paint with gradient effect."""
        path = self.path()
        if path.isEmpty():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw shadow
        shadow_pen = QPen(QColor(0, 0, 0, 40), 4)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(shadow_pen)
        painter.drawPath(path.translated(1, 1))

        # Draw main wire
        painter.setPen(self.pen())
        painter.drawPath(path)

    def hoverEnterEvent(self, event):
        self._current_color = self._hover_color
        self._update_pen()
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.isSelected():
            self._current_color = self._selected_color
        else:
            self._current_color = self._normal_color
        self._update_pen()
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                self._current_color = self._selected_color
            else:
                self._current_color = self._normal_color
            self._update_pen()
        return super().itemChange(change, value)

    def remove(self):
        """Remove this connection."""
        self._unregister_from_ports()
        scene = self.scene()
        if scene:
            scene.removeItem(self)

    def to_dict(self) -> dict:
        """Serialize connection to dictionary."""
        return {
            "id": str(self.connection_id),
            "source_node": str(self.source_node.node_id) if self.source_node else None,
            "source_port": self._source_port.port_def.name if self._source_port else None,
            "target_node": str(self.target_node.node_id) if self.target_node else None,
            "target_port": self._target_port.port_def.name if self._target_port else None,
        }
