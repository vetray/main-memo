"""화면 위를 튕기며 돌아다니는 메모 물체 모듈."""
import random

COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#9b59b6",
    "#e67e22", "#1abc9c", "#e84393", "#0984e3",
]
PADDING = 14
MIN_SPEED = 2
MAX_SPEED = 5


def random_velocity():
    dx = random.choice([-1, 1]) * random.randint(MIN_SPEED, MAX_SPEED)
    dy = random.choice([-1, 1]) * random.randint(MIN_SPEED, MAX_SPEED)
    return dx, dy


class Memo:
    """캔버스 위의 사각형(배경) + 텍스트로 이루어진 튕기는 메모 물체."""

    def __init__(self, canvas, text, x, y, canvas_width, canvas_height):
        self.canvas = canvas
        self.text = text
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.dx, self.dy = random_velocity()
        self.color = random.choice(COLORS)

        self.text_id = canvas.create_text(
            x, y, text=text, fill="#ffffff",
            font=("맑은 고딕", 13, "bold"), justify="center", width=220,
        )
        tx1, ty1, tx2, ty2 = canvas.bbox(self.text_id)
        self.rect_id = canvas.create_rectangle(
            tx1 - PADDING, ty1 - PADDING, tx2 + PADDING, ty2 + PADDING,
            fill=self.color, outline="", width=0,
        )
        canvas.tag_raise(self.text_id, self.rect_id)
        self._clamp_into_bounds()

    def move(self, dx, dy):
        self.canvas.move(self.rect_id, dx, dy)
        self.canvas.move(self.text_id, dx, dy)

    def _clamp_into_bounds(self):
        bbox = self.canvas.bbox(self.rect_id)
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        mx = -x1 if x1 < 0 else (self.canvas_width - x2 if x2 > self.canvas_width else 0)
        my = -y1 if y1 < 0 else (self.canvas_height - y2 if y2 > self.canvas_height else 0)
        if mx or my:
            self.move(mx, my)

    def change_color(self):
        candidates = [c for c in COLORS if c != self.color]
        self.color = random.choice(candidates)
        self.canvas.itemconfig(self.rect_id, fill=self.color)

    def step(self):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw > 100: self.canvas_width = cw
        if ch > 100: self.canvas_height = ch

        self.move(self.dx, self.dy)
        bbox = self.canvas.bbox(self.rect_id)
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        bounced = False

        if x1 <= 0:
            self.move(-x1, 0)
            self.dx = abs(self.dx)
            bounced = True
        elif x2 >= self.canvas_width:
            self.move(self.canvas_width - x2, 0)
            self.dx = -abs(self.dx)
            bounced = True

        if y1 <= 0:
            self.move(0, -y1)
            self.dy = abs(self.dy)
            bounced = True
        elif y2 >= self.canvas_height:
            self.move(0, self.canvas_height - y2)
            self.dy = -abs(self.dy)
            bounced = True

        if bounced:
            self.change_color()

    def bounce_with(self, other):
        """두 메모 물체가 부딪혔을 때 서로 튕겨 나가도록 처리."""
        b1, b2 = self.canvas.bbox(self.rect_id), self.canvas.bbox(other.rect_id)
        if not b1 or not b2:
            return
        if b1[0] >= b2[2] or b1[2] <= b2[0] or b1[1] >= b2[3] or b1[3] <= b2[1]:
            return

        c1x, c1y = (b1[0] + b1[2]) / 2, (b1[1] + b1[3]) / 2
        c2x, c2y = (b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2
        ox = ((b1[2] - b1[0]) + (b2[2] - b2[0])) / 2 - abs(c1x - c2x)
        oy = ((b1[3] - b1[1]) + (b2[3] - b2[1])) / 2 - abs(c1y - c2y)
        if ox <= 0 or oy <= 0:
            return

        if ox < oy:
            shift = ox / 2 + 1
            if c1x < c2x:
                self.dx, other.dx = -abs(self.dx), abs(other.dx)
                self.move(-shift, 0)
                other.move(shift, 0)
            else:
                self.dx, other.dx = abs(self.dx), -abs(other.dx)
                self.move(shift, 0)
                other.move(-shift, 0)
        else:
            shift = oy / 2 + 1
            if c1y < c2y:
                self.dy, other.dy = -abs(self.dy), abs(other.dy)
                self.move(0, -shift)
                other.move(0, shift)
            else:
                self.dy, other.dy = abs(self.dy), -abs(other.dy)
                self.move(0, shift)
                other.move(0, -shift)

        self._clamp_into_bounds()
        other._clamp_into_bounds()
        self.change_color()
        other.change_color()

    def delete(self):
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.text_id)
