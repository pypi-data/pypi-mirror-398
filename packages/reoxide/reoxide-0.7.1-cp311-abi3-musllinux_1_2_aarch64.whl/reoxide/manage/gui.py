# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2025 Michael Pucher <contact@cluo.sh>
from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, \
    QInputDialog, QLineEdit, QListWidget, \
    QMainWindow, QMessageBox, QPushButton, QStyleOptionViewItem, \
    QStyledItemDelegate, QTreeView, QWidget, QAbstractItemView, \
    QVBoxLayout
from PySide6.QtCore import QAbstractItemModel, QMimeData, \
    QModelIndex, QPersistentModelIndex, QThread, Signal, \
    Slot, QObject, Qt
from typing import Optional, Sequence, Any, override
from dataclasses import dataclass

from .client import ManageClient, PipelineBaseNode, \
    PipelineBaseAction, PipelineAction, PipelineRule, \
    PipelineGroup, PipelinePool, PipelineActionRule, \
    Plugin, parse_actions, parse_rules


PIPELINE_GROUPS = [
    'analysis',
    'base',
    'blockrecovery',
    'casts',
    'cleanup',
    'conditionalexe',
    'constsequence',
    'deadcode',
    'deadcontrolflow',
    'deindirect',
    'doubleload',
    'doubleprecis',
    'dynamic',
    'fixateglobals',
    'fixateproto',
    'floatprecision',
    'localrecovery',
    'merge',
    'nodejoin',
    'noproto',
    'normalanalysis',
    'normalizebranches',
    'protorecovery',
    'protorecovery_a',
    'protorecovery_b',
    'returnsplit',
    'segment',
    'siganalysis',
    'splitcopy',
    'splitpointer',
    'stackptrflow',
    'stackvars',
    'subvar',
    'switchnorm',
    'typerecovery',
    'unreachable'
]


@dataclass
class GhidraActionRuleBase:
    name: str
    plugin: str


@dataclass
class GhidraAction(GhidraActionRuleBase):
    pass


@dataclass
class GhidraRule(GhidraActionRuleBase):
    pass


class PipelineModel(QAbstractItemModel):
    root: PipelineGroup
    apply_pipeline = Signal(PipelineGroup)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root = PipelineGroup(None, "universal", [])

    def get_node(
        self,
        index: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> PipelineBaseNode:
        if index.isValid():
            item: PipelineBaseNode = index.internalPointer()
            if item:
                return item
        return self.root

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.ItemDataRole.DisplayRole \
            and role != Qt.ItemDataRole.EditRole:
            return None

        item: PipelineBaseNode = self.get_node(index)
        match index.column():
            case 0:
                return item.TYPENAME
            case 1 if isinstance(item, PipelineAction) and item.extra_args:
                args = ", ".join([str(x) for x in item.extra_args])
                return f'{item.name}({args})'
            case 1:
                return item.name
            case 2 if isinstance(item, PipelineActionRule):
                return item.group_name
            case 3 if isinstance(item, PipelineActionRule):
                return item.plugin
            case _:
                return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.DisplayRole
    ) -> bool:
        if not index.isValid():
            return False

        if role != Qt.ItemDataRole.DisplayRole \
            and role != Qt.ItemDataRole.EditRole:
            return False

        item: PipelineBaseNode = self.get_node(index)
        match index.column():
            case 0:
                return False
            case 1 if isinstance(item, PipelineGroup):
                if not value:
                    return False
                item.name = value
                self.dataChanged.emit(
                    index,
                    index,
                    [Qt.ItemDataRole.DisplayRole]
                )
                return True
            case 1 if isinstance(item, PipelinePool):
                if not value:
                    return False
                item.name = value
                self.dataChanged.emit(
                    index,
                    index,
                    [Qt.ItemDataRole.DisplayRole]
                )
                return True
            case 2 if isinstance(item, PipelineActionRule):
                item.group_name = value
                self.dataChanged.emit(
                    index,
                    index,
                    [Qt.ItemDataRole.DisplayRole]
                )
                return True
            case _:
                return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsDropEnabled

        base_flags = QAbstractItemModel.flags(self, index) \
            | Qt.ItemFlag.ItemIsDragEnabled
        item: PipelineBaseNode = self.get_node(index)

        if isinstance(item, PipelineGroup):
            base_flags |= Qt.ItemFlag.ItemIsDropEnabled
        if isinstance(item, PipelinePool):
            base_flags |= Qt.ItemFlag.ItemIsDropEnabled

        match index.column():
            case 1 if isinstance(item, PipelineActionRule):
                # For actions and rules, the name comes from the plugin
                return base_flags
            case 1:
                # Names for groups and pools are editable
                return base_flags | Qt.ItemFlag.ItemIsEditable
            case 2 if isinstance(item, PipelineActionRule):
                # Groups for actions and rules are editable
                return base_flags | Qt.ItemFlag.ItemIsEditable
            case 2:
                # Groups are not editable for groups and pools
                return base_flags
            case _:
                return base_flags

    def headerData(self, section: int, orientation, role=None):
        if orientation != Qt.Orientation.Horizontal:
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        return ["Type", "Name", "Group", "Plugin"][section]

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        node: Optional[PipelineBaseNode] = parent.internalPointer()
        if not node:
            node = self.root

        if isinstance(node, PipelineGroup):
            children = node.actions
        elif isinstance(node, PipelinePool):
            children = node.rules
        else:
            return QModelIndex()

        if row >= len(children):
            return QModelIndex()
        return self.createIndex(row, column, children[row])

    def parent(
        self,
        child: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> QModelIndex:
        if not child.isValid():
            return QModelIndex()

        node: Optional[PipelineBaseNode] = child.internalPointer()
        if node:
            parent = node.parent
        else:
            parent = None

        if parent == self.root or not parent:
            return QModelIndex()

        assert parent.parent
        if isinstance(parent.parent, PipelineGroup):
            assert isinstance(parent, PipelineBaseAction)
            child_number = parent.parent.actions.index(parent)
        elif isinstance(parent.parent, PipelinePool):
            assert isinstance(parent, PipelineRule)
            child_number = parent.parent.rules.index(parent)
        else:
            assert False, "Technically unreachable"

        return self.createIndex(child_number, 0, parent)

    def supportedDragActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction | Qt.DropAction.CopyAction

    def mimeTypes(self) -> list[str]:
        return [
            "application/x-ghidra-action",
            "application/x-ghidra-rule"
        ]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        top_level_mime = "application/x-ghidra-action"
        data = []

        for index in indexes:
            if not index.isValid():
                continue
            if index.column() > 0:
                continue

            item: PipelineBaseNode = index.internalPointer()
            if not item:
                continue

            data.extend(item.serialize())

            if isinstance(item, PipelineBaseAction):
                top_level_mime = "application/x-ghidra-action"
            elif isinstance(item, PipelineRule):
                top_level_mime = "application/x-ghidra-rule"
            else:
                assert False, "Unreachable"

        mime_data.setData(top_level_mime, b'\x00'.join(data))
        return mime_data

    def canDropMimeData(self, data, action, row, column, parent) -> bool:
        is_rule = data.hasFormat("application/x-ghidra-rule")
        is_action = data.hasFormat("application/x-ghidra-action")
        if not is_rule and not is_action:
            return False

        node = self.get_node(parent)
        if is_rule and not isinstance(node, PipelinePool):
            return False
        if is_action and not isinstance(node, PipelineGroup):
            return False

        return True

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex
    ):
        if not self.canDropMimeData(data, action, row, column, parent):
            return False
        if action == Qt.DropAction.IgnoreAction:
            return False

        parent_node = self.get_node(parent)

        if data.hasFormat("application/x-ghidra-action"):
            # From canDropMimeData check
            assert isinstance(parent_node, PipelineGroup)
            action_bytearray = data.data("application/x-ghidra-action")
            action_bytes = bytes(action_bytearray.data())
            stream = iter(action_bytes.split(b'\x00'))
            actions = parse_actions(parent_node, stream)
            self.insertActions(actions, row, parent)
            return True

        elif data.hasFormat("application/x-ghidra-rule"):
            # From canDropMimeData check
            assert isinstance(parent_node, PipelinePool)
            rule_bytearray = data.data("application/x-ghidra-rule")
            rule_bytes = bytes(rule_bytearray.data())
            stream = iter(rule_bytes.split(b'\x00'))
            actions = parse_rules(parent_node, stream)
            self.insertRules(actions, row, parent)
            return True

        return False

    def insertActionsAtSelection(
        self,
        items: Sequence[PipelineBaseAction],
        selection: QModelIndex
    ) -> Sequence[QModelIndex]:
        selected_node = self.get_node(selection)
        parent = selection

        # If user selected a rule, pick the parent pool
        if isinstance(selected_node, PipelineRule):
            selected_node = selected_node.parent
            parent = self.parent(parent)
            assert selected_node is not None

        # If user selected a group, insert new element at
        # last position, otherwise insert right after the
        # selected element
        if isinstance(selected_node, PipelineGroup):
            row = len(selected_node.actions)
        else:
            old_selected = selected_node
            selected_node = selected_node.parent
            parent = self.parent(parent)
            assert selected_node is not None
            assert isinstance(selected_node, PipelineGroup)
            assert isinstance(old_selected, PipelineBaseAction)
            row = selected_node.actions.index(old_selected) + 1

        for item in items:
            item.parent = selected_node

        self.insertActions(items, row, parent)
        return [
            self.index(row + i, 0, parent)
            for i in range(len(items))
        ]

    def insertActions(
        self,
        items: Sequence[PipelineBaseAction],
        row: int,
        parent: QModelIndex | QPersistentModelIndex
    ):
        """
        Insert items *after* already checking that inserting is ok
        """
        parent_node = self.get_node(parent)
        assert isinstance(parent_node, PipelineGroup)
        if row < 0:
            row = len(parent_node.actions)

        self.beginInsertRows(parent, row, row + len(items) - 1)
        parent_node.actions[row:row] = items
        self.endInsertRows()

    def insertRulesAtSelection(
        self,
        items: Sequence[PipelineRule],
        selection: QModelIndex
    ) -> Sequence[QModelIndex]:
        selected_node = self.get_node(selection)
        parent = selection


        if isinstance(selected_node, PipelinePool):
            row = len(selected_node.rules)
        elif isinstance(selected_node, PipelineRule):
            # If user selected a rule, pick the parent pool
            old_selected = selected_node
            selected_node = selected_node.parent
            parent = self.parent(parent)
            assert selected_node is not None
            assert isinstance(selected_node, PipelinePool)
            row = selected_node.rules.index(old_selected) + 1
        else:
            # If we don't have a pool, we can't insert anything
            return []

        for item in items:
            item.parent = selected_node

        self.insertRules(items, row, parent)
        return [
            self.index(row + i, 0, parent)
            for i in range(len(items))
        ]

    def insertRules(
        self,
        items: Sequence[PipelineRule],
        row: int,
        parent: QModelIndex | QPersistentModelIndex
    ):
        """
        Insert items *after* already checking that inserting is ok
        """
        parent_node = self.get_node(parent)
        assert isinstance(parent_node, PipelinePool)
        if row < 0:
            row = len(parent_node.rules)

        self.beginInsertRows(parent, row, row + len(items) - 1)
        parent_node.rules[row:row] = items
        self.endInsertRows()

    def removeRows(
        self,
        row: int,
        count: int,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> bool:
        parent_node = self.get_node(parent)
        if isinstance(parent_node, PipelineGroup):
            children = parent_node.actions
        elif isinstance(parent_node, PipelinePool):
            children = parent_node.rules
        else:
            assert False, "Unreachable"
        assert row + count <= len(children)

        self.beginRemoveRows(parent, row, row + count - 1)
        for i in range(row, row + count):
            del children[i]
        self.endRemoveRows()
        return True

    def columnCount(self, parent=None):
        # We have type, name, group, plugin
        return 4

    def rowCount(self, parent=None):
        if not parent:
            return 0
        if parent.isValid() and parent.column() > 0:
            return 0

        node: PipelineBaseNode = self.get_node(parent)
        if isinstance(node, PipelineGroup):
            return len(node.actions)
        elif isinstance(node, PipelinePool):
            return len(node.rules)
        else:
            return 0
    
    @Slot()
    def trigger_pipeline_apply(self):
        self.apply_pipeline.emit(self.root)

    @Slot(PipelineGroup)
    def replace_pipeline(self, root: PipelineGroup):
        self.beginResetModel()
        self.root = root
        self.endResetModel()


class ActionRuleModel(QAbstractItemModel):
    items: Sequence[GhidraActionRuleBase]

    def __init__(self, *args, header='Action', **kwargs):
        super().__init__(*args, **kwargs)
        self.items = []
        self.header = header
        self.mime = f"application/x-ghidra-{self.header.lower()}"

    def data(self, index, role = None):
        if not index.isValid():
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        row = index.row()
        if row >= len(self.items):
            return None

        col = index.column()
        if col >= 2:
            return None

        if col == 0:
            return self.items[row].name
        else:
            return self.items[row].plugin

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled \
            | Qt.ItemFlag.ItemIsSelectable \
            | Qt.ItemFlag.ItemIsDragEnabled

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()
        if row >= len(self.items):
            return QModelIndex()
        return self.createIndex(row, column, self.items[row])

    def parent(
        self,
        child: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> QModelIndex:
        return QModelIndex()

    def supportedDragActions(self) -> Qt.DropAction:
        return Qt.DropAction.CopyAction

    def mimeTypes(self) -> list[str]:
        return [self.mime]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        data = []

        for index in indexes:
            if not index.isValid():
                continue
            if index.column() > 0:
                continue

            item = index.internalPointer()
            if not item:
                continue

            if isinstance(item, GhidraAction):
                data.extend(PipelineAction(
                    name=item.name,
                    plugin=item.plugin,
                    group_name='base',
                    extra_args=[],
                    parent=None
                ).serialize())
            elif isinstance(item, GhidraRule):
                data.extend(PipelineRule(
                    name=item.name,
                    plugin=item.plugin,
                    group_name='base',
                    parent=None
                ).serialize())
            else:
                assert False, "Should only drag actions and rules"

        mime_data.setData(self.mime, b'\x00'.join(data))
        return mime_data

    def headerData(self, section: int, orientation, role=None):
        if orientation != Qt.Orientation.Horizontal:
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        return [self.header, "Plugin"][section]

    def rowCount(self, parent=None):
        if not parent:
            return 0
        if parent.isValid() and parent.column() > 0:
            return 0

        parent_item = self
        if parent.isValid():
            item = parent.internalPointer()
            if item:
                parent_item = item

        if parent_item != self:
            return 0;

        return len(self.items)

    def columnCount(self, parent=None):
        return 2

    @Slot(list)
    def replace_items(self, plugins: list[Plugin]):
        if self.header == 'Action':
            items = [
                GhidraAction(a, p.name)
                for p in plugins
                for a in p.actions
            ]
        else:
            items = [
                GhidraRule(a, p.name)
                for p in plugins
                for a in p.rules
            ]

        self.beginResetModel()
        self.items = items
        self.endResetModel()


class PipelineTreeView(QTreeView):
    load_pipeline = Signal(str)
    save_pipeline = Signal(str, PipelineGroup)
    delete_pipeline = Signal(str)

    def __init__(
        self,
        pipeline_selection: PipelineSelection,
        action_view: QTreeView,
        rule_view: QTreeView,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.pipeline_selection = pipeline_selection
        self.action_view = action_view
        self.rule_view = rule_view

    def dragEnterEvent(self, event):
        # We need to accept the action here, otherwise our
        # canDropMimeData will only be called once if it
        # returns false
        event.acceptProposedAction()
        self.setState(QAbstractItemView.State.DraggingState)

    @Slot()
    def delete_selected(self):
        model = self.model()
        selected = [
            index
            for index in self.selectedIndexes()
            if index.column() == 0
        ]
        self.clearSelection()

        # Note: Currently we only allow one selection, for multiple
        # selections this will probably invalidate the indices, so
        # we will have the change the method when we allow multiple
        # selections.
        assert len(selected) == 1
        index = selected[0]
        if index.isValid():
            model.removeRows(index.row(), 1, index.parent())

    @Slot()
    def add_group(self):
        text, ok = QInputDialog.getText(
            self,
            "Create new action group",
            "Name:",
            QLineEdit.EchoMode.Normal
        )

        if not ok:
            return

        if not text:
            QMessageBox.critical(
                self,
                "Error creating action group",
                "Name of new group must not be empty"
            )
            return

        group = PipelineGroup(
            name=text,
            parent=None,
            actions=[]
        )

        model = self.model()
        assert isinstance(model, PipelineModel)
        selected = [
            index
            for index in self.selectedIndexes()
            if index.column() == 0
        ]

        inserted = model.insertActionsAtSelection(
            [group], 
            selected[0] if selected else QModelIndex()
        )
        if inserted:
            self.scrollTo(inserted[0])

    @Slot()
    def add_pool(self):
        text, ok = QInputDialog.getText(
            self,
            "Create new rule pool",
            "Name:",
            QLineEdit.EchoMode.Normal
        )

        if not ok:
            return

        if not text:
            QMessageBox.critical(
                self,
                "Error creating rule pool",
                "Name of new rule pool must not be empty"
            )
            return

        pool = PipelinePool(
            name=text,
            parent=None,
            rules=[]
        )

        model = self.model()
        assert isinstance(model, PipelineModel)
        selected = [
            index
            for index in self.selectedIndexes()
            if index.column() == 0
        ]

        inserted = model.insertActionsAtSelection(
            [pool], 
            selected[0] if selected else QModelIndex()
        )
        if inserted:
            self.scrollTo(inserted[0])

    @Slot()
    def trigger_load_pipeline(self):
        items = self.pipeline_selection.selectedItems()
        if items:
            pipeline_name = items[0].text()
        else:
            pipeline_name = 'current'
        self.load_pipeline.emit(pipeline_name)

    @Slot()
    def trigger_save_pipeline(self):
        name, ok = QInputDialog.getText(
            self,
            "Save current pipeline",
            "Name:",
            QLineEdit.EchoMode.Normal
        )

        if not ok:
            return

        if not name:
            QMessageBox.critical(
                self,
                "Error saving current pipeline",
                "Name of the pipeline must not be empty."
            )
            return 

        model = self.model()
        assert isinstance(model, PipelineModel)
        self.save_pipeline.emit(name, model.root)

    @Slot()
    def add_action(self):
        action_select = self.action_view.selectedIndexes()
        actions = []
        for index in action_select:
            if index.column() != 0:
                continue

            ghidra_action = index.internalPointer()
            assert isinstance(ghidra_action, GhidraAction)

            actions.append(PipelineAction(
                name=ghidra_action.name,
                group_name='base',
                plugin=ghidra_action.plugin,
                parent=None,
                extra_args=[]
            ))

        model = self.model()
        assert isinstance(model, PipelineModel)
        selected = [
            index
            for index in self.selectedIndexes()
            if index.column() == 0
        ]

        inserted = model.insertActionsAtSelection(
            actions, 
            selected[0] if selected else QModelIndex()
        )
        if inserted:
            self.scrollTo(inserted[0])

    @Slot()
    def add_rule(self):
        rule_select = self.rule_view.selectedIndexes()
        rules = []
        for index in rule_select:
            if index.column() != 0:
                continue

            ghidra_rule = index.internalPointer()
            assert isinstance(ghidra_rule, GhidraRule)

            rules.append(PipelineRule(
                name=ghidra_rule.name,
                group_name='base',
                plugin=ghidra_rule.plugin,
                parent=None
            ))

        model = self.model()
        assert isinstance(model, PipelineModel)
        selected = [
            index
            for index in self.selectedIndexes()
            if index.column() == 0
        ]

        inserted = model.insertRulesAtSelection(
            rules, 
            selected[0] if selected else QModelIndex()
        )
        if inserted:
            self.scrollTo(inserted[0])

    @Slot()
    def trigger_delete_pipeline(self):
        items = self.pipeline_selection.selectedItems()
        if not items:
            QMessageBox.information(
                self,
                "Delete pipeline",
                "No pipeline selected."
            )
            return

        reply = QMessageBox.question(
            self,
            "Delete pipeline",
            "Are you sure you want to delete the selected pipeline?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.delete_pipeline.emit(items[0].text())

    @Slot()
    def trigger_load_default_pipeline(self):
        self.load_pipeline.emit('default')
        self.pipeline_selection.clearSelection()


class MainWindow(QMainWindow):
    def __init__(self, widget: QWidget):
        super().__init__()
        self.setWindowTitle("ReOxide Manager")
        self.setCentralWidget(widget)

    @Slot()
    def pipeline_applied(self):
        QMessageBox.information(
            self,
            'Pipeline applied',
            'Pipeline has been applied successfully. ' \
            + 'Please refresh any running decompilers.'
        )

    @Slot(str)
    def pipeline_apply_failed(self, err: str):
        QMessageBox.critical(
            self,
            'Pipeline not applied',
            f'Pipline apply failed with error: {err}' 
        )

    @Slot(str)
    def pipeline_save_failed(self, err: str):
        QMessageBox.critical(
            self,
            'Pipeline not saved',
            f'Pipline save failed with error: {err}' 
        )

    @Slot(str)
    def pipeline_delete_failed(self, err: str):
        QMessageBox.critical(
            self,
            'Pipeline not delete',
            f'Pipline delete failed with error: {err}' 
        )


class ClientObject(QObject):
    client: Optional[ManageClient]
    plugins_listed = Signal(list)
    pipeline_fetched = Signal(PipelineGroup)
    pipeline_applied = Signal()
    pipeline_apply_failed = Signal(str)
    pipeline_save_failed = Signal(str)
    pipeline_delete_failed = Signal(str)
    pipelines_listed = Signal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None

    def connect_to_daemon(self):
        self.client = ManageClient()
        self.get_plugins()
        self.list_pipelines()
        self.fetch_pipeline('current')

    @Slot()
    def get_plugins(self):
        if not self.client:
            return

        try:
            plugins = self.client.list_plugins()
        except TimeoutError:
            # TODO
            return

        self.plugins_listed.emit(plugins)

    @Slot(str)
    def fetch_pipeline(self, name: str):
        if not self.client:
            return

        try:
            pipeline = self.client.fetch_pipeline(name)
        except TimeoutError:
            # TODO
            return

        self.pipeline_fetched.emit(pipeline)

    @Slot(PipelineGroup)
    def apply_pipeline(self, pipeline: PipelineGroup):
        if not self.client:
            return

        try:
            err = self.client.apply_pipeline(pipeline)
            if err:
                self.pipeline_apply_failed.emit(err)
            else:
                self.pipeline_applied.emit()
        except TimeoutError:
            msg = 'Timeout while waiting for reoxided'
            self.pipeline_apply_failed.emit(msg)

    @Slot(str, PipelineGroup)
    def save_pipeline(
        self,
        name: str,
        pipeline: PipelineGroup
    ):
        if not self.client:
            return

        try:
            err = self.client.save_pipeline(name, pipeline)
            if err:
                self.pipeline_save_failed.emit(err)
                return

            pipelines = self.client.list_pipelines()
            self.pipelines_listed.emit(pipelines)
        except TimeoutError:
            msg = 'Timeout while waiting for reoxided'
            self.pipeline_save_failed.emit(msg)

    @Slot(str)
    def delete_pipeline(self, name: str):
        if not self.client:
            return

        try:
            err = self.client.delete_pipeline(name)
            if err:
                self.pipeline_delete_failed.emit(err)

            pipelines = self.client.list_pipelines()
            self.pipelines_listed.emit(pipelines)
        except TimeoutError:
            msg = 'Timeout while waiting for reoxided'
            self.pipeline_delete_failed.emit(msg)

    @Slot()
    def list_pipelines(self):
        if not self.client:
            return

        try:
            pipelines = self.client.list_pipelines()
        except TimeoutError:
            # TODO
            return

        self.pipelines_listed.emit(pipelines)


class ClientThread(QThread):
    get_plugins = Signal()
    fetch_pipeline = Signal(str)
    apply_pipeline = Signal(PipelineGroup)
    save_pipeline = Signal(str, PipelineGroup)
    delete_pipeline = Signal(str)
    list_pipelines = Signal()

    plugins_listed = Signal(list)
    pipeline_fetched = Signal(PipelineGroup)
    pipeline_applied = Signal()
    pipeline_apply_failed = Signal(str)
    pipeline_save_failed = Signal(str)
    pipeline_delete_failed = Signal(str)
    pipelines_listed = Signal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_obj = ClientObject()
        self.client_obj.moveToThread(self)

        self.get_plugins.connect(
            self.client_obj.get_plugins,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.plugins_listed.connect(
            self._plugins_listed,
            Qt.ConnectionType.QueuedConnection
        )

        self.fetch_pipeline.connect(
            self.client_obj.fetch_pipeline,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.pipeline_fetched.connect(
            self._pipline_fetched,
            Qt.ConnectionType.QueuedConnection
        )

        self.apply_pipeline.connect(
            self.client_obj.apply_pipeline,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.pipeline_applied.connect(
            self._pipeline_applied,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.pipeline_apply_failed.connect(
            self._pipeline_apply_failed,
            Qt.ConnectionType.QueuedConnection
        )

        self.list_pipelines.connect(
            self.client_obj.list_pipelines,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.pipelines_listed.connect(
            self._pipelines_listed,
            Qt.ConnectionType.QueuedConnection
        )

        self.save_pipeline.connect(
            self.client_obj.save_pipeline,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.pipeline_save_failed.connect(
            self._pipeline_save_failed,
            Qt.ConnectionType.QueuedConnection
        )

        self.delete_pipeline.connect(
            self.client_obj.delete_pipeline,
            Qt.ConnectionType.QueuedConnection
        )
        self.client_obj.pipeline_delete_failed.connect(
            self._pipeline_delete_failed,
            Qt.ConnectionType.QueuedConnection
        )

    def __del__(self):
        self.quit()
        self.wait()

    @override
    def run(self):
        self.client_obj.connect_to_daemon()
        super().run()

    @Slot(list)
    def _plugins_listed(self, plugins: list[Plugin]):
        self.plugins_listed.emit(plugins)

    @Slot(PipelineGroup)
    def _pipline_fetched(self, pipeline: PipelineGroup):
        self.pipeline_fetched.emit(pipeline)

    @Slot()
    def _pipeline_applied(self):
        self.pipeline_applied.emit()

    @Slot(str)
    def _pipeline_apply_failed(self, msg: str):
        self.pipeline_apply_failed.emit(msg)

    @Slot(str)
    def _pipeline_save_failed(self, msg: str):
        self.pipeline_save_failed.emit(msg)

    @Slot(str)
    def _pipeline_delete_failed(self, msg: str):
        self.pipeline_delete_failed.emit(msg)

    @Slot(list)
    def _pipelines_listed(self, pipelines: list[str]):
        self.pipelines_listed.emit(pipelines)


class PipelineItemDelegate(QStyledItemDelegate):
    @override
    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex
    ) -> QWidget:
        if index.isValid() and index.column() == 2:
            return QComboBox(parent)
        return super().createEditor(parent, option, index)

    @override
    def setEditorData(
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex
    ):
        if index.isValid() and index.column() == 2:
            assert isinstance(editor, QComboBox)
            editor.addItems(PIPELINE_GROUPS)
            editor.setCurrentIndex(editor.findText(index.data()))
        return super().setEditorData(editor, index)

    @override
    def setModelData(
        self,
        editor: QWidget,
        model: QAbstractItemModel,
        index: QModelIndex | QPersistentModelIndex
    ):
        if index.isValid() and index.column() == 2:
            assert isinstance(editor, QComboBox)
            model.setData(index, editor.currentText())
        return super().setModelData(editor, model, index)


class PipelineSelection(QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @Slot(list)
    def addPipelines(self, names: list[str]):
        self.clear()
        self.addItems(names)


def run_gui():
    app = QApplication(sys.argv)

    action_model = ActionRuleModel(header='Action')
    action_view = QTreeView()
    action_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    action_view.setDragEnabled(True)
    action_view.setModel(action_model)

    rule_model = ActionRuleModel(header='Rule')
    rule_view = QTreeView()
    rule_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    rule_view.setDragEnabled(True)
    rule_view.setModel(rule_model)

    h = QHBoxLayout()
    left_vertical = QVBoxLayout()

    pipelines = PipelineSelection()
    size_policy = pipelines.sizePolicy()
    size_policy.setVerticalStretch(1)
    pipelines.setSizePolicy(size_policy)
    left_vertical.addWidget(pipelines)

    pipeline_controls = QHBoxLayout()
    left_vertical.addLayout(pipeline_controls)

    load_pipeline = QPushButton("&Load selected pipeline")
    pipeline_controls.addWidget(load_pipeline)
    save_current_pipeline = QPushButton("&Save current pipeline")
    pipeline_controls.addWidget(save_current_pipeline)
    delete_pipeline = QPushButton("&Delete selected pipeline")
    pipeline_controls.addWidget(delete_pipeline)

    pipeline_model = PipelineModel()
    pipeline_view = PipelineTreeView(pipelines, action_view, rule_view)
    pipeline_view.setModel(pipeline_model)
    pipeline_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    pipeline_view.viewport().setAcceptDrops(True)
    pipeline_view.setDropIndicatorShown(True);
    pipeline_view.setDragEnabled(True)
    pipeline_view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
    pipeline_view.setDragDropOverwriteMode(False)
    pipeline_view.setItemDelegateForColumn(2, PipelineItemDelegate(pipeline_view))
    size_policy = pipeline_view.sizePolicy()
    size_policy.setVerticalStretch(3)
    pipeline_view.setSizePolicy(size_policy)
    left_vertical.addWidget(pipeline_view)

    node_controls = QHBoxLayout()
    left_vertical.addLayout(node_controls)
    delete_node = QPushButton("Remove selected")
    delete_node.clicked.connect(pipeline_view.delete_selected)
    node_controls.addWidget(delete_node)
    add_action = QPushButton("Add A&ction")
    add_action.clicked.connect(pipeline_view.add_action)
    node_controls.addWidget(add_action)
    add_rule = QPushButton("Add &Rule")
    add_rule.clicked.connect(pipeline_view.add_rule)
    node_controls.addWidget(add_rule)

    adding = QHBoxLayout()
    left_vertical.addLayout(adding)
    button_add_group = QPushButton("Add &group")
    button_add_group.clicked.connect(pipeline_view.add_group)
    adding.addWidget(button_add_group)
    button_add_pool = QPushButton("Add &pool")
    button_add_pool.clicked.connect(pipeline_view.add_pool)
    adding.addWidget(button_add_pool)

    pipeline_apply = QHBoxLayout()
    left_vertical.addLayout(pipeline_apply)
    apply_button = QPushButton("&Apply pipeline")
    apply_button.clicked.connect(pipeline_model.trigger_pipeline_apply)
    pipeline_apply.addWidget(apply_button)
    reset_button = QPushButton("&Reset to default")
    reset_button.clicked.connect(
        pipeline_view.trigger_load_default_pipeline)
    pipeline_apply.addWidget(reset_button)
    h.addLayout(left_vertical)

    v = QVBoxLayout()
    v.addWidget(action_view)
    v.addWidget(rule_view)
    h.addLayout(v)

    w = QWidget()
    w.setLayout(h)
    window = MainWindow(w)
    window.show()
    window.resize(1200, 800)

    client_thread = ClientThread()
    client_thread.plugins_listed.connect(action_model.replace_items)
    client_thread.plugins_listed.connect(rule_model.replace_items)
    client_thread.pipeline_fetched.connect(
        pipeline_model.replace_pipeline)

    load_pipeline.clicked.connect(pipeline_view.trigger_load_pipeline)
    save_current_pipeline.clicked.connect(pipeline_view.trigger_save_pipeline)
    delete_pipeline.clicked.connect(pipeline_view.trigger_delete_pipeline)
    pipeline_view.load_pipeline.connect(client_thread.fetch_pipeline)
    pipeline_view.save_pipeline.connect(client_thread.save_pipeline)
    pipeline_view.delete_pipeline.connect(client_thread.delete_pipeline)

    pipeline_model.apply_pipeline.connect(
        client_thread.apply_pipeline)
    client_thread.pipeline_applied.connect(
        window.pipeline_applied)
    client_thread.pipeline_apply_failed.connect(
        window.pipeline_apply_failed)
    client_thread.pipelines_listed.connect(pipelines.addPipelines)
    client_thread.pipeline_save_failed.connect(
        window.pipeline_save_failed)
    client_thread.pipeline_delete_failed.connect(
        window.pipeline_delete_failed)

    client_thread.start()
    app.aboutToQuit.connect(client_thread.quit)

    sys.exit(app.exec())
