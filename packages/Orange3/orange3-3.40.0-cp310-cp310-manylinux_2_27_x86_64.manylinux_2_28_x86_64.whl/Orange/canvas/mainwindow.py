from orangecanvas.localization.si import plsi, plsi_sz, z_besedo
from orangecanvas.localization import Translator  # pylint: disable=wrong-import-order
_tr = Translator("Orange", "biolab.si", "Orange")
del Translator
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import (
    QFormLayout, QCheckBox, QLineEdit, QWidget, QVBoxLayout, QLabel
)
from orangecanvas.application.settings import UserSettingsDialog, FormLayout
from orangecanvas.document.interactions import PluginDropHandler
from orangecanvas.document.usagestatistics import UsageStatistics
from orangecanvas.utils.overlay import NotificationOverlay

from orangewidget.workflow.mainwindow import OWCanvasMainWindow


class OUserSettingsDialog(UserSettingsDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        w = self.widget(0)  # 'General' tab
        layout = w.layout()
        assert isinstance(layout, QFormLayout)
        cb = QCheckBox(self.tr(_tr.m[13, "Automatically check for updates"]))
        cb.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        layout.addRow(_tr.m[14, "Updates"], cb)
        self.bind(cb, "checked", "startup/check-updates")

        # Reporting Tab
        tab = QWidget()
        self.addTab(tab, self.tr(_tr.m[15, "Reporting"]),
                    toolTip=_tr.m[16, "Settings related to reporting"])

        form = FormLayout()
        line_edit_mid = QLineEdit()
        self.bind(line_edit_mid, "text", "reporting/machine-id")
        form.addRow(_tr.m[17, "Machine ID:"], line_edit_mid)

        box = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        cb1 = QCheckBox(
            self.tr(_tr.m[18, "Share"]),
            toolTip=self.tr(
                _tr.m[19, "Share anonymous usage statistics to improve Orange"])
        )
        self.bind(cb1, "checked", "reporting/send-statistics")
        cb1.clicked.connect(UsageStatistics.set_enabled)
        layout.addWidget(cb1)
        box.setLayout(layout)
        form.addRow(self.tr(_tr.m[20, "Anonymous Statistics"]), box)
        label = QLabel(("<a " + ("href=\"https://orange.biolab.si/statistics-more-info\">" + (_tr.m[21, "More info..."] + "</a>"))))
        label.setOpenExternalLinks(True)
        form.addRow(self.tr(""), label)

        tab.setLayout(form)

        # Notifications Tab
        tab = QWidget()
        self.addTab(tab, self.tr(_tr.m[22, "Notifications"]),
                    toolTip=_tr.m[23, "Settings related to notifications"])

        form = FormLayout()

        box = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        cb = QCheckBox(
            self.tr(_tr.m[24, "Enable notifications"]), self,
            toolTip=_tr.m[25, "Pull and display a notification feed."]
        )
        self.bind(cb, "checked", "notifications/check-notifications")

        layout.addWidget(cb)
        box.setLayout(layout)
        form.addRow(self.tr(_tr.m[26, "On startup"]), box)

        notifs = QWidget(self, objectName="notifications-group")
        notifs.setLayout(QVBoxLayout())
        notifs.layout().setContentsMargins(0, 0, 0, 0)

        cb1 = QCheckBox(self.tr(_tr.m[27, "Announcements"]), self,
                        toolTip=(_tr.m[28, "Show notifications about Biolab announcements.\n"] + (_tr.m[29, "This entails events and courses hosted by the developers of "] + _tr.m[30, "Orange."])))

        cb2 = QCheckBox(self.tr(_tr.m[31, "Blog posts"]), self,
                        toolTip=(_tr.m[32, "Show notifications about blog posts.\n"] + _tr.m[33, "We'll only send you the highlights."]))
        cb3 = QCheckBox(self.tr(_tr.m[34, "New features"]), self,
                        toolTip=(_tr.m[35, "Show notifications about new features in Orange when a new "] + (_tr.m[36, "version is downloaded and installed,\n"] + _tr.m[37, "should the new version entail notable updates."])))

        self.bind(cb1, "checked", "notifications/announcements")
        self.bind(cb2, "checked", "notifications/blog")
        self.bind(cb3, "checked", "notifications/new-features")

        notifs.layout().addWidget(cb1)
        notifs.layout().addWidget(cb2)
        notifs.layout().addWidget(cb3)

        form.addRow(self.tr(_tr.m[38, "Show notifications about"]), notifs)
        tab.setLayout(form)


class MainWindow(OWCanvasMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_overlay = NotificationOverlay(self.scheme_widget)
        self.notification_server = None
        self.scheme_widget.setDropHandlers([
            PluginDropHandler("orange.canvas.drophandler")
        ])

    def open_canvas_settings(self):
        # type: () -> None
        """Reimplemented."""
        dlg = OUserSettingsDialog(self, windowTitle=self.tr(_tr.m[39, "Preferences"]))
        dlg.show()
        status = dlg.exec()
        if status == 0:
            self.user_preferences_changed_notify_all()

    def set_notification_server(self, notif_server):
        self.notification_server = notif_server

        # populate notification overlay with current notifications
        for notif in self.notification_server.getNotificationQueue():
            self.notification_overlay.addNotification(notif)

        notif_server.newNotification.connect(self.notification_overlay.addNotification)
        notif_server.nextNotification.connect(self.notification_overlay.nextWidget)

    def create_new_window(self):  # type: () -> CanvasMainWindow
        window = super().create_new_window()
        window.set_notification_server(self.notification_server)
        return window
