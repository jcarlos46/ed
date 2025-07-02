#!/usr/bin/env python3
import curses
import os
import sys
import threading
import time
import subprocess
from datetime import datetime

class CursesTextEditor:
    """
    Editor de texto usando curses que mantém as funcionalidades do editor GUI:
    - Sobrescrita de caracteres
    - Limite de 80 caracteres por linha
    - Salvamento automático a cada 5 segundos
    - Navegação apenas com setas
    - Quebra de linha apenas no final do documento ou quando linha atinge 80 caracteres
    """
    
    def __init__(self, stdscr, initial_file_path=None):
        self.stdscr = stdscr
        self.lines = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.file_path = initial_file_path
        self.has_unsaved_changes = False
        self.running = True
        self.scroll_offset = 0
        
        # Configuração do curses
        stdscr.keypad(True)  # Habilita teclas de função e setas

        curses.curs_set(2)  # Cursor muito visível (bloco sólido)
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # Linha atual (texto preto, fundo ciano)
        curses.init_pair(2, curses.COLOR_WHITE, -1)                   # Limite excedido (texto branco, fundo padrão)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_RED)     # Linha atual + limite excedido (texto preto, fundo vermelho)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Barra de status
        
        # Obtém dimensões da tela
        self.height, self.width = stdscr.getmaxyx()
        self.text_height = self.height - 2  # Reserva espaço para status
        self.text_width = min(self.width, 80)  # Limita a 80 colunas
        
        # Carrega arquivo inicial se fornecido
        if initial_file_path:
            self.load_file(initial_file_path)
        else:
            # Cria arquivo com timestamp se não foi fornecido
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            self.file_path = f"{timestamp}.txt"
            self.save_file()
        
        # Inicia thread de salvamento automático
        self.auto_save_thread = threading.Thread(target=self.auto_save_loop, daemon=True)
        self.auto_save_thread.start()
    
    def load_file(self, file_path):
        """Carrega um arquivo existente"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.lines = content.split('\n') if content else [""]
            self.file_path = file_path
            self.has_unsaved_changes = False
        except FileNotFoundError:
            self.lines = [""]
            self.has_unsaved_changes = True
        except Exception as e:
            self.lines = [f"Erro ao carregar arquivo: {e}"]
            self.has_unsaved_changes = True
    
    def save_file(self):
        """Salva o arquivo atual"""
        if not self.file_path:
            return False
        
        try:
            content = '\n'.join(self.lines)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.has_unsaved_changes = False
            return True
        except Exception as e:
            return False
    
    def auto_save_loop(self):
        """Loop de salvamento automático executado em thread separada"""
        while self.running:
            time.sleep(5)
            if self.has_unsaved_changes and self.file_path:
                self.save_file()
    
    def get_current_line(self):
        """Retorna a linha atual"""
        if 0 <= self.cursor_y < len(self.lines):
            return self.lines[self.cursor_y]
        return ""
    
    def set_current_line(self, text):
        """Define o conteúdo da linha atual"""
        while len(self.lines) <= self.cursor_y:
            self.lines.append("")
        self.lines[self.cursor_y] = text
    
    def handle_printable_char(self, char):
        """Manipula caracteres imprimíveis com sobrescrita e limite de linha"""
        current_line = self.get_current_line()
        
        # Verifica limite de 80 caracteres
        if self.cursor_x >= 80:
            return
        
        # Sobrescrita: substitui caractere na posição atual
        if self.cursor_x < len(current_line):
            new_line = current_line[:self.cursor_x] + char + current_line[self.cursor_x + 1:]
        else:
            # Adiciona caractere no final da linha
            new_line = current_line + ' ' * (self.cursor_x - len(current_line)) + char
        
        self.set_current_line(new_line)
        self.cursor_x += 1
        self.has_unsaved_changes = True
    
    def handle_enter(self):
        """Manipula a tecla Enter conforme regras específicas"""
        current_line = self.get_current_line()
        
        # Permite quebra de linha apenas:
        # 1. No final do documento
        # 2. Quando a linha atual atingiu 80 caracteres
        
        is_last_line = self.cursor_y == len(self.lines) - 1
        line_at_limit = len(current_line) >= 80
        
        if is_last_line and self.cursor_x >= len(current_line):
            # Estamos no final da última linha - cria nova linha
            self.lines.append("")
            self.cursor_y += 1
            self.cursor_x = 0
            self.has_unsaved_changes = True
        elif line_at_limit:
            # Linha atingiu 80 caracteres - vai para próxima linha ou cria nova
            if self.cursor_y + 1 < len(self.lines):
                self.cursor_y += 1
                self.cursor_x = 0
            else:
                self.lines.append("")
                self.cursor_y += 1
                self.cursor_x = 0
                self.has_unsaved_changes = True
        else:
            # Move cursor para o final da linha atual ou início da próxima
            if self.cursor_x < len(current_line):
                self.cursor_x = len(current_line)
            elif self.cursor_y + 1 < len(self.lines):
                self.cursor_y += 1
                self.cursor_x = 0
    
    def handle_backspace(self):
        """Move cursor para trás sem apagar"""
        if self.cursor_x > 0:
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.get_current_line())
    
    def handle_delete(self):
        """Move cursor para frente sem apagar"""
        current_line = self.get_current_line()
        if self.cursor_x < len(current_line):
            self.cursor_x += 1
        elif self.cursor_y + 1 < len(self.lines):
            self.cursor_y += 1
            self.cursor_x = 0
    
    def handle_arrow_keys(self, key):
        """Manipula as teclas de seta"""
        if key == curses.KEY_UP and self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = min(self.cursor_x, len(self.get_current_line()))
        elif key == curses.KEY_DOWN and self.cursor_y < len(self.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = min(self.cursor_x, len(self.get_current_line()))
        elif key == curses.KEY_LEFT:
            self.handle_backspace()
        elif key == curses.KEY_RIGHT:
            self.handle_delete()
    
    def adjust_scroll(self):
        """Ajusta o scroll para manter o cursor visível"""
        if self.cursor_y < self.scroll_offset:
            self.scroll_offset = self.cursor_y
        elif self.cursor_y >= self.scroll_offset + self.text_height:
            self.scroll_offset = self.cursor_y - self.text_height + 1
    
    def render_screen(self):
        """Renderiza a tela completa"""
        self.adjust_scroll()
        self.stdscr.clear()
        
        # Renderiza linhas visíveis
        for i in range(self.text_height):
            line_num = self.scroll_offset + i
            if line_num < len(self.lines):
                line = self.lines[line_num]
                display_line = line[:self.text_width]
                
                if line_num == self.cursor_y:
                    if len(line) >= 80:
                        color = curses.color_pair(3)  # Linha atual + limite excedido
                    else:
                        color = curses.color_pair(1)  # Linha atual
                else:
                    if len(line) >= 80:
                        color = curses.color_pair(2)  # Limite excedido
                    else:
                        color = 0  # Normal
                
                try:
                    self.stdscr.addstr(i, 0, display_line.ljust(self.text_width), color)
                except curses.error:
                    pass  # Ignora erros de desenho fora da tela
        
        # Renderiza barra de status
        status = f"Arquivo: {os.path.basename(self.file_path) if self.file_path else 'Novo'} | "
        status += f"Lin: {self.cursor_y + 1}, Col: {self.cursor_x + 1} | "
        status += f"{'*' if self.has_unsaved_changes else 'Salvo'} | "
        status += "Ctrl+Q: Sair, Ctrl+S: Salvar"
        
        try:
            self.stdscr.addstr(self.height - 1, 0, status[:self.width].ljust(self.width), 
                             curses.color_pair(4) | curses.A_REVERSE)
        except curses.error:
            pass
        
        # Posiciona cursor
        screen_y = self.cursor_y - self.scroll_offset
        screen_x = min(self.cursor_x, self.text_width - 1)
        
        if 0 <= screen_y < self.text_height and 0 <= screen_x < self.text_width:
            try:
                self.stdscr.move(screen_y, screen_x)
                # Força a atualização do cursor
                curses.curs_set(0)  # Esconde temporariamente
                curses.curs_set(2)  # Mostra novamente como bloco sólido
            except curses.error:
                pass
        
        self.stdscr.refresh()
    
    def run(self):
        """Loop principal do editor"""
        while self.running:
            self.render_screen()
            
            try:
                key = self.stdscr.getch()
                
                # Ctrl+Q (ASCII 17)
                if key == 17:  # Ctrl+Q
                    if self.has_unsaved_changes:
                        # Simples confirmação
                        self.stdscr.addstr(self.height - 2, 0, "Pressione 'y' para sair sem salvar ou qualquer tecla para continuar...")
                        self.stdscr.refresh()
                        confirm = self.stdscr.getch()
                        if confirm == ord('y') or confirm == ord('Y'):
                            self.running = False
                    else:
                        self.running = False
                
                # Ctrl+S (ASCII 19)
                elif key == 19:  # Ctrl+S
                    self.save_file()
                
                elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:  # Enter
                    self.handle_enter()
                
                elif key == curses.KEY_BACKSPACE or key == ord('\b') or key == 127:  # Backspace
                    self.handle_backspace()
                
                elif key == curses.KEY_DC:  # Delete
                    self.handle_delete()
                
                elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                    self.handle_arrow_keys(key)
                
                elif 32 <= key <= 126:  # Caracteres imprimíveis ASCII
                    self.handle_printable_char(chr(key))
                
            except KeyboardInterrupt:
                self.running = False
            except curses.error:
                pass  # Ignora erros de curses
    
    def cleanup(self):
        """Limpa recursos"""
        self.running = False

def main_curses(stdscr):
    """Função principal que roda dentro do curses"""
    file_to_open = None
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1]
    
    editor = CursesTextEditor(stdscr, file_to_open)
    try:
        subprocess.run(["stty", "-ixon"], check=True)
        editor.run()
    except Exception:
        pass
    finally:
        editor.cleanup()

def main():
    """Ponto de entrada principal"""
    try:
        curses.wrapper(main_curses)
    except KeyboardInterrupt:
        print("\nEditor interrompido pelo usuário")
    except Exception as e:
        print(f"\nErro no editor: {e}")

if __name__ == "__main__":
    main()