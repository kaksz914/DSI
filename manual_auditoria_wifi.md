# Manual de Auditoria Wi-Fi Automatizada (Guia Expert)

Este guia documenta o funcionamento da ferramenta `wifi_auditor.py` e os conceitos técnicos por trás do processo de auditoria de redes WPA/WPA2.

> **Aviso Legal:** Esta documentação e a ferramenta associada destinam-se estritamente ao uso em ambientes de teste autorizados. O usuário confirmou possuir todas as autorizações necessárias para executar estes testes em suas redes (ex: Starlink_S4).

---

## 1. Pré-requisitos
A ferramenta foi projetada para rodar em ambientes Linux (Kali Linux, Parrot OS, Ubuntu, etc).

*   **Adaptador Wi-Fi com suporte a Modo Monitor:** Nem todas as placas de rede conseguem "escutar" o tráfego do ar. Você precisa de um chipset compatível (ex: Atheros AR9271, Ralink RT5370, Realtek RTL8812AU).
*   **Aircrack-ng Suite:** O script automatiza as ferramentas deste pacote. Se não estiver instalado, o script tentará instalá-lo automaticamente via `apt`.
*   **Permissões de Root:** Você deve executar o script usando `sudo` para ter controle sobre a placa de rede.

## 2. Visão Geral do Processo (O que a ferramenta faz)

O processo de descobrir a senha de uma rede WPA2 sem estar conectado a ela envolve explorar como os dispositivos se autenticam. O ataque principal chama-se **Captura de Handshake (Ataque de Dicionário)**.

### Passo 1: Preparação do Ambiente
Para escutar o que outras redes e dispositivos estão conversando, sua placa de rede não pode estar conectada a uma rede específica (Modo Gerenciado). A ferramenta:
1. Desliga serviços que atrapalham (`NetworkManager`, `wpa_supplicant`).
2. Ativa o **Modo Monitor** na interface (geralmente criando a `wlan0mon`).

### Passo 2: Reconhecimento (Discovery)
A ferramenta usa o `airodump-ng` por debaixo dos panos para escutar os *Beacons* (anúncios) dos roteadores.
*   Ela lista todas as redes ao redor (BSSID/MAC, ESSID/Nome, Canal, Criptografia).
*   **Novo Recurso:** A ferramenta agora salva permanentemente os dados de *todas* as redes encontradas em um arquivo `redes_identificadas_log.json` para análise futura.

### Passo 3: O Handshake WPA/WPA2
Quando um celular ou laptop se conecta ao Wi-Fi, ele troca 4 mensagens com o roteador para provar que sabe a senha (Handshake de 4 vias).
*   A ferramenta "trava" (lock) a escuta no canal específico do roteador alvo.
*   Ela usa o `aireplay-ng` para enviar pacotes forjados de desautenticação (**Deauth Attack**) fingindo ser o roteador e expulsando os clientes conectados.
*   Desesperados, os clientes tentam se reconectar automaticamente. É nesse momento que o script captura o Handshake que voa pelo ar.

*Mecanismo Expert (Retry Automático):* Se a captura falhar (o cliente não desconectar ou estiver longe), a ferramenta intensifica o ataque e tenta novamente de forma autônoma antes de desistir.

### Passo 4: Quebra da Senha (Cracking Offline)
O Handshake capturado contém uma prova matemática da senha, mas não a senha em texto claro.
*   A ferramenta utiliza o `aircrack-ng` e pede que você forneça um arquivo de texto (**Dicionário ou Wordlist**) contendo milhões de senhas prováveis (ex: `rockyou.txt`).
*   O aircrack-ng vai testar cada senha do arquivo contra o Handshake. Se a senha matemática bater, ele te revela a senha em texto claro.
*   Se a senha real não estiver no seu dicionário, o ataque falha.

### Passo 5: Restauração do Sistema
Independente de sucesso ou erro grave, a ferramenta devolve a interface para o modo normal e religa sua internet via `NetworkManager`.

---

## 3. Como Executar

Abra o terminal na pasta do arquivo e rode:
```bash
sudo python3 wifi_auditor.py
```
Siga os menus interativos apresentados na tela.

---

## 4. Solução de Problemas Comuns

*   **Não encontrou interfaces Wi-Fi:** Seu adaptador não foi reconhecido pelo Linux ou você o conectou numa máquina virtual sem fazer o repasse USB adequado.
*   **Erro ao colocar em Modo Monitor:** Algumas placas de rede não suportam esse modo nativamente, exigindo a instalação de drivers customizados no Linux.
*   **Não captura o Handshake:**
    *   Ninguém está usando o Wi-Fi alvo (não há clientes para desconectar).
    *   Você está muito longe do alvo (o sinal de deauth não chega com força suficiente).
*   **Handshake capturado, mas senha não encontrada:** A senha do roteador alvo não estava dentro do seu arquivo de dicionário (`.txt`). Procure wordlists maiores.
