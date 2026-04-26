import tkinter as tk
import random

class PongGame(tk.Canvas):
    def __init__(self, master, width=600, height=400, **kwargs):
        super().__init__(master, width=width, height=height, bg="black", highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.paddle_w = 15
        self.paddle_h = 80
        self.ball_size = 15
        self.score_left = 0
        self.score_right = 0
        
        self.running = False
        
        # Player (Left)
        self.paddle1 = self.create_rectangle(30, self.h//2 - self.paddle_h//2, 30 + self.paddle_w, self.h//2 + self.paddle_h//2, fill="white")
        # AI (Right)
        self.paddle2 = self.create_rectangle(self.w - 30 - self.paddle_w, self.h//2 - self.paddle_h//2, self.w - 30, self.h//2 + self.paddle_h//2, fill="white")
        
        # Ball
        self.ball = self.create_oval(self.w//2 - self.ball_size//2, self.h//2 - self.ball_size//2, 
                                     self.w//2 + self.ball_size//2, self.h//2 + self.ball_size//2, fill="white")
        
        # Score text
        self.score_text = self.create_text(self.w//2, 30, text="0 - 0", fill="white", font=("Consolas", 20, "bold"))
        self.center_line = self.create_line(self.w//2, 0, self.w//2, self.h, fill="gray", dash=(4, 4))
        
        self.ball_dx = 5
        self.ball_dy = 5
        
        self.bind("<Up>", self.move_up)
        self.bind("<Down>", self.move_down)
        self.bind("<MouseWheel>", self.mouse_wheel)
        self.bind("<Button-4>", self.move_up) # Linux scroll up
        self.bind("<Button-5>", self.move_down) # Linux scroll down

    def start(self):
        self.focus_set()
        if not self.running:
            self.running = True
            self.game_loop()

    def stop(self):
        self.running = False

    def reset_ball(self):
        self.coords(self.ball, self.w//2 - self.ball_size//2, self.h//2 - self.ball_size//2, 
                    self.w//2 + self.ball_size//2, self.h//2 + self.ball_size//2)
        self.ball_dx = 5 * random.choice([1, -1])
        self.ball_dy = random.randint(2, 5) * random.choice([1, -1])

    def move_up(self, event=None):
        coords = self.coords(self.paddle1)
        if coords[1] > 0:
            self.move(self.paddle1, 0, -20)

    def move_down(self, event=None):
        coords = self.coords(self.paddle1)
        if coords[3] < self.h:
            self.move(self.paddle1, 0, 20)

    def mouse_wheel(self, event):
        if event.delta > 0:
            self.move_up()
        else:
            self.move_down()

    def game_loop(self):
        if not self.running:
            return
            
        # Move ball
        self.move(self.ball, self.ball_dx, self.ball_dy)
        b_coords = self.coords(self.ball)
        
        # Bounce top/bottom
        if b_coords[1] <= 0 or b_coords[3] >= self.h:
            self.ball_dy *= -1
            
        # AI Logic
        p2_coords = self.coords(self.paddle2)
        b_center_y = (b_coords[1] + b_coords[3]) / 2
        p2_center_y = (p2_coords[1] + p2_coords[3]) / 2
        if b_center_y < p2_center_y and p2_coords[1] > 0:
            self.move(self.paddle2, 0, -4)
        elif b_center_y > p2_center_y and p2_coords[3] < self.h:
            self.move(self.paddle2, 0, 4)

        # Collision with paddles
        p1_coords = self.coords(self.paddle1)
        
        # Left paddle collision
        if b_coords[0] <= p1_coords[2] and b_coords[2] >= p1_coords[0]:
            if b_coords[3] >= p1_coords[1] and b_coords[1] <= p1_coords[3]:
                self.ball_dx = abs(self.ball_dx) + 0.5 # Increase speed slightly
                
        # Right paddle collision
        if b_coords[2] >= p2_coords[0] and b_coords[0] <= p2_coords[2]:
            if b_coords[3] >= p2_coords[1] and b_coords[1] <= p2_coords[3]:
                self.ball_dx = -abs(self.ball_dx) - 0.5

        # Scoring
        if b_coords[0] <= 0:
            self.score_right += 1
            self.itemconfig(self.score_text, text=f"{self.score_left} - {self.score_right}")
            self.reset_ball()
        elif b_coords[2] >= self.w:
            self.score_left += 1
            self.itemconfig(self.score_text, text=f"{self.score_left} - {self.score_right}")
            self.reset_ball()

        self.after(20, self.game_loop)


class SnakeGame(tk.Canvas):
    def __init__(self, master, width=600, height=400, **kwargs):
        super().__init__(master, width=width, height=height, bg="#1a1a1a", highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.cell_size = 20
        self.running = False
        
        self.bind("<Up>", lambda e: self.change_dir("Up"))
        self.bind("<Down>", lambda e: self.change_dir("Down"))
        self.bind("<Left>", lambda e: self.change_dir("Left"))
        self.bind("<Right>", lambda e: self.change_dir("Right"))
        
        self.init_game()

    def init_game(self):
        self.delete("all")
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.dir = "Right"
        self.next_dir = "Right"
        self.food = self.spawn_food()
        self.score = 0
        self.score_text = self.create_text(50, 20, text=f"Score: {self.score}", fill="white", font=("Segoe UI", 12))
        
        self.draw_elements()

    def start(self):
        self.focus_set()
        if not self.running:
            self.init_game()
            self.running = True
            self.game_loop()

    def stop(self):
        self.running = False

    def change_dir(self, new_dir):
        opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if new_dir != opposites.get(self.dir):
            self.next_dir = new_dir

    def spawn_food(self):
        while True:
            x = random.randint(0, (self.w - self.cell_size) // self.cell_size) * self.cell_size
            y = random.randint(0, (self.h - self.cell_size) // self.cell_size) * self.cell_size
            if (x, y) not in getattr(self, 'snake', []):
                return (x, y)

    def draw_elements(self):
        self.delete("snake")
        self.delete("food")
        
        # Draw food
        fx, fy = self.food
        self.create_oval(fx, fy, fx + self.cell_size, fy + self.cell_size, fill="#e74c3c", tags="food")
        
        # Draw snake
        for i, (sx, sy) in enumerate(self.snake):
            color = "#2ecc71" if i == 0 else "#27ae60"
            self.create_rectangle(sx, sy, sx + self.cell_size, sy + self.cell_size, fill=color, outline="#1a1a1a", tags="snake")

    def game_loop(self):
        if not self.running:
            return
            
        self.dir = self.next_dir
        hx, hy = self.snake[0]
        
        if self.dir == "Up": hy -= self.cell_size
        elif self.dir == "Down": hy += self.cell_size
        elif self.dir == "Left": hx -= self.cell_size
        elif self.dir == "Right": hx += self.cell_size
        
        # Wrap around edges
        hx = hx % self.w
        hy = hy % self.h
        
        # Self collision
        if (hx, hy) in self.snake:
            self.running = False
            self.create_text(self.w//2, self.h//2, text="GAME OVER", fill="#e74c3c", font=("Segoe UI", 30, "bold"))
            self.create_text(self.w//2, self.h//2 + 40, text="Cliquez pour rejouer", fill="white", font=("Segoe UI", 12))
            self.bind("<Button-1>", lambda e: self.start())
            return
            
        self.snake.insert(0, (hx, hy))
        
        # Food collision
        if (hx, hy) == self.food:
            self.score += 10
            self.itemconfig(self.score_text, text=f"Score: {self.score}")
            self.food = self.spawn_food()
        else:
            self.snake.pop()
            
        self.draw_elements()
        self.after(100, self.game_loop)
