import pygame
import random
import psycopg2

#DATABASE
conn = psycopg2.connect(
    dbname="suppliers",
    user="postgres",
    password="Alim1234",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

def get_or_create_player(username):
    cur.execute("SELECT id FROM players WHERE username=%s", (username,))
    res = cur.fetchone()
    if res:
        return res[0]
    cur.execute("INSERT INTO players(username) VALUES(%s) RETURNING id", (username,))
    conn.commit()
    return cur.fetchone()[0]

def save_game(player_id, score, level):
    cur.execute(
        "INSERT INTO game_sessions(player_id, score, level_reached) VALUES(%s,%s,%s)",
        (player_id, score, level)
    )
    conn.commit()

def get_top10():
    cur.execute("""
        SELECT username, score FROM game_sessions
        JOIN players ON players.id = game_sessions.player_id
        ORDER BY score DESC LIMIT 10
    """)
    return cur.fetchall()

def get_best(player_id):
    cur.execute("SELECT MAX(score) FROM game_sessions WHERE player_id=%s", (player_id,))
    res = cur.fetchone()[0]
    return res if res else 0


#SETTINGS
settings = {
    "difficulty": 1,
    "controls": "WASD",
    "grid": True
}


pygame.init()
#Const values
WIDTH, HEIGHT = 800, 600
CELL = 20
PADDING = 4

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Bandal", 28)

# COLORS
LIGHT_GREEN = (34,139,34)
DARK_GREEN  = (44,160,44)
WHITE = (255,255,255)

SNAKE_COLOR = (180, 0, 0)
APPLE  = (247, 10, 109)
PEAR   = (0,255,0)
PEACH  = (247, 137, 10)
POISON = (11, 26, 4)
OBST   = (50,50,50)

SPEED  = (255,255,255)
SLOW   = (255,255,255)
SHIELD = (56, 54, 179)


#DRAW
def draw_text(text, x, y, selected=False):
    color = (255,255,0) if selected else WHITE
    screen.blit(font.render(text, True, color), (x,y))

def draw_bg():
    for r in range(HEIGHT//CELL):
        for c in range(WIDTH//CELL):
            color = LIGHT_GREEN if (r+c)%2==0 else DARK_GREEN
            rect = pygame.Rect(c*CELL, r*CELL, CELL, CELL)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (0,60,0), rect, 1)


def random_position(snake, obstacles):
    while True:
        pos = (random.randint(0, WIDTH//CELL-1)*CELL,
               random.randint(0, HEIGHT//CELL-1)*CELL)
        if pos not in snake and pos not in obstacles:
            return pos


#POWERUPS 
def spawn_powerup(snake, obstacles):
    if random.random() < 0.01:
        return random.choice(["speed", "slow", "shield"]), random_position(snake, obstacles)
    return None, None


#USERNAME
def get_username():
    name = ""
    while True:
        screen.fill((0,0,0))
        draw_text("Enter Username:", 280, 250)
        draw_text(name, 280, 300)

        for e in pygame.event.get():
            if e.type == pygame.QUIT: exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and name:
                    return name
                elif e.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    name += e.unicode

        pygame.display.flip()


#Menu
def main_menu():
    options = ["Play", "Leaderboard", "Settings", "Exit"]
    selected = 0

    while True:
        screen.fill((0,0,0))
        for i,opt in enumerate(options):
            draw_text(opt, 350, 200+i*50, i==selected)

        for e in pygame.event.get():
            if e.type == pygame.QUIT: exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP: selected = (selected-1)%len(options)
                if e.key == pygame.K_DOWN: selected = (selected+1)%len(options)
                if e.key == pygame.K_RETURN:
                    return options[selected]

        pygame.display.flip()


#SETTINGS MENU
def settings_menu():
    opts = ["Difficulty", "Controls", "Grid", "Back"]
    sel = 0

    while True:
        screen.fill((0,0,0))

        draw_text(f"Difficulty: {settings['difficulty']}", 300, 200, sel==0)
        draw_text(f"Controls: {settings['controls']}", 300, 250, sel==1)
        draw_text(f"Grid: {settings['grid']}", 300, 300, sel==2)
        draw_text("Back", 300, 350, sel==3)

        for e in pygame.event.get():
            if e.type == pygame.QUIT: exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP: sel = (sel-1)%4
                if e.key == pygame.K_DOWN: sel = (sel+1)%4

                if e.key == pygame.K_RETURN:
                    if sel == 0:
                        settings["difficulty"] = settings["difficulty"]%3 + 1
                    elif sel == 1:
                        settings["controls"] = "ARROWS" if settings["controls"]=="WASD" else "WASD"
                    elif sel == 2:
                        settings["grid"] = not settings["grid"]
                    elif sel == 3:
                        return

        pygame.display.flip()


#GAME
def game(player_id, best):
    snake=[(100,100)]
    direction=(CELL,0)

    obstacles=[]
    food=random_position(snake, obstacles)
    food_type="apple"
    food_val=1

    poison=None
    poison_timer=0

    powerup=None
    power_pos=None
    effect=None
    effect_end=0

    score=0
    level=1
    lives=3

    base_speed = {1:8, 2:10, 3:14}[settings["difficulty"]]
    speed = base_speed
  
    #Game loop
    while True:
        draw_bg()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: exit()
            if e.type == pygame.KEYDOWN:
                if settings["controls"]=="WASD":
                    if e.key==pygame.K_w and direction!=(0,CELL): direction=(0,-CELL)
                    if e.key==pygame.K_s and direction!=(0,-CELL): direction=(0,CELL)
                    if e.key==pygame.K_a and direction!=(CELL,0): direction=(-CELL,0)
                    if e.key==pygame.K_d and direction!=(-CELL,0): direction=(CELL,0)
                else:
                    if e.key==pygame.K_UP and direction!=(0,CELL): direction=(0,-CELL)
                    if e.key==pygame.K_DOWN and direction!=(0,-CELL): direction=(0,CELL)
                    if e.key==pygame.K_LEFT and direction!=(CELL,0): direction=(-CELL,0)
                    if e.key==pygame.K_RIGHT and direction!=(-CELL,0): direction=(CELL,0)

        head=(snake[0][0]+direction[0], snake[0][1]+direction[1])

        # COLLISIONS
        if not (0<=head[0]<WIDTH and 0<=head[1]<HEIGHT):
            if effect != "shield":
                break
        if head in snake:
            if effect != "shield":
                break
        if head in obstacles:
            if effect != "shield":
                break

        snake.insert(0, head)

        # FOOD
        if head==food:
            score+=food_val
            food=random_position(snake, obstacles)

            food_type=random.choice(["apple","pear","peach"])
            food_val={"apple":1,"pear":2,"peach":3}[food_type]

            if score%5==0:
                level+=1
                speed+=2
                obstacles.append(random_position(snake, obstacles))
        else:
            snake.pop()

        # POISON
        if poison is None and random.random()<0.01:
            poison=random_position(snake, obstacles)
            poison_timer=pygame.time.get_ticks()

        if poison and pygame.time.get_ticks()-poison_timer>6000:
            poison=None

        if poison and head==poison:
            lives-=1
            poison=None
            if lives<=0:
                break

        # POWERUPS
        if powerup is None:
            powerup, power_pos = spawn_powerup(snake, obstacles)

        if powerup and head==power_pos:
            if powerup=="speed":
                speed+=5
                effect="speed"
                effect_end=pygame.time.get_ticks()+5000
            elif powerup=="slow":
                speed=max(5, speed-5)
                effect="slow"
                effect_end=pygame.time.get_ticks()+5000
            elif powerup=="shield":
                effect="shield"
                effect_end=pygame.time.get_ticks()+5000
            powerup=None

        if effect and pygame.time.get_ticks()>effect_end:
            speed = base_speed + (level-1)*2
            effect=None

        # DRAW SNAKE
        for s in snake:
            pygame.draw.rect(screen, SNAKE_COLOR,
                (s[0]+PADDING//2, s[1]+PADDING//2, CELL-PADDING, CELL-PADDING))

        # FOOD
        col={"apple":APPLE,"pear":PEAR,"peach":PEACH}[food_type]
        pygame.draw.rect(screen, col,
            (food[0]+PADDING//2, food[1]+PADDING//2, CELL-PADDING, CELL-PADDING))

        # POISON
        if poison:
            pygame.draw.rect(screen, POISON,
                (poison[0]+PADDING//2, poison[1]+PADDING//2, CELL-PADDING, CELL-PADDING))

        # POWERUP
        if powerup:
            color = {"speed":SPEED,"slow":SLOW,"shield":SHIELD}[powerup]
            pygame.draw.rect(screen, color,
                (power_pos[0]+PADDING//2, power_pos[1]+PADDING//2, CELL-PADDING, CELL-PADDING))

        # OBSTACLES
        for o in obstacles:
            pygame.draw.rect(screen, OBST,
                (o[0], o[1], CELL, CELL))

        draw_text(f"Score:{score}",10,10)
        draw_text(f"Level:{level}",10,40)
        draw_text(f"Best:{best}",10,70)
        draw_text(f"Lives:{lives}",10,100)

        pygame.display.flip()
        clock.tick(speed)

    return score, level


#LEADERBOARD 
def leaderboard():
    data=get_top10()
    while True:
        screen.fill((0,0,0))
        draw_text("TOP 10",350,50)

        for i,row in enumerate(data):
            draw_text(f"{i+1}. {row[0]} - {row[1]}",280,120+i*30)

        for e in pygame.event.get():
            if e.type==pygame.QUIT: exit()
            if e.type==pygame.KEYDOWN: return

        pygame.display.flip()


#MAIN
username=get_username()
player_id=get_or_create_player(username)

while True:
    best=get_best(player_id)
    choice = main_menu()

    if choice=="Play":
        score, level = game(player_id, best)
        save_game(player_id, score, level)

    elif choice=="Leaderboard":
        leaderboard()

    elif choice=="Settings":
        settings_menu()

    elif choice=="Exit":
        break

pygame.quit()