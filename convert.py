import os
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from markitdown import MarkItDown

# Настройки темы
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Создаем промежуточный класс для поддержки DnD в CustomTkinter
class TkinterDnDCtk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class ModernConverter(TkinterDnDCtk):
    def __init__(self):
        super().__init__()

        self.title("Markdown Pro Converter")
        self.geometry("1000x650")
        
        self.md_converter = MarkItDown()
        self.output_directory = ""
        self.source_filename = ""

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        logo = ctk.CTkLabel(self.sidebar, text="MD Converter", font=ctk.CTkFont(size=20, weight="bold"))
        logo.pack(pady=20, padx=20)

        self.btn_open = ctk.CTkButton(self.sidebar, text="📁 Выбрать файл", command=self.open_file_dialog)
        self.btn_open.pack(pady=10, padx=20)

        self.btn_dest = ctk.CTkButton(self.sidebar, text="⚙️ Папка сохранения", 
                                       fg_color="transparent", border_width=1,
                                       command=self.choose_directory)
        self.btn_dest.pack(pady=10, padx=20)

        self.btn_copy = ctk.CTkButton(self.sidebar, text="📋 Копировать текст", 
                                       command=self.copy_to_clipboard, state="disabled")
        self.btn_copy.pack(pady=10, padx=20)

        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Сохранить .md", 
                                       fg_color="#28a745", hover_color="#218838",
                                       command=self.save_file, state="disabled")
        self.btn_save.pack(pady=10, padx=20)

        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"],
                                                               command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.pack(side="bottom", padx=20, pady=20)
        self.appearance_mode_optionemenu.set("System")

    def setup_main_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Зона Drag-and-Drop
        # Используем обычный tk.Label внутри ctk, так как DnD лучше работает с нативными виджетами
        self.drop_frame = tk.Label(
            self.main_container, 
            text="\n\n⬇️\nПеретащите сюда файл PDF или Word\n\n",
            bg="#3b3b3b" if ctk.get_appearance_mode() == "Dark" else "#e1e1e1",
            fg="gray80" if ctk.get_appearance_mode() == "Dark" else "gray20",
            relief="groove",
            borderwidth=2,
            font=("Arial", 12, "italic")
        )
        self.drop_frame.pack(fill="x", pady=(0, 20))
        
        # Регистрация DnD
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        self.text_preview = ctk.CTkTextbox(self.main_container, font=("Consolas", 13))
        self.text_preview.pack(expand=True, fill="both")

        self.status_label = ctk.CTkLabel(self.main_container, text="Готов к работе", font=ctk.CTkFont(size=11))
        self.status_label.pack(anchor="w", pady=(10, 0))

    def handle_drop(self, event):
        file_path = event.data.strip('{}')
        self.process_file(file_path)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.docx *.xlsx *.pptx")])
        if file_path: self.process_file(file_path)

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path: 
            self.output_directory = path
            messagebox.showinfo("Папка выбрана", f"Файлы будут сохраняться в:\n{path}")

    def process_file(self, file_path):
        if not os.path.isfile(file_path): return
        name = os.path.basename(file_path)
        self.status_label.configure(text=f"⏳ Обработка: {name}...", text_color="#3498db")
        self.text_preview.delete("1.0", tk.END)
        
        thread = threading.Thread(target=self.convert_task, args=(file_path,), daemon=True)
        thread.start()

    def convert_task(self, file_path):
        try:
            result = self.md_converter.convert(file_path)
            name = os.path.splitext(os.path.basename(file_path))[0]
            self.after(0, self.on_complete, result.text_content, name)
        except Exception as e:
            err = str(e)
            self.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{err}"))

    def on_complete(self, content, name):
        self.text_preview.insert("1.0", content)
        self.source_filename = name
        self.btn_save.configure(state="normal")
        self.btn_copy.configure(state="normal")
        self.status_label.configure(text="✅ Конвертация завершена", text_color="#28a745")

    def copy_to_clipboard(self):
        content = self.text_preview.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Инфо", "Текст скопирован в буфер обмена!")

    def save_file(self):
        content = self.text_preview.get("1.0", tk.END)
        if self.output_directory:
            final_path = os.path.join(self.output_directory, f"{self.source_filename}.md")
        else:
            final_path = filedialog.asksaveasfilename(defaultextension=".md", initialfile=f"{self.source_filename}.md")
        
        if final_path:
            with open(final_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Успех", "Файл сохранен!")

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        # Обновляем цвет зоны сброса при смене темы
        if new_mode == "Dark":
            self.drop_frame.config(bg="#3b3b3b", fg="gray80")
        else:
            self.drop_frame.config(bg="#e1e1e1", fg="gray20")

if __name__ == "__main__":
    app = ModernConverter()
    app.mainloop()