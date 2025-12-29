"""
Excel 파일 -> TableSpec 변환

주요 기능 :
- Excel 파일 읽기 (pandas)
- 시트별 테이블 파싱
- ColumnSpec 생성
- TableSpec 생성
"""

import pandas as pd
import re
from pathlib import Path

from devbooster.config.config_loader import get_table_patterns, get_table_whitelist
from .models import TableSpec, ColumnSpec

def parse_excel(file_path: str | Path) -> list[TableSpec]:
    """
    Excel 파일에서 테이블 정보 추출

    Args:
        file_path: Excel 파일 경로

    Example:
        >>> tables = parse_excel("examples/tables.xlsx")
        >>> print(tables[0].name)
        TB_NOTICE

    TODO:
        - [] 여러 시트 동시 처리
        - [] 에러 처리 강화
        - [] 컬럼명 검증
        - [] 진행률 표시

    """
    file_path = Path(file_path)

    # 파일 존재 확인
    if not file_path.exists():
        raise FileNotFoundError(f"파일 없음: {file_path}")

    # Excel 파일 열기
    excel_file = pd.ExcelFile(file_path)

    tables = []

    # 각 시트 처리
    for sheet_name in excel_file.sheet_names:

        if not _is_valid_table_name(sheet_name):
            print(f" 건너뜀: {sheet_name}")
            continue

        print(f" 파싱 중: {sheet_name}")

        # 시트 읽기
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # TableSpec 생성
        table = _parse_sheet(df,sheet_name)
        tables.append(table)

        print(f"✅ {sheet_name}: {len(table.columns)}개 컬럼")

    return tables

def _parse_sheet(df: pd.DataFrame, sheet_name: str) -> TableSpec:
    """
    시트 하나 -> TableSpec

    Args:
        df: pandas DataFrame
        sheet_name: 시트명 (테이블명)

    Returns:
        TableSpec

    TODO:
        - [] 필수 컬럼 검증
        - [] 빈 행 처리
        - [] 중복 컬럼명 체크

    """

    # 필수 컬럼 확인
    required_columns = ["컬럼명", "데이터타입", "NULL", "설명"]
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"{sheet_name}: 필수 컬럼 없음 = {missing}")

    # 각 행 -> ColumnSpec
    columns = []
    for idx, row in df.iterrows():
        try:
            col = _parse_column(row)
            columns.append(col)
        except Exception as e:
            print(f"⚠️ {sheet_name} 행 {idx+2} 에러: {e}")
            # TODO: 에러처리 개선
            continue

    if not columns:
        raise ValueError(f"{sheet_name}: 컬럼 없음")

    #TableSpec 생성
    return TableSpec(
        name=sheet_name,
        columns=columns
    )

def _parse_column(row: pd.Series) -> ColumnSpec:
    """
    DataFrame 행 하나 -> ColumnSpec

    Args:
        row: pandas Series

    Returns:
        ColumnSpec

    TODO:
        - [] 데이터 타입 정규화
        - [] 기본값 파싱 개선
        - [] NULL 체크 강화

    """

    # 컬럼명 (필수)
    name = str(row["컬럼명"]).strip()

    # TODO: VARCHAR2 등은 괄호 안에 length가 포함되는 경우가 많음. 예) VARCHAR2(100)
    #   매핑 실패할 가능성이 있으므로 추후 확인 후 fix 할 것.
    # 데이터 타입 (필수)
    data_type = str(row["데이터타입"]).strip().upper()

    # 길이 (선택)
    length = None
    if "길이" in row and pd.notna(row["길이"]):
        try:
            length = int(row["길이"])
        except:
            length = None

    # NULL 허용 (필수)
    nullable = str(row['NULL']).strip().upper() == "Y"

    # PK 명시 (선택)
    explicit_pk = False
    if 'PK' in row and pd.notna(row["PK"]):
        explicit_pk = str(row["PK"]).strip().upper() == "Y"

    # 기본값 (선택)
    default = None
    if "기본값" in row and pd.notna(row["기본값"]):
        default = str(row['기본값']).strip()

    # 설명 (필수)
    comment = str(row["설명"]).strip()

    col = ColumnSpec(
        name=name,
        data_type=data_type,
        length=length,
        nullable=nullable,
        default=default,
        comment=comment,
        explicit_pk=explicit_pk,
    )

    return col

def _is_valid_table_name(name: str) -> bool:
    """
    테이블명 유효성

    순서:
        1. 화이트리스트 체크 (우선순위 최상위)
        2. 제외 패턴 체크

    Args:
        name: 테이블명

    Returns:
        bool: 유효하면 True, 제외대상이면 False
    """

    name_upper = name.upper()

    # 화이트 리스트 체크 (리스트에 있으면 무조건 허용)
    whitelist = get_table_whitelist()
    for pattern in whitelist:
        if re.search(pattern, name_upper):
            return True


    # 제외 테이블 패턴
    exclude_patterns = get_table_patterns()

    for pattern in exclude_patterns:
        if re.search(pattern, name_upper):
            return False

    return True

# =========================== 테스트 ===============================
if __name__ == "__main__":
    """
    간단 테스트
    
    실행: python -m devbooster.core.parser
    """

    print("=" * 50)
    print("Parser 테스트")
    print("=" * 50)

    # TODO: 실제 Excel 파일로 테스트
    test_file = "examples/test_simple.xlsx"

    if Path(test_file).exists():
        tables = parse_excel(test_file)

        for table in tables:
            print(f"\n테이블: {table.name}")
            print(f"모듈: {table.module}")
            print(f"클래스: {table.class_name}")
            print(f"컬럼 수: {len(table.columns)}")
            print(f"PK: {table.pk_columns}")

    else:
        print(f"⚠️ 샘플 파일 없음: {test_file}")
        print("-> examples/test_simple.xlsx 만들어주세요!")

    print("\n"+"="*50)