"""
서보 ID를 바꾸는 스크립트.

사용법:
    python3 set_id.py <현재_ID> <바꿀_ID>

예:
    python3 set_id.py 1 2

주의: 버스에 서보가 "딱 하나만" 연결된 상태에서 실행할 것.
      두 개 이상 연결된 상태에서 실행하면 둘 다 같은 ID로 바뀌어버릴 수 있음.
"""
import sys
import time
from rustypot import Scs0009PyController

PORT = "/dev/cu.usbmodem5B790178941"  # ls /dev/cu.* 로 확인한 실제 포트로 바꿀 것


def robust(fn, tries=10, delay=0.1):
    last_err = None
    for _ in range(tries):
        try:
            return fn(), None
        except Exception as e:
            last_err = e
            time.sleep(delay)
    return None, last_err


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    old_id, new_id = int(sys.argv[1]), int(sys.argv[2])
    c = Scs0009PyController(serial_port=PORT, baudrate=1000000, timeout=0.5)

    pos, err = robust(lambda: c.read_present_position(old_id))
    if err:
        print(f"[중단] 현재 ID {old_id}로 서보 응답이 없습니다: {err!r}")
        print("       -> 서보가 정말 이 ID로 연결돼 있는지 scan_ids.py로 먼저 확인하세요.")
        sys.exit(1)
    print(f"[확인] ID {old_id} 응답 OK -> {pos}")

    # EEPROM 잠금을 먼저 풀어야 ID 변경이 전원 재연결 후에도 유지되는 서보가 있음
    _, lock_err = robust(lambda: c.write_lock(old_id, False))
    if lock_err:
        print(f"[참고] write_lock(False) 호출 에러(무시 가능할 수 있음): {lock_err!r}")
    else:
        print("[확인] EEPROM 잠금 해제(write_lock False) 완료")
    time.sleep(0.1)

    _, err = robust(lambda: c.write_id(old_id, new_id))
    # 주의: write 명령은 서보가 ACK를 안 보내는 경우가 많아서
    # 여기서 timeout 에러가 나도 "실패"가 아니라 정상일 수 있음 (아래에서 재확인함).
    if err:
        print(f"[참고] write_id 호출 중 에러 보고됨(정상 응답 미수신, ACK 없는 서보 특성일 수 있음): {err!r}")
    else:
        print("[확인] write_id 호출 완료 (ACK 수신)")

    time.sleep(0.5)

    pos_new, err_new = robust(lambda: c.read_present_position(new_id))
    pos_old, err_old = robust(lambda: c.read_present_position(old_id), tries=5)

    print()
    if err_new is None:
        print(f"[성공] 새 ID {new_id}로 응답 옴 -> {pos_new}")
    else:
        print(f"[실패] 새 ID {new_id}로도 응답 없음: {err_new!r}")

    if err_old is not None:
        print(f"[정상] 이전 ID {old_id}로는 더 이상 응답 없음 (ID 변경 성공 신호)")
    else:
        print(f"[경고] 이전 ID {old_id}로도 여전히 응답이 옵니다 -> {pos_old}")
        print("        두 서보가 동시에 연결돼 있었을 가능성이 있습니다. 물리적으로 하나만 연결됐는지 확인하세요.")


if __name__ == "__main__":
    main()
