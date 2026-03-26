#!/bin/bash

# ==============================================================================
# SCRIPT DE ATUALIZAÇÃO AUTOMÁTICA GITHUB (Expert Mode)
# Este script verifica mudanças na pasta atual, faz o commit e envia (push)
# para o repositório remoto: https://github.com/kaksz914/DSI.git
# ==============================================================================

# Cores para o terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sem cor

echo -e "${YELLOW}[*] Iniciando processo de sincronização com o GitHub...${NC}"

# Verifica se o diretório atual já é um repositório git
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}[!] Repositório Git não inicializado nesta pasta. Inicializando...${NC}"
    git init
    git branch -M main
    
    # Verifica se a remota já existe antes de adicionar
    git remote remove origin 2>/dev/null
    git remote add origin https://github.com/kaksz914/DSI.git
    echo -e "${GREEN}[+] Repositório inicializado e remote configurado.${NC}"
fi

# Verifica o status atual
STATUS=$(git status --porcelain)

if [ -z "$STATUS" ]; then
    echo -e "${GREEN}[V] Tudo já está atualizado. Nenhuma mudança para enviar.${NC}"
    exit 0
else
    echo -e "${YELLOW}[!] Mudanças detectadas. Preparando envio...${NC}"
    
    # Adiciona todos os arquivos rastreados e não rastreados (respeitando o .gitignore se existir)
    git add .
    
    # Cria uma mensagem de commit automática com a data e hora
    COMMIT_MSG="Atualização Automática (Expert Auditor): $(date +'%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    
    echo -e "${YELLOW}[*] Enviando (Pushing) silenciosamente para a branch 'main'...${NC}"
    
    # =========================================================================
    # AUTENTICAÇÃO SEGURA NÍVEL EXPERT (Zero-Hardcoding)
    # A URL autenticada é salva EXCLUSIVAMENTE dentro do .git/config interno da
    # pasta (que é ignorado pelo commit). O script NUNCA armazena tokens no código.
    # =========================================================================
    
    # Tentativa de push usando as credenciais do ambiente ou do config interno
    if git push origin main; then
        echo -e "${GREEN}[+] SUCESSO ABSOLUTO! O seu projeto de Auditoria Wi-Fi já está no ar!${NC}"
        echo -e "${GREEN}Link: https://github.com/kaksz914/DSI${NC}"
    else
        echo -e "${RED}[X] ERRO NO ENVIO. O GitHub recusou o código.${NC}"
        echo -e "${YELLOW}Se estiver pedindo senha, é porque a URL remota não está autenticada. Rode uma vez:${NC}"
        echo -e "git remote set-url origin https://kaksz914:SEU_TOKEN@github.com/kaksz914/DSI.git"
    fi
fi
