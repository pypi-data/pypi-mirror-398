import ffmpeg
from fractions import Fraction


class VideoInfo:
    def __init__(self, path: str):
        self.path = path
        try:
            self.probe = ffmpeg.probe(path)
        except ffmpeg.Error as e:
            raise Exception(f"FFmpeg probe failed: {e}")

    def get_video_stream(self):
     
        return next((s for s in self.probe["streams"] if s.get("codec_type") == "video"), None)

    def get_audio_stream(self):
       
        return next((s for s in self.probe["streams"] if s.get("codec_type") == "audio"), None)

    def get_duration(self):
      
        return float(self.probe["format"].get("duration", 0.0))

    def get_resolution(self):
       
        v_stream = self.get_video_stream()
        if v_stream:
            return int(v_stream.get("width", 0)), int(v_stream.get("height", 0))
        return (0, 0)

    def get_fps(self):
        
        v_stream = self.get_video_stream()
        if not v_stream:
            return None

        r_rate = v_stream.get("r_frame_rate")
        if r_rate and r_rate != "0/0":
            return float(Fraction(r_rate))

        avg_rate = v_stream.get("avg_frame_rate")
        if avg_rate and avg_rate != "0/0":
            return float(Fraction(avg_rate))

        nb_frames = v_stream.get("nb_frames")
        duration = self.probe["format"].get("duration") or v_stream.get("duration")
        if nb_frames and duration:
            return float(Fraction(int(nb_frames), int(float(duration))))

        return None

    def get_codec(self):
        v_stream = self.get_video_stream()
        if v_stream:
            return v_stream.get("codec_name", "unknown")
        return "unknown"
