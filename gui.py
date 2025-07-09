import pygame
import sys
from PIL import Image, ImageDraw, ImageFont
import string
from datetime import datetime

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
        self.char_width = 10  # Largura fixa dos caracteres (monospace) - diminuído
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
        
        # Configurações da fonte
        try:
            self.font = pygame.font.Font("assets/CourierPrime-Regular.ttf", self.font_size)
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
                if event.key == pygame.K_RETURN:
                    # Nova linha - retorno do carro
                    self.cursor_line += 1
                    self.cursor_col = 0
                    # Resetar dead key se houver
                    self.dead_key = None
                    
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
                
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    # Ctrl+S para salvar
                    self.save_image()
                    
                elif event.key == pygame.K_TAB:
                    # Tab move cursor para próxima posição de tabulação (múltiplo de 8)
                    next_tab = ((self.cursor_col // 8) + 1) * 8
                    if next_tab < self.max_chars_per_line:
                        self.cursor_col = next_tab
                    
                else:
                    # Inserir caractere
                    if event.unicode and event.unicode.isprintable() and event.unicode != ' ':
                        # Processar dead key
                        final_char = self.handle_dead_key(event.unicode)
                        
                        if final_char is not None:  # Só adicionar se não for um dead key pendente
                            # Verificar se não excede o limite da linha
                            if self.cursor_col < self.max_chars_per_line:
                                self.add_char_at_position(self.cursor_line, self.cursor_col, final_char)
                                self.cursor_col += 1
                            else:
                                # Ir para próxima linha automaticamente
                                self.cursor_line += 1
                                self.cursor_col = 0
                                self.add_char_at_position(self.cursor_line, self.cursor_col, final_char)
                                self.cursor_col += 1
                    
                    elif event.key == pygame.K_SPACE:
                        # Tratar espaço separadamente
                        if self.cursor_col < self.max_chars_per_line:
                            self.add_char_at_position(self.cursor_line, self.cursor_col, ' ')
                            self.cursor_col += 1
                        else:
                            # Ir para próxima linha automaticamente
                            self.cursor_line += 1
                            self.cursor_col = 0
                            self.add_char_at_position(self.cursor_line, self.cursor_col, ' ')
                            self.cursor_col += 1
                        # Resetar dead key se houver
                        self.dead_key = None
                        
        return True
    
    def draw(self):
        # Limpar tela
        self.screen.fill(self.bg_color)
        
        # Desenhar grid de referência (opcional - para debug)
        # self.draw_grid()
        
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
    
    def draw_grid(self):
        """Desenha um grid para debug (opcional)"""
        # Linhas verticais
        for col in range(self.max_chars_per_line + 1):
            x = self.left_margin + col * self.char_width
            pygame.draw.line(self.screen, (200, 200, 200), 
                           (x, self.top_margin), 
                           (x, self.height - 100), 1)
        
        # Linhas horizontais
        for line in range(20):  # Desenhar 20 linhas
            y = self.top_margin + line * self.line_height
            pygame.draw.line(self.screen, (200, 200, 200), 
                           (self.left_margin, y), 
                           (self.left_margin + self.max_chars_per_line * self.char_width, y), 1)
    
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
        max_line = max([line for line, col in self.char_matrix.keys()] + [self.cursor_line])
        img_width = self.left_margin + self.right_margin + self.max_chars_per_line * self.char_width
        img_height = self.top_margin + self.bottom_margin + (max_line + 1) * self.line_height
        
        # Criar imagem PIL
        img = Image.new('RGB', (img_width, img_height), (40, 40, 40))
        draw = ImageDraw.Draw(img)
        
        # Tentar usar uma fonte melhor para a imagem
        try:
            pil_font = ImageFont.truetype("CourierPrime-Regular.ttf", self.font_size)
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
        print(f"Imagem salva como {filename}")
    
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