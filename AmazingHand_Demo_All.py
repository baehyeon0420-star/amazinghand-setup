"""
손가락 4개(서보 8개) 전체를 같이 움직이는 데모.
ID 배정: 손가락별로 (1,2) (3,4) (5,6) (7,8) 쌍.
"""
import time
import numpy as np

from rustypot import Scs0009PyController

PORT = "/dev/cu.usbmodem5B790178941"

# 손가락별 (관절1 ID, 관절2 ID) 쌍. 필요하면 순서/이름 바꿔서 쓰세요.
FINGERS = {
    "finger_A": (1, 2),
    "finger_B": (3, 4),
    "finger_C": (5, 6),
    "finger_D": (7, 8),
}

MIDDLE_POS = {sid: 0 for pair in FINGERS.values() for sid in pair}  # 나중에 캘리브레이션 값으로 교체

c = Scs0009PyController(serial_port=PORT, baudrate=1000000, timeout=0.5)


def robust(fn, tries=10, delay=0.05):
    last_err = None
    for _ in range(tries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            time.sleep(delay)
    print(f"[경고] 재시도 {tries}회 후에도 실패: {last_err!r}")
    return None


def enable_torque_without_jump(sid):
    """토크 켤 때 서보가 엉뚱한 위치로 튀지 않도록,
    지금 위치를 먼저 읽어서 goal_position으로 설정한 뒤 토크를 켠다."""
    pos = robust(lambda: c.read_present_position(sid))
    if pos is not None:
        robust(lambda: c.write_goal_position(sid, pos[0] if isinstance(pos, list) else pos))
    robust(lambda: c.write_torque_enable(sid, 1))


def all_ids():
    return [sid for pair in FINGERS.values() for sid in pair]


def close_finger(id1, id2):
    robust(lambda: c.write_goal_speed(id1, 6))
    robust(lambda: c.write_goal_speed(id2, 6))
    robust(lambda: c.write_goal_position(id1, np.deg2rad(MIDDLE_POS[id1] + 90)))
    robust(lambda: c.write_goal_position(id2, np.deg2rad(MIDDLE_POS[id2] - 90)))


def open_finger(id1, id2):
    robust(lambda: c.write_goal_speed(id1, 6))
    robust(lambda: c.write_goal_speed(id2, 6))
    robust(lambda: c.write_goal_position(id1, np.deg2rad(MIDDLE_POS[id1] - 30)))
    robust(lambda: c.write_goal_position(id2, np.deg2rad(MIDDLE_POS[id2] + 30)))


def main():
    print("모든 서보 토크 켜는 중 (현재 위치 유지, 안 튐)...")
    for sid in all_ids():
        enable_torque_without_jump(sid)
    time.sleep(0.5)
    print("시작합니다. 중지하려면 Ctrl+C.")

    while True:
        print("전체 손가락 닫기")
        for id1, id2 in FINGERS.values():
            close_finger(id1, id2)
        time.sleep(3)

        print("전체 손가락 펴기")
        for id1, id2 in FINGERS.values():
            open_finger(id1, id2)
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
