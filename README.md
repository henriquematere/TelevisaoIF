# Painel TV IFMS

Sistema web para gerenciamento e exibição de conteúdos institucionais em TVs do IFMS.  
Permite o controle centralizado de avisos, cardápios, imagens, slideshows, horários e dispositivos, com painel administrativo intuitivo e design responsivo.

## :tv: Visão Geral

Este projeto foi desenvolvido para facilitar a comunicação visual no IFMS, exibindo informações relevantes em pontos estratégicos, como pátio, secretaria, refeitório e outras áreas.  
Tudo pode ser gerenciado de forma remota pelo painel admin.

## :rocket: Funcionalidades

- **Painel Administrativo**: cadastro, edição e exclusão de conteúdos (avisos, cardápio, imagens, etc)
- **Controle de Dispositivos**: define quais telas cada TV exibe e gerencia permissões por IP
- **Exibição em tempo real**: informações atualizadas instantaneamente nas TVs
- **Agendamento de Conteúdos**: define horários para exibir/ocultar mensagens e imagens
- **Destaque para Horário Atual**: horário sempre em destaque nas telas
- **Identidade Visual IFMS**: cores institucionais e logo em todas as telas
- **Slideshows de Imagens**: exibição sequencial de imagens em qualquer tela
- **Responsivo**: painel admin e exibição adaptados para qualquer dispositivo
- **Segurança e LGPD**: autenticação temporária e controles de exibição conforme regras de privacidade

## :gear: Tecnologias

- **Backend:** Python 3, Flask
- **Banco:** SQLite (simples e prático pra deploy rápido)
- **Frontend:** HTML5, CSS, JavaScript
- **Outros:** Jinja2, Werkzeug, gunicorn (opcional para deploy)

## :computer: Como rodar localmente

1. Clone o repositório:
   ```bash
   git clone https://github.com/henriquematere/TelevisaoIF
   cd TelevisaoIF
   ```
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/Scripts/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicie o servidor:
   ```bash
   python app.py
   ```
5. Acesse em [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)  
   O painel admin fica em `/admin`.
## :information_source: Guia Completo do Painel Administrativo

### Como colocar uma TV no ar (passo a passo):

1. **Crie um Modelo de Tela**
   - Acesse o menu **“Modelos de Tela”** (botão “Gerenciar Modelos”).
   - Clique em “Adicionar Modelo”.
   - Escolha um nome para o modelo (ex: “Secretaria”, “Pátio”, etc).
   - Defina avisos, imagens (com opção de slideshow e agendamento) e o layout desejado.
   - *Função*: Um modelo define o que será exibido em uma ou mais TVs, centralizando as configurações de conteúdo.

2. **Cadastre um Dispositivo (TV)**
   - Acesse o menu **“Dispositivos (TVs)”** (botão “Gerenciar Dispositivos”).
   - Clique em “Adicionar Dispositivo”.
   - Dê um nome para o dispositivo (ex: “TV Pátio Central”).
   - Escolha o modelo de tela que será exibido nesta TV.
   - (Opcional) Adicione uma observação de localização.
   - *Função*: O dispositivo representa cada TV física; vincular a um modelo garante que ela sempre mostre o conteúdo certo.

3. **Configure conteúdos do modelo (opcional e a qualquer momento)**
   - **Avisos Individuais**: Acesse o modelo e adicione/remova avisos que serão exibidos apenas nas TVs desse modelo.
   - **Imagens**: Faça upload de imagens para slideshow, defina períodos de exibição.
   - **Cardápio/Refeições** (para modelos tipo pátio/refeitório): Edite o cardápio do dia e/ou imagem.
   - **Intervalos**: Configure horários para exibição de intervalos, avisos sonoros, etc.
   - **Aviso Geral**: Acesse “Aviso Geral” para cadastrar um aviso que será exibido em todas as telas/TVs do campus.

4. **Gerencie usuários do painel**
   - Vá em “Usuários do Painel” > “Gerenciar Usuários”.
   - Cadastre novos administradores ou remova/edite usuários existentes.
   - *Função*: Controle quem pode acessar o painel, garantindo segurança.

5. **(Opcional) Configure a previsão do tempo**
   - Acesse o arquivo `app.py` e insira sua chave da API OpenWeatherMap.
   - O sistema exibirá automaticamente a previsão do tempo nas TVs.

6. **Pronto!**
   - Tudo que você alterar no painel administrativo é atualizado **instantaneamente** nas TVs cadastradas.

---

### Função de cada área do painel

- **Tela do Pátio**
  - Visualizar a tela de exibição como aparece na TV do pátio.
  - Configurar cardápio e avisos exclusivos do pátio.
  - Definir intervalos (ex: horário de recreio, almoço).

- **Modelos de Tela**
  - Criar, editar ou remover modelos (layouts).
  - Cada modelo pode ter suas imagens, avisos, regras e horários próprios.

- **Dispositivos (TVs)**
  - Cadastrar TVs e associar ao modelo correspondente.
  - Gerenciar ou remover dispositivos (ex: se trocar de TV ou mudar de local).

- **Usuários do Painel**
  - Gerenciar administradores e operadores do sistema.
  - Resetar senha, remover acesso, etc.

- **Aviso Geral**
  - Configurar avisos de destaque que aparecem em todas as TVs ao mesmo tempo.
  - Útil para emergências, comunicados institucionais, etc.

---

## :camera: Prints

Login: <img width="1583" height="777" alt="image" src="https://github.com/user-attachments/assets/b149b74a-7fc3-444f-9669-69e4dde1875b" />
Painel: <img width="1590" height="775" alt="image" src="https://github.com/user-attachments/assets/fd5d2166-b130-4c5d-a07e-7ebe2d8e99d0" />


## :lock: Segurança e Privacidade

- Apenas IPs autorizados conseguem acessar áreas sensíveis do sistema.
- Senhas e permissões são controladas pelo painel admin.
- Não armazena dados pessoais dos usuários das TVs (apenas admin).

## :wrench: Customização

- Para trocar as cores ou o logo, edite os arquivos estáticos em `/static/`
- Telas personalizadas podem ser criadas ou ajustadas via painel admin.

## :satellite: APIs e Integrações
- OpenWeatherMap: Para exibir o clima, é necessário configurar a chave de API no topo do app.py.

## :page_facing_up: Licença

Este projeto é open-source e pode ser utilizado ou modificado conforme necessidade do IFMS.  
Licença sugerida: MIT.
