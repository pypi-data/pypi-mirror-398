"""
파일 생성 및 ZIP 압축

주요기능:
- 파일 저장 (인코딩 통일)
- 디렉토리 구조 생성
- ZIP 압축
- 결과 정리
"""

import zipfile
from pathlib import Path

class FileWriter:
    """파일 작성기"""

    def __init__(self, output_dir:str | Path = "generated"):
        """
        Writer 초기화

        Args:
            output_dir: 출력 디렉토리

        TODO:
            - [] 출력 디렉토리 검증
            - [] 덮어쓰기 옵션
        """

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 출력 디렉토리: {self.output_dir}")

    def write_files(
            self,
            files: dict[str, str],
            module: str
    ) -> list[Path]:
        """
        파일들 저장

        Args:
            files: {파일명: 내용} 딕셔너리
            module: 모듈명 (폴더명)

        Returns:
            생성된 파일 경로 리스트

        TODO:
            - [] 파일명 검증
            - [] 내용 검증
        """

        # 모듈 디렉토리 생성
        module_dir = self.output_dir / module
        module_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        for filename, content in files.items():
            file_path = module_dir / filename

            # 파일 저장  (UTF-8)
            file_path.write_text(
                content,
                encoding = "utf-8",
                newline = "\n"      # 개행 통일
            )

            created_files.append(file_path)
            print(f"✅ {file_path.relative_to(self.output_dir)}")

        return created_files

    def create_zip(
            self,
            zip_name: str = "generated.zip"
    ) -> Path:
        """
        ZIP 파일 생성

        Args:
            zip_name: ZIP 파일명

        Returns:
            생성된 ZIP 파일 경로

        TODO:
            - [] 압축 레벨 옵션
            - [] 제외 파일 패턴
        """

        zip_path = self.output_dir / zip_name

        # 기존 ZIP 삭제
        if zip_path.exists():
            zip_path.unlink()

        # ZIP 생성
        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zf:
            # output_dir 내 모든 파일 추가
            for file_path in self.output_dir.rglob("*"):
                # ZIP 파일 자신은 제외
                if file_path == zip_path:
                    continue

                # 디렉토리는 제외
                if file_path.is_dir():
                    continue

                # ZIP에 추가
                arcname = file_path.relative_to(self.output_dir)
                zf.write(file_path, arcname)
                print(f"📦 {arcname}")

        print(f"✅ ZIP 생성: {zip_path}")
        return zip_path

    def clean(self):
        """
        출력 디렉토리 정리

        TODO:
            - [] 확인 프롬프트
            - [] 부분 삭제 옵션
        """

        import shutil

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            print(f"🗑️ 삭제: {self.output_dir}")

# ==================== 테스트 ========================
if __name__ == "__main__":
    """
    테스트 실행
    
    python -m devbooster.core.writer
    """

    print("=" * 50)
    print("Writer 테스트")
    print("=" * 50)

    # 테스트 파일
    test_files = {
        "NoticeMapper.xml" : """<?xml version="1.0" encoding="UTF-8"?>
        <mapper namespace="egovframework.notice.service.impl.NoticeMapper">
            <select id="selectNoticeList">
                SELECT * FROM TB_NOTICE
            </select>
        </mapper>""",
        "NoticeVO.java" : """package egovframework.notice.service;
        public class NoticeVO {
            private Long noticeId;
            private String title;
            
            // getters/setters...
        }"""
    }

    # Writer 생성
    writer = FileWriter("test_output")

    # 파일 저장
    print("\n📝 파일 저장:")
    created = writer.write_files(test_files,"notice")
    print(f"총 {len(created)}개 파일 생성")

    # ZIP 생성
    print("\n📦 ZIP 생성:")
    zip_path = writer.create_zip("test.zip")

    # 결과 확인
    print("\n📊 결과:")
    print(f"    파일: {len(created)}개")
    print(f"    ZIP: {zip_path}")
    print(f"    크기: {zip_path.stat().st_size} bytes")

    # 정리 (주석처리)
    # writer.clean()

    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")
    print("=" * 50)

