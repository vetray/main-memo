"""메모 화면보호기 - 전체화면에서 메모가 튕겨 다니는 화면보호기 겸 메모장."""
import random
import tkinter as tk
from memo import Memo

MAX_LEN = 30
BG_COLOR = "#000000"


class ScreenSaverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("메모 화면보호기")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg=BG_COLOR)

        self.width = root.winfo_screenwidth()
        self.height = root.winfo_screenheight()

        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.memos = []
        self.paused = False
        self.mode = "NORMAL"  # NORMAL | TYPING | CONFIRM

        self.input_frame = self.input_window_id = self.input_entry = None
        self.error_text_id = self.error_timer = None
        self.confirm_frame = self.confirm_window_id = self.confirm_target = None

        self.hint_id = self.canvas.create_text(
            self.width // 2, self.height - 28,
            text="N: 메모 추가    Space: 일시정지/재생    Esc: 종료",
            fill="#555555", font=("맑은 고딕", 11),
        )

        self.root.bind("<Key>", self.on_global_key)
        self.show_input(first=True)
        self.game_loop()

    # ---------- 메모 입력 UI ----------

    def show_input(self, first=False):
        if self.mode == "TYPING":
            return
        self.mode = "TYPING"

        self.input_frame = tk.Frame(self.canvas, bg="#1a1a1a", padx=24, pady=18, bd=1, relief="solid")
        title = "첫 메모를 적어주세요 (최대 30자)" if first else "새 메모를 적어주세요 (최대 30자)"
        tk.Label(self.input_frame, text=title, bg="#1a1a1a", fg="#e0e0e0", font=("맑은 고딕", 12)).pack(pady=(0, 10))

        self.input_entry = tk.Entry(
            self.input_frame, font=("맑은 고딕", 14), width=30, justify="center",
            bg="#2a2a2a", fg="#ffffff", insertbackground="#ffffff", relief="flat",
        )
        self.input_entry.pack(ipady=4)
        self.input_entry.focus_set()

        tk.Label(self.input_frame, text="Enter: 추가  |  Esc: 취소", bg="#1a1a1a", fg="#777777", font=("맑은 고딕", 9)).pack(pady=(8, 0))
        self.input_entry.bind("<Return>", lambda e: self.submit_input())
        self.input_entry.bind("<Escape>", lambda e: (self.hide_input(), "break")[1])

        self.input_window_id = self.canvas.create_window(self.width // 2, self.height // 2, window=self.input_frame)

    def hide_input(self):
        if self.input_frame is not None:
            self.input_frame.destroy()
            self.input_frame = None
        if self.input_window_id is not None:
            self.canvas.delete(self.input_window_id)
            self.input_window_id = None
        self.input_entry = None
        self._clear_error()
        self.mode = "NORMAL"
        self.root.focus_set()

    def submit_input(self):
        if not self.input_entry:
            return "break"
        text = self.input_entry.get().strip()
        if not text or len(text) > MAX_LEN:
            self.show_error("1~30자 이내로 입력해주세요")
            return "break"
        self.add_memo(text)
        self.hide_input()
        return "break"

    def show_error(self, message):
        self._clear_error()
        self.error_text_id = self.canvas.create_text(
            self.width // 2, self.height // 2 + 80,
            text=message, fill="#ff6b6b", font=("맑은 고딕", 12, "bold"),
        )
        self.error_timer = self.root.after(1600, self._clear_error)

    def _clear_error(self):
        if self.error_text_id is not None:
            self.canvas.delete(self.error_text_id)
            self.error_text_id = None
        if self.error_timer is not None:
            self.root.after_cancel(self.error_timer)
            self.error_timer = None

    # ---------- 메모 삭제 확인 대화상자 ----------

    def show_confirm(self, memo):
        if self.mode != "NORMAL":
            return
        self.mode = "CONFIRM"
        self.confirm_target = memo

        self.confirm_frame = tk.Frame(self.canvas, bg="#1e1e1e", padx=24, pady=18, bd=1, relief="solid")
        tk.Label(self.confirm_frame, text=f'"{memo.text}"\n이 메모를 지울까요?', bg="#1e1e1e", fg="#ffffff",
                 font=("맑은 고딕", 13, "bold"), justify="center").pack(pady=(0, 14))

        btns = tk.Frame(self.confirm_frame, bg="#1e1e1e")
        btns.pack()
        tk.Button(btns, text="확인 (Enter)", bg="#e74c3c", fg="#ffffff", font=("맑은 고딕", 10, "bold"),
                  relief="flat", padx=10, pady=3, command=self.confirm_delete).pack(side="left", padx=8)
        tk.Button(btns, text="취소 (Esc)", bg="#3e3e3e", fg="#ffffff", font=("맑은 고딕", 10),
                  relief="flat", padx=10, pady=3, command=self.cancel_confirm).pack(side="left", padx=8)

        self.confirm_window_id = self.canvas.create_window(self.width // 2, self.height // 2, window=self.confirm_frame)

    def confirm_delete(self):
        if self.confirm_target in self.memos:
            self.memos.remove(self.confirm_target)
            self.confirm_target.delete()
        self.cancel_confirm()

    def cancel_confirm(self):
        if self.confirm_frame is not None:
            self.confirm_frame.destroy()
            self.confirm_frame = None
        if self.confirm_window_id is not None:
            self.canvas.delete(self.confirm_window_id)
            self.confirm_window_id = None
        self.confirm_target = None
        self.mode = "NORMAL"
        self.root.focus_set()

    # ---------- 메모 물체 관리 ----------

    def add_memo(self, text):
        mx = min(200, max(50, self.width // 4))
        my = min(150, max(50, self.height // 4))
        x = random.randint(mx, max(mx + 10, self.width - mx))
        y = random.randint(my, max(my + 10, self.height - my))
        memo = Memo(self.canvas, text, x, y, self.width, self.height)
        for item_id in (memo.rect_id, memo.text_id):
            self.canvas.tag_bind(item_id, "<Button-1>", lambda e, m=memo: self.show_confirm(m))
            self.canvas.tag_bind(item_id, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(item_id, "<Leave>", lambda e: self.canvas.config(cursor=""))
        self.memos.append(memo)

    # ---------- 키보드 이벤트 ----------

    def on_global_key(self, event):
        if self.mode == "NORMAL":
            if event.keysym in ("n", "N") or event.char in ("n", "N", "ㅜ") or event.keycode == 78:
                self.show_input(first=False)
            elif event.keysym == "space" or event.char == " ":
                self.paused = not self.paused
            elif event.keysym == "Escape":
                self.root.destroy()
        elif self.mode == "CONFIRM":
            if event.keysym in ("Return", "y", "Y") or event.char in ("y", "Y", "ㅛ"):
                self.confirm_delete()
            elif event.keysym in ("Escape", "n", "N") or event.char in ("n", "N", "ㅜ"):
                self.cancel_confirm()

    # ---------- 게임 루프 ----------

    def game_loop(self):
        if self.mode == "NORMAL" and not self.paused:
            for memo in self.memos:
                memo.step()
            n = len(self.memos)
            for i in range(n):
                for j in range(i + 1, n):
                    self.memos[i].bounce_with(self.memos[j])
        self.root.after(30, self.game_loop)


def main():
    root = tk.Tk()
    ScreenSaverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
