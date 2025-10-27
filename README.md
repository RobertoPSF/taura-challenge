# taura-challenge

Este repositório contém a API do desafio Taura — um serviço que orquestra scanners (por exemplo, Katana e Nuclei), persiste achados e permite análise assistida por IA.

## Requisitos

- Docker & docker-compose
- Variáveis de ambiente opcionais:
  - `OPENAI_API_KEY` — chave da OpenAI, usada pelo serviço de análise (utilize .env)

## Como rodar (via Docker / Makefile) — recomendado

O projeto inclui um `Makefile` e configuração `docker-compose.yml` para facilitar execução em containers.

- Construir a imagem e subir o serviço:

  make build

Após subir, a API estará disponível em `http://localhost:5000`. A documentação Swagger com as rotas disponíveis pode ser acessada em:

- Swagger UI: http://localhost:5000/docs

## Testes

- Em Docker (via Makefile / compose):

  make test
