#  Análise de Projetos II | VOX Note - Bot para Reuniões do Discord

Projeto desenvolvido para a disciplina **Análise de Projetos II** do 4ᵒ semestre do curso de **Análise e Desenvolvimento de Sistemas** da **CEUNSP**.  
O VOX Note é um bot para Discord que captura o áudio de reuniões, transcreve e gera atas resumidas com auxílio de inteligência artificial, facilitando o registro e a consulta de informações importantes.

---

##  Colaboradores
- **Gerente**: Raian Infante Pereira  
- **Scrum Master**: Gabriele Martins  
- **Programador 1**: Enzo Vinicius  
- **Programador 2**: Enzo Guimarães  
- **Analista de Negócios**: Alisson Ryan  
- **Documentador Técnico**: Samuel  
- **Designer**: Allan Vinícius  
- **Inspetor de Qualidade**: Nicolas Lopes  
- **Analista de Testes**: Igor Lopes  

---

##  Objetivo do Projeto
O VOX Note foi criado para eliminar a necessidade de anotações manuais durante reuniões no Discord, garantindo um registro fiel e resumido dos tópicos discutidos.  
Com ele, as equipes podem focar no conteúdo da conversa enquanto o bot cuida da documentação, gerando mais produtividade e objetividade para as reuniões.

---

##  Funcionalidades Principais
- Captura de áudio de canais de voz no Discord.
- Transcrição automática para arquivo `.txt`.
- Resumo objetivo com uso de inteligência artificial.
- Priorização de informações relevantes.
- Exportação e armazenamento de atas.

---

##  Requisitos do Sistema

### Software
- **Python** >= 3.10
- Bibliotecas:
  - `discord.py`
  - `openai` (para IA de resumo)
  - `whisper` (para transcrição de áudio)
  - Outras listadas em `requirements.txt`

### Hardware
- Processador: Dual-core ou superior.
- Memória RAM: Mínimo 4 GB.
- Espaço em disco: Mínimo 2 GB livre.

### Configuração do Discord
- Criar um bot no [Discord Developer Portal](https://discord.com/developers/applications).
- Habilitar as permissões necessárias (áudio, mensagens).
- Gerar o **Token do Bot**.

---
## Instalacão 

### Clonar o repositório
`git clone https://github.com/usuario/repositorio.git`
`cd repositorio`

### Instalar dependências
`pip install -r requirements.txt`

### Configurar variáveis de ambiente
### (Exemplo no arquivo .env.example)
`DISCORD_TOKEN=seu_token_aqui`
`OPENAI_API_KEY=sua_chave_api_aqui`
