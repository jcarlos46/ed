import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import sys

class TextEditor:
    """
    Uma aplicação de editor de texto simples com uma interface gráfica
    construída com a biblioteca Tkinter do Python, com um estilo simplificado.
    Possui sobrescrita de caracteres, backspace/delete que apenas movem o cursor,
    salvamento automático, e impõe um limite de 80 caracteres por linha.
    Remove suporte a TAB e limita navegação apenas às setas.
    Permite abrir um arquivo existente como argumento na inicialização.
    **Quebra de linha permitida APENAS após a última linha do documento ou
    quando a linha atual atinge 80 caracteres.**
    **O texto é visualmente centralizado na janela com um tema escuro.**
    """
    def __init__(self, root, initial_file_path=None):
        """Inicializa o editor de texto."""
        self.root = root
        self.file_path = None
        self.auto_save_id = None
        self.setup_ui()

        if initial_file_path:
            self.open_file(file_path=initial_file_path)
        elif self.file_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            new_filename = f"{timestamp}.txt"
            self.file_path = os.path.join(os.getcwd(), new_filename)
            self.save_file()
            self.root.title(f"Editor de Texto - {new_filename}")

    def setup_ui(self):
        """Configura a interface gráfica do utilizador."""
        self.root.geometry("800x600")
        
        # --- NOVO: Define o fundo da janela principal para escuro ---
        self.root.configure(bg="#2d2d2d")

        # --- Frame para o texto que será centralizado ---
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        content_frame = tk.Frame(self.root, bg="#2d2d2d")
        content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # --- Área de Texto Principal ---
        self.text_area = tk.Text(
            content_frame,
            wrap='none',
            undo=True,
            font=("Courier", 14),
            padx=10,
            pady=10,
            background="#2d2d2d",
            insertbackground="white",
            foreground="#A0A0A0"
        )
        self.text_area.pack(expand=True, fill='both')

        # Configurações de tags (cores)
        self.text_area.tag_configure('current_line', background="#404040", foreground="white")
        self.text_area.tag_configure('limit_exceeded', background="#663333", foreground="white")

        # --- Bindings de Eventos e Atalhos ---
        self.text_area.bind('<KeyRelease>', self.update_status)
        self.text_area.bind('<ButtonRelease>', self.update_status)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_editor)

        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-s>", self.save_file)
        self.root.bind("<Control-q>", self.exit_editor)
        self.root.bind("<Control-n>", self.new_file)

        self.text_area.bind('<BackSpace>', self.handle_backspace)
        self.text_area.bind('<Delete>', self.handle_delete)
        self.text_area.bind('<Return>', self.handle_enter_key)
        self.text_area.bind('<Key>', self.handle_key_press_for_overwrite)
        self.text_area.bind('<Tab>', self.handle_no_op)
        self.text_area.bind('<Home>', self.handle_no_op)
        self.text_area.bind('<End>', self.handle_no_op)
        self.text_area.bind('<Prior>', self.handle_no_op)
        self.text_area.bind('<Next>', self.handle_no_op)
        self.text_area.bind('<Control-Home>', self.handle_no_op)
        self.text_area.bind('<Control-End>', self.handle_no_op)
        self.text_area.bind('<Control-Left>', self.handle_no_op)
        self.text_area.bind('<Control-Right>', self.handle_no_op)

        self.start_auto_save()
        self.text_area.focus_set()
        self.update_status()

    def handle_no_op(self, event=None):
        """Função vazia para desabilitar o comportamento padrão de uma tecla."""
        return "break"

    def handle_enter_key(self, event=None):
        """
        Manipula a tecla Enter para permitir quebras de linha apenas:
        1. No final do documento.
        2. Quando a linha atual já atingiu 80 caracteres.
        Caso contrário, move o cursor para o final da linha atual ou início da próxima.
        """
        MAX_LINE_LENGTH = 80

        current_index = self.text_area.index(tk.INSERT)
        line_num, col_num = map(int, current_index.split('.'))

        line_start_index = f"{line_num}.0"
        line_end_index_incl_newline = f"{line_num}.end"
        line_content = self.text_area.get(line_start_index, line_end_index_incl_newline).replace('\n', '')
        current_line_length = len(line_content)

        # Verifica se estamos na última linha do documento
        last_line_index = self.text_area.index(tk.END + "-1c linestart").split('.')[0]
        is_last_line = (line_num == int(last_line_index))

        # Se a linha atual atingiu 80 caracteres
        if current_line_length >= MAX_LINE_LENGTH:
            next_line_start = f"{line_num + 1}.0"
            next_line_end = f"{line_num + 1}.end"
            
            # Verifica se a próxima linha existe e tem conteúdo
            if self.text_area.compare(next_line_start, "<", tk.END):
                next_line_content = self.text_area.get(next_line_start, next_line_end).replace('\n', '')
                if next_line_content:  # Se há conteúdo na próxima linha
                    # Vai para o início da próxima linha
                    self.text_area.mark_set(tk.INSERT, next_line_start)
                else:  # Se a próxima linha está vazia
                    # Cria uma nova linha
                    self.text_area.edit_separator()
                    self.text_area.insert(tk.INSERT, '\n')
            else:  # Se não há próxima linha
                # Cria uma nova linha
                self.text_area.edit_separator()
                self.text_area.insert(tk.INSERT, '\n')
            
            self.update_status()
            return "break"

        # Se estamos na última linha e no final dela
        if is_last_line and col_num == current_line_length:
            self.text_area.edit_separator()
            self.text_area.insert(tk.INSERT, '\n')
            self.update_status()
            return "break"

        # Caso contrário, move o cursor
        if col_num < current_line_length:
            self.text_area.mark_set(tk.INSERT, line_end_index_incl_newline)
        else:
            next_line_start = f"{line_num + 1}.0"
            if self.text_area.compare(next_line_start, "<", tk.END):
                self.text_area.mark_set(tk.INSERT, next_line_start)
            else:
                self.text_area.mark_set(tk.INSERT, line_end_index_incl_newline)

        self.update_status()
        return "break"

    def start_auto_save(self):
        """Inicia o agendamento do salvamento automático."""
        self.auto_save_id = self.root.after(5000, self.auto_save_file)

    def auto_save_file(self):
        """
        Verifica se há alterações e salva o arquivo automaticamente.
        Em seguida, reagenda-se.
        """
        if self.has_changes() and self.file_path:
            self.save_file()

        self.auto_save_id = self.root.after(5000, self.auto_save_file)

    def handle_backspace(self, event=None):
        """Move o cursor para trás sem apagar o caractere."""
        current_index = self.text_area.index(tk.INSERT)
        if current_index != "1.0":
            self.text_area.mark_set(tk.INSERT, f"{current_index}-1c")
        self.update_status()
        return "break"

    def handle_delete(self, event=None):
        """Move o cursor para frente sem apagar o caractere."""
        current_index = self.text_area.index(tk.INSERT)
        if current_index != self.text_area.index(tk.END + "-1c"):
            self.text_area.mark_set(tk.INSERT, f"{current_index}+1c")
        self.update_status()
        return "break"

    def handle_key_press_for_overwrite(self, event=None):
        """
        Manipula o pressionamento de tecla para implementar a sobrescrita
        e impor o limite de 80 caracteres por linha.
        """
        MAX_LINE_LENGTH = 80

        self.text_area.tag_remove('limit_exceeded', '1.0', 'end')

        if event.state & 0x4:
            if event.keysym in ['z', 'y']:
                return None

        if not (event.state & 0x4) and event.char and len(event.char) == 1 and \
           event.keysym not in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Return']:

            current_index = self.text_area.index(tk.INSERT)
            line_start_index = f"{current_index.split('.')[0]}.0"
            line_content = self.text_area.get(line_start_index, current_index)

            current_line_length = len(line_content)

            if current_line_length >= MAX_LINE_LENGTH:
                self.text_area.tag_add('limit_exceeded', line_start_index, f"{current_index.split('.')[0]}.end")
                return "break"

            char_at_cursor = self.text_area.get(current_index, f"{current_index}+1c")
            if char_at_cursor and char_at_cursor != '\n' and current_index != self.text_area.index(tk.END + "-1c"):
                self.text_area.delete(current_index)

            return None

        return None

    def new_file(self, event=None):
        """Cria um novo ficheiro, limpando a área de texto."""
        if self.has_changes():
            if not messagebox.askyesno("Guardar Alterações?", "O ficheiro atual tem alterações não guardadas. Quer continuar?"):
                return

        self.text_area.delete(1.0, tk.END)
        self.file_path = None
        self.update_status()

    def open_file(self, event=None, file_path=None):
        """Abre um ficheiro existente."""
        if file_path is None:
            path = filedialog.askopenfilename(
                filetypes=[("Ficheiros de Texto", "*.txt"), ("Todos os Ficheiros", "*.*")]
            )
            if not path:
                return
        else:
            path = file_path

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, content)
            self.file_path = path
            self.root.title(f"Editor de Texto - {os.path.basename(path)}")
            self.update_status()
        except FileNotFoundError:
            messagebox.showerror("Erro ao Abrir", f"O ficheiro não foi encontrado:\n{path}")
            self.file_path = None
            self.new_file()
        except Exception as e:
            messagebox.showerror("Erro ao Abrir", f"Não foi possível abrir o ficheiro:\n{e}")

    def save_file(self, event=None):
        """Guarda o ficheiro atual. Se for novo, pede um caminho."""
        if self.file_path:
            try:
                content = self.text_area.get(1.0, "end-1c")
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.root.title(f"Editor de Texto - {os.path.basename(self.file_path)}")
            except Exception as e:
                messagebox.showerror("Erro ao Guardar", f"Não foi possível guardar o ficheiro:\n{e}")
        else:
            self.save_as_file()
        return "break"

    def save_as_file(self):
        """Guarda o ficheiro atual num novo local."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Ficheiros de Texto", "*.txt"), ("Todos os Ficheiros", "*.*")]
        )
        if not path:
            return

        self.file_path = path
        self.save_file()

    def has_changes(self):
        """Verifica se existem alterações não guardadas."""
        if not self.file_path:
            return len(self.text_area.get(1.0, "end-1c")) > 0

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return self.text_area.get(1.0, "end-1c") != f.read()
        except FileNotFoundError:
            return True
        except Exception:
            return True

    def update_status(self, event=None):
        """Atualiza o destaque da linha atual e centraliza-a.
           Também gerencia o destaque de limite de linha."""

        self.text_area.tag_remove('current_line', '1.0', 'end')

        current_line_index_str = self.text_area.index(tk.INSERT).split('.')[0]
        line_start_index = f"{current_line_index_str}.0"
        line_end_index = f"{current_line_index_str}.end"
        self.text_area.tag_add('current_line', line_start_index, line_end_index)

        self.text_area.tag_remove('limit_exceeded', '1.0', 'end')

        current_line_content = self.text_area.get(line_start_index, line_end_index).replace('\n', '')
        if len(current_line_content) >= 80:
             self.text_area.tag_add('limit_exceeded', line_start_index, line_end_index)

        self.text_area.yview_pickplace(tk.INSERT)

    def exit_editor(self, event=None):
        """Sai da aplicação, verificando se há alterações não guardadas."""
        if self.auto_save_id:
            self.root.after_cancel(self.auto_save_id)

        if self.has_changes():
            if messagebox.askyesno("Sair", "Tem alterações não guardadas. Quer sair mesmo assim?"):
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    main_window = tk.Tk()

    file_to_open = None
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1]

    editor = TextEditor(main_window, initial_file_path=file_to_open)
    main_window.mainloop()