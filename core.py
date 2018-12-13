# Copyright - Kiven, 2018
from pos_utils import *
import nxt.locator as locator
from nxt.motor import *

from nxt.sensor import *
from time import sleep
from threading import Thread


_GREEN_BLACK_BOUNDARY_ = 20  # todo: adapt these two values
_GREEN_WHITE_BOUNDARY_ = 39
_LIGHT_BASE_ = 0
_CM_EACH_ROLL_ = 0

print("PyLego initializing.")
print("Copyright - Kiven, 2018")

# initializing fields.
# P.S. *private* fields and functions begin with '_',
# they are not supposed to be invoked by any users (for details please google or baidu it)
# and the author will not be responsible for any mistakes caused by this

b = None
L = None
R = None
lmove = Thread()
rmove = Thread()
M = None
_lock = False
light = None
sonic = None
touch = None
guard_process = True
_debug = False

pos = Position()  # which marks the position of the robot
boxes = Boxes()  # which stores all the boxes here


_degree_to_spin_r = _to_rolls = \
{
    '90': 0.7,
    '45': 0.33,
    '30': 0.22,
    '15': 0.11,
    '-90': -0.7,
    '-45': -0.35,
    '-30': -0.233,
}


def _guard():
    pass


def to_cm(r): -> float
    # this converts the roll param to centimeters
    if r >= 15:  # todo: complete this
    	roll = r / 360
    return _CM_EACH_ROLL_*roll


def reset(remote=False):
    global b, L, R, M, lmove, rmove, _lock, light, sonic, touch
    try:
        locator.read_config()
    except:
        locator.make_config()
    print("Connecting")
    connect_method = locator.Method(not remote, remote)
    b = locator.find_one_brick(method=connect_method, debug=True)
    print("Connection to brick established\n")

    print("Initializing sensors")
    L = Motor(b, PORT_B)
    R = Motor(b, PORT_C)
    M = SynchronizedMotors(L, R, 2)
    lmove = Thread()
    rmove = Thread()
    _lock = False
    light = Light(b, PORT_3)
    sonic = Ultrasonic(b, PORT_2)
    touch = Touch(b, PORT_4)

    # calibrate light sensor
    light.set_illuminated(True)
    light.set_illuminated(False)

    print("Initialization completed\n")


if not b:
    try:
        reset(_debug)
    except:
        reset(True)

'''
def _handle_threads():
    def _do():
        global kill
        kill = True
        sleep(0.1)
        kill = False
    Thread(target=_do()).run()
'''


def l(r=1, p=75, t=None, b=True):  # changed the rule
    sleep(0.2)
    if r < 15:
        r *= 360
    L.turn(p, r, b)


def r(r=1, p=75, t=None, b=True):
    sleep(0.2)
    if r < 15:
        r *= 360
    R.turn(p, r, b)


right = r


def _l(r=1, p=100, t=None, b=True):  # changed the rule
    if r < 15:  # todo: say this in the documentation
        r *= 360
    L.turn(p, r, b)


def _r(p=100, r=1, t=None, b=True):
    if r < 15:  # todo: say this in the documentation
        r *= 360
    R.turn(p, r, b)


def spin(r=1, p=75):
    sleep(0.2)
    global _lock
    if type(r) == str:
        pos.track(int(r), 0)
        r = _to_rolls[r]
    if r < 0:
        r, p = -r, -p
    if r < 15:
        r = int(360*r)  # considered that the _to_roll returns float
    op1 = Thread(target=_locked(L.turn), args=(-p, r, False))
    op2 = Thread(target=_locked(R.turn), args=(p, r, False))
    op1.start()
    op2.start()
    while _lock:
        pass
    L.brake()
    R.brake()
    # print("exit turn")


def _locked(func):
    def output(*args):
        global _lock
        # print("locked")
        _lock = True
        func(*args)
        _lock = False
        # print("unlocked")
    return output


def hold_on():
    Thread(target=_locked(raw_input),
           args=("To end this hold-on, please enter anything: ",))\
        .start()
    global _lock
    while _lock:
        L.turn(1, 1)
        sleep(0.5)
        R.turn(1, 1)


def f(r=1, p=75, t=None):
    global _lock
    pos.track(0, to_cm(r))
    if not r or r==0:  # unlimited
        M.run(p)
    else:
        M.turn(p, r if r >= 15 else r*360, False)


def b(r=1, p=75, t=None):
    f(r, -p, t)


def _test():
    m = SynchronizedMotors(L, R, 0.5)
    m.turn(100, 360)


def stop():
    L.brake()
    R.brake()
    sleep(0.2)
    L.idle()
    R.idle()


def _discover(boxes, pos, sonic_dist):
    # this method records a new block
    # if this one is an existed one, return false
    _DELTA_ = 0
    if sonic_dist > 200:
        return False
    robo_pos = pos
    x = robo_pos.x
    y = robo_pos.y
    d = robo_pos.d
    dx = int(sin(rad(d)) * float(sonic_dist))
    dy = int(cos(rad(d)) * float(sonic_dist))
    t_x = x + dx
    t_y = y + dy
    pos = Position(t_x, t_y)
    if boxes.overlapped(pos):
        return False
    else:
        boxes.add(pos)
        return True


def discover(boxes):
    # automatically rotate 360 and record every boxes detected within 200 cm
    global pos
    for i in range(12):
        _discover(boxes, pos, distance())
        spin('30')

def _calibrate_light_sensor_by_black():
    global _LIGHT_BASE_
    _LIGHT_BASE_ = brightness() - 10


def brightness():
    global _LIGHT_BASE_
    if _LIGHT_BASE_ == 0:
        _calibrate_light_sensor_by_black()
    return light.get_lightness() - _LIGHT_BASE_


def distance():
    return sonic.get_distance()


def green():
    if _GREEN_WHITE_BOUNDARY_ > brightness() > _GREEN_BLACK_BOUNDARY_:
        return True
    return False


def black():
    if brightness() < _GREEN_BLACK_BOUNDARY_:
        return True
    return False


def white():
    if brightness() > _GREEN_WHITE_BOUNDARY_:
        return True
    return False


def hit():
    return touch.is_pressed() or distance() < 5


def sound():
    Thread(target=b.play_tone_and_wait, args=(3, 1000)).start()
