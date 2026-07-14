import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from markitdown import MarkItDown

class AdvancedConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown Pro Converter")
        self.root.geometry("800x600")
        
        # Инициализируем конвертер один раз
        self.md_converter = MarkItDown()
        self.current_content = ""
        self.source_filename = ""
        self.output_directory = ""

        self.setup_ui()

    def setup_ui(self):
        # --- Верхняя панель ---
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        self.drop_zone = tk.Label(
            top_frame, 
            text="Перетащите файл сюда (PDF, DOCX) или нажмите для выбора",
            bg="#ebf5ff", fg="#2c3e50",
            font=("Arial", 11, "italic"),
            height=4, relief="groove", cursor="hand2"
        )
        self.drop_zone.pack(fill="x", pady=5)
        
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.handle_drop)
        self.drop_zone.bind("<Button-1>", lambda e: self.open_file_dialog())

        # --- Предпросмотр ---
        ttk.Label(self.root, text="Предпросмотр (можно редактировать перед сохранением):", 
                  font=("Arial", 9, "bold")).pack(anchor="w", padx=10)

        preview_frame = ttk.Frame(self.root)
        preview_frame.pack(expand=True, fill="both", padx=10, pady=5)

        self.text_preview = tk.Text(preview_frame, wrap="word", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.text_preview.yview)
        self.text_preview.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.text_preview.pack(side="left", expand=True, fill="both")

        # --- Низ ---
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill="x")

        self.btn_dir = ttk.Button(bottom_frame, text="📁 Папка сохранения", command=self.choose_directory)
        self.btn_dir.pack(side="left", padx=5)

        self.dir_label = ttk.Label(bottom_frame, text="Сохранить рядом с оригиналом", foreground="gray")
        self.dir_label.pack(side="left", padx=5)

        self.save_btn = ttk.Button(bottom_frame, text="💾 Сохранить .md", command=self.save_file, state="disabled")
        self.save_btn.pack(side="right", padx=5)

        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def handle_drop(self, event):
        file_path = event.data.strip('{}')
        self.process_file(file_path)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Документы", "*.pdf *.docx *.pptx *.xlsx"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.process_file(file_path)

    def choose_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_directory = dir_path
            self.dir_label.config(text=f"Папка: {os.path.basename(dir_path)}", foreground="black")

    def process_file(self, file_path):
        if not os.path.isfile(file_path): return
        
        self.status_var.set("🔄 Читаю файл... (для PDF это может занять до 10-20 секунд)")
        self.text_preview.delete(1.0, tk.END)
        self.save_btn.config(state="disabled")
        self.drop_zone.config(bg="#fff9db") # Желтый фон во время работы

        thread = threading.Thread(target=self.convert_task, args=(file_path,), daemon=True)
        thread.start()

    def convert_task(self, file_path):
        try:
            # Сама конвертация
            result = self.md_converter.convert(file_path)
            content = result.text_content
            filename = os.path.splitext(os.path.basename(file_path))[0]
            
            # Передаем данные в основной поток через функцию обратного вызова
            self.root.after(0, self.on_conversion_complete, content, filename)
            
        except Exception as e:
            # Исправленная передача ошибки
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.on_conversion_error(msg))

    def on_conversion_complete(self, content, filename):
        self.current_content = content
        self.source_filename = filename
        self.text_preview.insert(tk.END, content)
        self.save_btn.config(state="normal")
        self.status_var.set("✅ Готово! Можете отредактировать текст и сохранить.")
        self.drop_zone.config(bg="#ebf5ff")

    def on_conversion_error(self, msg):
        self.status_var.set("❌ Ошибка")
        self.drop_zone.config(bg="#fee2e2")
        messagebox.showerror("Ошибка конвертации", f"Не удалось обработать файл:\n{msg}")

    def save_file(self):
        content_to_save = self.text_preview.get(1.0, tk.END)
        
        if self.output_directory:
            final_path = os.path.join(self.output_directory, f"{self.source_filename}.md")
        else:
            final_path = filedialog.asksaveasfilename(
                defaultextension=".md",
                initialfile=f"{self.source_filename}.md",
                filetypes=[("Markdown", "*.md")]
            )
        
        if final_path:
            try:
                with open(final_path, "w", encoding="utf-8") as f:
                    f.write(content_to_save)
                messagebox.showinfo("Успех", "Файл сохранен!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = AdvancedConverterApp(root)
    root.mainloop()