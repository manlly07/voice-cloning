import os
import threading
from tkinter import Tk, Label, Button, filedialog, Listbox, messagebox
from pydub import AudioSegment
from pyannote.audio import Pipeline
from pyannote.core import Segment
import simpleaudio as sa
import pyaudio
import wave
# Tải mô hình speaker diarization
auth_token = "YOUR_AUTH_TOKEN"
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=auth_token)


class AudioDiarizationApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Audio Diarization App")

        # Giao diện chính
        self.label = Label(master, text="Select an audio file for diarization:")
        self.label.pack(pady=10)

        self.select_button = Button(master, text="Choose Audio File", command=self.select_audio_file)
        self.select_button.pack(pady=5)

        self.diarize_button = Button(master, text="Run Diarization", command=self.start_diarization_thread)
        self.diarize_button.pack(pady=5)

        self.file_list = Listbox(master, width=50, height=10)
        self.file_list.pack(pady=10)
        self.file_list.bind('<<ListboxSelect>>', self.play_selected_audio)

        self.selected_audio_file = None
        self.output_dir = "diarized_segments"
        self.current_audio_player = None  # Lưu trạng thái file đang phát
        os.makedirs(self.output_dir, exist_ok=True)

        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None

    def select_audio_file(self):
        filetypes = [("Audio files", "*.mp3 *.wav *.flac")]
        self.selected_audio_file = filedialog.askopenfilename(title="Open Audio File", filetypes=filetypes)
        if self.selected_audio_file:
            messagebox.showinfo("File Selected", f"Selected file: {os.path.basename(self.selected_audio_file)}")

    def start_diarization_thread(self):
        """Chạy quá trình diarization trên một luồng riêng."""
        if not self.selected_audio_file:
            messagebox.showerror("Error", "Please select an audio file first.")
            return
        self.diarize_button.config(state="disabled")  # Vô hiệu hóa nút trong khi xử lý
        thread = threading.Thread(target=self.run_diarization)
        thread.start()

    def run_diarization(self):
        try:
            # Tiến hành speaker diarization
            diarization = pipeline({"uri": "filename", "audio": self.selected_audio_file})
            audio = AudioSegment.from_file(self.selected_audio_file)

            speakers_segments = {}

            # Tách đoạn âm thanh theo speaker
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start_time_ms = turn.start * 1000
                end_time_ms = turn.end * 1000
                segment = audio[start_time_ms:end_time_ms]

                if speaker not in speakers_segments:
                    speakers_segments[speaker] = []
                speakers_segments[speaker].append(segment)

            # Ghép và lưu các file tách
            self.file_list.delete(0, 'end')
            for speaker, segments in speakers_segments.items():
                combined_audio = sum(segments)
                output_filename = os.path.join(self.output_dir, f"speaker_{speaker}.wav")
                combined_audio.export(output_filename, format="wav")
                self.file_list.insert('end', output_filename)

            messagebox.showinfo("Success", f"Diarization completed! Files saved in {self.output_dir}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.diarize_button.config(state="normal")  # Kích hoạt lại nút sau khi xử lý xong
    def stop_audio(self):
        """Dừng phát âm thanh nếu có."""
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    def play_selected_audio(self, event):
        try:
            selected_index = self.file_list.curselection()
            if selected_index:
                file_to_play = self.file_list.get(selected_index[0])

                # Dừng file đang phát (nếu có)
                self.stop_audio()
                # Phát tệp mới
                self.start_audio_playback(file_to_play)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while playing the audio: {e}")

    def cleanup(self):
        """Dọn dẹp tài nguyên khi thoát ứng dụng."""
        self.stop_audio()
        self.pyaudio_instance.terminate()

    def start_audio_playback(self, file_path):
            """Phát tệp âm thanh sử dụng PyAudio."""
            def play_audio():
                with wave.open(file_path, 'rb') as wf:
                    self.stream = self.pyaudio_instance.open(
                        format=self.pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True
                    )
                    data = wf.readframes(1024)
                    while data and self.stream.is_active():
                        self.stream.write(data)
                        data = wf.readframes(1024)

                    self.stop_audio()  # Đảm bảo luồng dừng khi phát xong

            threading.Thread(target=play_audio).start()


if __name__ == "__main__":
    root = Tk()
    app = AudioDiarizationApp(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
