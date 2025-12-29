"""
CLI 엔트리포인트

모든것을 연결하는 지휘자
"""

import click
from pathlib import Path
from ..core.parser import parse_excel
from ..core.analyzer import TableAnalyzer
from ..core.renderer import TemplateRenderer
from ..core.writer import FileWriter

from devbooster import __version__


@click.group()
@click.version_option(version=__version__, prog_name="DevBooster")
def cli():
    """DevBooster - CRUD 코드 생성기"""
    pass


@cli.command()
@click.option(
    "--input","-i",
    type=click.Path(exists=True),
    required=True,
    help="Excel 파일 경로"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="generated",
    help="출력 디렉토리"
)
@click.option(
    "--framework", "-f",
    type=click.Choice(["egov","boot"]),
    default="egov",
    help="프레임워크"
)
@click.option(
    "--database", "-d",
    type=click.Choice(["oracle","mysql"]),
    default="oracle",
    help="데이터베이스"
)
@click.option(
    "--use-ai/--no-ai",
    default=True,
    help="AI 분석 사용"
)



def generate(input, output, framework, database,use_ai):
    """
    CRUD 코드 생성

    Example:
        # AI 사용 (기본)
        devbooster generate -i table.xlsx

        # AI 미사용
        devbooster generate -i table.xlsx --no-ai
    """

    click.echo("=" * 50)
    click.echo("DevBooster 시작")
    click.echo("=" * 50)

    # 1. 파싱
    click.echo(f"\n📁 Excel 로드: {input}")
    tables = parse_excel(input)
    click.echo(f"✅ {len(tables)}개 테이블 발견")

    # 2. 분석 + 생성
    analyzer = TableAnalyzer(use_ai=use_ai)
    renderer = TemplateRenderer(framework, database)
    writer = FileWriter(output)

    for table in tables:
        click.echo(f"\n📄 처리 중: {table.name}")

        # 진단
        diagnosis = analyzer.analyze(table)
        click.echo(f"    PK: {diagnosis.has_pk}")

        if diagnosis.warnings:
            for warning in diagnosis.warnings:
                click.echo(f"    ⚠️ {warning}")

        # 코드 생성
        identifier = diagnosis.identifier_candidates[0] if diagnosis.identifier_candidates else [col.name for col in table.pk_columns]
        outputs = renderer.render_all(table,identifier)

        # 파일 저장
        writer.write_files(outputs, table.module)

    # 3. ZIP 생성
    click.echo("\n📦 ZIP 생성 중...")
    zip_path = writer.create_zip()

    click.echo("\n" + "=" * 50)
    click.echo("✅ 완료!")
    click.echo(f"📦 결과: {zip_path}")
    click.echo("=" * 50)


if __name__ == "__main__":
    cli()