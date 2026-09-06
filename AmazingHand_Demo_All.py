"""
손가락 4개(서보 8개) 전체를 같이 움직이는 데모.
ID 배정: 손가락별로 (1,2) (3,4) (5,6) (7,8) 쌍.

서보 위치 표현 범위는 대략 -150도 ~ +150도. 손가락1(1,2)은 중립이 0도라
±90/±30을 그대로 써도 안전하지만, 손가락2,3,4(3~8)는 중립이 142~146도로
범위 끝(+150)에 거의 붙어있어서 같은 폭을 못 씀. 그래서 각 서보마다
"열림 각도"/"닫힘 각도"를 직접 지정하고, 두 관절이 반대 방향으로 움직이도록
(미러링) 해서 손가락1과 같은 종류의 오므리기/펴기 동작을 만든다.
"""
import time
import numpy as np

from rustypot import Scs0009PyController

PORT = "/dev/cu.usbmodem5B790178941"

# 손가락별 (관절1 ID, 관절2 ID) 쌍.
FINGERS = {
    "finger_A": (1, 2),
    "finger_B": (3, 4),
    "finger_C": (5, 6),
    "finger_D": (7, 8),
}

# 서보별 (열렸을 때 각도, 닫혔을 때 각도), 단위 도.
# finger_A: 기존 검증된 값 그대로 (중립 0 기준 ±90/±30, 관절1·2 반대 방향).
# finger_B/C/D: 중립이 144도 근처(+150에 거의 붙음)라, 관절마다 범위 안에서
#   반대 방향으로 최대한 크게 움직이게 잡음 (한쪽은 -90까지, 반대쪽은 +150 안 넘게 +4까지).
# 4,6,8번은 혼을 다시 끼워서 중립을 0도 근처로 재조립함(2026-09-06).
# 이제 1,2번과 똑같은 미러링 폭(±90/∓30)을 그대로 쓸 수 있음.
OPEN_DEG = {
    1: -30, 2: 30,
    3: 144, 4: -30,
    5: 141, 6: -30,
    7: 144, 8: -30,
}
CLOSE_DEG = {
    1: 90, 2: -90,
    3: 54, 4: 90,
    5: 24, 6: 118,   # 다른 손가락보다 덜 굽혀져서 폭을 더 늘림
    7: 54, 8: 90,
}

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


def move_all(deg_table, speed=4):
    for sid in all_ids():
        robust(lambda sid=sid: c.write_goal_speed(sid, speed))
    for sid in all_ids():
        robust(lambda sid=sid: c.write_goal_position(sid, np.deg2rad(deg_table[sid])))


def main():
    print("모든 서보 토크 켜는 중 (현재 위치 유지, 안 튐)...")
    for sid in all_ids():
        enable_torque_without_jump(sid)
    time.sleep(0.5)
    print("시작합니다. 중지하려면 Ctrl+C.")

    while True:
        print("전체 손가락 닫기")
        move_all(CLOSE_DEG)
        time.sleep(3)

        print("전체 손가락 펴기")
        move_all(OPEN_DEG)
        time.sleep(1)


def disable_all_torque():
    print("종료 처리 중: 모든 서보 토크 끄는 중...")
    for sid in all_ids():
        robust(lambda sid=sid: c.write_torque_enable(sid, 0))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        disable_all_torque()
