import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import sys # Importar o módulo sys

class TextEditor:
    """
    Uma aplicação de editor de texto simples com uma interface gráfica
    construída com a biblioteca Tkinter do Python, com um estilo simplificado,
    sem menus, barras de rolagem ou rodapé.
    Possui sobrescrita de caracteres, backspace/delete que apenas movem o cursor,
    salvamento automático, e impõe um limite de 80 caracteres por linha.
    Remove suporte a TAB e limita navegação apenas às setas.
    Permite abrir um arquivo existente como argumento na inicialização.
    """
    def __init__(self, root, initial_file_path=None): # Adicionado initial_file_path
        """Inicializa o editor de texto."""
        self.root = root
        self.file_path = None  # Caminho para o ficheiro atualmente aberto
        self.auto_save_id = None # Para controlar o agendamento do auto-save
        self.setup_ui()

        # --- Lógica para abrir arquivo inicial ou criar novo com timestamp ---
        if initial_file_path:
            # Se um caminho de arquivo foi fornecido, tenta abri-lo
            self.open_file(file_path=initial_file_path)
        elif self.file_path is None: # Se nenhum arquivo foi carregado (e não havia inicial_file_path)
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            new_filename = f"{timestamp}.txt"
            # Define o caminho do arquivo no diretório atual do script
            self.file_path = os.path.join(os.getcwd(), new_filename)
            # Salva o arquivo vazio imediatamente
            self.save_file()
            # Embora a barra de título esteja oculta, é bom manter o controle interno
            self.root.title(f"Fluxo - {new_filename}")

    def setup_ui(self):
        """Configura a interface gráfica do utilizador."""
        # Não define um título para a janela (barra de título removida)
        self.root.geometry("1024x600")

        # --- Área de Texto Principal ---
        text_frame = tk.Frame(self.root)
        text_frame.pack(expand=True, fill='both')

        self.text_area = tk.Text(
            text_frame, 
            wrap='none', # Importante: 'none' para não quebrar visualmente o texto em 80 colunas
            undo=True, # Mantém o undo para Ctrl+Z
            font=("Courier", 14), # Fonte Courier
            padx=10,
            pady=10,
            background="#2d2d2d", 
            insertbackground="white", 
            foreground="#A0A0A0" # Cinza claro para as outras linhas
        )
        self.text_area.pack(side='left', expand=True, fill='both')

        # Configura a tag para destacar a linha atual
        self.text_area.tag_configure('current_line', background="#404040", foreground="white")
        # Configura a tag para o aviso de limite de caracteres excedido (vermelho suave)
        self.text_area.tag_configure('limit_exceeded', background="#663333", foreground="white") # Um tom de vermelho/vinho

        # --- Bindings de Eventos e Atalhos ---
        self.text_area.bind('<KeyRelease>', self.update_status)
        self.text_area.bind('<ButtonRelease>', self.update_status)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_editor)

        self.root.bind("<Control-o>", self.open_file)
        self.root.bind("<Control-s>", self.save_file)
        self.root.bind("<Control-q>", self.exit_editor)
        self.root.bind("<Control-n>", self.new_file)

        # Implementa o backspace para APENAS mover o cursor para trás
        self.text_area.bind('<BackSpace>', self.handle_backspace)
        # Implementa o delete para APENAS mover o cursor para frente
        self.text_area.bind('<Delete>', self.handle_delete)
        
        # Implementa a sobrescrita para caracteres digitáveis e o bloqueio de linha
        # Ignora eventos com a tecla Control pressionada
        self.text_area.bind('<Key>', self.handle_key_press_for_overwrite)

        # --- Desabilita TAB ---
        # Apenas '<Tab>' é geralmente suficiente para cobrir tanto Tab quanto Shift+Tab
        self.text_area.bind('<Tab>', self.handle_no_op) 

        # --- Desabilita outras teclas de navegação além das setas ---
        self.text_area.bind('<Home>', self.handle_no_op)
        self.text_area.bind('<End>', self.handle_no_op)
        self.text_area.bind('<Prior>', self.handle_no_op) # PageUp
        self.text_area.bind('<Next>', self.handle_no_op)  # PageDown
        self.text_area.bind('<Control-Home>', self.handle_no_op)
        self.text_area.bind('<Control-End>', self.handle_no_op)
        self.text_area.bind('<Control-Left>', self.handle_no_op)
        self.text_area.bind('<Control-Right>', self.handle_no_op)


        # --- Inicia o salvamento automático ---
        self.start_auto_save()

        # Foca na área de texto e atualiza a UI inicial
        self.text_area.focus_set()
        self.update_status()

    def handle_no_op(self, event=None):
        """Função vazia para desabilitar o comportamento padrão de uma tecla."""
        return "break" # Impede qualquer ação padrão

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

        # Remove o destaque de limite de TODAS as linhas antes de aplicar (para limpar estados antigos)
        self.text_area.tag_remove('limit_exceeded', '1.0', 'end')

        # Verifica se a tecla Control NÃO está pressionada e se é um caractere imprimível
        if not (event.state & 0x4) and event.char and len(event.char) == 1 and \
           event.keysym not in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Return']:
            
            current_index = self.text_area.index(tk.INSERT)
            line_start_index = f"{current_index.split('.')[0]}.0"
            line_content = self.text_area.get(line_start_index, current_index)
            
            current_line_length = len(line_content)

            # Se a linha já tem 80 caracteres ou mais
            if current_line_length >= MAX_LINE_LENGTH:
                # Se a tecla pressionada NÃO é Enter, bloqueia a digitação
                if event.keysym != 'Return':
                    # Aplica o destaque de limite à linha atual
                    self.text_area.tag_add('limit_exceeded', line_start_index, f"{current_index.split('.')[0]}.end")
                    return "break" # Impede que o caractere seja inserido
            
            # Se a linha está dentro do limite ou se é a tecla Enter
            # Lógica de sobrescrita (como antes)
            char_at_cursor = self.text_area.get(current_index, f"{current_index}+1c")
            if char_at_cursor and char_at_cursor != '\n' and current_index != self.text_area.index(tk.END + "-1c"):
                self.text_area.delete(current_index)
            
            return None # Deixa o Tkinter inserir o caractere normalmente

        return None 

    def new_file(self, event=None):
        """Cria um novo ficheiro, limpando a área de texto."""
        if self.has_changes():
            if not messagebox.askyesno("Guardar Alterações?", "O ficheiro atual tem alterações não guardadas. Quer continuar?"):
                return
        
        self.text_area.delete(1.0, tk.END)
        self.file_path = None 
        self.update_status()

    def open_file(self, event=None, file_path=None): # Adicionado file_path como argumento opcional
        """Abre um ficheiro existente."""
        if file_path is None: # Se não foi passado um caminho, pede ao usuário
            path = filedialog.askopenfilename(
                filetypes=[("Ficheiros de Texto", "*.txt"), ("Todos os Ficheiros", "*.*")]
            )
            if not path:
                return
        else: # Se o caminho foi passado como argumento
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
            # Se o arquivo não existe, volta ao estado de "novo arquivo" ou cria um com timestamp
            self.file_path = None # Garante que o estado seja de "nenhum arquivo aberto"
            self.new_file() # Reinicia como um novo arquivo para evitar loop no salvamento automático
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
            # Se o arquivo não existe no disco (foi excluído externamente, por exemplo)
            # mas o editor ainda aponta para ele, consideramos que há alterações a serem salvas (como um novo arquivo)
            return True 
        except Exception:
            return True

    def update_status(self, event=None):
        """Atualiza o destaque da linha atual e centraliza-a.
           Também gerencia o destaque de limite de linha."""
        
        # Remove o destaque anterior da linha atual
        self.text_area.tag_remove('current_line', '1.0', 'end')
        
        # Adiciona o destaque à linha atual
        current_line_index_str = self.text_area.index(tk.INSERT).split('.')[0]
        line_start_index = f"{current_line_index_str}.0"
        line_end_index = f"{current_line_index_str}.end"
        self.text_area.tag_add('current_line', line_start_index, line_end_index)

        # Atualiza a verificação de limite de linha ao mover o cursor ou soltar tecla/botão
        # Remove o destaque de limite de TODAS as linhas antes de aplicar (para limpar estados antigos)
        self.text_area.tag_remove('limit_exceeded', '1.0', 'end')
        
        # Re-verifica a linha atual para aplicar o destaque de limite se necessário
        current_line_content = self.text_area.get(line_start_index, line_end_index).replace('\n', '')
        if len(current_line_content) >= 80:
             self.text_area.tag_add('limit_exceeded', line_start_index, line_end_index)


        # Centraliza a linha atual na tela
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
    
    # Verifica se um caminho de arquivo foi passado como argumento
    file_to_open = None
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1] # O primeiro argumento após o nome do script

    editor = TextEditor(main_window, initial_file_path=file_to_open)
    main_window.mainloop()