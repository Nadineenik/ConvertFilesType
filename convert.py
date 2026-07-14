import os
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from markitdown import MarkItDown
import pypandoc
from fpdf import FPDF

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class TkinterDnDCtk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class UniversalConverter(TkinterDnDCtk):
    def __init__(self):
        super().__init__()

        self.title("Universal Doc Converter Pro")
        self.geometry("1100x750")
        
        self.md_converter = MarkItDown()
        self.source_filename = ""
        self.output_directory = "" # Сюда сохраняем путь

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        logo = ctk.CTkLabel(self.sidebar, text="CONVERTER", font=ctk.CTkFont(size=20, weight="bold"))
        logo.pack(pady=20, padx=20)

        # 1. Выбор файла
        self.btn_open = ctk.CTkButton(self.sidebar, text="📁 Выбрать файл", command=self.open_file_dialog)
        self.btn_open.pack(pady=10, padx=20)

        # 2. Выбор папки (МЫ ЕЁ ВЕРНУЛИ)
        self.btn_dest = ctk.CTkButton(self.sidebar, text="⚙️ Папка сохранения", 
                                       fg_color="transparent", border_width=1,
                                       command=self.choose_directory)
        self.btn_dest.pack(pady=10, padx=20)
        
        self.dir_info_label = ctk.CTkLabel(self.sidebar, text="Папка: не выбрана", font=ctk.CTkFont(size=10), text_color="gray")
        self.dir_info_label.pack(pady=(0, 10))

        # 3. Выбор формата
        ctk.CTkLabel(self.sidebar, text="Экспортировать в:", font=ctk.CTkFont(size=12)).pack(pady=(20, 0))
        self.export_type = ctk.CTkOptionMenu(self.sidebar, values=["Markdown (.md)", "Word (.docx)", "PDF (.pdf)", "Text (.txt)"])
        self.export_type.pack(pady=5, padx=20)

        # 4. Кнопка запуска
        self.btn_save = ctk.CTkButton(self.sidebar, text="🚀 Сохранить результат", 
                                       fg_color="#28a745", hover_color="#218838",
                                       command=self.save_file, state="disabled")
        self.btn_save.pack(pady=20, padx=20)

        self.btn_copy = ctk.CTkButton(self.sidebar, text="📋 Копировать текст", 
                                       fg_color="transparent", border_width=1,
                                       command=self.copy_to_clipboard, state="disabled")
        self.btn_copy.pack(pady=5, padx=20)

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"], command=ctk.set_appearance_mode)
        self.appearance_mode_menu.pack(side="bottom", padx=20, pady=20)
        self.appearance_mode_menu.set("System")

    def setup_main_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.drop_frame = tk.Label(
            self.main_container, 
            text="\n\n⬇️\nПеретащите любой файл сюда\n(PDF, Word, Markdown, TXT)\n\n",
            bg="#3b3b3b" if ctk.get_appearance_mode() == "Dark" else "#e1e1e1",
            fg="gray80" if ctk.get_appearance_mode() == "Dark" else "gray20",
            relief="groove", borderwidth=2, font=("Arial", 12, "italic")
        )
        self.drop_frame.pack(fill="x", pady=(0, 20))
        
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        self.text_preview = ctk.CTkTextbox(self.main_container, font=("Consolas", 13))
        self.text_preview.pack(expand=True, fill="both")

        self.status_label = ctk.CTkLabel(self.main_container, text="Готов к работе", font=ctk.CTkFont(size=11))
        self.status_label.pack(anchor="w", pady=(10, 0))

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.output_directory = path
            folder_name = os.path.basename(path)
            self.dir_info_label.configure(text=f"Папка: .../{folder_name}", text_color="#3498db")

    def handle_drop(self, event):
        file_path = event.data.strip('{}')
        self.process_file(file_path)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename()
        if file_path: self.process_file(file_path)

    def process_file(self, file_path):
        if not os.path.isfile(file_path): return
        ext = os.path.splitext(file_path)[1].lower()
        
        self.status_label.configure(text=f"⏳ Чтение: {os.path.basename(file_path)}...", text_color="#3498db")
        self.text_preview.delete("1.0", tk.END)
        
        if ext in ['.pdf', '.docx', '.pptx', '.xlsx']:
            self.export_type.set("Markdown (.md)")
        elif ext in ['.md', '.txt']:
            self.export_type.set("Word (.docx)")

        thread = threading.Thread(target=self.convert_to_preview_task, args=(file_path, ext), daemon=True)
        thread.start()

    def convert_to_preview_task(self, file_path, ext):
        try:
            if ext == '.txt' or ext == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                result = self.md_converter.convert(file_path)
                content = result.text_content
            
            name = os.path.splitext(os.path.basename(file_path))[0]
            self.after(0, self.on_preview_ready, content, name)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка чтения: {e}"))

    def on_preview_ready(self, content, name):
        self.text_preview.insert("1.0", content)
        self.source_filename = name
        self.btn_save.configure(state="normal")
        self.btn_copy.configure(state="normal")
        self.status_label.configure(text="✅ Файл загружен. Настройте формат и сохраните.", text_color="#28a745")

    def save_file(self):
        target_format = self.export_type.get()
        content = self.text_preview.get("1.0", tk.END)
        
        ext_map = {
            "Markdown (.md)": ".md",
            "Word (.docx)": ".docx",
            "PDF (.pdf)": ".pdf",
            "Text (.txt)": ".txt"
        }
        ext = ext_map[target_format]
        
        # Если папка уже выбрана, формируем путь сами
        if self.output_directory:
            final_path = os.path.join(self.output_directory, f"{self.source_filename}{ext}")
            # Если такой файл уже есть, лучше спросить подтверждение или добавить (1)
            if os.path.exists(final_path):
                if not messagebox.askyesno("Файл существует", "Файл с таким именем уже есть. Перезаписать?"):
                    final_path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"{self.source_filename}{ext}", initialdir=self.output_directory)
        else:
            # Если папка не выбрана - вызываем диалог
            final_path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=f"{self.source_filename}{ext}")
        
        if not final_path: return

        try:
            if target_format in ["Markdown (.md)", "Text (.txt)"]:
                with open(final_path, "w", encoding="utf-8") as f: f.write(content)
            
            elif target_format == "Word (.docx)":
                pypandoc.convert_text(content, 'docx', format='md', outputfile=final_path)
            
            elif target_format == "PDF (.pdf)":
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, content.encode('latin-1', 'replace').decode('latin-1'))
                pdf.output(final_path)

            messagebox.showinfo("Успех", f"Сохранено в:\n{final_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text_preview.get("1.0", tk.END))
        messagebox.showinfo("Инфо", "Текст скопирован в буфер обмена!")

if __name__ == "__main__":
    app = UniversalConverter()
    app.mainloop()