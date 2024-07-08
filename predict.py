import os
import tempfile
import subprocess
import json
import shutil
from pathlib import Path
from cog import BasePredictor, Input, Path as CogPath

class Predictor(BasePredictor):
    def get_video_info(self, video_path):
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        duration = float(info['format']['duration'])
        return duration

    def predict(
        self,
        input_video: CogPath = Input(description="Input video file"),
        output_fps: float = Input(description="Output frame rate (fps)", default=24.0),
        use_advanced_method: bool = Input(description="Use advanced frame interpolation method", default=False)
    ) -> CogPath:
        # Create a more persistent output directory
        output_dir = Path("/tmp/cog_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "output.mp4"

        input_duration = self.get_video_info(input_video)
        print(f"Input video duration: {input_duration:.2f} seconds")

        if use_advanced_method:
            filter_complex = f"minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps={output_fps}'"
        else:
            filter_complex = f"fps=fps={output_fps}"
        
        cmd = [
            "ffmpeg",
            "-i", str(input_video),
            "-filter:v", filter_complex,
            "-c:a", "copy",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("FFmpeg stdout:", result.stdout)
            print("FFmpeg stderr:", result.stderr)
        except subprocess.CalledProcessError as e:
            print("FFmpeg command failed")
            print("FFmpeg stdout:", e.stdout)
            print("FFmpeg stderr:", e.stderr)
            raise

        if not output_path.exists():
            raise FileNotFoundError(f"Output file was not created at {output_path}")
        
        output_duration = self.get_video_info(output_path)
        print(f"Output video duration: {output_duration:.2f} seconds")
        print(f"Output frame rate: {output_fps} fps")
        
        duration_diff = abs(input_duration - output_duration)
        if duration_diff > 0.1:  # Allow for a small difference due to potential rounding
            print(f"Warning: Output duration differs from input by {duration_diff:.2f} seconds")
        else:
            print("Video duration maintained successfully")
        
        print(f"Output file size: {output_path.stat().st_size} bytes")
        print(f"Output file exists: {output_path.exists()}")
        
        return CogPath(output_path)
