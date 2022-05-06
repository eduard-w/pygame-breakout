import pygame, sys, math, random, time
from pygame.locals import *

SCREEN_SIZE = (600,400)
WHITE = (255,255,255)
LIGHT_GREY = (150,150,150)
GREY = (100,100,100)
DARK_GREY = (50,50,50)
BLACK = (0,0,0)
GREEN = (0,200,0)
RED = (200,0,0)

class Block(pygame.sprite.Sprite):
	def __init__(self, pos):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.image.fill(BLACK)
		self.rect = self.image.get_rect(center=pos)

class Ball(pygame.sprite.Sprite):

	def __init__(self, pos):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((10,10))
		self.image.fill(GREEN)
		self.rect = self.image.get_rect(center=pos)
		self.pos = [float(pos[0]),float(pos[1])]
		self.set_direction(math.pi*1.5)

	def set_direction(self,angle):
		global ball_speed
		self.vel = [math.cos(angle)*ball_speed, math.sin(angle)*ball_speed]

	def game_update(self):
		self.pos[0] += self.vel[0]
		self.pos[1] += self.vel[1]

	def update(self):
		self.rect.center = (round(self.pos[0]),round(self.pos[1]))

class Paddle(pygame.sprite.Sprite):
	def __init__(self, pos):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((100,10))
		self.image.fill((0,100,0))
		self.rect = self.image.get_rect(center=pos)

	def update(self):
		x = pygame.mouse.get_pos()[0]
		if x-self.rect.width/2 > 1 and x-1+self.rect.width/2 < SCREEN_SIZE[0]:
			self.rect.centerx = x

class Powerup(pygame.sprite.Sprite):
	def __init__(self, pos):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((10,10))
		self.image.fill(RED)
		self.rect = self.image.get_rect(center=pos)

	def update(self):
		self.rect.y += 1

class Button():
	active_buttons = set()

	def __init__(self, text, perform_action):
		global button_font
		self.text = text
		self.perform_action = perform_action
		self.font_size = button_font.size(text)
		self.rect = pygame.Rect((0,0),(self.font_size[0]+4, self.font_size[1]+4))
		self.surface = pygame.Surface(self.rect.size)
		self.surface.fill(BLACK)
		self.backgrounds = {
			"default": button_font.render(text, False, BLACK, DARK_GREY),
			"mouse_hover": button_font.render(text, False, BLACK, GREY),
			"mouse_click": button_font.render(text, False, BLACK, LIGHT_GREY)
		}
		self.active_background = None

	def set_background(self, background):
		if self.active_background != background:
			self.surface.blit(self.backgrounds[background], (2,2))
			self.active_background = background
			self.draw()

	def draw(self):
		screen.blit(self.surface, self.rect)

def main():
	pygame.init()
	if not pygame.font.get_init():
		pygame.font.init()
	clock = pygame.time.Clock()
	random.seed(time.time())

	# init fonts and screen
	global screen, screen_center, bg, title_font, button_font
	title_font = pygame.font.Font(None, 80)
	button_font = pygame.font.Font(None, 60)
	pygame.display.set_caption("Pygame Breakout")
	screen = pygame.display.set_mode(SCREEN_SIZE)
	screen_center = screen.get_rect().center
	bg = pygame.Surface(SCREEN_SIZE)
	bg.fill(DARK_GREY)

	# init buttons
	global buttons
	buttons = {
		"new_game": Button("New Game", new_game),
		"quit": Button("Quit", quit),
		"continue_game": Button("Continue", continue_game),
		"next_level": Button("Next Level", next_level)
	}

	# init game scene
	border_t = pygame.sprite.Sprite()
	border_t.rect = pygame.Rect(-10,-10,SCREEN_SIZE[0]+20,10)
	border_b = pygame.sprite.Sprite()
	border_b.rect = pygame.Rect(-10,SCREEN_SIZE[1],SCREEN_SIZE[0]+20,10)
	border_l = pygame.sprite.Sprite()
	border_l.rect = pygame.Rect(-10,-10,10,SCREEN_SIZE[1]+20)
	border_r = pygame.sprite.Sprite()
	border_r.rect = pygame.Rect(SCREEN_SIZE[0],-10,10,SCREEN_SIZE[1]+20)

	global balls, blocks, powerups
	borders = pygame.sprite.Group(border_t, border_b, border_l, border_r)
	balls = pygame.sprite.Group()
	player = pygame.sprite.GroupSingle(Paddle((300,350)))
	blocks = pygame.sprite.Group()
	powerups = pygame.sprite.Group()

	start_menu()
	
	# game loop
	while(True):
		button_action = None
		for event in pygame.event.get():
			if event.type == KEYUP:
				if event.key == K_ESCAPE:
					if game_paused:
						continue_game()
					else:
						pause_game()
			if event.type == QUIT:
				quit()
			if event.type == MOUSEMOTION:
				for button in Button.active_buttons:
					if button.rect.collidepoint(event.pos):
						button.set_background("mouse_hover")
					else:
						button.set_background("default")
			if event.type == MOUSEBUTTONDOWN:
				for button in Button.active_buttons:
					if button.rect.collidepoint(event.pos):
						button.set_background("mouse_click")
			if event.type == MOUSEBUTTONUP:
				for button in Button.active_buttons:
					if button.rect.collidepoint(event.pos):
						button_action = button.perform_action
		pygame.event.pump()

		if button_action:
			button_action()

		if not game_paused:
			# collision checks
			coll = None
			for ball in balls:
				colls = []
				for group in (borders,blocks,player):
					colls.extend(pygame.sprite.spritecollide(ball,group,False))
				if colls:
					# determine collision area
					for sprite in colls:
						coll = coll.union(sprite.rect) if coll else sprite.rect
					coll = coll.clip(ball.rect)

					# check if corner brushed
					if (coll.width != 1 or coll.height != 1):

						# if ball touches paddle change direction depending on point of collision
						if isinstance(colls[0], Paddle):
							dx = ball.pos[0]-player.sprite.rect.centerx
							dy = ball.pos[1]-player.sprite.rect.centery
							if dx != 0:
								m = (abs(dy-15)/abs(dx))
								ball.set_direction(math.atan(m))
								if dx<0: ball.vel[0] = -ball.vel[0]
							else:
								ball.set_direction(math.pi*1.5)

						# destroy all blocks
						for sprite in colls:
							if blocks in sprite.groups():
								# 5% chance for block to drop powerup
								if random.random() < 0.05:
									powerups.add(Powerup(sprite.rect.center))

								screen.blit(bg,sprite.rect,sprite.rect)
								sprite.kill()
								del sprite

						# horizontal collision						
						if (coll.width >= coll.height):
							ball.vel[1] = -ball.vel[1]
						# vertical collision
						if (coll.width <= coll.height):
							ball.vel[0] = -ball.vel[0]

						# if ball touches bottom of screen -> kill ball
						if colls[0] == border_b:
							ball.kill()
							del ball	

			for powerup in pygame.sprite.spritecollide(player.sprite,powerups,True):
				balls_copy = set()
				for ball in balls:
					ball_copy = Ball(ball.pos)
					ball_copy.vel[0] = ball.vel[0]
					ball_copy.vel[1] = -ball.vel[1]
					balls_copy.add(ball_copy)
				balls.add(balls_copy)

			# destroy any remaining powerups
			for sprite in pygame.sprite.spritecollide(border_b,powerups,False):
				sprite.kill()
				del sprite

			for ball in balls:
				ball.game_update()

			for group in [blocks,player,powerups,balls]:
				group.clear(screen,bg)
				group.update()
				group.draw(screen)

			# if all balls are gone -> game lost
			if not balls:
				global ball_speed
				launch_menu("You Lost (Score: {})".format(ball_speed-2), ("new_game", "quit"))

			# if all blocks are gone -> game won
			if not blocks:
				launch_menu("You Won", ("next_level", "quit"))

		pygame.display.update()
		clock.tick(60)

def init_level():
	global balls, blocks, powerups

	# clear remaining objects
	for group in (balls,blocks,powerups):
		for sprite in group:
			sprite.kill()
			del sprite

	# (re-)inititalize level
	balls.add(Ball((300,340)))
	for x in range(50, 551, 20):
		for y in range(50, 251, 20):
			blocks.add(Block((x,y)))

def launch_menu(title, button_keys):
	global game_paused, buttons, title_font
	game_paused = True
	y_offset = -120
	calc_screen_pos = lambda size: (screen_center[0]-size[0]/2,screen_center[1]-size[1]/2 + y_offset)
	bg.set_alpha(175)
	screen.blit(bg, (0,0))
	bg.set_alpha(None)
	screen.blit(title_font.render(title, False, BLACK), calc_screen_pos(title_font.size(title)))
	y_offset += 120
	for button_key in button_keys:
		button = buttons[button_key]
		button.rect.topleft = calc_screen_pos(button.surface.get_size())
		y_offset += 60
		Button.active_buttons.add(button)
		button.set_background("default")
		button.draw()
	pygame.mouse.set_visible(True)
	pygame.event.set_grab(False)

def exit_menu():
	global game_paused
	game_paused = False
	Button.active_buttons.clear()
	screen.blit(bg, (0,0))
	pygame.mouse.set_visible(False)
	pygame.event.set_grab(True)

def start_menu():
	launch_menu("Pygame Breakout", ("new_game", "quit"))

def new_game():
	global ball_speed
	ball_speed = 2
	init_level()
	exit_menu()
	
def continue_game():
	exit_menu()

def pause_game():
	launch_menu("Game Paused", ("continue_game", "quit"))

def next_level():
	global ball_speed
	ball_speed += 1
	init_level()
	exit_menu()

def quit():
	pygame.quit()
	sys.exit()

if __name__ == '__main__': main()