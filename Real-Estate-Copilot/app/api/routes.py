from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import shutil, os, uuid
from datetime import datetime

from app.models.property_form import InteriorConditionForm
from app.agents.property_agent import analyze_property
from app.rag.inspection_rag import analyze_inspection_report
from app.reports.property_intelligence_pdf import generate_property_intelligence_pdf
from app.config import UPLOAD_DIR, OUTPUT_DIR

app    = FastAPI(title="Real Estate Copilot API", version="1.0")
bearer = HTTPBearer()

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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