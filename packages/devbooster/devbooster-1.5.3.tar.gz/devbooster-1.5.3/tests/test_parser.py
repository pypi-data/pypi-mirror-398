"""
parser.py 테스트
"""

import pytest
from pathlib import Path
from devbooster.core.parser import parse_excel,_parse_column
from devbooster.core.models import ColumnSpec
import pandas as pd

def test_parse_column():
    """컬럼 파싱 테스트"""

    # 샘플 데이터
    row = pd.Series({
        "컬럼명": "NOTICE_ID",
        "데이터타입": "NUMBER",
        "길이": 10,
        "NULL": "N",
        "기본값": None,
        "설명": "공지사항ID"
    })

    # 파싱
    col = _parse_column(row)

    # 검증
    assert col.name == "NOTICE_ID"
    assert col.data_type == "NUMBER"
    assert col.length == 10
    assert col.nullable == False
    assert col.comment == "공지사항ID"
    assert col.is_pk == True

def test_parse_column_with_default():
    """기본값 있는 컬럼 테스트"""

    row = pd.Series({
        "컬럼명": "USE_YN",
        "데이터타입": "CHAR",
        "길이": 1,
        "NULL": "N",
        "기본값": "Y",
        "설명": "사용여부"
    })

    col = _parse_column(row)

    assert col.name == "USE_YN"
    assert col.default == "Y"
    assert col.is_special == True
    assert col.special_type == "USE_YN"


def test_parse_excel_not_exists():
    """파일 없을 때 에러"""

    with pytest.raises(FileNotFoundError):
        parse_excel("not_exist.xlsx")


# TODO: 실제 Excel 파일 테스트
# def test_parse_excel_real_file():
#   """실제 파일 파싱 테스트"""
#   tables = parse_excel("examples/test_simple.xlsx")
#   assert len(tables) > 0