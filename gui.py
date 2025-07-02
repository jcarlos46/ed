import tkinter as tk
from tkinter import messagebox
import sys
import os
from datetime import datetime

class FluxoEditor:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.setup_ui()
        self.load_file_if_provided()
        
    def setup_window(self):
        """Configura a janela principal"""
        self.root.title("Fluxo - Editor sem Backspace")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        # Remove decorações para visual minimalista
        self.root.overrideredirect(False)  # Mantém barra de título para facilitar uso
        
        # Centraliza na tela
        self.center_window()
        
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_variables(self):
        """Inicializa variáveis do editor"""
        self.lines = []
        self.current_line = ""
        self.filename = None
        
    def setup_ui(self):
        """Cria a interface do usuário"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior para espaçamento
        top_spacer = tk.Frame(main_frame, bg='#1a1a1a')
        top_spacer.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Frame central para conteúdo
        content_frame = tk.Frame(main_frame, bg='#1a1a1a')
        content_frame.pack(side=tk.TOP, fill=tk.X, padx=40)
        
        # Área de texto para histórico (últimas 4 linhas)
        self.history_text = tk.Text(
            content_frame,
            height=4,
            font=('Courier', 14),
            bg='#1a1a1a',
            fg='#666666',
            border=0,
            highlightthickness=0,
            state=tk.DISABLED,
            wrap=tk.WORD,
            cursor='arrow'
        )
        self.history_text.pack(fill=tk.X, pady=(0, 20))
        
        # Label para linha atual
        self.current_label = tk.Label(
            content_frame,
            text="",
            font=('Courier', 14, 'bold'),
            bg='#1a1a1a',
            fg='#ffffff',
            anchor='w',
            justify='left'
        )
        self.current_label.pack(fill=tk.X, pady=(0, 20))
        
        # Frame inferior para espaçamento
        bottom_spacer = tk.Frame(main_frame, bg='#1a1a1a')
        bottom_spacer.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Label de status (no fundo)
        self.status_label = tk.Label(
            main_frame,
            text="Pressione Escape para sair",
            font=('Courier', 10),
            bg='#1a1a1a',
            fg='#444444'
        )
        self.status_label.pack(side=tk.BOTTOM, pady=10)
        
        # Bind de eventos
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<Return>', self.on_enter)
        self.root.bind('<Escape>', self.on_escape)
        
        # Impede backspace e delete
        self.root.bind('<BackSpace>', lambda e: "break")
        self.root.bind('<Delete>', lambda e: "break")
        
        # Foco na janela para capturar teclas
        self.root.focus_set()
        
    def create_filename(self):
        """Cria nome de arquivo com timestamp"""
        now = datetime.now()
        return now.strftime("%d-%m-%Y-%H-%M-%S.txt")
        
    def load_file_if_provided(self):
        """Carrega arquivo se fornecido via argumento"""
        if len(sys.argv) > 1:
            self.filename = sys.argv[1]
            if not self.filename.endswith('.txt'):
                self.filename += '.txt'
                
            if os.path.exists(self.filename):
                try:
                    with open(self.filename, 'r', encoding='utf-8') as f:
                        self.lines = [line.rstrip('\n\r') for line in f.readlines()]
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao carregar arquivo: {e}")
        else:
            self.filename = self.create_filename()
            
        # Cria arquivo se não existir
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    pass
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao criar arquivo: {e}")
                
        self.update_display()
        
    def save_incremental(self, line):
        """Salva uma linha incrementalmente"""
        try:
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
                f.flush()
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
            return False
            
    def save_complete(self):
        """Salva o arquivo completo"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                for line in self.lines:
                    f.write(line + '\n')
                if self.current_line.strip():
                    f.write(self.current_line + '\n')
                f.flush()
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
            return False
            
    def update_display(self):
        """Atualiza a exibição com degradê"""
        # Atualiza histórico com degradê
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete('1.0', tk.END)
        
        # Mostra últimas 4 linhas com degradê
        recent_lines = self.lines[-4:] if len(self.lines) >= 4 else self.lines
        
        # Cores do degradê (do mais transparente ao mais opaco)
        fade_colors = ['#333333', '#444444', '#555555', '#666666']
        
        for i, line in enumerate(recent_lines):
            color_index = i if i < len(fade_colors) else len(fade_colors) - 1
            self.history_text.insert(tk.END, line + '\n')
            
            # Aplica cor do degradê
            line_start = f"{i+1}.0"
            line_end = f"{i+1}.end"
            self.history_text.tag_add(f"fade_{i}", line_start, line_end)
            self.history_text.tag_config(f"fade_{i}", foreground=fade_colors[color_index])
            
        self.history_text.config(state=tk.DISABLED)
        
        # Atualiza linha atual com cursor
        cursor = "▋"
        self.current_label.config(text=self.current_line + cursor)
        
    def on_key_press(self, event):
        """Processa teclas pressionadas"""
        char = event.char
        
        # Ignora teclas especiais e não imprimíveis
        if not char or not char.isprintable():
            return "break"
            
        # Adiciona caractere à linha atual
        self.current_line += char
        self.update_display()
        return "break"
        
    def on_enter(self, event):
        """Processa Enter - nova linha"""
        # Adiciona linha atual ao histórico
        self.lines.append(self.current_line)
        
        # Salva incrementalmente
        self.save_incremental(self.current_line)
        
        # Limpa linha atual
        self.current_line = ""
        
        # Atualiza display
        self.update_display()
        return "break"
        
    def on_escape(self, event):
        """Processa Escape - sair"""
        # Salva arquivo completo antes de sair
        self.save_complete()
        self.root.quit()
        return "break"
        
    def run(self):
        """Inicia o editor"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.save_complete()
            
if __name__ == "__main__":
    editor = FluxoEditor()
    editor.run()