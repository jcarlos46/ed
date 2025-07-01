import os
import sys
from datetime import datetime

IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    import msvcrt
else:
    import tty
    import termios

COLOR_FADED = "\033[90m"
COLOR_RESET = "\033[0m"
COLOR_CURRENT = "\033[97m"
COLOR_SUCCESS = "\033[92m"

def get_char():
    if IS_WINDOWS:
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):
            msvcrt.getwch()
            return None
        return ch
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                sys.stdin.read(2)
                return None
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def clear_screen():
    os.system('cls' if IS_WINDOWS else 'clear')

def create_filename():
    now = datetime.now()
    return now.strftime("%d-%m-%Y-%H-%M-%S.txt")

def save_to_file(lines, current, filename, mode='w'):
    """
    Salva o arquivo de forma otimizada.
    mode='w' para reescrita completa (primeira vez)
    mode='a' para append incremental (linhas adicionais)
    """
    try:
        if mode == 'a':
            # Modo incremental - apenas adiciona a nova linha
            with open(filename, 'a', encoding='utf-8') as f:
                if current.strip():
                    f.write(current + '\n')
                    f.flush()  # Força escrita imediata
        else:
            # Modo completo - reescreve tudo (usado na primeira vez e no final)
            with open(filename, 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line + '\n')
                if current.strip():
                    f.write(current + '\n')
                f.flush()
        return True
    except Exception as e:
        print(f"\nErro ao salvar: {e}")
        return False

def print_editor(lines, current):
    clear_screen()
    
    # Mostra as últimas 4 linhas
    start = max(0, len(lines) - 4)
    for line in lines[start:]:
        print(f"{COLOR_FADED}{line}{COLOR_RESET}")
    
    # Linha atual sem cursor customizado
    print(f"{COLOR_CURRENT}{current}{COLOR_RESET}", end="", flush=True)

def load_file(filename):
    """Carrega um arquivo existente e retorna as linhas"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n\r') for line in f.readlines()]
        return lines
    except FileNotFoundError:
        print(f"Arquivo '{filename}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao abrir arquivo: {e}")
        return None

def main():
    # Verifica se foi passado um argumento (nome do arquivo)
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Tenta carregar arquivo existente
        if os.path.exists(filename):
            loaded_lines = load_file(filename)
            if loaded_lines is not None:
                lines = loaded_lines
            else:
                lines = []
        else:
            # Arquivo não existe, será criado
            lines = []
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    pass
            except Exception as e:
                print(f"Erro ao criar arquivo {filename}: {e}")
                return
    else:
        # Sem argumento, cria arquivo com timestamp
        filename = create_filename()
        lines = []
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                pass
        except Exception as e:
            print(f"Erro ao criar arquivo {filename}: {e}")
            return
    
    current = ""
    exit_key = 'Ctrl+Z' if IS_WINDOWS else 'Ctrl+D'
    
    # Salva o estado inicial completo do arquivo
    if lines:
        save_to_file(lines, "", filename, mode='w')
    
    print(f"Editor sem backspace - Arquivo: {filename}")
    print(f"Pressione {exit_key} ou digite ':q' para sair")
    
    try:
        print_editor(lines, current)
        
        while True:
            ch = get_char()
            if ch is None:
                continue
            
            # Teclas de saída
            if (IS_WINDOWS and ch == '\x1a') or (not IS_WINDOWS and ch == '\x04'):
                break
            
            # Ignora backspace
            elif ch in ('\x08', '\x7f'):
                continue
            
            # Nova linha
            elif ch == '\r' or ch == '\n':
                if current.strip() == ':q':
                    break
                
                lines.append(current)
                
                # Salvamento incremental otimizado - apenas a nova linha
                save_to_file([], current, filename, mode='a')
                
                current = ""
                print_editor(lines, current)
            
            # Caracteres imprimíveis
            elif ch.isprintable():
                current += ch
                print_editor(lines, current)
    
    finally:
        # Salvamento final completo para garantir integridade
        clear_screen()
        print("Encerrando...")
        final_save = save_to_file(lines, current, filename, mode='w')
        if not final_save:
            print("Erro no salvamento final")

if __name__ == "__main__":
    main()
