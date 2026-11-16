import threading
import queue
import tkinter as tk
from parking import Status
from config import NUM_BAYS, CAMERA_POLL_MS, SIMULATION


class ParkingUI:
    def __init__(self, root, controller):
        self.root = root
        self.ctrl = controller
        self.busy = False
        self.results = queue.Queue()
        self.active_slot = None
        self.message = tk.StringVar(value='주차칸을 선택하세요')
        root.title('ParkLocker')
        root.geometry('800x480')
        root.minsize(800, 480)
        root.configure(bg='#f5f7fa')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.header = tk.Label(root, text='ParkLocker  |  주차 현황', font=('Arial', 25, 'bold'), bg='#f5f7fa')
        self.header.pack(pady=(18, 8))
        self.grid_frame = tk.Frame(root, bg='#f5f7fa')
        self.grid_frame.pack(fill='both', expand=True, padx=20)
        self.buttons = {}
        for number in range(1, NUM_BAYS + 1):
            button = tk.Button(self.grid_frame, font=('Arial', 21, 'bold'), relief='flat',
                               command=lambda n=number: self.select(n))
            button.pack(side='left', fill='both', expand=True, padx=8, pady=12)
            self.buttons[number] = button
        self.footer = tk.Frame(root, bg='#f5f7fa')
        self.footer.pack(fill='x', padx=24, pady=(0, 12))
        tk.Label(self.footer, textvariable=self.message, bg='#f5f7fa',
                 font=('Arial', 15), wraplength=740).pack()
        self.action = tk.Frame(root, bg='#f5f7fa')
        self.action.pack(fill='x', padx=24, pady=(0, 14))
        self.refresh()
        self.poll_camera()
        self._check_results()

    def refresh(self):
        labels = {Status.EMPTY: '빈 칸', Status.WAITING: '등록 대기',
                  Status.REGISTERED: '주차중', Status.EXITING: '출차중'}
        colors = {Status.EMPTY: '#d9f0d6', Status.WAITING: '#ffe3aa',
                  Status.REGISTERED: '#f6cece', Status.EXITING: '#dce5fc'}
        for n, button in self.buttons.items():
            status = self.ctrl.parking.bays[n].status
            button.config(text=f'{n}번\n{labels[status]}', bg=colors[status],
                          state='disabled' if self.busy else 'normal')
        self.root.after(500, self.refresh)

    def poll_camera(self):
        # Camera inference should eventually be moved to a background worker.
        # For now this is the lightweight stub from camera.py.
        if not self.busy:
            ok = self.ctrl.update_camera()
            if not ok and self.ctrl.last_error:
                self.message.set(self.ctrl.last_error)
        self.root.after(CAMERA_POLL_MS, self.poll_camera)

    def _clear_actions(self):
        for widget in self.action.winfo_children():
            widget.destroy()

    def _action_button(self, title, callback):
        tk.Button(self.action, text=title, font=('Arial', 16, 'bold'), height=2,
                  command=callback).pack(side='left', expand=True, fill='x', padx=6)

    def select(self, number):
        if self.busy:
            return
        self.active_slot = number
        self._clear_actions()
        bay = self.ctrl.parking.get_bay(number)
        if bay.status == Status.EMPTY:
            self.message.set(f'{number}번 칸은 비어 있습니다.')
        elif bay.status == Status.WAITING:
            self.message.set(f'{number}번: 얼굴과 지문을 차례로 등록합니다.')
            self._action_button('등록 시작', lambda: self._run('register', number))
        elif bay.status == Status.REGISTERED:
            self.message.set(f'{number}번: 얼굴과 지문을 차례로 인증합니다.')
            self._action_button('출차 인증', lambda: self._run('authenticate', number))
        else:
            self.message.set(f'{number}번: 출차 승인됨. 차량이 사라지면 완료됩니다.')
            self._action_button('돌아가기', self._clear_actions)

    def _run(self, operation, number):
        if self.busy:
            return
        self.busy = True
        self._clear_actions()
        self.message.set('등록 중입니다. 카메라를 바라보고 지문 센서를 사용하세요.' if operation == 'register'
                         else '인증 중입니다. 카메라를 바라보고 지문 센서를 사용하세요.')

        def work():
            try:
                result = getattr(self.ctrl, operation)(number)
                error = self.ctrl.last_error
            except Exception as exc:
                result, error = False, str(exc)
            self.results.put((operation, number, result, error))

        threading.Thread(target=work, daemon=True).start()

    def _check_results(self):
        try:
            while True:
                self._finished(*self.results.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self._check_results)

    def _finished(self, operation, number, result, error):
        self.busy = False
        if result:
            self.message.set('등록 완료! 출차 시 해당 칸을 선택하세요.' if operation == 'register'
                             else '인증 성공! 출구 차단기가 열렸습니다.')
        else:
            self.message.set(error or '처리에 실패했습니다. 다시 시도해 주세요.')
        self._clear_actions()
        if not result:
            self._action_button('다시 시도', lambda: self._run(operation, number))
        self._action_button('닫기', self._clear_actions)

    def close(self):
        if self.busy:
            self.message.set('작업이 진행 중입니다. 완료 후 종료하세요.')
            return
        self.root.destroy()
