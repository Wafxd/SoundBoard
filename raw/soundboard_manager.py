import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
from PIL import Image, ImageTk

KEYMAP_FILE = "keymap.json"

class SoundboardManager:
    def __init__(self, root):
        self.sounds = []
        self.temp_thumbnails = {}
        self.temp_thumbnails_ext = {}  # Menyimpan ekstensi thumbnail
        self.root = root
        root.title("Soundboard Manager")

        self.listbox = tk.Listbox(root, width=50)
        self.listbox.pack(pady=10)

        # Frame tombol kiri dan kanan
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        # Tombol kiri
        left_buttons = tk.Frame(button_frame)
        left_buttons.grid(row=0, column=0, padx=10)

        tk.Button(left_buttons, text="Tambah Sound", width=20, command=self.add_sound).pack(pady=5)
        tk.Button(left_buttons, text="Hapus Sound", width=20, command=self.remove_sound).pack(pady=5)

        # Tombol kanan
        right_buttons = tk.Frame(button_frame)
        right_buttons.grid(row=0, column=1, padx=10)

        tk.Button(right_buttons, text="Pilih Tombol", width=20, command=self.assign_key).pack(pady=5)
        tk.Button(right_buttons, text="Tambah Thumbnail", width=20, command=self.add_thumbnail).pack(pady=5)

        # Label assign key
        self.key_label = tk.Label(root, text="Klik Pilih Tombol")
        self.key_label.pack(pady=5)

        # Tombol save assignments (melebar)
        tk.Button(root, text="Simpan semua", width=50, bg="green", fg="white", command=self.save_keymap).pack(pady=10)

        self.load_keymap()

    def add_sound(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if file_path:
            self.sounds.append({"key": "", "path": file_path})
            self.refresh_listbox()

    def add_thumbnail(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]

        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.gif")])
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()  # Ambil ekstensi
            img = Image.open(file_path)

            if ext == '.gif':  # Jika file adalah animasi .gif
                frames = []
                for frame in range(img.n_frames):
                    img.seek(frame)  # Pindah ke frame tertentu
                    img_cropped = img.copy()
                    size = min(img_cropped.size)
                    img_cropped = img_cropped.crop((
                        (img_cropped.width - size) // 2,
                        (img_cropped.height - size) // 2,
                        (img_cropped.width + size) // 2,
                        (img_cropped.height + size) // 2
                    ))
                    frames.append(img_cropped)
                self.temp_thumbnails[index] = frames
            else:  # Jika file bukan animasi .gif
                size = min(img.size)
                img_cropped = img.crop((
                    (img.width - size) // 2,
                    (img.height - size) // 2,
                    (img.width + size) // 2,
                    (img.height + size) // 2
                ))
                self.temp_thumbnails[index] = [img_cropped]  # Simpan gambar tunggal dalam list
            self.temp_thumbnails_ext[index] = ext  # Simpan ekstensi
            self.sounds[index]["thumbnail"] = f"thumb_{index}{ext} (pending)"
            self.refresh_listbox()

    def remove_sound(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]

        thumbnail_path = self.sounds[index].get("thumbnail")
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                os.remove(thumbnail_path)
            except Exception as e:
                print(f"Gagal menghapus thumbnail: {e}")

        del self.sounds[index]
        self.refresh_listbox()

    def assign_key(self):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]

        def on_key(event):
            key = event.keysym
            for i, item in enumerate(self.sounds):
                if item["key"] == key and i != index:
                    messagebox.showwarning("Tombol udh dipilih oy", f"The key '{key}' Coba tombol lain.")
                    self.root.unbind("<Key>")
                    self.key_label.config(text="Klik button Masukkan Tombol")
                    return

            self.sounds[index]["key"] = key
            self.key_label.config(text=f"Assigned key '{key}'")
            self.refresh_listbox()
            self.root.unbind("<Key>")
            self.key_label.after(2000, lambda: self.key_label.config(text="Assign Key:"))

        self.key_label.config(text="Sedang Memilih...")
        self.root.bind("<Key>", on_key)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for sound in self.sounds:
            key = sound["key"] if sound["key"] else "(unassigned)"
            filename = os.path.basename(sound["path"])
            thumb = os.path.basename(sound.get("thumbnail", "(no thumb)"))
            self.listbox.insert(tk.END, f"{key} | {filename} | {thumb}")

    def save_keymap(self):
        os.makedirs("thumbnails", exist_ok=True)
        for index, frames in self.temp_thumbnails.items():
            ext = self.temp_thumbnails_ext.get(index, ".png")  # Default fallback .png
            path = os.path.join("thumbnails", f"thumb_{index}{ext}")
            if ext == '.gif':
                frames[0].save(path, save_all=True, append_images=frames[1:], loop=0)  # Menyimpan animasi dengan semua frame
            else:
                frames[0].save(path)  # Simpan gambar biasa
            self.sounds[index]["thumbnail"] = path

        self.temp_thumbnails.clear()
        self.temp_thumbnails_ext.clear()

        keymap = {
            item["key"]: {
                "path": item["path"],
                "thumbnail": item.get("thumbnail", "")
            }
            for item in self.sounds if item["key"]
        }

        with open(KEYMAP_FILE, "w") as f:
            json.dump(keymap, f, indent=2)

        messagebox.showinfo("Saved", "Key assignments saved!")
        self.refresh_listbox()

    def load_keymap(self):
        if os.path.exists(KEYMAP_FILE):
            with open(KEYMAP_FILE, "r") as f:
                data = json.load(f)
                self.sounds = [
                    {"key": k, "path": v["path"], "thumbnail": v.get("thumbnail", "")}
                    for k, v in data.items()
                ]
            self.refresh_listbox()


if __name__ == "__main__":
    root = tk.Tk()
    app = SoundboardManager(root)
    root.mainloop()
