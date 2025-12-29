"""설정 파일 로더"""

import os
from pathlib import Path


CONFIG_DIR = Path(__file__).parent / "config_data"

def load_patterns_from_file(filename: str) -> list[str]:
    """
    설정 파일에서 패턴 로드

    Args:
        filename: 파일명 (예: "table_rules.txt")

    Returns:
        list[str]: 패턴 리스트 (주석/빈 줄 제외)
    """
    file_path = CONFIG_DIR / filename

    if not file_path.exists():
        print(f"⚠️  설정 파일 없음: {file_path}")
        return []

    patterns = []
    with open(file_path, 'r', encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 빈 줄, 주석, 구분선 무시
            if not line or line.startswith("#") or line.startswith("=") or line.startswith("-"):
                continue

            patterns.append(line)

    return patterns

# 전역 캐싱
_TABLE_WHITELIST: list[str] = []
_TABLE_PATTERNS: list[str] = []
_PK_PATTERNS: list[str] = []
_PREFIX_PATTERNS: list[str] = []
_COLUMN_PATTERNS: list[str] = []

def get_table_whitelist() -> list[str]:
    """테이블 제외 패턴 가져오기 (캐싱)"""
    global _TABLE_WHITELIST
    if not _TABLE_WHITELIST:
        _TABLE_WHITELIST = load_patterns_from_file("table_whitelist.txt")
        print(f"✅   table_whitelist.txt 로드: {len(_TABLE_WHITELIST)}개 패턴")
    return _TABLE_WHITELIST

def get_table_patterns() -> list[str]:
    """테이블 제외 패턴 가져오기 (캐싱)"""
    global _TABLE_PATTERNS
    if not _TABLE_PATTERNS:
        _TABLE_PATTERNS = load_patterns_from_file("table_rules.txt")
        print(f"✅   table_rules.txt 로드: {len(_TABLE_PATTERNS)}개 패턴")
    return _TABLE_PATTERNS

def get_pk_patterns() -> list[str]:
    """PK 명명 규칙 가져오기 (캐싱)"""
    global _PK_PATTERNS
    if not _PK_PATTERNS:
        _PK_PATTERNS = load_patterns_from_file("pk_rules.txt")
        print(f"✅   pk_rules.txt 로드: {len(_PK_PATTERNS)}개 패턴")
    return _PK_PATTERNS


def get_prefix_patterns() -> list[str]:
    """접두사 명명 규칙 가져오기 (캐싱)"""
    global _PREFIX_PATTERNS
    if not _PREFIX_PATTERNS:
        _PREFIX_PATTERNS = load_patterns_from_file("prefix_rules.txt")
        print(f"✅   prefix_rules.txt 로드: {len(_PREFIX_PATTERNS)}개 패턴")
    return _PREFIX_PATTERNS

def get_column_patterns() -> list[str]:
    """컬럼 규칙 가져오기 (캐싱)"""
    global _COLUMN_PATTERNS
    if not _COLUMN_PATTERNS:
        _COLUMN_PATTERNS = load_patterns_from_file("column_rules.txt")
        print(f"✅   column_rules.txt 로드: {len(_COLUMN_PATTERNS)}개 패턴")
    return _COLUMN_PATTERNS

def reload_all_configs():
    """모든 설정 리로드 (런타임 중 파일 수정 시)"""
    global _TABLE_PATTERNS, _PK_PATTERNS, _COLUMN_PATTERNS, _PREFIX_PATTERNS
    _TABLE_PATTERNS = []
    _PK_PATTERNS = []
    _COLUMN_PATTERNS = []
    _PREFIX_PATTERNS = []
    print("✅    모든 설정 파일 리로드 완료!")


######### 테스트 ################
if __name__ == "__main__":
    """
    실행:
        python -m src.devbooster.config.config_loader
    """

    print(f"현재 파일: {Path(__file__)}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"CONFIG_DIR: {CONFIG_DIR}")
    print(f"CONFIG_DIR 존재? {CONFIG_DIR.exists()}")

    if CONFIG_DIR.exists():
        print(f"\n설정 파일 목록:")
        for file in CONFIG_DIR.glob("*.txt"):
            print(f"    - {file.name}")

    print(f"\n테스트: table_rules.txt 로드")
    patterns = get_table_patterns()
    for p in patterns:
        print(f"    - {p}")