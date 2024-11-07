from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi_socketio import SocketManager
import uuid
import threading
import time
import asyncio

app = FastAPI()
socket_manager = SocketManager(app=app, socketio_path="/ws/socket.io",)


# 存储任务进度
progress = {}
task_running = {}

async def async_long_running_task(task_id):
    for i in range(101):  # 模拟任务进度 0% 到 100%
        if not task_running.get(task_id, False):
            await socket_manager.emit('task_cancelled', {'task_id': task_id}, room=task_id)
            return
        time.sleep(0.1)  # 模拟耗时操作
        progress[task_id] = i  # 更新任务进度
        await socket_manager.emit('progress_update', {'task_id': task_id, 'progress': i}, room=task_id)
    await socket_manager.emit('task_finished', {'task_id': task_id})

def long_running_task(task_id):
    asyncio.run(async_long_running_task(task_id))

@socket_manager.on('start_task')
async def start_task(sid, data):
    task_id = str(uuid.uuid4())  # 为每个任务生成一个唯一的 ID
    progress[task_id] = 0 # 初始化进度
    task_running[task_id] = True  # 标记任务为正在运行
    print(f'Task {task_id} started')

    await socket_manager.enter_room(sid, task_id) # 将连接加入任务 ID 房间
    thread = threading.Thread(target=long_running_task, args=(task_id,))
    thread.start()
    await socket_manager.emit('task_started', {'task_id': task_id}, room=task_id)

@socket_manager.on('cancel_task')
def cancel_task(sid, data):
    task_id = data['task_id']
    if task_id in task_running and task_running[task_id]:
        task_running[task_id] = False # 标记任务为取消
        print(f"Cancelling task: {task_id}")
    elif task_id in task_running:
        print(f"Task {task_id} is already canceled")
    else:
        print(f"Task {task_id} does not exist")

@socket_manager.on('disconnect')
def handle_disconnect(sid):
    print(f'Client disconnected: {sid}')

@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/websocket_fastapi.html", "r") as f:
        return HTMLResponse(f.read())

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("server_fastapi:app", host='127.0.0.1', port=5000, reload=True)