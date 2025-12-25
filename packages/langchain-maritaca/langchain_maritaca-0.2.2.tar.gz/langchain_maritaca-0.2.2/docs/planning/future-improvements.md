# Future Improvements for langchain-maritaca

This document outlines planned improvements and enhancements for the langchain-maritaca package.

## High Priority

### 1. ~~Embeddings Support~~ ✅ IMPLEMENTED (v0.2.2)
~~Add embeddings class for RAG (Retrieval-Augmented Generation) workflows.~~

Since Maritaca AI does not provide native embeddings, we implemented `DeepInfraEmbeddings`
using the `intfloat/multilingual-e5-large` model as recommended by Maritaca AI.

```python
from langchain_maritaca import DeepInfraEmbeddings

embeddings = DeepInfraEmbeddings()
vectors = embeddings.embed_documents(["Olá", "Mundo"])
# Each vector has 1024 dimensions
```

**Features**:
- Sync and async methods (embed_query, embed_documents, aembed_query, aembed_documents)
- Automatic batching with configurable batch_size
- Supports 100 languages including Portuguese
- Model: `intfloat/multilingual-e5-large` (1024 dimensions, 512 max tokens)

**Status**: ✅ IMPLEMENTED
**Complexity**: Medium
**Impact**: High - Enables complete RAG pipelines with Maritaca

### 2. ~~Structured Output~~ ✅ IMPLEMENTED (v0.2.2)
~~Implement `with_structured_output()` method to return Pydantic models directly.~~

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    """Information about a person."""
    name: str = Field(description="Person's name")
    age: int = Field(description="Person's age")

model = ChatMaritaca()
structured_model = model.with_structured_output(Person)
result = structured_model.invoke("João tem 25 anos")
# Returns: Person(name="João", age=25)
```

**Supported methods**:
- `function_calling` (default): Uses tool calling API for reliable schema compliance
- `json_mode`: Uses JSON response format

**Options**:
- `include_raw=True`: Returns dict with `raw`, `parsed`, and `parsing_error` keys

**Status**: ✅ IMPLEMENTED
**Complexity**: Medium
**Impact**: High - Simplifies data extraction tasks, enables medical AI applications

---

## Medium Priority

### 3. Cache Integration
Add native support for LangChain caching to reduce API costs.

```python
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

set_llm_cache(InMemoryCache())
model = ChatMaritaca()  # Now uses cache automatically
```

**Status**: Planned
**Complexity**: Low
**Impact**: Medium - Reduces costs for repeated queries

### 4. Enhanced Callbacks
More granular callbacks for token-by-token streaming, cost tracking, and latency monitoring.

**Status**: Planned
**Complexity**: Low
**Impact**: Medium - Better observability

### 5. Configurable Retry Logic
Expose retry parameters for more control over error handling.

```python
model = ChatMaritaca(
    retry_if_rate_limited=True,
    retry_delay=1.0,
    retry_max_delay=60.0,
    retry_multiplier=2.0,
)
```

**Status**: Planned
**Complexity**: Low
**Impact**: Medium - Better resilience in production

### 6. Coverage Badge
Add Codecov integration to show test coverage in README.

**Status**: Planned
**Complexity**: Low
**Impact**: Low - Documentation improvement

---

## Low Priority

### 7. Token Counter
Implement `get_num_tokens()` method to estimate token count before API calls.

```python
model = ChatMaritaca()
tokens = model.get_num_tokens("Olá, como vai você?")
```

**Status**: Planned
**Complexity**: Medium (requires tokenizer)
**Impact**: Medium - Helps with cost estimation

### 8. Batch Optimization
Use batch API endpoint if available for better throughput.

**Status**: Planned
**Complexity**: Medium
**Impact**: Low - Performance improvement for batch operations

### 9. Multimodal/Vision Support
Add support for image inputs when Maritaca API supports it.

**Status**: Waiting for API support
**Complexity**: High
**Impact**: High - Enables vision tasks

### 10. Bilingual Documentation
Add Portuguese (PT-BR) version of README since the target audience is Brazilian developers.

**Status**: Planned
**Complexity**: Low
**Impact**: Medium - Better accessibility for Portuguese speakers

---

## Contributing

Contributions are welcome! If you'd like to work on any of these improvements:

1. Open an issue to discuss the implementation approach
2. Fork the repository
3. Create a feature branch
4. Submit a pull request

For questions or suggestions, please open an issue on GitHub.
