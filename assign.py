"""
버스에 지금 연결된 서보 딱 하나를 자동으로 찾아서 원하는 ID로 바꾸는 스크립트.
(스캔 -> 감지 -> 잠금해제 -> ID변경 -> 검증까지 한 번에)

사용법:
    python3 assign.py <바꿀_ID>

예:
    python3 assign.py 4

주의: 버스에 서보가 "딱 하나만" 연결된 상태에서 실행할 것.
"""
import sys
import time
from collections import Counter
from rustypot import Scs0009PyController

PORT = "/dev/cu.usbmodem5B790178941"
SCAN_RANGE = range(1, 9)


def robust(fn, tries=10, delay=0.05):
    last_err = None
    for _ in range(tries):
        try:
            return fn(), None
        except Exception as e:
            last_err = e
            time.sleep(delay)
    return None, last_err


def find_current_id(c):
    candidates = []
    for sid in SCAN_RANGE:
        ok = 0
        for _ in range(10):
            try:
                c.read_present_position(sid)
                ok += 1
            except Exception:
                pass
            time.sleep(0.02)
        if ok >= 7:  # 70% 이상 응답하면 "이 ID에 서보 있음"으로 판단
            candidates.append(sid)
    return candidates


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    new_id = int(sys.argv[1])

    c = Scs0009PyController(serial_port=PORT, baudrate=1000000, timeout=0.5)

    print("현재 연결된 서보의 ID를 찾는 중...")
    candidates = find_current_id(c)

    if len(candidates) == 0:
        print("[중단] 응답하는 서보를 못 찾았습니다. 연결 상태를 확인하세요.")
        sys.exit(1)
    if len(candidates) > 1:
        print(f"[중단] 여러 ID({candidates})에서 응답이 감지됐습니다 — 서보가 2개 이상 연결된 것 같습니다.")
        print("       하나만 남기고 다시 시도하세요.")
        sys.exit(1)

    old_id = candidates[0]
    print(f"[감지] 현재 ID: {old_id}")

    if old_id == new_id:
        print(f"[완료] 이미 목표 ID({new_id})입니다. 변경 불필요.")
        return

    _, lock_err = robust(lambda: c.write_lock(old_id, False))
    if lock_err:
        print(f"[참고] write_lock 에러(무시): {lock_err!r}")

    time.sleep(0.1)
    _, err = robust(lambda: c.write_id(old_id, new_id))
    if err:
        print(f"[참고] write_id 에러 보고(정상일 수 있음): {err!r}")

    time.sleep(0.3)

    pos_new, err_new = robust(lambda: c.read_present_position(new_id))
    pos_old, err_old = robust(lambda: c.read_present_position(old_id), tries=5)

    if err_new is None:
        print(f"[성공] ID {old_id} -> {new_id} 변경 완료, 새 ID 응답 OK -> {pos_new}")
    else:
        print(f"[실패] 새 ID {new_id}로 응답 없음: {err_new!r}")

    if err_old is not None:
        print(f"[정상] 이전 ID {old_id}로는 더 이상 응답 없음")
    else:
        print(f"[경고] 이전 ID {old_id}로도 여전히 응답 있음 -> {pos_old}")


if __name__ == "__main__":
    main()
