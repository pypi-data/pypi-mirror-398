"""설정 로더 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트를 파이썬 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root/"src"))

from devbooster.config.config_loader import (
    PROJECT_ROOT,
    CONFIG_DIR,
    get_table_patterns,
    get_table_whitelist,
    get_pk_patterns,
    get_prefix_patterns,
    get_column_patterns
)

print("=" * 50)
print("설정 로더 테스트")
print("=" * 50)

# 1. 경로 확인
print(f"\n[경로확인]")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"CONFIG_DIR: {CONFIG_DIR}")
print(f"CONFIG_DIR 존재? {CONFIG_DIR.exists()}")

# 2. 설정파일 목록
print(f"\n[설정 파일 목록]")
if CONFIG_DIR.exists():
    for file in sorted(CONFIG_DIR.glob("*.txt")):
        size = file.stat().st_size
        print(f"    ✅ {file.name:30s} ({size:,} bytes)")
else:
    print(" ❌ CONFIG_DIR이 존재하지 않습니다!")

# 3. 패턴 로드 테스트
print(f"\n[패턴 로드 테스트]")

print(f"\n1. table_rules.txt:")
table_patterns = get_table_patterns()
for i, pattern in enumerate(table_patterns, 1):
    print(f"  {i}. {pattern}")

print(f"\n2. table_whitelist.txt:")
whitelist = get_table_whitelist()
if whitelist:
    for i, pattern in enumerate(whitelist, 1):
        print(f"  {i}. {pattern}")
else:
    print("  (비어있음)")

print(f"\n3. pk_rules.txt:")
pk_patterns = get_pk_patterns()
if pk_patterns:
    for i, pattern in enumerate(pk_patterns, 1):
        print(f"  {i}. {pattern}")
else:
    print("  (비어있음)")

print(f"\n4. prefix_rules.txt:")
prefix_patterns = get_prefix_patterns()
if prefix_patterns:
    for i, pattern in enumerate(prefix_patterns, 1):
        print(f"  {i}. {pattern}")
else:
    print("  (비어있음)")

print(f"\n5. column_rules.txt:")
column_patterns = get_column_patterns()
if column_patterns:
    for i, pattern in enumerate(column_patterns, 1):
        print(f"  {i}. {pattern}")
else:
    print("  (비어있음)")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)