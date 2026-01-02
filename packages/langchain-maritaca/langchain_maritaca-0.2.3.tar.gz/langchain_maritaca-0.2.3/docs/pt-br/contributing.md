# Contribuindo

Obrigado pelo interesse em contribuir com o langchain-maritaca!

## Configuração do Ambiente

### 1. Clone o repositório

```bash
git clone https://github.com/anderson-ufrj/langchain-maritaca.git
cd langchain-maritaca
```

### 2. Instale as dependências de desenvolvimento

```bash
pip install -e ".[dev]"
```

Ou com uv:

```bash
uv pip install -e ".[dev]"
```

### 3. Configure o pre-commit

```bash
pre-commit install
```

## Executando Testes

### Testes Unitários

```bash
pytest tests/unit_tests/ -v
```

### Testes de Integração

Requer `MARITACA_API_KEY`:

```bash
export MARITACA_API_KEY="sua-chave"
pytest tests/integration_tests/ -v
```

### Todos os Testes

```bash
pytest
```

### Com Coverage

```bash
pytest --cov=langchain_maritaca --cov-report=html
```

## Linting e Formatação

### Verificar

```bash
ruff check langchain_maritaca tests
ruff format --check langchain_maritaca tests
```

### Corrigir

```bash
ruff check --fix langchain_maritaca tests
ruff format langchain_maritaca tests
```

### Type Checking

```bash
mypy langchain_maritaca
```

## Estrutura do Projeto

```
langchain-maritaca/
├── langchain_maritaca/
│   ├── __init__.py         # Exports públicos
│   ├── chat_models.py      # Implementação principal
│   └── version.py          # Versão do pacote
├── tests/
│   ├── unit_tests/         # Testes sem API real
│   └── integration_tests/  # Testes com API real
├── docs/                   # Documentação MkDocs
├── pyproject.toml          # Configuração do projeto
└── README.md
```

## Fluxo de Contribuição

### 1. Crie uma issue

Antes de começar, crie uma issue descrevendo a mudança proposta.

### 2. Fork e branch

```bash
git checkout -b feature/minha-feature
```

### 3. Faça suas mudanças

- Siga o estilo de código existente
- Adicione testes para novas funcionalidades
- Atualize a documentação se necessário

### 4. Teste

```bash
pytest
ruff check .
mypy langchain_maritaca
```

### 5. Commit

Siga o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: adiciona suporte a X"
git commit -m "fix: corrige bug em Y"
git commit -m "docs: atualiza documentação de Z"
```

### 6. Pull Request

Abra um PR com descrição clara das mudanças.

## Padrões de Código

### Docstrings

Use Google style:

```python
def funcao(param1: str, param2: int) -> bool:
    """Breve descrição.

    Descrição mais detalhada se necessário.

    Args:
        param1: Descrição do param1.
        param2: Descrição do param2.

    Returns:
        Descrição do retorno.

    Raises:
        ValueError: Quando ocorre erro.
    """
```

### Type Hints

Sempre use type hints:

```python
def processar(texto: str, limite: int | None = None) -> list[str]:
    ...
```

### Imports

Organize imports com isort (via ruff):

```python
# stdlib
import os
from typing import Any

# third-party
import httpx
from langchain_core.messages import AIMessage

# local
from langchain_maritaca.version import __version__
```

## Reportando Bugs

Inclua na issue:

1. Versão do Python
2. Versão do langchain-maritaca
3. Código para reproduzir
4. Mensagem de erro completa
5. Comportamento esperado vs real

## Sugerindo Features

Descreva na issue:

1. Problema que resolve
2. Solução proposta
3. Alternativas consideradas
4. Exemplos de uso

## Código de Conduta

- Seja respeitoso
- Aceite feedback construtivo
- Foque no que é melhor para a comunidade

## Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença MIT do projeto.
