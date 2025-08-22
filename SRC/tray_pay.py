from PyQt6 import QtWidgets


class Tray(QtWidgets.QSystemTrayIcon):
    def __init__(self, app, on_quit, actions: dict[str, callable]):
        icon = app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(icon)
        self.setToolTip("Hotkey watcher")
        menu = QtWidgets.QMenu()
        for title, cb in actions.items():
            menu.addAction(title, cb)
        menu.addSeparator()
        menu.addAction("Выход", on_quit)
        self.setContextMenu(menu)
        self.show()
