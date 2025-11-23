# app/main.py
from fastapi import FastAPI, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from pathlib import Path
import os

from .config import settings
from .database import Base, engine, get_db
from .models import VideoJob
from .services.video_service import generate_video_for_job 
from sqlalchemy.orm import Session

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Simple Video Generator")

# Mount static files
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/videos", StaticFiles(directory=settings.VIDEO_DIR), name="videos")

# Templates
templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Ensure storage directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VIDEO_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Render upload page for creating a new video job.
    """
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload(
    request: Request,
    title: str = Form(...),
    text_content: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Handle upload of text and images.
    Steps:
      - Save images to local storage
      - Create a VideoJob with status 'processing'
      - Generate video synchronously (MVP)
      - Update job status and video_path
    """
    # Create DB record with status 'processing'
    job = VideoJob(
        title=title,
        text_content=text_content,
        status="processing",
        video_path=None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Save uploaded images under a folder named by job id
    job_upload_dir = settings.UPLOAD_DIR / f"job_{job.id}"
    os.makedirs(job_upload_dir, exist_ok=True)

    for idx, file in enumerate(files):
        file_ext = Path(file.filename).suffix or ".jpg"
        dest_path = job_upload_dir / f"image_{idx}{file_ext}"
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

    # Generate video (synchronously for MVP)
    try:
        video_web_path = generate_video_for_job(db=db, job=job)
        job.status = "done"
        job.video_path = video_web_path
    except Exception as e:
        # Log error and mark job as failed
        print(f"Error generating video for job {job.id}: {e}")
        job.status = "failed"
        job.video_path = None

    db.add(job)
    db.commit()
    db.refresh(job)

    return RedirectResponse(
        url=f"/jobs/{job.id}",
        status_code=303
    )



@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Show the detail of a video job, including status and download link if ready.
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        return HTMLResponse("Job not found", status_code=404)

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )
