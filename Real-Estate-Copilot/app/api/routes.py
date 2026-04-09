from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import shutil, os, uuid
from datetime import datetime
from fastapi.staticfiles import StaticFiles

from app.models.property_form import InteriorConditionForm
from app.agents.property_agent import analyze_property
from app.rag.inspection_rag import analyze_inspection_report
from app.reports.property_intelligence_pdf import generate_property_intelligence_pdf
from app.config import UPLOAD_DIR, OUTPUT_DIR
from app.agents.preference_agent import chat as preference_chat, get_profile

app = FastAPI(title="Real Estate Copilot API", version="1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
bearer = HTTPBearer()

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/chat", response_class=HTMLResponse)
async def chat_ui():
    html_path = "/Users/peipeiguo/Desktop/AI Agent Learning/Real-Estate-Copilot/app/static/chat.html"
    with open(html_path) as f:
        return f.read()

# ── Simple JWT check (dev mode) ───────────────────────
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

# ── Health check ───────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0"}

# ── Inspection only ────────────────────────────────────
@app.post("/v1/inspection/analyze")
async def inspection_analyze(
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):
    file_id  = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = analyze_inspection_report(pdf_path)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

# ── Property intelligence (form only) ─────────────────
@app.post("/v1/property/analyze")
async def property_analyze(
    form: InteriorConditionForm,
    token: str = Depends(verify_token)
):
    try:
        result = analyze_property(form)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Full intelligence report (form + optional PDF) ────
class IntelligenceRequest(BaseModel):
    form:         InteriorConditionForm
    report_format: Optional[str] = "buyer"   # buyer / investor / none
    agent_name:   Optional[str] = None
    agent_license: Optional[str] = None

@app.post("/v1/property/intelligence")
async def property_intelligence(
    request: IntelligenceRequest,
    token: str = Depends(verify_token)
):
    try:
        result = analyze_property(request.form)

        if request.report_format in ("buyer", "investor"):
            timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_id  = str(uuid.uuid4())[:8]
            pdf_path   = os.path.join(
                OUTPUT_DIR,
                f"report_{report_id}_{timestamp}.pdf"
            )
            generate_property_intelligence_pdf(
                result=result,
                output_path=pdf_path,
                property_address=request.form.address,
                report_type=request.report_format,
                agent_name=request.agent_name,
                agent_license=request.agent_license,
            )
            result["report_url"] = f"/v1/report/{os.path.basename(pdf_path)}"

        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Download report PDF ───────────────────────────────
@app.get("/v1/report/{filename}")
async def get_report(
    filename: str,
    token: str = Depends(verify_token)
):
    pdf_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(pdf_path, media_type="application/pdf")

class ChatMessage(BaseModel):
    session_id: str
    message:    Optional[str] = None  # None = start new conversation
    reset:      bool = False

@app.post("/v1/preferences/chat")
async def preferences_chat(
    request: ChatMessage,
    token: str = Depends(verify_token)
):
    try:
        # Reset if requested
        msg = None if request.reset else request.message
        result = preference_chat(request.session_id, msg)
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/preferences/profile/{session_id}")
async def get_preference_profile(
    session_id: str,
    token: str = Depends(verify_token)
):
    profile = get_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "success", "data": profile}