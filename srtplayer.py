from os.path import expanduser
from pathlib import PurePath
import sys
from PySide import QtGui, QtCore
from srtplayer_base import SrtPlayer


class PlayerWidget(QtGui.QWidget):
    _SLIDER_UPDATE_TIME = 10
    _WINDOW_TITLE = "SrtPlayer"

    def __init__(self, window):
        super(PlayerWidget, self).__init__()
        self._window = window
        self.player = SrtPlayer()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        open_button = QtGui.QPushButton("Open")
        open_button.clicked.connect(self.show_open_dialog)

        self._play_pause_button = play_pause_button = QtGui.QPushButton("Play/Pause")
        play_pause_button.setEnabled(self.player.loaded)
        play_pause_button.clicked.connect(self.play_pause_event)
        self._text_field = text_field = QtGui.QTextEdit()
        text_field.setReadOnly(True)
        # text_field.setFont(QtGui.QFont("Helvetica", 14))
        self.player.text_changed.connect(self.update_text)

        self._slider = slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimumWidth(300)
        slider.sliderReleased.connect(self.set_time_from_slider)
        slider.sliderPressed.connect(lambda: self._timer_slider.stop())
        slider.setEnabled(self.player.loaded)
        self._timer_slider = timer_slider = QtCore.QTimer()
        timer_slider.timeout.connect(self.update_slider)
        timer_slider.start(self._SLIDER_UPDATE_TIME)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(open_button, 0, 0)
        grid.addWidget(play_pause_button, 0, 1)
        grid.addWidget(slider, 0, 2, 1, 3)
        grid.addWidget(text_field, 1, 0, 2, 5)

        self.update_status_bar()
        timer_status_bar = QtCore.QTimer()
        timer_status_bar.timeout.connect(self.update_status_bar)
        timer_status_bar.start(500)

        self.setLayout(grid)

        self._window.setWindowTitle(self._WINDOW_TITLE)


    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        file_name = e.mimeData().urls()[0].toLocalFile()
        self.open_file(file_name)

    @QtCore.Slot(str)
    def update_text(self, text):
        self._text_field.setPlainText(text)

    def update_slider(self):
        if self.player.loaded:
            self._slider.setValue(int(round(self.player.time / self.player.length * (
                self._slider.maximum() - self._slider.minimum()) + self._slider.minimum())))

    def set_time_from_slider(self):
        if self.player.loaded:
            time = (self._slider.value() - self._slider.minimum()) / (
                self._slider.maximum() - self._slider.minimum()) * self.player.length
            self.player.time = time
        self._timer_slider.start(self._SLIDER_UPDATE_TIME)
        self.update_status_bar()

    def show_open_dialog(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self, "Open file", expanduser("~"),
                                                      "Wave files (*.wav);;SubRip files (*.srt)")[0]
        self.open_file(file_name)

    def open_file(self, file_name):
        if not file_name.strip():
            return
        path = PurePath(file_name)
        if path.suffix == ".srt":
            try:
                self.player.load_subs(file_name)
            except ValueError as e:
                self._text_field.setPlainText(str(e))
        else:
            try:
                self.player.open(file_name)
            except Exception as e:
                self._text_field.setPlainText(str(e))
                self._window.setWindowTitle(self._WINDOW_TITLE + " - " + "Error")
            else:
                self._text_field.setPlainText("")
                self._window.setWindowTitle(self._WINDOW_TITLE + " - " + file_name)
        self._play_pause_button.setEnabled(self.player.loaded)
        self._slider.setEnabled(self.player.loaded)
        self.update_status_bar()

    def update_status_bar(self):
        status_bar = self._window.statusBar()
        ms = self.player.time
        ms /= 1000
        total_seconds = int(ms)
        hours = total_seconds // 3600
        total_seconds -= hours * 60 * 60
        minutes = total_seconds // 60
        total_seconds -= minutes * 60

        if self.player.loaded:
            if self.player.playing:
                message = "Playing "
            else:
                message = "Paused "
            if hours == 0:
                message += self.str_with_zeros(minutes, 2) + ":" + self.str_with_zeros(total_seconds, 2)
            else:
                message += str(hours) + ":" + self.str_with_zeros(minutes, 2) + ":" + self.str_with_zeros(total_seconds, 2)
        else:
            message = "Not loaded"

        status_bar.showMessage(message)

    def play_pause_event(self):
        self.player.play_pause()
        self.update_status_bar()

    @staticmethod
    def str_with_zeros(number, length):
        number_str = str(number)
        number_str = "0" * (length - len(number_str)) + number_str
        return number_str


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self._widget = PlayerWidget(self)
        self.setCentralWidget(self._widget)
        self.show()

    def closeEvent(self, event):
        self._widget.player.close()
        event.accept()


def main():
    app = QtGui.QApplication(sys.argv)
    MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()



