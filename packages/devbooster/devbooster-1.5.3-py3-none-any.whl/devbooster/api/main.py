"""
DevBooster FastAPI Server

Excel 파일 업로드 -> CRUD 코드 ZIP 다운로드
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil
import os
import requests
from pathlib import Path

from pip._internal.utils import temp_dir
from pydantic import BaseModel

from ..core.parser import parse_excel
from ..core.analyzer import TableAnalyzer
from ..core.renderer import TemplateRenderer
from ..core.writer import FileWriter

# FastAPI 앱
app = FastAPI(
    title="DevBooster API",
    description = "전자정부프레임워크 CRUD 코드 자동 생성 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
# 브라우저에게 내가 허용한 거라고 알려주는 설정
app.add_middleware(
    CORSMiddleware,
    # 누구를 들여보낼지?
    # ["*"] = 모두에게 다 허용
    # 실무에서는 특정 ["IP:PORT"] 로 특정함.
    allow_origins=["*"],

    # 쿠키나 인증정보를 받을지
    # True = ㅇㅇ 받아도 됨. (로그인 유지 등에 필요)
    allow_credentials=True,

    # 어떤 행동을 허락할지
    # ["*"] = GET, POST, PUT, DELETE, PATCH, OPTIONS .. 다 해!
    allow_methods=["*"],

    # 어떤 헤더를 허락할지
    # ["*"] = Content-Type, Authorization, X-Process-Time .. 아무거나 다 보내!
    allow_headers=["*"],
)

# K8s YAML에서 설정한 환경변수 가져오기 (없으면 기본값)
OLLAMA_HOST = os.getenv("OLLAMA_HOST","http://localhost:11434")

class ChatRequest(BaseModel):
    model: str = "qwen2.5-coder:7B"
    prompt: str

def cleanup_temp_dir(temp_dir: Path):
    """임시 디렉토리 정리 (백그라운드)"""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"🗑️ 정리 완료: {temp_dir}")
    except Exception as e:
        print(f"⚠️ 정리 실패: {e}")

@app.get("/")
def root():
    """
    헬스 체크
    Returns:
         서비스 정보
    """
    return{
        "service": "DevBooster API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints":{
            "docs": "/docs",
            "generate": "/generate"
        }
    }

@app.get("/health")
def health():
    """헬스 체크 (K8s용)"""
    return {"status": "ok"}

@app.get("/ollama/check")
def ollama_check():
    return {"status": "alive", "ollama_host": OLLAMA_HOST}

@app.post("/ask")
def ask_ai(request: ChatRequest):
    try:
        # Ollama API 호출 (Generate EndPoint)
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False
        }

        # 호스트 PC의 Ollama로 요청 발사!
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=60)
        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail=f"Ollama({OLLAMA_HOST})에 연결할 수 없습니다. 호스트 설정을 확인하세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Excel 테이블 명세서 (.xlsx)")
):
    """
    CRUD 코드 생성

    Args:
        file: Excel 파일 (.xlsx)
            # TODO: 추후에는 TB_로 시작하지 않더라도 지원하도록.. 대신 bak이나 tmp 등은 걸러내도록 해야함.
            - 시트명 = 테이블명 (TB_로 시작)
            - 컬럼: 컬럼명, 데이터타입, 길이, NULL, 기본값, 설명

    Returns:
        ZIP 파일 (생성된 CRUD 코드)

    Examples:
        curl -X POST "http://localhost:8000/generate" \\
            -F "file=@tables.xlsx" \\
            -o generated.zip
    """

    # 파일 확장자 체크
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Excel 파일(.xlsx)만 업로드 가능합니다."
        )

    # 임시 디렉토리 생성
    temp_dir = Path(tempfile.mkdtemp())
    excel_path = temp_dir / file.filename

    try:
        # 1. Excel 파일 저장
        with open(excel_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 2. 파싱
        print(f"📁 Excel 로드: {file.filename}")
        tables = parse_excel(excel_path)

        # TODO: 추후에는 TB_로 시작하지 않더라도 지원하도록.. 대신 bak이나 tmp 등은 걸러내도록 해야함.
        if not tables:
            raise HTTPException(
                status_code=400,
                detail="테이블을 찾을 수 없습니다. TB_로 시작하는 시트가 있는지 확인하세요"
            )

        print(f"✅ {len(tables)}개 테이블 발견")

        # 3. 코드 생성
        analyzer = TableAnalyzer()
        renderer = TemplateRenderer()
        output_dir = temp_dir / "generated"
        writer = FileWriter(output_dir)

        for table in tables:
            print(f"📄 처리 중: {table.name}")

            # 진단
            diagnosis = analyzer.analyze(table)
            print(f"    PK: {diagnosis.has_pk}")

            # Identifier 결정
            identifier = None
            if diagnosis.identifier_candidates:
                identifier = diagnosis.identifier_candidates[0]
                print(f"    Identifier: {identifier}")

            # 코드 생성
            outputs = renderer.render_all(table, identifier)

            # 파일 저장
            writer.write_files(outputs, table.module)

        # 4. ZIP 생성
        print("📦 ZIP 생성 중...")
        zip_path = writer.create_zip("generated.zip")

        print(f"✅ 완료: {zip_path}")

        background_tasks.add_task(cleanup_temp_dir,temp_dir)

        # 5. ZIP 파일 변환
        return FileResponse(
            path=zip_path,
            filename="generated.zip",
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=generated.zip"
            }
        )

    except HTTPException:
        # 에러 시 즉시 정리
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        # 에러 시 즉시 정리
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"❌ 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"코드 생성 중 오류 발생: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("DevBooster API Server")
    print("=" * 50)
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("=" * 50)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

