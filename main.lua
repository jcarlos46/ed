os.execute("stty -icanon -echo")

local linhas = {}
local linha_atual = ""

local function desenha_tela()
    os.execute("clear")

    -- Calcula a janela de 4 linhas anteriores
    local start = math.max(1, #linhas - 3)
    for i = start, #linhas do
        io.write("\27[90m")       -- cor cinza escura
        print(linhas[i])
    end

    io.write("\27[0m")           -- volta à cor normal
    io.write(linha_atual)
    io.flush()
end

print("Editor de Texto Simples (Ctrl+D para sair)")
desenha_tela()

while true do
    local ch = io.read(1)
    if not ch or ch == "\4" then
        break
    elseif ch == "\n" then
        table.insert(linhas, linha_atual)
        linha_atual = ""
        desenha_tela()
    elseif ch == "\127" or ch == "\8" then
        -- ignora backspace/delete
    elseif ch == "\27" then
        io.read(2) -- ignora sequências de seta
    else
        linha_atual = linha_atual .. ch
        desenha_tela()
    end
end

os.execute("stty sane")

print("\nTexto Final:")
for _, l in ipairs(linhas) do
    print(l)
end
