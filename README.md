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
