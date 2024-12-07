from pydub import AudioSegment
import os

from pyannote.audio import Pipeline
from pyannote.core import Segment
excerpt = Segment(start=2.0, end=5.0)

# Đảm bảo bạn đã thay YOUR_AUTH_TOKEN bằng token của mình
auth_token = "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"
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",  use_auth_token=auth_token)

# Tải mô hình speaker diarization từ Hugging Face
# pipeline = SpeakerDiarization.from_pretrained("pyannote/speaker-diarization", use_auth_token=auth_token)

# Đường dẫn đến tệp âm thanh của bạn (thay "audio_file.mp3" bằng đường dẫn chính xác)
audio_file = "Use1.mp3"

# Kiểm t ra xem tệp âm thanh có tồn tại không
if not os.path.exists(audio_file):
    print(f"Error: The audio file {audio_file} does not exist.")
else:
    try:
        # Tiến hành speaker diarization
        diarization = pipeline({"uri": "filename", "audio": audio_file})
        # Đọc file âm thanh bằng pydub
        audio = AudioSegment.from_file(audio_file)

        # Đảm bảo thư mục lưu các tệp âm thanh tồn tại
        output_dir = "diarized_segments"
        os.makedirs(output_dir, exist_ok=True)

        # Tạo từ điển để lưu các đoạn âm thanh theo speaker
        speakers_segments = {}

        # Lưu từng đoạn âm thanh cho từng speaker vào từ điển
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time_ms = turn.start * 1000  # chuyển sang ms
            end_time_ms = turn.end * 1000      # chuyển sang ms
            segment = audio[start_time_ms:end_time_ms]  # Cắt đoạn âm thanh

            if speaker not in speakers_segments:
                speakers_segments[speaker] = []
            speakers_segments[speaker].append(segment)

        # Ghép các đoạn âm thanh của mỗi speaker lại với nhau và lưu thành tệp
        for speaker, segments in speakers_segments.items():
            # Ghép tất cả các đoạn của speaker
            combined_audio = sum(segments)

            # Lưu tệp âm thanh cho speaker
            output_filename = os.path.join(output_dir, f"speaker_{speaker}.wav")
            combined_audio.export(output_filename, format="wav")
            print(f"Saved combined segment for speaker {speaker} to {output_filename}") # Xuất ra các file wav tương ứng với Speaker__
    except Exception as e:
        print(f"An error occurred during diarization or file handling: {e}")
