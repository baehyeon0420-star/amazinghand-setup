import time
import numpy as np

from rustypot import Scs0009PyController


ID_1 = 1  # Change to servo ID you want to calibrate
ID_2 = 2  # Change to servo ID you want to calibrate
MiddlePos_1 = 0  # Middle position for servo ID_1
MiddlePos_2 = 0  # Middle position for servo ID_2


c = Scs0009PyController(
        serial_port="/dev/cu.usbmodem5B790178941",
        baudrate=1000000,
        timeout=0.5,
    )


def robust(fn, tries=10, delay=0.05):
    """이 버스는 통신이 가끔 튀어서, 실패해도 스크립트가 죽지 않게 재시도한다."""
    last_err = None
    for _ in range(tries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            time.sleep(delay)
    print(f"[경고] 재시도 {tries}회 후에도 실패: {last_err!r}")
    return None


def main():

    robust(lambda: c.write_torque_enable(ID_1, 1))
    robust(lambda: c.write_torque_enable(ID_2, 1))
    # 1 = On / 2 = Off / 3 = Free

    while True:

        CloseFinger()
        time.sleep(3)

        OpenFinger()
        time.sleep(1)


def CloseFinger():
    robust(lambda: c.write_goal_speed(ID_1, 6))
    robust(lambda: c.write_goal_speed(ID_2, 6))
    Pos_1 = np.deg2rad(MiddlePos_1 + 90)
    Pos_2 = np.deg2rad(MiddlePos_2 - 90)
    robust(lambda: c.write_goal_position(ID_1, Pos_1))
    robust(lambda: c.write_goal_position(ID_2, Pos_2))
    time.sleep(0.01)


def OpenFinger():
    robust(lambda: c.write_goal_speed(ID_1, 6))
    robust(lambda: c.write_goal_speed(ID_2, 6))
    Pos_1 = np.deg2rad(MiddlePos_1 - 30)
    Pos_2 = np.deg2rad(MiddlePos_2 + 30)
    robust(lambda: c.write_goal_position(ID_1, Pos_1))
    robust(lambda: c.write_goal_position(ID_2, Pos_2))
    time.sleep(0.01)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
