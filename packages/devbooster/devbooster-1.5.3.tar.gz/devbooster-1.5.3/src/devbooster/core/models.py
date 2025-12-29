"""
DevBooster 핵심 데이터 모델

TableSpec: 테이블 하나의 전체 정보
ColumnSpec: 컬럼 하나의 정보
"""

from dataclasses import dataclass, field

@dataclass
class ColumnSpec:
    """ 컬럼 정보 """

    # 필수 정보
    name: str               # 컬럼명
    data_type: str          # 데이터 타입
    length: int | None      # 길이
    nullable: bool          # Null 허용여부
    default: str | None     # 기본값
    comment: str            # 주석

    explicit_pk: bool = False      # 명시적 PK

    # 자동 판단 속성
    is_pk: bool = field(default=False, init=False)
    is_special: bool = field(default=False, init=False)
    special_type: str | None = field(default=None, init=False)

    def __post_init__(self):
        """객체 생성 후 자동으로 실행되는 메서드"""

        # PK 자동 판단: 컬럼명이 _ID로 끝나면..
        # TODO: 1. PK는 엑셀에서 별도로 입력받도록 하고
        #  PK가 없는 경우 별도로 Identifier를 입력받아서 이 부분을 처리하도록 수정 필요
        # TODO: 2. 사용자가 입력하지 않는 경우 PK가 없는 것으로 간주. OR AI 판단 추천으로 고른다.
        #  단, AI 추천으로 고른 경우 경고문구를 반드시 붙일것.
        if self.explicit_pk:
            # 명시적 PK 우선
            self.is_pk = True
        # else:
        #     # 규칙기반
        #     name_upper = self.name.upper()
        #     # FK 패턴제외
        #     fk_prefixes = ("ENTRY_","ENT_","REG_","UPT_","UPD_","MOD_","CRT_")
        #     if any(name_upper.startswith(p) for p in fk_prefixes):
        #         self.is_pk = False
        #     # PK 패턴
        #     elif name_upper.endswith(("_ID","_SEQ","_NO")):
        #         self.is_pk = True

        # 특수 컬럼 자동 판단
        # TODO : 현재는 이렇게 쓰고.. 나중에는 직접 입력할 수 있게 하든지
        #  excel로 받게 하든지 하자
        special_columns = [
            "USE_YN",       # 사용여부
            "DEL_YN",       # 삭제여부
            "SECRET_YN",     # 비밀글여부
            "ATCH_FILE_ID", # 첨부파일ID
            "APRV_YN",       # 승인여부
        ]

        if self.name in special_columns:
            self.is_special = True
            self.special_type = self.name

    @property
    def camel_name(self) -> str:
        """
        snake_case -> camelCase
        NOTICE_ID -> noticeId
        """
        parts = self.name.lower().split("_")
        return parts[0]+"".join(p.capitalize() for p in parts[1:])

    @property
    def pascal_name(self) -> str:
        """
        snake_case -> PascalCase
        NOTICE_ID -> NoticeId
        """
        parts = self.name.lower().split("_")
        return "".join(p.capitalize() for p in parts)

    @property
    def java_type(self) -> str:
        """
        DB 타입 -> Java 타입 매핑 (간단 버전(oracle))
        """
        type_map = {
            "NUMBER": "Long",
            "VARCHAR2": "String",
            "VARCHAR": "String",
            "CHAR": "String",
            "DATE": "Date",
            "TIMESTAMP": "Date",
            "CLOB": "String",
            "BLOB": "byte[]",
        }
        return type_map.get(self.data_type,"String")

@dataclass
class TableSpec:
    """테이블 스펙"""

    # 필수 정보
    name: str       # 테이블명 (예: TB_NOTICE)
    columns: list[ColumnSpec]   # 컬럼 목록

    # 설정
    framework: str = "egov"
    database: str = "oracle"

    @property
    def module(self) -> str:
        """
        테이블명 -> 모듈명
        TB_NOTICE -> notice
        TB_USER_INFO -> userinfo
        """
        name = self.name
        name_len = len(self.name)

        # 접두사 제거
        prefixes = [
            "TB_", "TBL_",
            "TM_","TD_","TC_"
        ]

        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        parts = name.lower().split("_")

        if name_len == len(name):
            if len(parts[0]) == 1:
                name = "".join(parts[1:])

        return name


    @property
    def class_name(self) -> str:
        """
        테이블명 -> 클래스명 (PascalCase)
        TB_NOTICE -> Notice
        TB_USER_INFO -> UserInfo
        """
        module = self.module

        if not module:
            return  "Unknown"
        return module[0].upper()+module[1:]


    @property
    def explicit_pk_columns(self) -> list[ColumnSpec]:
        """명시적 PK만"""
        return [col for col in self.columns if col.explicit_pk]

    @property
    def pk_columns(self) -> list[ColumnSpec]:
        """PK 컬럼명 목록"""
        return [col for col in self.columns if col.is_pk]

    @property
    def pk_camel_names(self) -> list[str]:
        """PK CamelCase 목록"""
        return [col.camel_name for col in self.columns if col.is_pk]

    # TODO: 이하 has_aprv_yn 까지는 이렇게 적지말고
    #  따로 공용으로 적용할 수 있도록 로직 작업이 필요
    @property
    def has_use_yn(self) -> bool:
        """USE_YN 컬럼 존재 여부"""
        return any(col.special_type == "USE_YN" for col in self.columns)

    @property
    def has_del_yn(self) -> bool:
        """DEL_YN 컬럼 존재 여부"""
        return any(col.special_type == "DEL_YN" for col in self.columns)

    @property
    def has_secret_yn(self) -> bool:
        """SECRET_YN 컬럼 존재 여부"""
        return any(col.special_type == "SECRET_YN" for col in self.columns)

    @property
    def has_file(self) -> bool:
        """ATCH_FILE_ID 컬럼 존재 여부"""
        return any(col.special_type == "ATCH_FILE_ID" for col in self.columns)

    @property
    def has_aprv_yn(self) -> bool:
        """APRV_YN 컬럼 존재 여부"""
        return any(col.special_type == "APRV_YN" for col in self.columns)

    @property
    def logical_delete(self) -> bool:
        """논리 삭제 사용 여부"""
        return self.has_use_yn or self.has_del_yn


# =============== 테스트 코드 ======================
if __name__ == "__main__":
    """
    실행: 우클릭 -> Run 'models'
    """

    print("="*50)
    print("DevBooster Models Test")
    print("="*50)

    # 컬럼 생성 테스트
    columns = [
        ColumnSpec(
            name="NOTICE_ID",
            data_type="NUMBER",
            length=10,
            nullable=False,
            default=None,
            comment="공지사항ID",
        ),
        ColumnSpec(
            name="TITLE",
            data_type="VARCHAR2",
            length=200,
            nullable=False,
            default=None,
            comment="제목",
        ),
        ColumnSpec(
            name="CONTENT",
            data_type="CLOB",
            length=None,
            nullable=True,
            default=None,
            comment="내용",
        ),
        ColumnSpec(
            name="USE_YN",
            data_type="CHAR",
            length=1,
            nullable=False,
            default='Y',
            comment="사용여부",
        ),
        ColumnSpec(
            name="SECRET_YN",
            data_type="CHAR",
            length=1,
            nullable=False,
            default='N',
            comment="비밀글여부",
        )
    ]

    # 테이블 생성
    table = TableSpec(name="TB_NOTICE", columns=columns)

    # 결과 출력
    print(f"\n 테이블: {table.name}")
    print(f" 모듈: {table.module}")
    print(f" 클래스: {table.class_name}")
    print(f" PK: {table.pk_columns}")
    print(f" 논리삭제: {table.logical_delete}")
    print(f" 파일첨부: {table.has_file}")
    print(f" 비밀글: {table.has_secret_yn}")

    print(f"\n 컬럼목록: ({len(table.columns)}개) : ")
    for col in columns:
        pk_mark = "[PK]" if col.is_pk else "    "
        special_mark = f"[{col.special_type}]" if col.is_special else ""
        print(
            f" {pk_mark} {col.name:20} {col.data_type:10} -> {col.java_type:10} ({col.camel_name}) {special_mark}"
        )

    print("\n"+"="*50)
    print("테스트 완료!")
    print("="*50)

