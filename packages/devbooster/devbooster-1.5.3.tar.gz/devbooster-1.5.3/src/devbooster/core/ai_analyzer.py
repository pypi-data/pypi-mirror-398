"""
AI 기반 테이블 분석기
Qwen 2.5 Coder 7B 사용
"""

import subprocess
import json
from pathlib import Path

from openpyxl.styles.builtins import output

from .models import TableSpec

class AIAnalyzer:
    """AI 기반 분석기"""

    def __init__(self):
        """초기화"""
        self.available = self._check_qwen()
        if not self.available:
            print("⚠️ LLM을 찾을 수 없습니다. AI 기능 비활성화")

    def _check_qwen(self) -> bool:
        """Qwen 사용 가능 여부"""
        try:
            result = subprocess.run(
                ["ollama","list"],
                capture_output=True,
                timeout=5,
                text=False,
            )
            output = result.stdout.decode("utf-8", errors="replace")
            return "qwen2.5-coder" in output
        except:
            return False

    def analyze_pk(self, table: TableSpec) -> dict | None:
        """
        AI로 PK 분석

        Returns:
            {
                "pk": ["NOTICE_ID"],
                "confidence": 0.95,
                "reasoning": "..."
            }
        """
        if not self.available:
            return None

        try:
            # 프롬프트 생성
            prompt = self._build_prompt(table)

            # AI 호출
            response = self._call_qwen(prompt)

            # 파싱
            result = self._parse_response(response)

            return result
        except Exception as e:
            print(f"⚠️ AI 분석 실패: {e}")
            return None

    def _build_prompt(self, table: TableSpec) -> str:
        """프롬프트 생성"""

        # 컬럼 정보
        columns_desc = "\n".join([
            f"- {col.name} ({col.data_type}, "
            f"{'NOT NULL' if not col.nullable else 'NULL'}) - {col.comment}"
            for col in table.columns
        ])

        return f"""다음 테이블을 분석하여 Primary Key를 추천해주세요.
        반드시 JSON 형식으로만 답변하세요.
        
        테이블: {table.name}
        컬럼:
        {columns_desc}
        
        JSON 형식 (다른 텍스트 없이 이것만):
        {{
            "pk": ["컬럼명"],
            "confidence": 0.95,
            "reasoning": "간단한 이유"
        }}
        
        복합키인 경우:
        {{"pk": ["BOARD_ID", "FILE_SEQ"], "confidence": 0.9, "reasoning": "..."}}
"""

    def _call_qwen(self, prompt: str) -> str:
        """Qwen 호출"""

        try:
            result = subprocess.run(
                ["ollama","run","qwen2.5-coder:7b",prompt],
                capture_output=True,
                text=False,
                timeout=60,  # 1분 타임아웃
            )
            output = result.stdout.decode("utf-8", errors="replace")
            return output
        except subprocess.TimeoutExpired:
            print("⚠️   AI 응답 시간 초과 (60초)")
            return ""
        except Exception as e:
            print(f"⚠️  AI 호출 실패: {e}")
            return ""

    def _parse_response(self, response: str) -> dict | None:
        """JSON 파싱"""

        try:
            # JSON 부분만 추출
            start = response.find("{")
            end = response.rfind("}") + 1

            if start == -1 or end == 0:
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            # 검증
            if "pk" not in data or not isinstance(data["pk"],list):
                return None

            if "confidence" not in data:
                data["confidence"] = 0.8

            if "reasoning" not in data:
                data["reasoning"] = "AI 분석 결과"

            return data

        except json.JSONDecoder as e:
            print(f"⚠️  JSON 파싱 실패: {e}")
            return None
        except Exception as e:
            print(f"⚠️  응답 처리 실패: {e}")
            return None
