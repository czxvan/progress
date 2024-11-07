from flask import Flask, render_template
import time
import threading
from flask_socketio import SocketIO, join_room
import uuid

app = Flask(__name__)
socketio = SocketIO(app, path='/ws/socket.io')

# 存储任务进度
progress = {}
task_running = {}

def long_running_task(task_id):
    for i in range(101):  # 模拟任务进度 0% 到 100%
        if not task_running.get(task_id, False):
            socketio.emit('task_cancelled', {'task_id': task_id}, room=task_id)
            return
        time.sleep(0.1)  # 模拟耗时操作
        progress[task_id] = i  # 更新任务进度
        socketio.emit('progress_update', {'task_id': task_id, 'progress': i}, room=task_id)
    socketio.emit('task_finished', {'task_id': task_id})

@socketio.on('start_task')
def start_task(data):
    # 每次start_task都会创建新的任务，所以需要前端控制真正应当创建任务的时机
    task_id = str(uuid.uuid4())  # 为每个任务生成一个唯一的 ID
    progress[task_id] = 0  # 初始化进度
    task_running[task_id] = True  # 标记任务为正在运行
    print(f"Starting task: {task_id}")

    join_room(task_id)  # 将连接加入任务 ID 房间
    thread = threading.Thread(target=long_running_task, args=(task_id,))
    thread.start()
    socketio.emit('task_started', {'task_id': task_id}, room=task_id) # 向客户端返回任务 ID

@socketio.on('cancel_task')
def cancel_task(data):
    task_id = data['task_id']
    task_running[task_id] = False  # 标记任务为取消
    print(f"Cancelling task: {task_id}")

@app.route('/')
def index():
    return render_template('websocket.html')

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)