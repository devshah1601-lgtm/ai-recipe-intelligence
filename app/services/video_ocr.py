from pathlib import Path
import easyocr
import torch
from functools import lru_cache


class VideoOCR:
    def __init__(self, use_gpu=True):
        gpu_available = torch.cuda.is_available()

        self.use_gpu = use_gpu and gpu_available

        print(
            f"VideoOCR initialized | "
            f"GPU requested: {use_gpu} | "
            f"GPU enabled: {self.use_gpu}"
        )

        self.reader = easyocr.Reader(
            ["en"],
            gpu=self.use_gpu
        )

    def extract_text(self, frames_dir: str):
        frames = sorted(Path(frames_dir).glob("frame_*.png"))
        results = []

        for frame in frames:
            detections = self.reader.readtext(
                str(frame),
                detail=1,
                paragraph=False
            )

            for bbox, text, confidence in detections:
                text = text.strip()

                if confidence < 0.40 or len(text) < 2:
                    continue

                frame_number = int(frame.stem.split("_")[-1])

                timestamp = (frame_number - 1) / 2

                results.append({
                    "frame": frame.name,
                    "timestamp_seconds": round(timestamp, 2),
                    "text": text,
                    "confidence": round(float(confidence), 3),
                    "bbox": [
                        [round(float(x), 2), round(float(y), 2)]
                        for x, y in bbox
                    ],
                })

        return results

@lru_cache(maxsize=2)
def get_video_ocr(use_gpu: bool = True):
     return VideoOCR(use_gpu=use_gpu)