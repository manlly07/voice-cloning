import threading
import time
import librosa
import librosa.display
import numpy as np
from scipy.io.wavfile import write
import scipy.signal as signal
from pydub import AudioSegment, effects
import pyaudio
import wave
from tkinter import messagebox

# Biến cờ và trạng thái
stop_flag = threading.Event()
pause_flag = threading.Event()  # Cờ Pause
audio_thread = None  # Biến lưu thread âm thanh hiện tại
current_position = 0  # Vị trí phát âm thanh hiện tại
is_audio_playing = False  # Biến theo dõi trạng thái phát âm thanh
p = None  # Biến lưu instance của PyAudio
stream = None  # Biến lưu stream âm thanh

def normalize_audio(y):
    return y / np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else y

# Thay đổi cao độ
def pitch_shift(y, sr, n_steps):
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

# Tạo hiệu ứng formant
def formant_shift(y, shift_factor):
    y_shifted = np.interp(
        np.arange(0, len(y), shift_factor),
        np.arange(0, len(y)),
        y
    )
    return y_shifted

# Thêm hiệu ứng reverb
def add_reverb(y, sr, decay=0.3):
    impulse = np.random.randn(int(sr * decay))  # Tạo tín hiệu ngẫu nhiên
    impulse = signal.windows.hann(len(impulse)) * impulse  # Làm mịn tín hiệu
    reverb = np.convolve(y, impulse, mode='full')[:len(y)]
    return reverb

# Hàm để mở file
def open_file():
    global audio_thread, current_position
    if audio_thread and audio_thread.is_alive():
        stop_flag.set()
        audio_thread.join()

    file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

        stop_flag.clear()
        pause_flag.clear()
        current_position = 0

# Hàm phát âm thanh
def play_audio(audio_file):
    global current_position, is_audio_playing, p, stream
    is_audio_playing = True

    wf = wave.open(audio_file, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    wf.setpos(current_position)
    data = wf.readframes(1024)
    while data and not stop_flag.is_set():
        if pause_flag.is_set():
            time.sleep(0.1)
            continue
        stream.write(data)
        data = wf.readframes(1024)
        current_position = wf.tell()

    stream.stop_stream()
    stream.close()
    p.terminate()
    is_audio_playing = False

# Hàm để biến đổi âm thanh theo các nhân vật
def transform_audio():
    global audio_thread, current_position, is_audio_playing
    if is_audio_playing:
        messagebox.showwarning("Warning", "Vui lòng chờ âm thanh kết thúc trước khi thay đổi.")
        return

    output_file = "output.wav"
    try:
        file_path = entry_file.get()
        if not file_path:
            raise ValueError("Vui lòng chọn file âm thanh.")

        y, sr = librosa.load(file_path)
        selected_option = character_option.get()
        pitch_shift_value = float(entry_pitch_shift.get())

        if selected_option == "Conan":
            y = pitch_shift(y, sr, n_steps=2)
        elif selected_option == "Shin":
            y = pitch_shift(y, sr, n_steps=6)
        elif selected_option == "Doraemon":
            y = pitch_shift(y, sr, n_steps=-4)
            y = add_reverb(y, sr, decay=0.5)
            y = normalize_audio(y)
        elif selected_option == "Suspect":
            y = pitch_shift(y, sr, n_steps=-6)
            y = librosa.effects.time_stretch(y, rate=1.1)
            y = normalize_audio(y)
        elif selected_option == "Mẹ Shin":
            y = pitch_shift(y, sr, n_steps=5)
            y = librosa.effects.time_stretch(y, rate=1.1)
            y = add_reverb(y, sr, decay=0.3)
            y = normalize_audio(y)
        elif selected_option == "Nobita":
            y = pitch_shift(y, sr, n_steps=1)
            y = librosa.effects.time_stretch(y, rate=0.95)
            y = formant_shift(y, shift_factor=1.1)
        elif selected_option == "Clown":
            y = pitch_shift(y, sr, n_steps=10)
            y = librosa.effects.time_stretch(y, rate=1.2)
            y = normalize_audio(y)
        elif selected_option == "Donald":
            y = pitch_shift(y, sr, n_steps=12)
            y = librosa.effects.time_stretch(y, rate=1.4)
            y = y + 0.01 * np.random.randn(len(y))
            y = normalize_audio(y)

        if pitch_shift_value != 0:
            y = pitch_shift(y, sr, n_steps=pitch_shift_value)

        write(output_file, sr, (y * 32767).astype(np.int16))
        sound = AudioSegment.from_wav(output_file)
        audio_with_reverb = effects.normalize(sound)
        audio_with_reverb.export(output_file, format="wav")

        stop_flag.set()
        stop_flag.clear()

        current_position = 0
        audio_thread = threading.Thread(target=play_audio, args=(output_file,))
        audio_thread.start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Hàm để pause âm thanh
def pause_audio():
    pause_flag.set()

# Hàm để resume âm thanh
def resume_audio():
    pause_flag.clear()

# Hàm để clear toàn bộ thread âm thanh
def clear_audio():
    global audio_thread, p, stream, is_audio_playing
    if is_audio_playing:
        stop_flag.set()
        if audio_thread and audio_thread.is_alive():
            audio_thread.join()
        if stream:
            stream.stop_stream()
            stream.close()
        if p:
            p.terminate()

    is_audio_playing = False
    stop_flag.clear()
    pause_flag.clear()
