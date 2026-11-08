import math
import turtle


# 可调参数
WIDTH = 800
HEIGHT = 600
DELAY = 16
TS = DELAY / 1000

BGCOLOR = "#F4F4F4"
OUTCOLOR = "#222222"
PLATCOLOR = "#666666"
IRONCOLOR = "#888888"
NPCOLOR = "#E84B3C"
SPCOLOR = "#3978D5"
GOALCOLOR = "#E9B72F"
TCOLOR = "#222222"

FNAME = "Microsoft YaHei"
HUDSIZE = 14
WINSIZE = 30

FRTOP = -250
FRH = 100
FRW = 2000
FRCY = FRTOP - FRH / 2

# 平台数据格式：(中心 x，中心 y，宽度，高度)
PLATFORMS = (
    (0, FRCY, FRW, FRH),
    (-170, -185, 180, 18),
    (40, -105, 180, 18),
)

PLAYERSX = -330
PLAYERSY = FRTOP + 18
PLAYERW = 54
PLAYERH = 36
PLACC = 850
MAXHSPEED = 280
HFRICTION = 5
GRAVITY = 950
JUMPSPEED = 470

SMSX = -260
SMSY = FRTOP + 10
SMW = 30
SMH = 20
PICKRANGE = 72
DROP_GAP = 8

IRCX = 115
IRCY = -210
IRW = 54
IRH = 42
IRSTRENGTH = 90000
MINATTDISTANCE = 24
MAXATTACC = 500

GOAL_CENTER_X = 320
GOAL_CENTER_Y = FRTOP + 22
GOAL_RADIUS = 22

LEFT_KEY = "a"
RIGHT_KEY = "d"
JUMP_KEY = "space"
PICKUP_KEY = "e"


class Vector:
    """用于保存位置和速度的二维向量。"""

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Body:
    def __init__(self, x, y, width, height):
        self.position = Vector(x, y)
        self.velocity = Vector(0, 0)
        self.width = width
        self.height = height
        self.on_ground = False


screen = turtle.Screen()
screen.setup(WIDTH, HEIGHT)
screen.title("磁轨跃迁")
screen.bgcolor(BGCOLOR)
screen.tracer(0, 0)

pen = turtle.Turtle()
pen.hideturtle()
pen.speed(0)
pen.penup()

player = Body(PLAYERSX, PLAYERSY, PLAYERW, PLAYERH)
small_magnet = Body(
    SMSX,
    SMSY,
    SMW,
    SMH,
)

keys_down = set()
carrying_small_magnet = False
pickup_key_down = False
jump_key_down = False
game_won = False


def draw_rectangle(left, bottom, width, height, fill_color, OUTCOLOR):
    pen.penup()
    pen.goto(left, bottom)
    pen.pencolor(OUTCOLOR)
    pen.fillcolor(fill_color)
    pen.pensize(1)
    pen.pendown()
    pen.begin_fill()
    pen.goto(left + width, bottom)
    pen.goto(left + width, bottom + height)
    pen.goto(left, bottom + height)
    pen.goto(left, bottom)
    pen.end_fill()
    pen.penup()


def draw_magnet(body):
    left = body.position.x - body.width / 2
    bottom = body.position.y - body.height / 2
    half_width = body.width / 2

    draw_rectangle(left, bottom, half_width, body.height, NPCOLOR, OUTCOLOR)
    draw_rectangle(
        left + half_width,
        bottom,
        half_width,
        body.height,
        SPCOLOR,
        OUTCOLOR,
    )


def draw_world():
    pen.clear()

    for center_x, center_y, width, height in PLATFORMS:
        draw_rectangle(
            center_x - width / 2,
            center_y - height / 2,
            width,
            height,
            PLATCOLOR,
            OUTCOLOR,
        )

    draw_rectangle(
        IRCX - IRW / 2,
        IRCY - IRH / 2,
        IRW,
        IRH,
        IRONCOLOR,
        OUTCOLOR,
    )

    pen.goto(GOAL_CENTER_X, GOAL_CENTER_Y)
    pen.dot(GOAL_RADIUS * 2, GOALCOLOR)

    draw_magnet(player)
    if carrying_small_magnet:
        small_magnet.position.x = (
            player.position.x + player.width / 2 + small_magnet.width / 2 + DROP_GAP
        )
        small_magnet.position.y = player.position.y
        draw_magnet(small_magnet)
    else:
        draw_magnet(small_magnet)

    pen.goto(-WIDTH / 2 + 20, HEIGHT / 2 - 35)
    pen.color(TCOLOR)
    carrying_text = "是" if carrying_small_magnet else "否"
    pen.write(
        f"携带小磁铁：{carrying_text}",
        font=(FNAME, HUDSIZE, "normal"),
    )

    if game_won:
        pen.goto(0, 35)
        pen.color(TCOLOR)
        pen.write(
            "通关！",
            align="center",
            font=(FNAME, WINSIZE, "bold"),
        )

    screen.update()


def apply_iron_attraction(body, TS):
    dx = IRCX - body.position.x
    dy = IRCY - body.position.y
    distance = math.hypot(dx, dy)

    if distance == 0:
        return

    safe_distance = max(distance, MINATTDISTANCE)
    acceleration = min(
        IRSTRENGTH / (safe_distance * safe_distance),
        MAXATTACC,
    )
    body.velocity.x += acceleration * (dx / distance) * TS
    body.velocity.y += acceleration * (dy / distance) * TS


def overlaps_platform(body, center_x, center_y, width, height):
    body_left = body.position.x - body.width / 2
    body_right = body.position.x + body.width / 2
    body_bottom = body.position.y - body.height / 2
    body_top = body.position.y + body.height / 2

    platform_left = center_x - width / 2
    platform_right = center_x + width / 2
    platform_bottom = center_y - height / 2
    platform_top = center_y + height / 2

    return (
        body_right > platform_left
        and body_left < platform_right
        and body_top > platform_bottom
        and body_bottom < platform_top
    )


def move_body(body, TS):
    body.on_ground = False

    # 分轴移动并在碰撞时修正位置，避免穿过平台。
    body.position.x += body.velocity.x * TS
    for center_x, center_y, width, height in PLATFORMS:
        if overlaps_platform(body, center_x, center_y, width, height):
            platform_left = center_x - width / 2
            platform_right = center_x + width / 2
            if body.velocity.x > 0:
                body.position.x = platform_left - body.width / 2
                body.velocity.x = 0
            elif body.velocity.x < 0:
                body.position.x = platform_right + body.width / 2
                body.velocity.x = 0

    body.position.y += body.velocity.y * TS
    for center_x, center_y, width, height in PLATFORMS:
        if overlaps_platform(body, center_x, center_y, width, height):
            platform_bottom = center_y - height / 2
            platform_top = center_y + height / 2
            if body.velocity.y < 0:
                body.position.y = platform_top + body.height / 2
                body.velocity.y = 0
                body.on_ground = True
            elif body.velocity.y > 0:
                body.position.y = platform_bottom - body.height / 2
                body.velocity.y = 0


def update_player(TS):
    direction = 0
    if LEFT_KEY in keys_down and RIGHT_KEY not in keys_down:
        direction = -1
    elif RIGHT_KEY in keys_down and LEFT_KEY not in keys_down:
        direction = 1

    player.velocity.x += direction * PLACC * TS
    if direction == 0:
        friction_factor = max(0, 1 - HFRICTION * TS)
        player.velocity.x *= friction_factor

    player.velocity.x = max(
        -MAXHSPEED,
        min(MAXHSPEED, player.velocity.x),
    )
    player.velocity.y -= GRAVITY * TS
    apply_iron_attraction(player, TS)
    move_body(player, TS)


def update_dropped_magnet(TS):
    if carrying_small_magnet:
        return

    small_magnet.velocity.y -= GRAVITY * TS
    apply_iron_attraction(small_magnet, TS)
    move_body(small_magnet, TS)


def player_touches_goal():
    nearest_x = max(
        player.position.x - player.width / 2,
        min(GOAL_CENTER_X, player.position.x + player.width / 2),
    )
    nearest_y = max(
        player.position.y - player.height / 2,
        min(GOAL_CENTER_Y, player.position.y + player.height / 2),
    )
    return math.hypot(nearest_x - GOAL_CENTER_X, nearest_y - GOAL_CENTER_Y) <= GOAL_RADIUS


def game_loop():
    global game_won

    update_player(TS)
    update_dropped_magnet(TS)

    if carrying_small_magnet:
        small_magnet.position.x = (
            player.position.x + player.width / 2 + small_magnet.width / 2 + DROP_GAP
        )
        small_magnet.position.y = player.position.y

    if carrying_small_magnet and player_touches_goal():
        game_won = True

    draw_world()
    screen.ontimer(game_loop, DELAY)


def press_left():
    keys_down.add(LEFT_KEY)


def release_left():
    keys_down.discard(LEFT_KEY)


def press_right():
    keys_down.add(RIGHT_KEY)


def release_right():
    keys_down.discard(RIGHT_KEY)


def press_jump():
    global jump_key_down
    if not jump_key_down:
        jump_key_down = True
        if player.on_ground:
            player.velocity.y = JUMPSPEED
            player.on_ground = False


def release_jump():
    global jump_key_down
    jump_key_down = False


def press_pickup():
    global carrying_small_magnet, pickup_key_down

    if pickup_key_down:
        return
    pickup_key_down = True

    if carrying_small_magnet:
        carrying_small_magnet = False
        small_magnet.position.x = (
            player.position.x + player.width / 2 + small_magnet.width / 2 + DROP_GAP
        )
        small_magnet.position.y = player.position.y
        small_magnet.velocity.x = player.velocity.x
        small_magnet.velocity.y = player.velocity.y
        return

    distance = math.hypot(
        player.position.x - small_magnet.position.x,
        player.position.y - small_magnet.position.y,
    )
    if distance <= PICKRANGE:
        carrying_small_magnet = True


def release_pickup():
    global pickup_key_down
    pickup_key_down = False


screen.listen()
screen.onkeypress(press_left, LEFT_KEY)
screen.onkeyrelease(release_left, LEFT_KEY)
screen.onkeypress(press_right, RIGHT_KEY)
screen.onkeyrelease(release_right, RIGHT_KEY)
screen.onkeypress(press_jump, JUMP_KEY)
screen.onkeyrelease(release_jump, JUMP_KEY)
screen.onkeypress(press_pickup, PICKUP_KEY)
screen.onkeyrelease(release_pickup, PICKUP_KEY)

game_loop()
screen.mainloop()