"""
버스에 연결된 서보의 ID를 확인하는 스크립트.
통신이 원래 좀 불안정한 버스라, 여러 번 반복해서 성공률/관측값을 통계로 보여줌.

사용법:
    python3 scan_ids.py            # ID 1, 2 확인 (기본)
    python3 scan_ids.py 1 2 3      # 원하는 ID들 확인
"""
import sys
import time
from collections import Counter
from rustypot import Scs0009PyController

PORT = "/dev/cu.usbmodem5B790178941"  # ls /dev/cu.* 로 확인한 실제 포트로 바꿀 것
N_TRIES = 25


def main():
    ids = [int(x) for x in sys.argv[1:]] or [1, 2]
    c = Scs0009PyController(serial_port=PORT, baudrate=1000000, timeout=0.3)

    for sid in ids:
        ok, fail = 0, 0
        values = Counter()
        for _ in range(N_TRIES):
            try:
                pos = c.read_present_position(sid)
                ok += 1
                values[round(pos[0], 3)] += 1
            except Exception:
                fail += 1
            time.sleep(0.05)

        print(f"ID {sid}: 성공 {ok}/{N_TRIES}, 실패 {fail}/{N_TRIES}, 관측값 분포: {dict(values)}")

        if len(values) >= 2:
            print(f"  -> ⚠️ 값이 2개 이상 섞여 나옴 = 이 ID에 서보가 2개 이상 물려있어 충돌 중일 가능성 높음")
        elif ok == 0:
            print(f"  -> 이 ID로 응답하는 서보 없음")
        else:
            print(f"  -> 정상: 이 ID에 서보 1개만 응답 중")


if __name__ == "__main__":
    main()
