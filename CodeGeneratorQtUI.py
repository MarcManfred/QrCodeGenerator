import sys
import traceback
from PySide6.QtCore import QRunnable, QThreadPool, QSize, QDir, QByteArray, QBuffer, QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QColorDialog, QListView, QProgressBar, QStatusBar, QLabel
from PySide6.QtGui import QPixmap, QImage
from CodeGenerator import QrCodeGenerator
from PIL.ImageQt import ImageQt
from zipfile import ZipFile
from urllib.parse import urlparse


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__image_path = None
        self.__color = None
        self.__threadpool = QThreadPool()

        preview_label = QLabel("Preview")
        self.preview_qr = QLabel()
        self.set_preview_qr()
        reset_preview = QPushButton('Reset Preview')
        reset_preview.clicked.connect(self.reset_preview_qr)

        central_widget = QWidget()
        layout = QVBoxLayout()

        statusbar = QStatusBar()
        self.progress = QProgressBar()
        statusbar.addWidget(self.progress)
        self.progress.close()
        self.setStatusBar(statusbar)

        add_widget = QWidget()
        add_layout = QHBoxLayout()

        self.__enter_qr = QLineEdit()
        add_qr = QPushButton("Add")
        add_qr.clicked.connect(self.add_qr_entry)
        self.__list_qrs = QListWidget(central_widget)
        self.__list_qrs.itemClicked.connect(self.remove_qr)
        self.__get_qr = QPushButton("Create QR Code")
        self.__get_qr.clicked.connect(self.get_qrs)
        self.__get_qr.setEnabled(False)
        open_image_browser = QPushButton("Select Image")
        open_image_browser.clicked.connect(self.select_image)
        open_color_picker = QPushButton("Pick Color")
        open_color_picker.clicked.connect(self.pick_color)

        add_layout.addWidget(self.__enter_qr)
        add_layout.addWidget(add_qr)

        add_widget.setLayout(add_layout)

        self.qr_area = QrList(central_widget)

        self.__save_all_qrs = QPushButton("Save all")
        self.__save_all_qrs.clicked.connect(self.save_all)
        self.__save_all_qrs.setEnabled(False)

        layout.addWidget(add_widget)
        layout.addWidget(self.__list_qrs)
        layout.addWidget(self.__get_qr)
        layout.addWidget(open_image_browser)
        layout.addWidget(open_color_picker)
        layout.addWidget(
            preview_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(
            self.preview_qr, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(reset_preview)
        layout.addWidget(self.qr_area)
        layout.addWidget(self.__save_all_qrs)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def add_qr_entry(self):
        if self.__enter_qr.text():
            self.__list_qrs.addItem(QListWidgetItem(self.__enter_qr.text()))
            self.__get_qr.setEnabled(True)
            self.__enter_qr.clear()

    def get_qrs(self):

        worker = QR_Worker(self.create_qr_code)

        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.__threadpool.start(worker)

    def thread_complete(self):
        print('Thread complete')

    def progress_fn(self, n):
        print(f'{n}% done')
        self.progress.setValue(n)

    def remove_qr(self):
        current_item = self.__list_qrs.currentIndex()
        # print(current_item)
        if current_item:
            self.__list_qrs.takeItem(current_item.row())
            if self.__list_qrs.count() == 0:
                self.__get_qr.setEnabled(False)

    def select_image(self):
        self.__image_path, _ = QFileDialog.getOpenFileName(self,
                                                           "Open Image", "", "Image Files (*.png *.jpg )")
        self.set_preview_qr()
        # print(self.__image_path)

    def pick_color(self):
        self.__color = QColorDialog.getColor(
            "black", self, title="Pick qr code color").name()
        self.set_preview_qr()
        # print(self.__color)

    def set_preview_qr(self):
        code_generator = QrCodeGenerator(
            url="Test", image_path=self.__image_path, qr_color=self.__color)
        gen = code_generator.generate_code()
        qr = ImageQt(gen)
        pixmap = QPixmap(qr).scaledToWidth(100)
        self.preview_qr.setPixmap(pixmap)

    def reset_preview_qr(self):
        self.__image_path = None
        self.__color = None
        self.set_preview_qr()

    def create_qr_code(self, progress_callback):
        self.progress.reset()
        self.progress.show()
        qi = [self.__list_qrs.item(x).text()
              for x in range(self.__list_qrs.count())]
        for i, q in enumerate(qi):
            code_generator = QrCodeGenerator(
                url=q, image_path=self.__image_path, qr_color=self.__color)
            gen = code_generator.generate_code()
            qr_code = ImageQt(gen)
            url = urlparse(q)
            title = url.netloc.split(".")[0][:10]

            if title == "":
                title = f'Qr_{i+1}'

            item = QrListItem(qr_code, title)
            progress_callback.emit(i * 100/len(qi))
            self.qr_area.addItem(item)

        if self.qr_area.count() > 0:
            self.__save_all_qrs.setEnabled(True)

        self.__list_qrs.clear()
        self.progress.close()

    def save_all(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save All QR Codes", "", "Zip Files (*.zip)")

        if filename:
            with ZipFile(filename, 'w') as zip_file:
                for i in range(self.qr_area.count()):
                    qr_item = self.qr_area.item(i)
                    qr_filename = f"qr_{i+1}.png"

                    if isinstance(qr_item, QrListItem):

                        ba = QByteArray()
                        buff = QBuffer(ba)
                        ok = qr_item.qix.save(buff, "PNG")
                        assert ok

                        zip_file.writestr(qr_filename, ba.data())
            self.qr_area.clear()
            self.reset_preview_qr()


class QR_Worker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super(QR_Worker, self).__init__(*args, **kwargs)
        self.signals = QR_Worker_Signals()
        self.func = func
        self.args = args
        self.kwargs = kwargs

        self.kwargs['progress_callback'] = self.signals.progress

    @Slot(int, result=int)
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as _e:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class QR_Worker_Signals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)


class QrListItem(QListWidgetItem):
    def __init__(self, code: ImageQt, title: str):
        super(QrListItem, self).__init__()
        self.code = code
        self.qix = QPixmap.fromImage(code)
        self.setIcon(self.qix)
        self.setText(title)


class QrList(QListWidget):
    def __init__(self, parent: QWidget):
        super(QrList, self).__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setMovement(QListView.Movement.Static)
        self.itemDoubleClicked.connect(self.save_qr)
        self.setIconSize(QSize(100, 100))

    def save_qr(self):
        current_item = self.currentItem()
        current_index = self.currentIndex()
        if isinstance(current_item, QrListItem):
            im = QImage(current_item.code)
            file_name, _ = QFileDialog.getSaveFileName(self,
                                                       "Save QrCode", f"{current_item.text()}.png", "Image Files (*.png *.jpg)")

            if file_name:
                full_path = QDir.toNativeSeparators(file_name)
                # print(full_path)
                if im.save(full_path):
                    print("success")
                    self.takeItem(current_index.row())
                else:
                    print("error")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()

    app.exec()
