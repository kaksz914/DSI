import itertools
import string

def gerar_wordlist_avancada(output_file='cv_wordlist_elite.txt'):
    print('[+] Iniciando a geração da Wordlist CV Master Absoluta (Kriol + PT + Extreme Vars)...')
    
    ilhas = ['santiago', 'saovicente', 'saonicolau', 'sal', 'boavista', 'fogo', 'santoantao', 'brava', 'maio', 'cv', 'caboverde', 'caboverdiano', 'kriol']
    
    cidades = ['praia', 'mindelo', 'esparge', 'assomada', 'tarrafal', 'praiinha', 'palmarejo', 'safende', 'achada', 'fazenda', 'calheta', 'pedrabadejo', 'santamaria', 'espargos', 'salrei', 'pombas', 'ribgrande', 'portonovo']
    
    times = ['sporting', 'batuque', 'boavista', 'travadores', 'academica', 'mindelense', 'derby', 'fogo', 'amarante', 'vitoria', 'paulense', 'benfica', 'porto']
    
    # 1. Gírias e cultura crioula
    girias_kriol = [
        'morabeza', 'criolo', 'crioula', 'sabe', 'kriolu', 'sabura', 'festa', 'cvteledata', 'cabo',
        'funana', 'coladeira', 'morna', 'batuku', 'batuque', 'zouk', 'kizomba', 'sodade',
        'cachupa', 'catxupa', 'grogue', 'pontche', 'strela', 'txabeta', 'txuba', 'paxenxa',
        'fixe', 'manera', 'tudodretu', 'sabadu', 'domingu',
        'priguissa', 'rabola', 'cucuca', 'cuzcus', 'pastal', 'manduko',
        'fijon', 'xerem', 'canja', 'bafa', 'badiu', 'sampadjudu', 'dodu', 'doidu',
        'mininu', 'minina', 'rapaz', 'fidju', 'kuzé', 'keli', 'kelo', 'modi', 'undé',
        'dja', 'nha', 'bu', 'nho', 'nos', 'bsot', 'es', 'pamodi', 'purke', 'ma', 'si', 'nau',
        'katxorr', 'burru', 'porku', 'loku', 'dretu', 'fixi', 'kaxass', 'kopo',
        'finka', 'pe', 'mô', 'kabeça', 'odju', 'oridja', 'boka', 'denti', 'lingua'
    ]

    # 2. Léxico extremo (Palavrões CV + Variações)
    palavros_kriol = [
        'xuxadera', 'catota', 'cotota', 'catoti', 'pica', 'pika', 'fanadu', 'crica', 'krika', 
        'conona', 'konona', 'tabanka', 'badia', 'xatiada', 'xatiadu', 'puta', 'kabra',
        'kuzinha', 'fudidu', 'fudida', 'fdp', 'kuzão', 'merda', 'caralho', 'karalhu',
        'bosta', 'bostinha', 'cagad', 'kagadu', 'cu', 'ku', 'rabo', 'rabu', 'bunda',
        'mama', 'teta', 'mamae', 'papa', 'papai', 'nhafika', 'matxomba', 'panhon', 
        'kanbada', 'ladrão', 'ladron', 'gatu', 'gatuno', 'bandido', 'bandidu',
        'cabrão', 'kabron', 'corno', 'kornu', 'forsa', 'konta', 'dinheru', 'kumbu'
    ]
    
    # 3. NOVAS ADIÇÕES: Palavras do Português usadas identicamente em Cabo Verde
    pt_cv_comum = [
        'amor', 'vida', 'deus', 'jesus', 'familia', 'paz', 'alegria', 'tristeza', 'feliz', 'triste',
        'escola', 'casa', 'trabalho', 'dinheiro', 'carro', 'moto', 'viagem', 'ferias',
        'amigo', 'amiga', 'irmao', 'irma', 'mae', 'pai', 'filho', 'filha', 'tio', 'tia', 'avo',
        'praia', 'sol', 'mar', 'areia', 'vento', 'noite', 'dia', 'tarde', 'madrugada',
        'verde', 'amarelo', 'vermelho', 'azul', 'branco', 'preto', 'estrela', 'luz',
        'futebol', 'bola', 'jogo', 'vitoria', 'campeao', 'golo',
        'musica', 'danca', 'cantar', 'tocar', 'festa', 'bebida', 'comida', 'doce', 'salgado',
        'segredo', 'senha', 'password', 'acesso', 'admin', 'guest', 'convidado', 'privado'
    ]
    
    nomes = ['joao', 'maria', 'jose', 'carlos', 'antonio', 'ana', 'jorge', 'manuel', 'helena', 'nelson', 'elson', 'elza', 'amilton', 'gilson', 'edilson', 'edson', 'neusa', 'sofia', 'catia', 'nadia', 'ruben', 'kevin', 'vanderlei', 'jailson', 'jandira', 'adilson', 'ivan', 'kleyton', 'kleiton', 'vanessa', 'daniela', 'paulo', 'pedro', 'luis', 'rui', 'fernando', 'fatima', 'isabel', 'rosa', 'marta', 'silvia']
    
    operadoras = ['cvmovel', 'unitel', 'tmais', 'teledata', 'starlink', 'router', 'internet', 'fibra', 'wifi', 'nos', 'meo', 'vodafone']
    
    anos = [str(ano) for ano in range(1970, 2028)]
    anos_curtos = [str(ano)[2:] for ano in range(1970, 2028)] # Ex: 99, 00, 23, 24, 25
    
    sufixos_simples = ['123', '1234', '12345', '123456', '12345678', '123456789', '0000', '1111', '!', '@', '#', '!!', '@@', '##', '123!', '123@', '69', '666']
    prefixos_comuns = ['#', '@', '!', '*']
    
    # 4. NOVAS ADIÇÕES: Sufixos Complexos baseados em datas (o pedido explícito do usuário)
    sufixos_complexos = []
    for ano in range(2020, 2028):
        sufixos_complexos.append(f'@{ano}')
        sufixos_complexos.append(f'!{ano}')
        sufixos_complexos.append(f'#{ano}')
        sufixos_complexos.append(f'_{ano}')
        sufixos_complexos.append(f'@{str(ano)[2:]}') # Ex: @24
        sufixos_complexos.append(f'!{str(ano)[2:]}')
        
    sufixos_totais = sufixos_simples + sufixos_complexos
    
    # Combinar tudo na base principal
    palavras_base = ilhas + cidades + times + girias_kriol + palavros_kriol + pt_cv_comum + nomes + operadoras
    
    senhas = set()
    
    # Função auxiliar para adicionar se for >= 8 chars (WPA/WPA2 requirement)
    def add_if_valid(pw):
        if len(pw) >= 8:
            senhas.add(pw)
    
    # 1. Palavras puras, capitalize e UPPER
    for p in palavras_base:
        add_if_valid(p)
        add_if_valid(p.capitalize())
        add_if_valid(p.upper())
            
    # 2. Palavras + Sufixos Totais (ex: catoti@2025, Catoti@2025, etc)
    for p in palavras_base:
        for s in sufixos_totais:
            add_if_valid(p + s)
            add_if_valid(p.capitalize() + s)
            add_if_valid(p.upper() + s)

    # 3. Palavras + Anos Simples (ex: xuxadera2023)
    for p in palavras_base:
        for a in anos:
            add_if_valid(p + a)
            add_if_valid(p.capitalize() + a)
            
    # 4. Anos + Palavras (ex: 2024catota)
    for p in palavras_base:
        for a in anos:
            add_if_valid(a + p)
            add_if_valid(a + p.capitalize())

    # 5. Prefixos + Palavras + Sufixos Básicos (ex: @Krika123)
    for p in palavras_base:
        for pre in prefixos_comuns:
            for suf in ['123', '1234', '69', '!', '@']:
                add_if_valid(pre + p.capitalize() + suf)
                add_if_valid(pre + p + suf)

    # 6. Duas palavras combinadas (Apenas palavras curtas para evitar explosão de RAM e ficheiro gigante)
    # Ex: amorvida, deuscriolo
    palavras_curtas = [w for w in palavras_base if 3 <= len(w) <= 5]
    # Limitar a combinatória para não travar (pegar as top 100 palavras curtas)
    import random
    palavras_curtas = list(set(palavras_curtas))[:100] 
    
    for p1 in palavras_curtas:
        for p2 in palavras_curtas:
            if p1 != p2:
                add_if_valid(p1 + p2)
                add_if_valid(p1.capitalize() + p2.capitalize())
                add_if_valid(p1 + p2 + '123')
                
    # 7. Padrões Numéricos Puros e Teclado
    senhas.update([
        '12345678', '123456789', '1234567890', '01234567', '00000000', '11111111', '87654321',
        'qawsedrf', 'asdfghjkl', 'zxcvbnm', 'qwertyuiop', '69696969', '12341234', '123123123',
        '12345678a', '12345678A', '12345678@'
    ])
    
    # 8. L33t Speak básico para TODOS os termos base (versão light para não explodir)
    leet_map = {'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '5'}
    
    # Vamos focar leet speak apenas em palavras maiores que 5 letras para ter impacto
    leet_targets = [w for w in palavras_base if len(w) >= 5]
    
    for p in leet_targets:
        leet_word = p
        for k, v in leet_map.items():
            leet_word = leet_word.replace(k, v)
            
        if leet_word != p: # Só adiciona se houve mutação
            add_if_valid(leet_word)
            add_if_valid(leet_word.capitalize())
            add_if_valid(leet_word + '123')
            add_if_valid(leet_word + '!')
            # Leet + ano atual
            for a in ['2023', '2024', '2025']:
                add_if_valid(leet_word + a)
                add_if_valid(leet_word.capitalize() + '@' + a)

    # Tratamento especial explícito solicitado: catoti@2025, Catoti@2025 etc
    # Isso já foi coberto nos passos 2 e 3 de forma dinâmica para TODAS as palavras,
    # mas garantindo que as exatas mencionadas não falhem:
    add_if_valid("catoti@2024")
    add_if_valid("Catoti@2024")
    add_if_valid("catoti@2025")
    add_if_valid("Catoti@2025")

    # Escreve o arquivo final
    with open(output_file, 'w', encoding='utf-8') as f:
        for s in sorted(senhas):
            f.write(s + '\n')
            
    print(f'[+] Wordlist SUPREMA gerada com {len(senhas)} combinações únicas (PT + Kriol + Datas). Salvo em {output_file}')

if __name__ == '__main__':
    gerar_wordlist_avancada()
