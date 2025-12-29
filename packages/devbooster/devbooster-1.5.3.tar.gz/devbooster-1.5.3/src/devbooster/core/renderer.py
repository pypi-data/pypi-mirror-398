"""
템플릿 렌더링 엔진

주요 기능:
- jinja2 환경 설정
- 템플릿 로드
- 컨텍스트 빌드
- 코드 생성
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from .models import TableSpec, ColumnSpec

class TemplateRenderer:
    """템플릿 렌더러"""

    def __init__(self, framework: str = "egov", database: str = "oracle"):
        """
        렌더러 초기화

        Args:
            framework: 프레임워크 (egov, boot)
            database: 데이터베이스 (oracle, mysql)

        TODO:
            - [] 프레임워크별 검증
            - [] 템플릿 존재 확인
        """

        self.framework = framework
        self.database = database

        # 템플릿 디렉토리 설정
        template_dir = self._get_template_dir()

        # jinja2 환경 생성
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 커스텀 필터 등록
        self._register_filters()

        print(f"📁 템플릿 디렉토리: {template_dir}")

    def _get_template_dir(self) -> Path:
        """템플릿 디렉토리 경로"""

        # src/devbooster/templates/egov/oracle/
        base_dir = Path(__file__).parent.parent / "templates"
        template_dir = base_dir / self.framework / self.database

        if not template_dir.exists():
            raise FileNotFoundError(
                f"템플릿 디렉토리 없음: {template_dir}"
            )

        return template_dir

    def _register_filters(self):
        """Jinja2 커스텀 필터 등록"""

        self.env.filters["camel"] = self._to_camel_case
        self.env.filters["pascal"] = self._to_pascal_case
        self.env.filters["lower"] = str.lower
        self.env.filters["upper"] = str.upper

    def _to_camel_case(self, snake_str: str) -> str:
        """
        snake_case -> camelCase

        예: NOTICE_ID -> noticeId
        """
        parts = snake_str.lower().split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    def _to_pascal_case(self, snake_str: str) -> str:
        """
        snake_case -> PascalCase

        예: NOTICE_ID -> NoticeId
        """
        parts = snake_str.lower().split("_")
        return "".join(p.capitalize() for p in parts)

    def render_mapper(
            self,
            table: TableSpec,
            identifier: list[str] | None = None
    ) -> str:
        """
        Mapper.xml 생성

        Args:
            table: 테이블 스펙
            identifier: Identifier 컬럼들 (없으면 PK 사용)

        Returns:
            생성된 Mapper.xml 내용

        TODO:
            - [] 동적 쿼리 개선
            - [] 페이징 처리
            - [] 조인 쿼리
        """

        # Identifier 기본값
        if identifier is None:
            identifier = table.pk_columns

        # 컨텍스트 빌드
        context = self._build_context(table, identifier)

        # 템플릿 렌더링
        template = self.env.get_template("mapper.xml.j2")
        return template.render(context)

    def render_vo(self, table: TableSpec) -> str:
        """
        VO.java 생성

        Args:
            table: 테이블 스펙

        Returns:
            생성된 VO.java 내용

        TODO:
            - [] Lombok 지원
            - [] Validation 어노테이션
            - [] 상속 구조
        """

        # 컨텍스트 빌드
        context = self._build_context(table)

        # 템플릿 렌더링
        template = self.env.get_template("vo.java.j2")
        return template.render(context)

        # 임시: 간단한 VO 생성
        # return self._generate_simple_vo(table)

    def render_mapper_java(self, table: TableSpec) -> str:
        """
        Mapper.java 생성

        Args:
            table: 테이블 스펙

        Returns:
            생성된 Mapper.java 내용
        """

        context = self._build_context(table)

        template = self.env.get_template("mapper.java.j2")
        return template.render(context)

    def render_service(self, table: TableSpec) -> str:
        """
        Service.java 생성

        Args:
            table: 테이블 스펙

        Returns:
            생성된 Service.java 내용
        """

        context = self._build_context(table)

        template = self.env.get_template("service.java.j2")
        return template.render(context)

    def render_service_impl(self, table: TableSpec) -> str:
        """
        ServiceImpl.java 생성

        Args:
            table: 테이블 스펙

        Returns:
            생성된 ServiceImpl.java 내용
        """

        context = self._build_context(table)

        template = self.env.get_template("service_impl.java.j2")
        return template.render(context)

    def render_controller(self, table: TableSpec) -> str:
        """
        Controller.java 생성

        Args:
            table: 테이블 스펙

        Returns:
            생성된 Controller.java 내용
        """

        context = self._build_context(table)

        template = self.env.get_template("controller.java.j2")
        return template.render(context)

    def _build_context(
            self,
            table: TableSpec,
            identifier: list[str] | None = None
    ) -> dict:
        """
        템플릿 컨텍스트 빌드

        Returns:
            템플릿에서 사용할 변수들
        """

        return{
            # 테이블 정보
            "table": table,
            "table_name": table.name,
            "module": table.module,
            "class_name": table.class_name,

            # 컬럼 정보
            "columns": table.columns,
            "pk_columns": table.pk_columns,

            # Identifier
            "identifier": identifier or table.pk_columns,

            # 특수 기능
            "has_use_yn": table.has_use_yn,
            "has_del_yn": table.has_del_yn,
            "has_secret_yn": table.has_secret_yn,
            "has_file": table.has_file,
            "logical_delete": table.logical_delete,

            # 설정
            "framework": self.framework,
            "database": self.database,
        }

    def _generate_simple_vo(self, table: TableSpec) -> str:
        """
        간단한 VO 생성 (템플릿 없이)

        TODO: 템플릿으로 대체
        """

        lines = [
            f"package egovframework.{table.module}.service;",
            "",
            "/**",
            f" * {table.name} VO",
            " */",
            f"public class {table.class_name}VO {{",
            "",
        ]

        # 필드
        for col in table.columns:
            lines.append(f"    /** {col.comment} */")
            java_type = col.java_type
            field_name = self._to_camel_case(col.name)
            lines.append(f"     private {java_type} {field_name};")
            lines.append("")

        # Getter/Setter (간단히)
        for col in table.columns:
            java_type = col.java_type
            field_name = self._to_camel_case(col.name)
            method_name = self._to_pascal_case(col.name)

            # Getter
            lines.append(f"    public {java_type} get{method_name}() {{")
            lines.append(f"         return {field_name};")
            lines.append("      }")
            lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def render_all(
            self,
            table: TableSpec,
            identifier: list[str] | None = None
    ) -> dict[str, str]:
        """
        모든 파일 생성

        Args:
            table: 테이블 스펙
            identifier: Identifier

        Returns:
            {파일명: 내용} 딕셔너리
        """

        outputs = {}

        # Mapper.xml
        mapper_context = self.render_mapper(table, identifier)
        outputs[f"{table.class_name}Mapper.xml"] = mapper_context

        # VO.java
        vo_content = self.render_vo(table)
        outputs[f"{table.class_name}VO.java"] = vo_content

        # Mapper.java
        mapper_java_content = self.render_mapper_java(table)
        outputs[f"{table.class_name}Mapper.java"] = mapper_java_content

        # Service.java
        vo_service = self.render_service(table)
        outputs[f"{table.class_name}Service.java"] = vo_service

        # ServiceImpl.java
        vo_service_impl = self.render_service_impl(table)
        outputs[f"{table.class_name}ServiceImpl.java"] = vo_service_impl

        # Controller.java
        vo_controller = self.render_controller(table)
        outputs[f"{table.class_name}Controller.java"] = vo_controller

        return outputs


# ================== 테스트 ==========================
if __name__ == "__main__":
    """
    테스트 실행
    
    python -m devbooster.core.renderer
    """

    from .models import ColumnSpec, TableSpec

    print("=" * 50)
    print("Renderer 테스트")
    print("=" * 50)

    # 테스트 데이터
    columns = [
        ColumnSpec(
            name="NOTICE_ID",
            data_type="NUMBER",
            length=10,
            nullable=False,
            default=None,
            comment="공지사항ID"
        ),
        ColumnSpec(
            name="TITLE",
            data_type="VARCHAR2",
            length=200,
            nullable=False,
            default=None,
            comment="제목"
        ),
        ColumnSpec(
            name="CONTENT",
            data_type="CLOB",
            length=None,
            nullable=True,
            default=None,
            comment="내용"
        ),
        ColumnSpec(
            name="USE_YN",
            data_type="CHAR",
            length=1,
            nullable=False,
            default="Y",
            comment="사용여부"
        ),
    ]

    table = TableSpec(name="TB_NOTICE", columns=columns)

    # 렌더러 생성
    try:
        renderer = TemplateRenderer()

        # 전체 생성
        outputs = renderer.render_all(table)

        print(f"\n✅ {len(outputs)}개 파일 생성:")
        for filename in outputs.keys():
            print(f"  - {filename}")

        # Mapper.xml 미리보기
        print("\n📄 NoticeMapper.xml 미리보기:")
        print("-" * 50)
        mapper = outputs["NoticeMapper.xml"]
        print(mapper[:500] + "..." if len(mapper) > 500 else mapper)

    except FileNotFoundError as e:
        print(f"\n⚠️ {e}")
        print("-> 템플릿 파일을 먼저 만들어주세요!")

