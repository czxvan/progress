import sys
import socketio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QLabel
from PyQt5.QtCore import QThread, pyqtSignal

# 创建 SocketIO 客户端
sio = socketio.Client()

class Worker(QThread):
    progress_update = pyqtSignal(int)
    task_cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.task_id = None

    def run(self):
        if not sio.connected:
            try:
                # 连接到 WebSocket 服务器
                sio.connect('http://127.0.0.1:5000')
            except Exception as e:
                print(f"连接失败: {e}")
                return

        sio.emit('start_task', {'empty': 'empty'})

        @sio.on('task_started')
        def handle_started(data):
            self.task_id = data['task_id']

        @sio.on('progress_update')
        def handle_progress(data):
            self.progress_update.emit(data['progress'])

        @sio.on('task_cancelled')
        def handle_cancelled(data):
            self.task_cancelled.emit()

        # # Keep the thread alive and listen for events
        # while True:
        #     sio.sleep(1)  # Prevent busy wait

class ProgressApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = None

    def init_ui(self):
        self.setWindowTitle('WebSocket Progress Bar Example')
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.start_button = QPushButton('Start Task')
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        self.cancel_button = QPushButton('Cancel Task')
        self.cancel_button.clicked.connect(self.cancel_task)
        layout.addWidget(self.cancel_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel('Progress: 0%')
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def start_task(self):
        # 同一时间只允许有一个任务在运行
        if self.worker is None:
            self.worker = Worker()
            self.worker.progress_update.connect(self.update_progress)
            self.worker.task_cancelled.connect(self.on_task_cancelled)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()

    def cancel_task(self):
        if self.worker is not None and self.worker.task_id:
            sio.emit('cancel_task', {'task_id': self.worker.task_id})

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)
        self.status_label.setText(f'Progress: {progress}%')

    def on_task_cancelled(self):
        self.status_label.setText('Task Cancelled')
        self.progress_bar.setValue(0)  # 重置进度条
        self.worker = None  # 重置 worker

    def on_worker_finished(self):
        print('Worker finished, maybe connection failed.')
        self.worker = None  # 重置 worker

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProgressApp()
    window.show()
    sys.exit(app.exec_())