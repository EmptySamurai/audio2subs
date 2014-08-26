__author__ = 'emptysamurai'

from PySide import QtGui, QtCore
from srtplayer.subplayer import SubPlayer
from os.path import expanduser
from pathlib import PurePath
import sys


class Player(QtGui.QWidget):
    _SLIDER_UPDATE_TIME = 10

    def __init__(self):
        super(Player, self).__init__()
        self._player = SubPlayer()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        open_button = QtGui.QPushButton("Open")
        open_button.clicked.connect(self.show_open_dialog)

        self._play_pause_button = play_pause_button = QtGui.QPushButton("Play/Pause")
        play_pause_button.setEnabled(self._player.loaded)
        play_pause_button.clicked.connect(self._player.play_pause)
        self._text_field = text_field = QtGui.QTextEdit()
        text_field.setReadOnly(True)
        self._player.text_changed.connect(self.update_text)

        self._slider = slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimumWidth(300)
        slider.sliderReleased.connect(self.set_time_from_slider)
        slider.sliderPressed.connect(lambda: self._timer_slider.stop())
        slider.setEnabled(self._player.loaded)
        self._timer_slider = timer_slider = QtCore.QTimer()
        timer_slider.timeout.connect(self.update_slider)
        timer_slider.start(self._SLIDER_UPDATE_TIME)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(open_button, 0, 0)
        grid.addWidget(play_pause_button, 0, 1)
        grid.addWidget(slider, 0, 2, 1, 3)
        grid.addWidget(text_field, 1, 0, 2, 5)

        self.setLayout(grid)

        self.setWindowTitle('SrtPlayer')
        self.show()

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
        if self._player.loaded:
            self._slider.setValue(int(round(self._player.time / self._player.length * (
                self._slider.maximum() - self._slider.minimum()) + self._slider.minimum())))

    def set_time_from_slider(self):
        if self._player.loaded:
            time = (self._slider.value() - self._slider.minimum()) / (
                self._slider.maximum() - self._slider.minimum()) * self._player.length
            self._player.time = time
        self._timer_slider.start(self._SLIDER_UPDATE_TIME)

    def show_open_dialog(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self, 'Open file', expanduser("~"), "*.wav")[0]
        self.open_file(file_name)

    def open_file(self, file_name):
        if not file_name.strip():
            return
        path = PurePath(file_name)
        if path.suffix == ".srt":
            try:
                self._player.load_subs(file_name)
            except ValueError as e:
                self._text_field.setPlainText(str(e))
        else:
            try:
                self._player.open(file_name)
            except ValueError as e:
                self._text_field.setPlainText(str(e))
                self.setWindowTitle("SrtPlayer - " + "Error")
            else:
                self._text_field.setPlainText("")
                self.setWindowTitle("SrtPlayer - " + file_name)
        self._play_pause_button.setEnabled(self._player.loaded)
        self._slider.setEnabled(self._player.loaded)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Player()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()



