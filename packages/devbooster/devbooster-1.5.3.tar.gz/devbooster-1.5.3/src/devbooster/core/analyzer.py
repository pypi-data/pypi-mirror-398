"""
테이블 진단 및 분석

주요 기능:
- PK 존재 여부 확인
- PK 품질 평가
- Identifier 후보 추천
- 경고/위험 요소 탐지
"""

from dataclasses import dataclass, field
from .models import TableSpec,ColumnSpec

# AI Analyzer import 안전하게
try:
    from .ai_analyzer import AIAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    AIAnalyzer = None

@dataclass
class TableDiagnosis:
    """테이블 진단 결과"""

    table: TableSpec
    has_pk: bool
    pk_quality: str     # "good", "weak", "none"
    identifier_candidates: list[list[str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    source: str = "rules"   # "explicit", "ai", "rules"
    ai_confidence: float | None = None # AI 신뢰도 (0-1)

    def __str__(self) -> str:
        """진단 결과 출력"""
        lines = [
            "=" * 50,
            f"테이블: {self.table.name}",
            "=" * 50,
            f"PK 존재: {'✅ Yes' if self.has_pk else '❌No'}",
            f"PK 품질: {self.pk_quality}",
        ]

        if self.warnings:
            lines.append("\n⚠️ 경고:")
            for w in self.warnings:
                lines.append(f" - {w}")

        if self.risks:
            lines.append("\n🚨 위험:")
            for r in self.risks:
                lines.append(f" - {r}")

        if self.identifier_candidates:
            lines.append("\n💡 추천 Identifier:")
            for i, candidate in enumerate(self.identifier_candidates[:3],1):
                cols_str = " + ".join(candidate)
                lines.append(f" {i}. {cols_str}")

        lines.append("=" * 50)
        return "\n".join(lines)

class TableAnalyzer:
    """테이블 분석기"""

    def __init__(self, use_ai: bool = True):
        """
        Args:
             use_ai: AI 분석 사용 여부
        """
        print(f"🔧   TableAnalyzer 초기화 (use_ai={use_ai})")

        self.use_ai = use_ai
        self.ai_analyzer = None

        # AI 초기화 (안전하게)
        if use_ai and AI_AVAILABLE:
            print(" AI 모듈 발견")
            try:
                self.ai_analyzer = AIAnalyzer()
                print(f"    AI 인스턴스 생성: {self.ai_analyzer}")
                print(f"    available: {self.ai_analyzer.available}")

                if self.ai_analyzer.available:
                    print("✅    AI 분석기 활성화")
                else:
                    print("⚠️   AI를 찾을 수 없습니다. 규칙 기반 사용")
                    self.ai_analyzer = None
            except Exception as e:
                print(f"⚠️  AI 초기화 실패: {e}")
                import traceback
                traceback.print_exc()
                self.ai_analyzer = None
        elif use_ai:
            print("⚠️   AI 모듈을 찾을 수 없습니다. 규칙 기반 사용")

    def analyze(self,table: TableSpec) -> TableDiagnosis:
        """
        테이블 진단

        Args:
            table: 분석할 테이블

        Returns:
            TableDiagnosis

        TODO:
            - [] 타입 일관성 체크
            - [] 네이밍 컨벤션 체크
            - [] 인덱스 제안
        """

        # 명시적 PK 확인
        explicit_pk = table.pk_columns

        if explicit_pk:
            # PK 명시됨 - 그대로 사용
            print("PK가 명시되어 사용합니다.")
            return TableDiagnosis(
                table=table,
                has_pk=True,
                pk_quality="good",
                identifier_candidates=[[col.name for col in explicit_pk]],
                warnings=[],
                risks=[],
                source="explicit"
            )

        # AI 분석 시도
        if self.use_ai and self.ai_analyzer and self.ai_analyzer.available:
            print("🤖 AI 분석 중..")
            try:
                ai_result = self.ai_analyzer.analyze_pk(table)
                if ai_result and ai_result.get("confidence",0) > 0.8:
                    print(f"✅   AI 추천: {ai_result['pk']}")

                    # AI 결과를 is_pk에 설정
                    for col in table.columns:
                        if col.name in ai_result['pk']:
                            col.is_pk = True

                    return TableDiagnosis(
                        table=table,
                        has_pk=False,
                        pk_quality="ai_recommended",
                        identifier_candidates=[ai_result["pk"]],
                        warnings=[
                            f"🤖 AI 추천: {', '.join(ai_result['pk'])}",
                            f"  신뢰도: {ai_result.get('confidence',0):.0%}",
                            f"  이유: {ai_result.get('reasoning','N/A')}"
                        ],
                        risks=["AI 추천은 참고용입니다. 검토 후 사용하세요."],
                        source="ai",
                        ai_confidence=ai_result.get('confidence',0)
                    )
            except Exception as e:
                print(f"⚠️  AI 분석 실패: {e}")

            print("⚠️   AI 분석 실패 - 규칙 기반 사용")

        # 규칙기반 풀백
        print("📄    규칙 기반 분석...")
        return self._analyzer_with_rules(table)

    def _analyzer_with_rules(self, table: TableSpec) -> TableDiagnosis:
        """규칙 기반 분석"""
        pk_candidates = []

        for col in table.columns:
            name_upper = col.name.upper()

            # FK 제외
            fk_prefixes = ("ENTRY_","ENT_","REG_","UPT_","UPD_","MOD_","CRT_")
            if any(name_upper.startswith(p) for p in fk_prefixes):
                continue

            # PK 패턴
            if name_upper.endswith(("_ID","_SEQ","_NO")):
                pk_candidates.append(col)
                col.is_pk = True

        if pk_candidates:

            # PK 검사
            has_pk = len(table.pk_columns) > 0
            pk_quality = self._assess_pk_quality(table)

            # 후보 추천
            candidates = self._recommend_identifiers(table)

            # 경고 생성
            warnings = self._generate_warnings(table,has_pk)

            # 위험 요소
            risks = self._detect_risks(table)

            return TableDiagnosis(
                table=table,
                has_pk=has_pk,
                pk_quality=pk_quality,
                identifier_candidates=candidates,
                warnings=warnings,
                risks=risks,
                source="rules"
            )

        return TableDiagnosis(
            table=table,
            has_pk=False,
            pk_quality="none",
            identifier_candidates=[],
            warnings=["⚠️   PK를 찾을 수 없습니다."],
            risks=["Excel에 PK 컬럼을 명시하세요."],
            source="rules"
        )

    def _assess_pk_quality(self, table: TableSpec) -> str:
        """
        PK 품질 평가

        Returns:
            "good": PK 있고 품질 좋음
            "weak": PK 있지만 문제 있음
            "none": PK 없음
            "poor": 형편없음
        """
        pk_cols = table.pk_columns

        if not pk_cols:
            return "none"

        # 단일 PK
        if len(pk_cols) == 1:
            col = pk_cols[0]
            # NOT NULL이고 숫자형이면 good
            if not col.nullable and col.data_type in ("NUMBER","INTEGER"):
                return "good"
            return "weak"

        # 너무 많은 복합키 -> weak
        if len(pk_cols) >= 3:
            return "weak"

        # TODO: 더 많은 품질 체크

        return "poor"

    def _recommend_identifiers(
            self,
            table: TableSpec,
    ) -> list[list[str]]:
        """
        Identifier 후보 추천

        Returns:
            추천 후보 리스트(점수 순)
            예: [["NOTICE_ID"],["USER_ID","REG_DATE"], ... ]

        TODO:
            - [] 복합키 조합 알고리즘 개선
            - [] 도메인 지식 반영
            - [] 통계 기반 추천

        """
        candidates_with_score = []

        # 1. PK가 있으면 그게 1순위
        pk_cols = table.pk_columns
        if pk_cols:
            candidates_with_score.append(
                ([col.name for col in pk_cols], 999, 0)
            )


        # 2. 단일 컬럼 후보
        for col in table.columns:
            score = self._score_column(col)

            if score >= 90:
                # 완벽한 단일키
                candidates_with_score.append(
                    ([col.name],score,1)
                )
            elif score >= 70:
                # 일반 단일키
                candidates_with_score.append(
                    ([col.name],score,3)
                )

        # 3. 2개 복합키 후보 (간단히)
        # TODO: 더 똑똑한 조합 알고리즘
        for i, col1 in enumerate(table.columns):
            for col2 in table.columns[i+1:]:
                score1 = self._score_column(col1)
                score2 = self._score_column(col2)
                avg_score = (score1 + score2) / 2

                # 복합 패턴을 조금 더 위로 (게시판번호+ 파일seq 등으로 구성된 유형때문에..)
                if self._is_practical_compound(col1,col2):
                    # 실용적 복합키
                    candidates_with_score.append(
                        ([col1.name, col2.name], avg_score, 2)
                    )
                elif avg_score >= 60:
                    # 일반 복합키
                    candidates_with_score.append(
                        ([col1.name,col2.name], avg_score, 4)
                    )

        # 점수로 정렬
        candidates_with_score.sort(
            key=lambda x: (x[2], -x[1])
        )

        # 중복 제거 (set 사용 못 하니 수동)
        unique_candidates = []
        seen = set()
        for candidate, _, _ in candidates_with_score:
            key = tuple(sorted(candidate))
            if key not in seen:
                seen.add(key)
                unique_candidates.append(candidate)

        return unique_candidates[:5]       # 상위 5개만

    def _is_practical_compound(
            self,
            col1: ColumnSpec,
            col2: ColumnSpec
    ) -> bool:
        """실용적인 복합키 패턴 감지"""

        name1 = col1.name.lower()
        name2 = col2.name.lower()

        # ID + SEQ
        if('id' in name1 and 'seq' in name2) or \
            ('seq' in name1 and 'id' in name2):
            return True

        # ID + NO
        if('id' in name1 and 'no' in name2) or \
            ('no' in name1 and 'id' in name2):
            return True

        # ID + DATE (NOT NULL만)
        if('id' in name1 and 'date' in name2) or \
                ('date' in name1 and 'id' in name2):
            return True

        # CODE + CODE
        if 'cd' in name1 and 'cd' in name2:
            return True

        return False



    def _score_column(self, col: ColumnSpec) -> int:
        """
        컬럼 점수 계산(0-100)

        점수 기준:
        - id/no/seq/key 포함: +30
        - NOT NULL: +30
        - 적절한 타입: +20
        - 적절한 길이: +10
        - 날짜/시간 단독: -20

        TODO:
            - [] 도메인별 가중치
            - [] 학습 기반 점수

        """

        score = 0
        name_lower = col.name.lower()

        # 1. 컬럼명에 식별자 키워드 포함
        id_keywords = ["id","no","seq","key","code","num"]
        if any(keyword in name_lower for keyword in id_keywords):
            score += 30

        # 2. NOT NULL
        if not col.nullable:
            score += 30

        # 3. 타입 적합성
        good_types = ["NUMBER","VARCHAR2","VARCHAR","BIGINT","INT"]
        if col.data_type in good_types:
            score += 20

        # 4. 길이 적절 (너문 길면 식별자로 부적합)
        if col.length:
            if col.length <= 50:
                score += 10
            elif col.length > 200:
                score -= 10

        # 5. 날짜/시간 단독은 감점 (중복 가능성)
        if col.data_type in ["DATE","TIMESTAMP","DATETIME"]:
            score -= 20

        # 6. 이미 PK면 가산점
        if col.is_pk:
            score += 20

        return max(0, min(100, score))

    def _generate_warnings(
            self,
            table: TableSpec,
            has_pk: bool
    ) -> list[str]:
        """
        경고 메시지 생성

        TODO:
            - [] 더 많은 경고 케이스
        """

        warnings = []

        # PK 없음
        if not has_pk:
            warnings.append("PK 없음 - Identifier 지정 필요")

        # 논리삭제 컬럼 없음
        if not table.logical_delete:
            warnings.append("USE_YN/DEL_YN 없음 - 물리삭제 사용")

        # TODO: 더 많은 경고

        return warnings

    def _detect_risks(self, table: TableSpec) -> list[str]:
        """
        위험 요소 탐지

        TODO:
            - [] 더 많은 위험 케이스
        """

        risks = []

        # PK에 nullable 컬럼
        pk_cols = [col for col in table.columns if col.is_pk]
        if any(col.nullable for col in pk_cols):
            risks.append("PK에 nullable 컬럼 포함")

        # 컬럼 수 너무 많음
        if len(table.columns) > 50:
            risks.append(f"컬럼 수 과다 ({len(table.columns)}개)")

        # TODO: 더 많은 위험 요소

        return risks


# =================== 테스트 ==========================
if __name__ == "__main__":
    """
    테스트 실행
    
    python -m devbooster.core.analyzer
    """

    from .models import ColumnSpec,TableSpec

    print("=" * 50)
    print("Analyzer 테스트")
    print("=" * 50)

    # 테스트 데이터: PK 없는 테이블
    columns = [
        ColumnSpec(
            name="USER_ID",
            data_type="VARCHAR2",
            length=20,
            nullable=False,
            default=None,
            comment="사용자ID"
        ),
        ColumnSpec(
            name="USER_NAME",
            data_type= "VARCHAR2",
            length=100,
            nullable=True,
            default=None,
            comment="사용자명"
        ),
        ColumnSpec(
            name="REG_DATE",
            data_type="DATE",
            length=None,
            nullable=False,
            default="SYSDATE",
            comment="등록일"
        ),
        ColumnSpec(
            name="USE_YN",
            data_type="CHAR",
            length=1,
            nullable=False,
            default="Y",
            comment="사용여부"
        )
    ]

    # PK 없는 테이블
    table = TableSpec(name="TB_USER", columns=columns)

    # 분석
    analyzer = TableAnalyzer()
    diagnosis = analyzer.analyze(table)

    # 결과 출력
    print(diagnosis)

    # 상세 정보
    print("\n📊 컬럼별 점수:")
    for col in columns:
        score = analyzer._score_column(col)
        print(f" {col.name:20} -> {score:3d}점")