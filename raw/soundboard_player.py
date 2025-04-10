import tkinter as tk
from PIL import Image, ImageTk
import pygame
import keyboard
import json
import os
from PIL import ImageDraw

KEYMAP_FILE = "keymap.json"

class SoundboardPlayer:
    def __init__(self, root):
        self.root = root
        self.keymap = {}
        self.image_cache = {}  # Buat nyimpan ImageTk agar gak ke-GC
        self.gif_cache = {}  # Cache untuk GIF animasi

        pygame.mixer.init()
        root.title("Soundboard Player")

        # Frame buat thumbnail grid
        self.thumb_frame = tk.Frame(root)
        self.thumb_frame.pack(pady=10)

        self.stop_button = tk.Button(root, text="STOP", command=self.stop_music, bg="red", fg="white")
        self.stop_button.pack(pady=10)

        self.load_keymap()
        keyboard.hook(self.handle_key_press)

    def load_keymap(self):
        if os.path.exists(KEYMAP_FILE):
            with open(KEYMAP_FILE, "r") as f:
                self.keymap = json.load(f)

            self.populate_thumbnails()
        else:
            tk.Label(self.thumb_frame, text="No keymap.json found!").grid(row=0, column=0)

    def create_rounded_image(self, img, radius=10):
        img = img.convert("RGBA")
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.width, img.height), radius=radius, fill=255)
        img.putalpha(mask)
        return img

    def populate_thumbnails(self):
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()

        for i, (key, data) in enumerate(self.keymap.items()):
            row = i // 3
            col = i % 3

            thumb_path = data.get("thumbnail")
            if thumb_path and os.path.exists(thumb_path):
                if thumb_path.lower().endswith(".gif"):
                    self.display_gif(thumb_path, row, col, key)
                else:
                    img = Image.open(thumb_path).resize((150, 150))
                    # Apply rounded corner
                    rounded = self.create_rounded_image(img)

                    photo = ImageTk.PhotoImage(rounded)
                    self.image_cache[i] = photo  # biar ga kehapus

                    label = tk.Label(self.thumb_frame, image=photo, cursor="hand2", bd=0)
                    label.grid(row=row, column=col, padx=10, pady=10)
                    label.bind("<Button-1>", lambda e, k=key: self.play_music(k))
            else:
                img = Image.new("RGB", (150, 150), color="gray")
                rounded = self.create_rounded_image(img)

                photo = ImageTk.PhotoImage(rounded)
                self.image_cache[i] = photo

                label = tk.Label(self.thumb_frame, image=photo, cursor="hand2", bd=0)
                label.grid(row=row, column=col, padx=10, pady=10)
                label.bind("<Button-1>", lambda e, k=key: self.play_music(k))

    def display_gif(self, thumb_path, row, col, key):
        gif = Image.open(thumb_path)
        frames = []
        for frame in range(gif.n_frames):
            gif.seek(frame)
            # Resize setiap frame agar ukurannya 150x150 dan beri rounded corner
            frame_resized = gif.copy().resize((150, 150))
            frame_rounded = self.create_rounded_image(frame_resized)  # Terapkan rounded corner
            frames.append(frame_rounded)

        self.gif_cache[key] = {
            "frames": frames,
            "index": 0,
            "label": None,
        }

        self.update_gif(key, row, col)

    def update_gif(self, key, row, col):
        gif_data = self.gif_cache[key]
        frame = gif_data["frames"][gif_data["index"]]

        # Convert frame to ImageTk.PhotoImage
        photo = ImageTk.PhotoImage(frame)

        # Cache the photo to prevent it from being garbage collected
        self.image_cache[key] = photo

        if not gif_data["label"]:
            gif_data["label"] = tk.Label(self.thumb_frame, image=photo, cursor="hand2", bd=0)
            gif_data["label"].grid(row=row, column=col, padx=10, pady=10)
            gif_data["label"].bind("<Button-1>", lambda e, k=key: self.play_music(k))

        gif_data["label"].config(image=photo)

        # Update the frame index and loop the animation
        gif_data["index"] = (gif_data["index"] + 1) % len(gif_data["frames"])
        self.root.after(100, self.update_gif, key, row, col)  # Update every 100 ms

    def handle_key_press(self, event):
        key = event.name
        if key in ["minus", "subtract", "-"]:
            self.stop_music()
        elif key in self.keymap:
            self.play_music(key)

    def play_music(self, key):
        try:
            pygame.mixer.music.load(self.keymap[key]["path"])
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error loading sound: {e}")

    def stop_music(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SoundboardPlayer(root)
    root.mainloop()
