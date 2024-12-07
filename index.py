import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from pydub import AudioSegment, effects
import pyaudio
import wave
import threading
import time
import librosa
import numpy as np
from scipy.io.wavfile import read, write
import scipy.signal as signal
from scipy.signal import firwin, lfilter, kaiserord  # Thêm kaiserord vào
import noisereduce as nr
import soundfile as sf


# Biến cờ và trạng thái
stop_flag = threading.Event()
pause_flag = threading.Event()  # Cờ Pause
audio_thread = None  # Biến lưu thread âm thanh hiện tại
current_position = 0  # Vị trí phát âm thanh hiện tại
is_audio_playing = False  # Biến theo dõi trạng thái phát âm thanh
p = None  # Biến lưu instance của PyAudio
stream = None  # Biến lưu stream âm thanh

def reduce_noise(input_path, output_path):
    y, sr = librosa.load(input_path)
    y_denoised = nr.reduce_noise(y=y, sr=sr)
    sf.write(output_path, y_denoised, sr)

def bandPassFilter(input_path, output_path):
    # Đọc file WAV
    fs, signal = read(input_path)

    # Tạo bộ lọc Bandpass
    nyq_rate = fs / 2.0
    low_cutoff_hz = 300.0
    high_cutoff_hz = 3400.0
    width = 500.0 / nyq_rate
    ripple_db = 60.0

    N, beta = kaiserord(ripple_db, width)
    if N % 2 == 0:
        N += 1
    hBP_FIR = firwin(N, [low_cutoff_hz / nyq_rate, high_cutoff_hz / nyq_rate], window=('kaiser', beta), pass_zero=False)

    # Áp dụng bộ lọc Bandpass
    filtered_signal = lfilter(hBP_FIR, 1.0, signal)

    # Ghi tín hiệu đã lọc ra file WAV
    write(output_path, fs, np.int16(filtered_signal))

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
    # Use signal.windows.hann instead of signal.hann
    impulse = signal.windows.hann(len(impulse)) * impulse  # Làm mịn tín hiệu
    reverb = np.convolve(y, impulse, mode='full')[:len(y)]
    return reverb



# Hàm để mở file wav
def open_file():
    global audio_thread, current_position
    # Kiểm tra và hủy thread âm thanh hiện tại nếu có
    if audio_thread and audio_thread.is_alive():
        stop_flag.set()  # Đặt cờ dừng
        audio_thread.join()  # Đợi thread kết thúc

    # Chọn file âm thanh mới
    file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

        # Khởi tạo và phát lại âm thanh mới
        stop_flag.clear()  # Xóa cờ dừng
        pause_flag.clear()  # Xóa cờ tạm dừng
        current_position = 0  # Reset vị trí âm thanh

# Hàm phát âm thanh
def play_audio(audio_file):
    global current_position, is_audio_playing, p, stream
    is_audio_playing = True  # Đặt trạng thái là đang phát âm thanh

    # Mở file âm thanh (wav)
    wf = wave.open(audio_file, 'rb')

    # Khởi tạo PyAudio
    p = pyaudio.PyAudio()

    # Mở stream để phát âm thanh
    stream = p.open(format=pyaudio.paInt16,
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Đọc và phát âm thanh
    wf.setpos(current_position)  # Set vị trí phát âm thanh hiện tại
    data = wf.readframes(1024)
    while data and not stop_flag.is_set():
        if pause_flag.is_set():  # Nếu pause, tạm dừng
            time.sleep(0.1)
            continue
        stream.write(data)
        data = wf.readframes(1024)
        current_position = wf.tell()  # Cập nhật vị trí hiện tại

    # Đóng stream và PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()
    is_audio_playing = False  # Đặt trạng thái là không còn phát âm thanh

# Hàm để biến đổi âm thanh theo các nhân vật
def transform_audio():
    global audio_thread, current_position, is_audio_playing
    if is_audio_playing:  # Nếu đang phát âm thanh, không cho phép biến đổi
        messagebox.showwarning("Warning", "Vui lòng chờ âm thanh kết thúc trước khi thay đổi.")
        return
    

    output_file = "output.wav"
    

    try:
        file_path = entry_file.get()
        if not file_path:
            raise ValueError("Vui lòng chọn file âm thanh.")

        # Lọc nhiễu
        reduce_noise(file_path, output_file)

        # Lọc tần số
        bandPassFilter(output_file, output_file)


        # Đọc file wav
        # sound = AudioSegment.from_wav(file_path)
        y, sr = librosa.load(output_file)
        # Lấy lựa chọn từ người dùng
        selected_option = character_option.get()
        pitch_shift_value = float(entry_pitch_shift.get())



        # Biến đổi âm thanh theo nhân vật
        if selected_option == "Conan":
            y = pitch_shift(y, sr, n_steps=2)
        elif selected_option == "Shin":
            y = pitch_shift(y, sr, n_steps=6)
        elif selected_option == "Doraemon":
            y = pitch_shift(y, sr, n_steps=-4)  # Giọng trầm
            y = add_reverb(y, sr, decay=0.5)  # Vang nhẹ
            y = normalize_audio(y)
        elif selected_option == "Suspect":
            y = pitch_shift(y, sr, n_steps=-6)  # Giảm pitch để trầm hơn
            y = librosa.effects.time_stretch(y, rate=1.1)  # Tăng tốc độ
            y = normalize_audio(y)  # Chuẩn hóa âm lượng
        elif selected_option == "Mẹ Shin":
            y = pitch_shift(y, sr, n_steps=5)  # Giảm pitch để trầm hơn
            y = librosa.effects.time_stretch(y, rate=1.1)  # Tăng tốc độ
            y = add_reverb(y, sr, decay=0.3)  # Giảm vang
            y = normalize_audio(y)  # Chuẩn hóa âm lượng
        elif selected_option == "Nobita":
            y = pitch_shift(y, sr, n_steps=1)  # Giọng trung bình
            y = librosa.effects.time_stretch(y, rate=0.95)  # Tăng chậm nhẹ
            y = formant_shift(y, shift_factor=1.1)  # Làm giọng dày hơn
        elif selected_option == "Clown":
            y = pitch_shift(y, sr, n_steps=10)  # Tăng cao độ
            y = librosa.effects.time_stretch(y, rate=1.2)  # Tăng tốc độ
            y = normalize_audio(y)  # Chuẩn hóa tín hiệu
        elif selected_option == "Donald":
            y = pitch_shift(y, sr, n_steps=12)  # Tăng cao độ
            y = librosa.effects.time_stretch(y, rate=1.4)  # Tăng tốc độ
            y = y + 0.01 * np.random.randn(len(y))  # Thêm méo tiếng
            y = normalize_audio(y)  # Chuẩn hóa tín hiệu

        if pitch_shift_value != 0:
            y = pitch_shift(y, sr, n_steps=pitch_shift_value)

        # y.export(output_file, format="wav")
        write(output_file, sr, (y * 32767).astype(np.int16))  # Chuẩn hóa tín hiệu
        sound = AudioSegment.from_wav(output_file)
        audio_with_reverb = effects.normalize(sound)  # Thêm hiệu ứng normalize
        audio_with_reverb.export(output_file, format="wav")


        # Hủy thread cũ (nếu có)
        stop_flag.set()  # Đặt cờ dừng và chờ thread kết thúc
        stop_flag.clear()  # Xóa cờ dừng

        # Tạo thread mới để phát âm thanh
        current_position = 0  # Reset vị trí âm thanh
        audio_thread = threading.Thread(target=play_audio, args=(output_file,))
        audio_thread.start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Hàm để pause âm thanh
def pause_audio():
    pause_flag.set()  # Đặt cờ pause

# Hàm để resume âm thanh
def resume_audio():
    pause_flag.clear()  # Xóa cờ pause

# Hàm để clear toàn bộ thread âm thanh
def clear_audio():
    global audio_thread, p, stream, is_audio_playing
    if is_audio_playing:
        stop_flag.set()  # Đặt cờ dừng
        if audio_thread and audio_thread.is_alive():
            audio_thread.join()  # Đợi thread kết thúc
        if stream:
            stream.stop_stream()  # Dừng stream
            stream.close()  # Đóng stream
        if p:
            p.terminate()  # Dừng PyAudio

    # Reset các biến trạng thái
    is_audio_playing = False
    stop_flag.clear()
    pause_flag.clear()
    
# Giao diện chính
root = tk.Tk()
root.title("Biến Đổi Âm Thanh WAV")
root.geometry("500x500")
root.configure(bg='#f0f0f0')  # Light grey background

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Chọn file âm thanh
label_file = tk.Label(frame, text="Chọn file WAV:")
label_file.grid(row=0, column=0, sticky="w", pady=5)

entry_file = tk.Entry(frame, width=40)
entry_file.grid(row=1, column=0, pady=5)

button_browse = tk.Button(frame, text="Duyệt", command=open_file)
button_browse.grid(row=1, column=1, padx=5)

# Tùy chọn nhân vật
label_option = tk.Label(frame, text="Chọn nhân vật:")
label_option.grid(row=2, column=0, sticky="w", pady=5)

character_option = tk.StringVar()
character_option.set("Conan")  # Default value
options = ["Conan", "Shin", "Doraemon", "Suspect", "Mẹ Shin", "Nobita", "Clown", "Donald"]
character_menu = ttk.OptionMenu(frame, character_option, *options)
character_menu.grid(row=2, column=1, pady=5)

label_pitch_shift = tk.Label(frame, text="Pitch Shift")
label_pitch_shift.grid(row=3, column=0, sticky="w", pady=5)

entry_pitch_shift = tk.Entry(frame, width=10)
entry_pitch_shift.grid(row=3, column=1, pady=5)
entry_pitch_shift.insert(0, "0")  # Mặc định là không thay đổi cao độ

# Nút chuyển đổi âm thanh
button_transform = tk.Button(frame, text="Transform Audio", command=transform_audio, width=25)
button_transform.grid(row=4, column=0, pady=5)

# Nút Pause và Resume
button_pause = ttk.Button(frame, text="Pause Audio", command=pause_audio, width=25)
button_pause.grid(row=5, column=0, pady=5)

button_resume = ttk.Button(frame, text="Resume Audio", command=resume_audio, width=25)
button_resume.grid(row=5, column=1, pady=5)

# Nút Clear (dừng hoàn toàn và giải phóng tài nguyên)
button_clear = ttk.Button(frame, text="Clear Audio", command=clear_audio, width=25)
button_clear.grid(row=6, column=0, pady=5)
# Chạy giao diện
root.mainloop()
