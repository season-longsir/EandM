import math
import turtle


# 可调参数
WIDTH = 800
HEIGHT = 600
DELAY = 16
TS = DELAY / 1000

BGCOLOR = '#F4F4F4'
OUTCOLOR = '#222222'
PLATCOLOR = '#666666'
IRONCOLOR = '#888888'
NPCOLOR = '#E84B3C'
SPCOLOR = '#3978D5'
POLECOLOR = '#FFFFFF'
GOALCOLOR = '#E9B72F'
TCOLOR = '#222222'

FNAME = 'Microsoft YaHei'
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
PLAYERSY = FRTOP + 30
PLAYERW = 54
PLAYERH = 54
PLACC = 850
MAXHSPEED = 280
HFRICTION = 10
GRAVITY = 4000
JUMPSPEED = 1000
VERFF = 0.25

SMSX = -260
SMSY = FRTOP + 20
SMW = 30
SMH = 30
PICKRANGE = 72
DROP_GAP = 8

IRCX = 115
IRCY = 0  #-210
IRW = 54
IRH = 42
IRSTRENGTH = 3000000
MINATTDISTANCE = 100
MAXATTACC = 500

SOLID = PLATFORMS + ((IRCX, IRCY, IRW, IRH),)
VERFSSPEED = (
    (GRAVITY + MAXATTACC)
    * TS
    * VERFF
    / (1 - VERFF)
    + 1
)

GCX = 320
GCY = FRTOP + 22
GR = 22

LEFT_KEY = 'a'
RIGHT_KEY = 'd'
JUMP_KEY = 'space'
PICKUP_KEY = 'e'


class Vector:
    '''用于保存位置和速度的二维向量。'''

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
screen.title('磁轨跃迁 Electric and Magnetic')
screen.bgcolor(BGCOLOR)
screen.tracer(0, 0)

pen = turtle.Turtle()
pen.hideturtle()
pen.speed(0)
pen.penup()

player = Body(PLAYERSX, PLAYERSY, PLAYERW, PLAYERH)
sm_magnet = Body(
    SMSX,
    SMSY,
    SMW,
    SMH,
)

ks_d = set()
carryingsm = False
pickupkd = False
jumpkd = False
gamewon = False


def drrectangle(left, bottom, width, height, fill_color, OUTCOLOR):
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


def drmagnet(body: Body):
    size = body.width
    left = body.position.x - body.width / 2
    bottom = body.position.y - size / 2
    half_width = size / 2

    drrectangle(left, bottom, half_width, size, NPCOLOR, OUTCOLOR)
    drrectangle(
        left + half_width,
        bottom,
        half_width,
        size,
        SPCOLOR,
        OUTCOLOR,
    )
    pen.color(POLECOLOR)
    pen.goto(left + half_width / 2, body.position.y)
    pen.write(
        'N',
        align='center',
        font=(FNAME, max(8, int(body.width / 3)), 'bold'),
    )
    pen.goto(left + half_width + half_width / 2, body.position.y)
    pen.write(
        'S',
        align='center',
        font=(FNAME, max(8, int(body.width / 3)), 'bold'),
    )


def drworld():
    pen.clear()

    for center_x, center_y, width, height in PLATFORMS:
        drrectangle(
            center_x - width / 2,
            center_y - height / 2,
            width,
            height,
            PLATCOLOR,
            OUTCOLOR,
        )

    drrectangle(
        IRCX - IRW / 2,
        IRCY - IRH / 2,
        IRW,
        IRH,
        IRONCOLOR,
        OUTCOLOR,
    )

    pen.goto(GCX, GCY)
    pen.dot(GR * 2, GOALCOLOR)

    drmagnet(player)
    if carryingsm:
        sm_magnet.position.x = (
            player.position.x + player.width / 2 + sm_magnet.width / 2 + DROP_GAP
        )
        sm_magnet.position.y = player.position.y
        drmagnet(sm_magnet)
    else:
        drmagnet(sm_magnet)

    pen.goto(-WIDTH / 2 + 20, HEIGHT / 2 - 35)
    pen.color(TCOLOR)
    # carrying_text = '是' if carryingsm else '否'
    # pen.write(
    #     f'携带小磁铁：{carrying_text}',
    #     font=(FNAME, HUDSIZE, 'normal'),
    # )

    if gamewon:
        pen.goto(0, 35)
        pen.color(TCOLOR)
        pen.write(
            '通关！',
            align='center',
            font=(FNAME, WINSIZE, 'bold'),
        )

    screen.update()


def appironatt(body: Body, TS):
    dx = IRCX - body.position.x
    dy = IRCY - body.position.y
    distance = math.hypot(dx, dy)

    if distance == 0:
        return
    if distance < MINATTDISTANCE:
        safe_distance = distance
        acceleration = min(
            IRSTRENGTH / (safe_distance * safe_distance),
            MAXATTACC,
        )
        body.velocity.x += acceleration * (dx / distance) * TS
        body.velocity.y += acceleration * (dy / distance) * TS


def ovlplatform(body: Body, center_x, center_y, width, height):
    bl = body.position.x - body.width / 2
    br = body.position.x + body.width / 2
    bb = body.position.y - body.height / 2
    bt = body.position.y + body.height / 2

    pl = center_x - width / 2
    pr = center_x + width / 2
    pb = center_y - height / 2
    pt = center_y + height / 2

    return (
        br > pl
        and bl < pr
        and bt > pb
        and bb < pt
    )


def touchmago(body: Body):
    mago = (
        (IRCX, IRCY, IRW, IRH),
    )
    for other_body in (player, sm_magnet):
        if other_body is body:
            continue
        mago += (
            (
                other_body.position.x,
                other_body.position.y,
                other_body.width,
                other_body.height,
            ),
        )

    for center_x, center_y, width, height in mago:
        if (
            body.position.x + body.width / 2 >= center_x - width / 2
            and body.position.x - body.width / 2 <= center_x + width / 2
            and body.position.y + body.height / 2 >= center_y - height / 2
            and body.position.y - body.height / 2 <= center_y + height / 2
        ):
            return True
    return False


def appverf(body:Body):
    if not touchmago(body):
        return

    body.velocity.y *= VERFF
    if abs(body.velocity.y) <= VERFSSPEED:
        body.velocity.y = 0


def mvbody(body:Body, TS):
    body.on_ground = False

    body.position.x += body.velocity.x * TS
    for center_x, center_y, width, height in SOLID:
        if ovlplatform(body, center_x, center_y, width, height):
            pl = center_x - width / 2
            pr = center_x + width / 2
            if body.velocity.x > 0:
                body.position.x = pl - body.width / 2
                body.velocity.x = 0
            elif body.velocity.x < 0:
                body.position.x = pr + body.width / 2
                body.velocity.x = 0

    body.position.y += body.velocity.y * TS
    for center_x, center_y, width, height in SOLID:
        if ovlplatform(body, center_x, center_y, width, height):
            pb = center_y - height / 2
            pt = center_y + height / 2
            if body.velocity.y < 0:
                body.position.y = pt + body.height / 2
                body.velocity.y = 0
                body.on_ground = True
            elif body.velocity.y > 0:
                body.position.y = pb - body.height / 2
                body.velocity.y = 0


def updatep(TS):
    direction = 0
    if LEFT_KEY in ks_d and RIGHT_KEY not in ks_d:
        direction = -1
    elif RIGHT_KEY in ks_d and LEFT_KEY not in ks_d:
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
    appironatt(player, TS)
    appverf(player)
    mvbody(player, TS)


def updddropped(TS):
    if carryingsm:
        return

    friction_factor = max(0, 1 - HFRICTION * TS)
    sm_magnet.velocity.x *= friction_factor
    sm_magnet.velocity.y -= GRAVITY * TS
    appironatt(sm_magnet, TS)
    appverf(sm_magnet)
    mvbody(sm_magnet, TS)


def touchgoal():
    nearest_x = max(
        player.position.x - player.width / 2,
        min(GCX, player.position.x + player.width / 2),
    )
    nearest_y = max(
        player.position.y - player.height / 2,
        min(GCY, player.position.y + player.height / 2),
    )
    return math.hypot(nearest_x - GCX, nearest_y - GCY) <= GR


def game_loop():
    global gamewon

    updatep(TS)
    updddropped(TS)

    if carryingsm:
        sm_magnet.position.x = (
            player.position.x + player.width / 2 + sm_magnet.width / 2 + DROP_GAP
        )
        sm_magnet.position.y = player.position.y

    if carryingsm and touchgoal():
        gamewon = True

    drworld()
    screen.ontimer(game_loop, DELAY)


def pleft():
    ks_d.add(LEFT_KEY)


def rleft():
    ks_d.discard(LEFT_KEY)


def pright():
    ks_d.add(RIGHT_KEY)


def rright():
    ks_d.discard(RIGHT_KEY)


def pjump():
    global jumpkd
    if not jumpkd:
        jumpkd = True
        if player.on_ground:
            player.velocity.y = JUMPSPEED
            player.on_ground = False


def rjump():
    global jumpkd
    jumpkd = False


def ppick():
    global carryingsm, pickupkd

    if pickupkd:
        return
    pickupkd = True

    if carryingsm:
        carryingsm = False
        sm_magnet.position.x = (
            player.position.x + player.width / 2 + sm_magnet.width / 2 + DROP_GAP
        )
        sm_magnet.position.y = player.position.y
        sm_magnet.velocity.x = player.velocity.x
        sm_magnet.velocity.y = player.velocity.y
        return

    distance = math.hypot(
        player.position.x - sm_magnet.position.x,
        player.position.y - sm_magnet.position.y,
    )
    if distance <= PICKRANGE:
        carryingsm = True


def rpick():
    global pickupkd
    pickupkd = False


screen.listen()
screen.onkeypress(pleft, LEFT_KEY)
screen.onkeyrelease(rleft, LEFT_KEY)
screen.onkeypress(pright, RIGHT_KEY)
screen.onkeyrelease(rright, RIGHT_KEY)
screen.onkeypress(pjump, JUMP_KEY)
screen.onkeyrelease(rjump, JUMP_KEY)
screen.onkeypress(ppick, PICKUP_KEY)
screen.onkeyrelease(rpick, PICKUP_KEY)

game_loop()
screen.mainloop()