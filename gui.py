import pygame
import sys
from PIL import Image, ImageDraw, ImageFont
import string
from datetime import datetime
import json
import os
from tkinter import filedialog, messagebox
import tkinter as tk

class TypewriterSimulator:
    def __init__(self):
        pygame.init()
        
        # Configurações da janela
        self.width = 900
        self.height = 700
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Simulador de Máquina de Escrever")
        
        # Cores
        self.bg_color = (40, 40, 40)     # Fundo escuro
        self.text_color = (240, 235, 220)  # Texto claro
        self.cursor_color = (255, 0, 0)  # Cor do cursor
        
        # Configurações do texto
        self.font_size = 18
        self.char_width = 10  # Largura fixa dos caracteres (monospace)
        self.line_height = 24
        self.left_margin = 80
        self.top_margin = 80
        self.right_margin = 80
        self.bottom_margin = 80
        self.max_chars_per_line = 80
        
        # Estado do cursor
        self.cursor_line = 0
        self.cursor_col = 0
        
        # Matriz de caracteres - cada posição pode ter múltiplos caracteres sobrepostos
        self.char_matrix = {}  # {(linha, coluna): [lista_de_caracteres]}
        
        # Estado para caracteres compostos (dead keys)
        self.dead_key = None  # Armazena o caractere morto atual
        
        # Estado do arquivo atual
        self.current_file = None
        self.is_modified = False
        
        # Configurações da fonte
        try:
            self.font = pygame.font.Font("assets/Pica.ttf", self.font_size)
        except:
            try:
                self.font = pygame.font.SysFont("Courier Prime", self.font_size)
            except:
                try:
                    self.font = pygame.font.SysFont("Courier New", self.font_size)
                except:
                    self.font = pygame.font.Font(None, self.font_size)
        
        # Gerar sprites de caracteres
        self.char_sprites = self.generate_char_sprites()
        
        # Para o cursor piscante
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Clock para controle de FPS
        self.clock = pygame.time.Clock()
        
        # Inicializar Tkinter para diálogos de arquivo (oculto)
        self.root = tk.Tk()
        self.root.withdraw()  # Ocultar janela principal do Tkinter
        
    def generate_char_sprites(self):
        """Gera sprites para todos os caracteres"""
        sprites = {}
        
        # Caracteres básicos para gerar sprites
        chars = string.ascii_letters + string.digits + string.punctuation + " "
        
        # Adicionar caracteres especiais comuns
        special_chars = "áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"
        chars += special_chars
        
        for char in chars:
            try:
                # Criar surface para o caractere
                char_surface = pygame.Surface((self.char_width, self.line_height), pygame.SRCALPHA)
                
                # Renderizar caractere
                if char != ' ':  # Não renderizar espaço
                    text_surface = self.font.render(char, True, self.text_color)
                    # Centralizar o caractere no sprite
                    x = (self.char_width - text_surface.get_width()) // 2
                    y = (self.line_height - text_surface.get_height()) // 2
                    char_surface.blit(text_surface, (x, y))
                
                sprites[char] = char_surface
            except:
                # Se falhar ao renderizar o caractere, criar sprite vazio
                sprites[char] = pygame.Surface((self.char_width, self.line_height), pygame.SRCALPHA)
            
        return sprites
    
    def get_char_at_position(self, line, col):
        """Retorna a lista de caracteres na posição especificada"""
        return self.char_matrix.get((line, col), [])
    
    def add_char_at_position(self, line, col, char):
        """Adiciona um caractere na posição especificada (sobrepondo)"""
        if (line, col) not in self.char_matrix:
            self.char_matrix[(line, col)] = []
        self.char_matrix[(line, col)].append(char)
        self.is_modified = True
    
    def clear_document(self):
        """Limpa o documento atual"""
        self.char_matrix = {}
        self.cursor_line = 0
        self.cursor_col = 0
        self.current_file = None
        self.is_modified = False
        self.dead_key = None
    
    def populate_from_text(self, text):
        """Popula a máquina com texto, simulando digitação"""
        self.clear_document()
        
        line = 0
        col = 0
        
        for char in text:
            if char == '\n':
                line += 1
                col = 0
            elif char == '\t':
                # Tab para próxima posição de tabulação
                next_tab = ((col // 8) + 1) * 8
                if next_tab < self.max_chars_per_line:
                    col = next_tab
                else:
                    line += 1
                    col = 0
            else:
                if col >= self.max_chars_per_line:
                    line += 1
                    col = 0
                
                if char.isprintable():
                    self.add_char_at_position(line, col, char)
                    col += 1
        
        self.cursor_line = line
        self.cursor_col = col
        self.is_modified = False  # Arquivo carregado não conta como modificado
    
    def load_text_file(self):
        """Carrega um arquivo de texto"""
        try:
            file_path = filedialog.askopenfilename(
                title="Abrir arquivo de texto",
                filetypes=[
                    ("Arquivos de texto", "*.txt"),
                    ("Todos os arquivos", "*.*")
                ]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.populate_from_text(content)
                    self.current_file = file_path
                    filename = os.path.basename(file_path)
                    pygame.display.set_caption(f"Simulador de Máquina de Escrever - {filename}")
        except Exception as e:
            print(f"Erro ao carregar arquivo: {str(e)}")
    
    def save_state_file(self):
        """Salva o estado atual do simulador"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Salvar estado do simulador",
                defaultextension=".typewriter",
                filetypes=[
                    ("Arquivos do Simulador", "*.typewriter"),
                    ("Todos os arquivos", "*.*")
                ]
            )
            
            if file_path:
                state = {
                    'char_matrix': {f"{k[0]},{k[1]}": v for k, v in self.char_matrix.items()},
                    'cursor_line': self.cursor_line,
                    'cursor_col': self.cursor_col,
                    'max_chars_per_line': self.max_chars_per_line
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
                
                self.current_file = file_path
                self.is_modified = False
                filename = os.path.basename(file_path)
                pygame.display.set_caption(f"Simulador de Máquina de Escrever - {filename}")
        except Exception as e:
            print(f"Erro ao salvar: {str(e)}")
    
    def load_state_file(self):
        """Carrega um estado salvo do simulador"""
        try:
            file_path = filedialog.askopenfilename(
                title="Abrir estado do simulador",
                filetypes=[
                    ("Arquivos do Simulador", "*.typewriter"),
                    ("Todos os arquivos", "*.*")
                ]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # Restaurar matriz de caracteres
                self.char_matrix = {}
                for pos_str, chars in state['char_matrix'].items():
                    line, col = map(int, pos_str.split(','))
                    self.char_matrix[(line, col)] = chars
                
                # Restaurar cursor
                self.cursor_line = state['cursor_line']
                self.cursor_col = state['cursor_col']
                
                # Restaurar configurações se existirem
                if 'max_chars_per_line' in state:
                    self.max_chars_per_line = state['max_chars_per_line']
                
                self.current_file = file_path
                self.is_modified = False
                filename = os.path.basename(file_path)
                pygame.display.set_caption(f"Simulador de Máquina de Escrever - {filename}")
        except Exception as e:
            print(f"Erro ao carregar estado: {str(e)}")
    
    def export_to_text(self):
        """Exporta o conteúdo atual para um arquivo de texto"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Exportar para texto",
                defaultextension=".txt",
                filetypes=[
                    ("Arquivos de texto", "*.txt"),
                    ("Todos os arquivos", "*.*")
                ]
            )
            
            if file_path:
                # Encontrar dimensões do documento
                if not self.char_matrix:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("")
                    return
                
                max_line = max(pos[0] for pos in self.char_matrix.keys())
                
                lines = []
                for line_num in range(max_line + 1):
                    line_chars = []
                    max_col = -1
                    
                    # Encontrar última coluna com conteúdo nesta linha
                    for pos in self.char_matrix.keys():
                        if pos[0] == line_num:
                            max_col = max(max_col, pos[1])
                    
                    # Construir linha
                    if max_col >= 0:
                        for col in range(max_col + 1):
                            chars = self.char_matrix.get((line_num, col), [])
                            if chars:
                                # Usar o último caractere se houver sobreposição
                                line_chars.append(chars[-1])
                            else:
                                line_chars.append(' ')
                    
                    lines.append(''.join(line_chars).rstrip())
                
                # Remover linhas vazias do final
                while lines and not lines[-1]:
                    lines.pop()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                filename = os.path.basename(file_path)
        except Exception as e:
            print(f"Erro ao exportar: {str(e)}")
    
    def handle_dead_key(self, char):
        """Trata caracteres compostos (dead keys)"""
        if self.dead_key is None:
            # Primeiro caractere - verificar se é um dead key
            if char == '~':
                self.dead_key = '~'
                return None  # Não adicionar ainda
            else:
                return char  # Caractere normal
        else:
            # Segundo caractere - combinar com dead key
            if self.dead_key == '~':
                combinations = {
                    'a': 'ã',
                    'o': 'õ',
                    'n': 'ñ',
                    'A': 'Ã',
                    'O': 'Õ',
                    'N': 'Ñ'
                }
                result = combinations.get(char, char)  # Se não encontrar combinação, usar o caractere normal
                self.dead_key = None  # Resetar dead key
                return result
            else:
                # Dead key não reconhecido, resetar
                self.dead_key = None
                return char
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.VIDEORESIZE:
                # Redimensionar janela
                self.width = event.w
                self.height = event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                
                if event.key == pygame.K_RETURN:
                    # Nova linha - retorno do carro
                    self.cursor_line += 1
                    self.cursor_col = 0
                    # Resetar dead key se houver
                    self.dead_key = None
                    self.is_modified = True
                    
                elif event.key == pygame.K_BACKSPACE:
                    # Backspace apenas move o cursor para trás (não destrutivo)
                    if self.cursor_col > 0:
                        self.cursor_col -= 1
                    elif self.cursor_line > 0:
                        self.cursor_line -= 1
                        self.cursor_col = self.max_chars_per_line - 1
                    # Resetar dead key se houver
                    self.dead_key = None
                        
                elif event.key == pygame.K_LEFT:
                    # Mover cursor para esquerda
                    if self.cursor_col > 0:
                        self.cursor_col -= 1
                    elif self.cursor_line > 0:
                        self.cursor_line -= 1
                        self.cursor_col = self.max_chars_per_line - 1
                        
                elif event.key == pygame.K_RIGHT:
                    # Mover cursor para direita
                    if self.cursor_col < self.max_chars_per_line - 1:
                        self.cursor_col += 1
                    else:
                        self.cursor_line += 1
                        self.cursor_col = 0
                        
                elif event.key == pygame.K_UP:
                    # Mover cursor para linha acima
                    if self.cursor_line > 0:
                        self.cursor_line -= 1
                        
                elif event.key == pygame.K_DOWN:
                    # Mover cursor para linha abaixo
                    self.cursor_line += 1
                
                # Atalhos de teclado
                elif event.key == pygame.K_n and keys[pygame.K_LCTRL]:
                    # Ctrl+N - Novo documento
                    self.clear_document()
                    pygame.display.set_caption("Simulador de Máquina de Escrever")
                    
                elif event.key == pygame.K_o and keys[pygame.K_LCTRL]:
                    # Ctrl+O - Abrir arquivo
                    if keys[pygame.K_LSHIFT]:
                        # Ctrl+Shift+O - Abrir estado do simulador
                        self.load_state_file()
                    else:
                        # Ctrl+O - Abrir arquivo de texto
                        self.load_text_file()
                    
                elif event.key == pygame.K_s and keys[pygame.K_LCTRL]:
                    # Ctrl+S - Salvar
                    if keys[pygame.K_LSHIFT]:
                        # Ctrl+Shift+S - Salvar estado
                        self.save_state_file()
                    elif keys[pygame.K_LALT]:
                        # Ctrl+Alt+S - Exportar para texto
                        self.export_to_text()
                    else:
                        # Ctrl+S - Salvar como imagem
                        self.save_image()
                    
                elif event.key == pygame.K_TAB:
                    # Tab move cursor para próxima posição de tabulação (múltiplo de 8)
                    next_tab = ((self.cursor_col // 8) + 1) * 8
                    if next_tab < self.max_chars_per_line:
                        self.cursor_col = next_tab
                    self.is_modified = True
                    
                elif event.key == pygame.K_F1:
                    # F1 - Mostrar ajuda
                    self.show_help()
                    
                else:
                    # Inserir caractere
                    if event.unicode and event.unicode.isprintable() and event.unicode != ' ':
                        # Processar dead key
                        final_char = self.handle_dead_key(event.unicode)
                        
                        if final_char is not None:  # Só adicionar se não for um dead key pendente
                            # Verificar se não excede o limite da linha - PARAR no final
                            if self.cursor_col < self.max_chars_per_line:
                                self.add_char_at_position(self.cursor_line, self.cursor_col, final_char)
                                self.cursor_col += 1
                            # Se chegou no limite, simplesmente não adiciona o caractere
                            # e não move o cursor (simula travamento da máquina)
                    
                    elif event.key == pygame.K_SPACE:
                        # Tratar espaço separadamente
                        if self.cursor_col < self.max_chars_per_line:
                            self.add_char_at_position(self.cursor_line, self.cursor_col, ' ')
                            self.cursor_col += 1
                        # Se chegou no limite, simplesmente não adiciona o espaço
                        # e não move o cursor
                        
                        # Resetar dead key se houver
                        self.dead_key = None
                        
        return True
    
    def show_help(self):
        """Mostra os atalhos de teclado disponíveis"""
        help_text = """Atalhos:
Ctrl+N: Novo documento
Ctrl+O: Abrir arquivo de texto
Ctrl+Shift+O: Abrir estado do simulador
Ctrl+S: Salvar como imagem
Ctrl+Shift+S: Salvar estado
Ctrl+Alt+S: Exportar para texto
F1: Mostrar ajuda"""
        
        print(help_text)
    
    def draw(self):
        # Limpar tela
        self.screen.fill(self.bg_color)
        
        # Desenhar margens da "folha"
        self.draw_page_margins()
        
        # Desenhar todos os caracteres
        for (line, col), chars in self.char_matrix.items():
            x = self.left_margin + col * self.char_width
            y = self.top_margin + line * self.line_height
            
            # Desenhar todos os caracteres sobrepostos na posição
            for char in chars:
                if char in self.char_sprites:
                    self.screen.blit(self.char_sprites[char], (x, y))
                else:
                    # Para caracteres não pré-gerados, renderizar diretamente
                    try:
                        if char != ' ':
                            text_surface = self.font.render(char, True, self.text_color)
                            char_x = x + (self.char_width - text_surface.get_width()) // 2
                            char_y = y + (self.line_height - text_surface.get_height()) // 2
                            self.screen.blit(text_surface, (char_x, char_y))
                    except:
                        pass  # Ignorar caracteres que não podem ser renderizados
        
        # Desenhar cursor
        if self.cursor_visible:
            cursor_x = self.left_margin + self.cursor_col * self.char_width
            cursor_y = self.top_margin + self.cursor_line * self.line_height
            pygame.draw.line(self.screen, self.cursor_color, 
                           (cursor_x, cursor_y), 
                           (cursor_x, cursor_y + self.line_height), 2)
        
        pygame.display.flip()
    
    def draw_page_margins(self):
        """Desenha as margens da folha para mostrar os limites"""
        # Calcular dimensões da área de texto
        text_width = self.max_chars_per_line * self.char_width
        text_height = 25 * self.line_height  # Altura para 25 linhas
        
        # Desenhar retângulo das margens
        margin_color = (80, 80, 80)  # Cor das margens
        
        # Margem esquerda
        pygame.draw.line(self.screen, margin_color, 
                        (self.left_margin, self.top_margin), 
                        (self.left_margin, self.top_margin + text_height), 1)
        
        # Margem direita
        pygame.draw.line(self.screen, margin_color, 
                        (self.left_margin + text_width, self.top_margin), 
                        (self.left_margin + text_width, self.top_margin + text_height), 1)
        
        # Margem superior
        pygame.draw.line(self.screen, margin_color, 
                        (self.left_margin, self.top_margin), 
                        (self.left_margin + text_width, self.top_margin), 1)
        
        # Margem inferior
        pygame.draw.line(self.screen, margin_color, 
                        (self.left_margin, self.top_margin + text_height), 
                        (self.left_margin + text_width, self.top_margin + text_height), 1)
    
    def update_cursor(self):
        # Fazer cursor piscar
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # Piscar a cada 30 frames
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def save_image(self):
        # Gerar nome do arquivo com data e hora
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"typewriter_output_{timestamp}.png"
        
        # Calcular dimensões necessárias
        max_line = max([line for line, col in self.char_matrix.keys()] + [self.cursor_line]) if self.char_matrix else 0
        img_width = self.left_margin + self.right_margin + self.max_chars_per_line * self.char_width
        img_height = self.top_margin + self.bottom_margin + (max_line + 1) * self.line_height
        
        # Criar imagem PIL
        img = Image.new('RGB', (img_width, img_height), (40, 40, 40))
        draw = ImageDraw.Draw(img)
        
        # Tentar usar uma fonte melhor para a imagem
        try:
            pil_font = ImageFont.truetype("Pica.ttf", self.font_size)
        except:
            try:
                pil_font = ImageFont.truetype("cour.ttf", self.font_size)  # Courier New no Windows
            except:
                try:
                    pil_font = ImageFont.truetype("Courier New.ttf", self.font_size)
                except:
                    pil_font = ImageFont.load_default()
        
        # Desenhar todos os caracteres na imagem
        for (line, col), chars in self.char_matrix.items():
            x = self.left_margin + col * self.char_width
            y = self.top_margin + line * self.line_height
            
            # Desenhar todos os caracteres sobrepostos
            for char in chars:
                if char != ' ':  # Não desenhar espaços
                    try:
                        draw.text((x, y), char, fill=(240, 235, 220), font=pil_font)
                    except:
                        # Se falhar, tentar com fonte padrão
                        try:
                            draw.text((x, y), char, fill=(240, 235, 220))
                        except:
                            pass  # Ignorar caracteres que não podem ser desenhados
        
        # Salvar imagem
        img.save(filename)
        print(f"Imagem salva: {filename}")
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update_cursor()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    simulator = TypewriterSimulator()
    simulator.run()