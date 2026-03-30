import itertools
import string

def gerar_wordlist_avancada(output_file='cv_wordlist_elite.txt'):
    print('[+] Iniciando a geração da Wordlist CV Master Suprema (Kriol Raiz)...')
    
    ilhas = ['santiago', 'saovicente', 'saonicolau', 'sal', 'boavista', 'fogo', 'santoantao', 'brava', 'maio', 'cv', 'caboverde', 'caboverdiano', 'kriol']
    
    cidades = ['praia', 'mindelo', 'esparge', 'assomada', 'tarrafal', 'praiinha', 'palmarejo', 'safende', 'achada', 'fazenda', 'calheta', 'pedrabadejo', 'santamaria', 'espargos', 'salrei', 'pombas', 'ribgrande', 'portonovo']
    
    times = ['sporting', 'batuque', 'boavista', 'travadores', 'academica', 'mindelense', 'derby', 'fogo', 'amarante', 'vitoria', 'paulense']
    
    # 1. EXPANSÃO: Gírias, Expressões e Comida em Crioulo Raiz
    girias_kriol = [
        'morabeza', 'criolo', 'crioula', 'sabe', 'kriolu', 'sabura', 'festa', 'cvteledata', 'cabo',
        'funana', 'coladeira', 'morna', 'batuku', 'batuque', 'zouk', 'kizomba', 'sodade',
        'cachupa', 'catxupa', 'grogue', 'pontche', 'strela', 'txabeta', 'txuba', 'paxenxa',
        'fixe', 'manera', 'tudodretu', 'sabadu', 'domingu',
        # Novas adições raiz:
        'priguissa', 'rabola', 'xuxadera', 'cucuca', 'cuzcus', 'pastal', 'manduko',
        'fijon', 'xerem', 'canja', 'bafa', 'badiu', 'sampadjudu', 'dodu', 'doidu',
        'mininu', 'minina', 'rapaz', 'fidju', 'kuzé', 'keli', 'kelo', 'modi', 'undé',
        'dja', 'nha', 'bu', 'nho', 'nos', 'bsot', 'es', 'pamodi', 'purke', 'ma', 'si', 'nau',
        'katxorr', 'burru', 'porku', 'loku', 'dretu', 'fixi', 'kaxass', 'kopo',
        'finka', 'pe', 'mô', 'kabeça', 'odju', 'oridja', 'boka', 'denti', 'lingua'
    ]
    
    nomes = ['joao', 'maria', 'jose', 'carlos', 'antonio', 'ana', 'jorge', 'manuel', 'helena', 'nelson', 'elson', 'elza', 'amilton', 'gilson', 'edilson', 'edson', 'neusa', 'sofia', 'catia', 'nadia', 'ruben', 'kevin', 'vanderlei', 'jailson', 'jandira', 'adilson', 'ivan', 'kleyton', 'kleiton', 'vanessa', 'daniela']
    
    operadoras = ['cvmovel', 'unitel', 'tmais', 'teledata', 'starlink', 'router', 'internet', 'fibra', 'wifi']
    
    anos = [str(ano) for ano in range(1970, 2026)]
    sufixos_comuns = ['123', '1234', '12345', '123456', '12345678', '123456789', '0000', '1111', '!', '@', '#', '!!', '@@', '##', '123!', '123@']
    prefixos_comuns = ['#', '@', '!']
    
    palavras_base = ilhas + cidades + times + girias_kriol + nomes + operadoras
    
    senhas = set()
    
    # 1. Palavras puras, capitalize e UPPER
    for p in palavras_base:
        if len(p) >= 8:
            senhas.add(p)
            senhas.add(p.capitalize())
            senhas.add(p.upper())
            
    # 2. Palavras + Sufixos
    for p in palavras_base:
        for s in sufixos_comuns:
            combo1 = p + s
            combo2 = p.capitalize() + s
            if len(combo1) >= 8: senhas.add(combo1)
            if len(combo2) >= 8: senhas.add(combo2)

    # 3. Palavras + Anos (ex: catxupa2023)
    for p in palavras_base:
        for a in anos:
            combo1 = p + a
            combo2 = p.capitalize() + a
            if len(combo1) >= 8: senhas.add(combo1)
            if len(combo2) >= 8: senhas.add(combo2)
            
    # 4. Anos + Palavras (ex: 2024xuxadera)
    for p in palavras_base:
        for a in anos:
            combo1 = a + p
            combo2 = a + p.capitalize()
            if len(combo1) >= 8: senhas.add(combo1)
            if len(combo2) >= 8: senhas.add(combo2)

    # 5. Prefixos + Palavras + Sufixos (ex: @Rabola123)
    for p in palavras_base:
        for pre in prefixos_comuns:
            for suf in ['123', '1234']:
                combo = pre + p.capitalize() + suf
                if len(combo) >= 8: senhas.add(combo)

    # 6. Duas palavras combinadas (Amostragem para evitar estouro de memória)
    # Limitando a palavras de até 6 caracteres para combinações
    palavras_curtas = [w for w in palavras_base if len(w) <= 6]
    for p1 in palavras_curtas:
        for p2 in palavras_curtas:
            if p1 != p2:
                combo1 = p1 + p2
                combo2 = p1.capitalize() + p2.capitalize()
                if len(combo1) >= 8: senhas.add(combo1)
                if len(combo2) >= 8: senhas.add(combo2)
                
    # 7. Números de telefone e padrões numéricos comuns
    senhas.update([
        '12345678', '123456789', '1234567890', '01234567', '00000000', '11111111', '87654321',
        'qawsedrf', 'asdfghjkl', 'zxcvbnm', 'qwertyuiop'
    ])
    
    # 8. L33t Speak básico para palavras da cultura (ex: c@txup@, xux@d3r@)
    leet_map = {'a': '@', 'e': '3', 'i': '1', 'o': '0'}
    leet_targets = ['cvmovel', 'unitel', 'starlink', 'santiago', 'mindelo', 'caboverde', 'morabeza', 'catxupa', 'xuxadera', 'priguissa', 'rabola']
    
    for p in leet_targets:
        leet_word = p
        for k, v in leet_map.items():
            leet_word = leet_word.replace(k, v)
        if len(leet_word) >= 8:
            senhas.add(leet_word)
            senhas.add(leet_word.capitalize())
            senhas.add(leet_word + '123')
            senhas.add(leet_word + '!')

    # Escreve o arquivo final
    with open(output_file, 'w', encoding='utf-8') as f:
        for s in sorted(senhas):
            f.write(s + '\n')
            
    print(f'[+] Wordlist Kriol gerada com {len(senhas)} combinações únicas (Nível Root). Salvo em {output_file}')

if __name__ == '__main__':
    gerar_wordlist_avancada()
