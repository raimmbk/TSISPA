import pygame
import random
import json
import os

pygame.init()

# CONFIG
WIDTH, HEIGHT = 500, 700
FPS = 60
ROAD_SCROLL = 6
FONT = pygame.font.SysFont("Arial", 20)
BIG = pygame.font.SysFont("Arial", 40)

# Colors
WHITE=(255,255,255)
BLACK=(0,0,0)
RED=(200,0,0)
GREEN=(0,200,0)
BLUE=(0,120,255)
ORANGE=(255,140,0)
GRAY=(120,120,120)
YELLOW=(255,215,0)
SILVER=(192,192,192)
BRONZE=(205,127,50)

# Powerup colors
SHIELD_COLOR = (0,120,255)
NITRO_COLOR = (255,140,0)
REPAIR_COLOR = (200,0,0)

LEADERBOARD_FILE="leaderboard.json"

#IMAGES
ROAD = pygame.image.load("AnimatedStreet.png")
ROAD = pygame.transform.scale(ROAD,(WIDTH,HEIGHT))
PLAYER_IMG = pygame.transform.scale(pygame.image.load("Player.png"),(50,90))
ENEMY_IMG = pygame.transform.scale(pygame.image.load("Enemy.png"),(50,90))

#DATA
def load_lb():
    if os.path.exists(LEADERBOARD_FILE):
        return json.load(open(LEADERBOARD_FILE))
    return []

def save_lb(data):
    json.dump(data, open(LEADERBOARD_FILE,"w"), indent=4)

#BUTTON
class Button:
    def __init__(self,x,y,w,h,text):
        self.rect=pygame.Rect(x,y,w,h)
        self.text=text
    def draw(self,s):
        pygame.draw.rect(s,GRAY,self.rect)
        s.blit(FONT.render(self.text,True,WHITE),(self.rect.x+10,self.rect.y+10))
    def click(self,pos):
        return self.rect.collidepoint(pos)

#ENTITIES
#Player class
class Player:
    def __init__(self):
        self.x=WIDTH//2
        self.y=HEIGHT-120
        self.speed=6
        self.hp=3
        self.shield=0
        self.nitro=0

    def reset(self):
        self.x=WIDTH//2
        self.y=HEIGHT-120
        self.hp=3
        self.shield=0
        self.nitro=0

    def move(self,dx,dy):
        self.x+=dx*self.speed
        self.y+=dy*self.speed
        self.x=max(0,min(WIDTH-50,self.x))
        self.y=max(0,min(HEIGHT-100,self.y))

    def update(self):
        if self.shield>0:self.shield-=1
        if self.nitro>0:self.nitro-=1

    def draw(self,s):
        s.blit(PLAYER_IMG,(self.x,self.y))
        if self.shield>0:
            pygame.draw.circle(s,SHIELD_COLOR,(self.x+25,self.y+40),50,2)
#Coin class
class Coin:
    def __init__(self):
        self.x=random.randint(50,WIDTH-50)
        self.y=-20
        self.t=random.choices(["bronze","silver","gold"],[60,30,10])[0]
        if self.t=="bronze":self.v=1;self.c=BRONZE;self.r=10
        elif self.t=="silver":self.v=3;self.c=SILVER;self.r=8
        else:self.v=5;self.c=YELLOW;self.r=6

    def update(self):self.y+=ROAD_SCROLL
    def draw(self,s):pygame.draw.circle(s,self.c,(int(self.x),int(self.y)),self.r)
#Enemy class
class Enemy:
    def __init__(self,speed):
        self.x=random.randint(50,WIDTH-100)
        self.y=-100
        self.speed=speed

    def update(self):self.y+=self.speed
    def draw(self,s):s.blit(ENEMY_IMG,(self.x,self.y))
#Obstacles
class Obstacle:
    def __init__(self,t):
        self.x=random.randint(50,WIDTH-100)
        self.y=-50
        self.t=t

    def update(self):self.y+=ROAD_SCROLL

    def draw(self,s):
        if self.t=="barrier":pygame.draw.rect(s,BLACK,(self.x,self.y,50,50))
        elif self.t=="speed_bump":pygame.draw.rect(s,GRAY,(self.x,self.y,50,20))
        elif self.t=="boost":pygame.draw.rect(s,ORANGE,(self.x,self.y,50,20))
#Powerups
class PowerUp:
    def __init__(self):
        self.x=random.randint(50,WIDTH-50)
        self.y=-40
        self.t=random.choice(["shield","nitro","repair"])

    def update(self):self.y+=ROAD_SCROLL

    def draw(self,s):
        c=SHIELD_COLOR if self.t=="shield" else NITRO_COLOR if self.t=="nitro" else REPAIR_COLOR
        pygame.draw.circle(s,c,(self.x,int(self.y)),12)

#Game
class Game:
    #Choosing menu options
    def __init__(self):
        self.s=pygame.display.set_mode((WIDTH,HEIGHT))
        self.c=pygame.time.Clock()

        self.state="menu"
        self.player=Player()

        self.reset_game()

        self.buttons={
            "play":Button(180,200,120,40,"PLAY"),
            "lb":Button(180,260,120,40,"LEADERBOARD"),
            "quit":Button(180,320,120,40,"QUIT"),

            "retry":Button(180,400,120,40,"RESTART"),
            "back":Button(180,460,120,40,"MENU")
        }
    #Restarting the parameters
    def reset_game(self):
        self.coins=[]
        self.enemies=[]
        self.obs=[]
        self.pups=[]
        self.score=0
        self.dist=0
        self.enemy_speed=4

    # SAFE SPAWN
    def safe_x(self):
        while True:
            x=random.randint(50,WIDTH-100)
            if abs(x-self.player.x)>100:
                return x
    #Spawn items
    def spawn(self):
        if random.random()<0.5:self.coins.append(Coin())
        if random.random()<0.3:
            e=Enemy(self.enemy_speed)
            e.x=self.safe_x()
            self.enemies.append(e)
        if random.random()<0.3:
            o=Obstacle(random.choice(["barrier","speed_bump","boost"]))
            o.x=self.safe_x()
            self.obs.append(o)
        if random.random()<0.25:
            p=PowerUp()
            p.x=self.safe_x()
            self.pups.append(p)
    #Collisions
    def hit(self,a,b):
        return abs(a.x-b.x)<40 and abs(a.y-b.y)<60
    #Checking for collisions
    def check(self):
        for c in self.coins[:]:
            if self.hit(c,self.player):
                self.score+=c.v*10
                self.coins.remove(c)

        for e in self.enemies[:]:
            if self.hit(e,self.player):
                if self.player.shield<=0:self.player.hp-=1
                self.enemies.remove(e)

        for o in self.obs[:]:
            if self.hit(o,self.player):
                if o.t=="boost":self.enemy_speed+=1
                elif o.t=="barrier" and self.player.shield<=0:self.player.hp-=1
                self.obs.remove(o)

        for p in self.pups[:]:
            if self.hit(p,self.player):
                if p.t=="shield":self.player.shield=300
                elif p.t=="nitro":self.player.nitro=200;self.enemy_speed+=1
                elif p.t=="repair":self.player.hp=min(3,self.player.hp+1)
                self.pups.remove(p)

        if self.player.hp<=0:
            self.save_score()
            self.state="gameover"
    #Saving the score
    def save_score(self):
        data=load_lb()
        data.append({"name":"Player","score":self.score,"dist":self.dist})
        data=sorted(data,key=lambda x:x["score"],reverse=True)[:10]
        save_lb(data)

    def update(self):
        self.dist+=1
        self.score+=1

        self.player.update()

        for l in [self.coins,self.enemies,self.obs,self.pups]:
            for i in l:i.update()

        self.coins=[c for c in self.coins if c.y<HEIGHT]
        self.enemies=[e for e in self.enemies if e.y<HEIGHT]
        self.obs=[o for o in self.obs if o.y<HEIGHT]
        self.pups=[p for p in self.pups if p.y<HEIGHT]

        self.check()

        if random.random()<0.05:self.spawn()

    def draw(self):
        self.s.blit(ROAD,(0,0))
        self.player.draw(self.s)

        for l in [self.coins,self.enemies,self.obs,self.pups]:
            for i in l:i.draw(self.s)

        self.s.blit(FONT.render(f"Score:{self.score} HP:{self.player.hp}",True,WHITE),(10,10))

    def leaderboard(self):
        self.s.fill(BLACK)
        self.s.blit(BIG.render("LEADERBOARD",True,WHITE),(120,30))

        y=120
        for i,d in enumerate(load_lb()):
            self.s.blit(FONT.render(f"{i+1}. {d['score']} Dist:{d['dist']}",True,WHITE),(120,y))
            y+=30

        self.buttons["back"].draw(self.s)

    def gameover(self):
        self.s.fill(BLACK)
        self.s.blit(BIG.render("GAME OVER",True,RED),(140,200))
        self.s.blit(FONT.render(f"Score:{self.score}",True,WHITE),(180,280))

        self.buttons["retry"].draw(self.s)
        self.buttons["back"].draw(self.s)

    def menu(self):
        self.s.fill(BLACK)
        self.s.blit(BIG.render("RACER",True,WHITE),(180,100))
        for b in [self.buttons["play"],self.buttons["lb"],self.buttons["quit"]]:b.draw(self.s)

    def run(self):
        run=True
        while run:
            self.c.tick(FPS)

            for e in pygame.event.get():
                if e.type==pygame.QUIT:run=False

                if e.type==pygame.MOUSEBUTTONDOWN:
                    pos=pygame.mouse.get_pos()

                    if self.state=="menu":
                        if self.buttons["play"].click(pos):self.state="play"
                        if self.buttons["lb"].click(pos):self.state="leaderboard"
                        if self.buttons["quit"].click(pos):run=False

                    elif self.state=="gameover":
                        if self.buttons["retry"].click(pos):
                            self.player.reset()
                            self.reset_game()
                            self.state="play"
                        if self.buttons["back"].click(pos):self.state="menu"

                    elif self.state=="leaderboard":
                        if self.buttons["back"].click(pos):self.state="menu"

            keys=pygame.key.get_pressed()
            dx=dy=0
            if keys[pygame.K_LEFT]:dx=-1
            if keys[pygame.K_RIGHT]:dx=1
            if keys[pygame.K_UP]:dy=-1
            if keys[pygame.K_DOWN]:dy=1

            self.player.move(dx,dy)

            if self.state=="menu":self.menu()
            elif self.state=="play":self.update();self.draw()
            elif self.state=="leaderboard":self.leaderboard()
            elif self.state=="gameover":self.gameover()

            pygame.display.flip()

        pygame.quit()

if __name__=="__main__":Game().run()