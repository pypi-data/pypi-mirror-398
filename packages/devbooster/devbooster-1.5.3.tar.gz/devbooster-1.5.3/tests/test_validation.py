"""테이블명 검증 테스트"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from devbooster.core.parser import _is_valid_table_name

print("=" * 60)
print("테이블명 검증 테스트")
print("=" * 60)

# 테스트 케이스: (테이블명, 예상결과, 설명)
test_cases = [
    # 정상 테이블
    ("TB_USERS", True, "정상 테이블"),
    ("T_ORDERS", True, "정상 테이블"),
    ("PRODUCTS", True, "정상 테이블"),
    ("USER_ADDRESSES", True, "정상 테이블"),

    # 접미사 패턴
    ("TB_USERS_BAK", False, "백업 접미사"),
    ("ORDERS_TEMP", False, "임시 접미사"),
    ("PRODUCTS_OLD", False, "구버전 접미사"),
    ("ITEMS_TEST", False, "테스트 접미사"),

    # 접두사 패턴
    ("TEMP_ORDERS", False, "임시 접두사"),
    ("TEST_PRODUCTS", False, "테스트 접두사"),
    ("BACKUP_USERS", False, "백업 접두사"),

    # 날짜 패턴
    ("TB_USERS_20241225", False, "날짜 접미사 (8자리)"),
    ("ORDERS_241225", False, "날짜 접미사 (6자리)"),
    ("20241225_USERS", False, "날짜 접두사 (8자리)"),
    ("241225_ORDERS", False, "날짜 접두사 (6자리)"),
]

print("\n[테스트 실행]\n")

success_count = 0
fail_count = 0

for table_name, expected, description in test_cases:
    result = _is_valid_table_name(table_name)

    if result == expected:
        status = "✅"
        success_count += 1
    else:
        status = "❌"
        fail_count += 1

    result_str = "허용" if result else "차단"
    expected_str = "허용" if expected else "차단"

    print(f"{status} {table_name:25s} → {result_str:4s} (예상: {expected_str:4s}) | {description}")

print("\n" + "=" * 60)
print(f"결과: 성공 {success_count}개 / 실패 {fail_count}개 / 총 {len(test_cases)}개")
print("=" * 60)

if fail_count == 0:
    print("🎉 모든 테스트 통과!")
else:
    print(f"⚠️ {fail_count}개 테스트 실패!")