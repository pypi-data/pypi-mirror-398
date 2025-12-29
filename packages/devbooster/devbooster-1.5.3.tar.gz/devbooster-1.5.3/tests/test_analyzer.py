"""
analyzer.py 테스트
"""

import pytest
from devbooster.core.analyzer import TableAnalyzer, TableDiagnosis
from devbooster.core.models import TableSpec, ColumnSpec

def test_analyzer_with_pk():
    """PK가 있는 테이블 리스트"""

    columns = [
        ColumnSpec(
            name="NOTICE_ID",
            data_type="NUMBER",
            length=10,
            nullable=False,
            default=None,
            comment="공지ID"
        ),
        ColumnSpec(
            name="TITLE",
            data_type="VARCHAR2",
            length=200,
            nullable=False,
            default=None,
            comment="제목"
        ),
    ]

    table = TableSpec(name="TB_NOTICE", columns=columns)

    analyzer = TableAnalyzer()
    diagnosis = analyzer.analyze(table)

    # 검증
    assert diagnosis.has_pk == True
    assert diagnosis.pk_quality == "good"
    assert len(diagnosis.identifier_candidates) > 0
    assert "NOTICE_ID" in diagnosis.identifier_candidates[0]

def test_analyzer_without_pk():
    """PK 없는 테이블 리스트"""

    columns = [
        ColumnSpec(
            name="USER_NAME",
            data_type="VARCHAR2",
            length=100,
            nullable=True,
            default=None,
            comment="사용자명"
        ),
    ]

    table = TableSpec(name="TB_USER", columns=columns)

    analyzer = TableAnalyzer()
    diagnosis = analyzer.analyze(table)

    # 검증
    assert diagnosis.has_pk == False
    assert diagnosis.pk_quality == "none"
    assert "PK 없음" in diagnosis.warnings[0]

def test_score_column():
    """컬럼 점수 테스트"""

    analyzer = TableAnalyzer()

    # 종은 컬럼(id+ NOT NULL + 적절한 타입)
    good_col = ColumnSpec(
        name="USER_ID",
        data_type="NUMBER",
        length=10,
        nullable=False,
        default=None,
        comment="사용자ID"
    )

    score = analyzer._score_column(good_col)
    assert score >= 70  # 높은 점수

    # 나쁜 컬럼 (nullable + 긴 길이)
    bad_col = ColumnSpec(
        name="DESCRIPTION",
        data_type="VARCHAR2",
        length=500,
        nullable=True,
        default=None,
        comment="설명"
    )

    score = analyzer._score_column(bad_col)
    assert score < 50   # 낮은 점수

# TODO: 더 많은 테스트 케이스


