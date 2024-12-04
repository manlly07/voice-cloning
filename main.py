import tkinter as tk
from tkinter import filedialog, messagebox
from audio_processing import transform_audio, open_file, play_audio, pause_audio, resume_audio, clear_audio

# Giao diện chính
root = tk.Tk()
root.title("Biến Đổi Âm Thanh WAV")
root.geometry("400x400")

# Chọn file âm thanh
label_file = tk.Label(root, text="Chọn file WAV:")
label_file.pack(pady=5)

entry_file = tk.Entry(root, width=40)
entry_file.pack(pady=5)

button_browse = tk.Button(root, text="Duyệt", command=open_file)
button_browse.pack(pady=5)

# Tùy chọn nhân vật
label_option = tk.Label(root, text="Chọn nhân vật:")
label_option.pack(pady=5)

character_option = tk.StringVar()
character_option.set("Conan")  # Default value

options = ["Conan", "Shin", "Doraemon", "Suspect", "Mẹ Shin", "Nobita", "Clown", "Donald"]
dropdown = tk.OptionMenu(root, character_option, *options)
dropdown.pack(pady=5)

label_pitch_shift = tk.Label(root, text="Thay đổi cao độ (bước):")
label_pitch_shift.pack(pady=5)
entry_pitch_shift = tk.Entry(root, width=10)
entry_pitch_shift.pack(pady=5)
entry_pitch_shift.insert(0, "0")  # Mặc định là không thay đổi cao độ

# Nút chuyển đổi âm thanh
button_transform = tk.Button(root, text="Biến Đổi Âm Thanh", command=transform_audio)
button_transform.pack(pady=20)

# Nút Pause và Resume
button_pause = tk.Button(root, text="Pause", command=pause_audio)
button_pause.pack(pady=5)

button_resume = tk.Button(root, text="Resume", command=resume_audio)
button_resume.pack(pady=5)

# Nút Clear (dừng hoàn toàn và giải phóng tài nguyên)
button_clear = tk.Button(root, text="Clear", command=clear_audio)
button_clear.pack(pady=5)

# Chạy giao diện
root.mainloop()
