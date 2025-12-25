# Instalação

## Requisitos

- Python 3.10 ou superior
- Uma chave de API da Maritaca AI ([Obtenha aqui](https://plataforma.maritaca.ai/))

## Instalar via PyPI

A forma recomendada de instalar o langchain-maritaca é via pip:

```bash
pip install langchain-maritaca
```

## Instalar com extras

Se você quiser usar todas as funcionalidades do LangChain:

```bash
pip install langchain-maritaca langchain langchain-community
```

## Instalar do código fonte

Para desenvolvimento ou para obter as últimas funcionalidades:

```bash
git clone https://github.com/anderson-ufrj/langchain-maritaca.git
cd langchain-maritaca
pip install -e .
```

## Verificar Instalação

```python
from langchain_maritaca import ChatMaritaca

print(ChatMaritaca)
# <class 'langchain_maritaca.chat_models.ChatMaritaca'>
```

## Dependências

langchain-maritaca possui dependências mínimas:

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| `langchain-core` | >=0.3.0 | Classes base do LangChain |
| `httpx` | >=0.25.0 | Cliente HTTP para chamadas de API |

## Próximos Passos

- [Início Rápido](quickstart.md) - Obtenha sua primeira resposta
- [Configuração](configuration.md) - Configure sua chave de API
