# app/services/video_service.py
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

# MoviePy v2.x: import directly from moviepy (no more moviepy.editor)
from moviepy import ImageSequenceClip

from ..config import settings
from ..models import VideoJob


def _get_image_files_for_job(job_id: int) -> List[Path]:
    """
    Collect all image files for a given job from the upload directory.
    """
    job_upload_dir = settings.UPLOAD_DIR / f"job_{job_id}"
    if not job_upload_dir.exists():
        raise FileNotFoundError(f"Upload directory not found for job {job_id}")

    image_files = sorted(
        [
            p
            for p in job_upload_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif"}
        ]
    )
    if not image_files:
        raise ValueError(f"No images found for job {job_id}")

    return image_files


def generate_video_for_job(
    db: Session,
    job: VideoJob,
    seconds_per_image: float = 2.0,
    fps: int = 24,
) -> str:
    """
    Create a simple slideshow video from all images of the job.

    MoviePy v2.x no longer provides `moviepy.editor`.
    We use ImageSequenceClip from `moviepy` directly.
    """
    image_files = _get_image_files_for_job(job.id)

    # Convert Paths to string paths for ImageSequenceClip
    image_paths = [str(p) for p in image_files]

    # durations: each image stays on screen for `seconds_per_image`
    durations = [seconds_per_image] * len(image_paths)

    # Create the video clip from the sequence of images
    clip = ImageSequenceClip(image_paths, durations=durations)

    # Output path
    output_path = settings.VIDEO_DIR / f"job_{job.id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write video file
    clip.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        audio=False,  # no audio for MVP
    )

    # Close clip to free resources
    clip.close()

    # Return the URL path that browser can access
    web_path = f"/videos/job_{job.id}.mp4"
    return web_path
