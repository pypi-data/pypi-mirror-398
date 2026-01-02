# langchain-maritaca Roadmap

Consolidated roadmap with detailed implementation steps for each planned feature.

> **Last Updated:** December 2025
> **Current Version:** v0.2.2

---

## Summary

| Feature | Priority | Complexity | Status |
|---------|----------|------------|--------|
| Cache Integration | High | Low | Planned |
| ~~Configurable Retry Logic~~ | High | Low | **IMPLEMENTED** |
| Enhanced Callbacks | Medium | Low | Planned |
| Token Counter | Medium | Medium | Planned |
| Batch Optimization | Low | Medium | Planned |
| Multimodal/Vision Support | Low | High | Blocked (API) |

---

## HIGH PRIORITY

### 1. Cache Integration

**Goal:** Enable LangChain's native caching to reduce API costs for repeated queries.

**Implementation Steps:**

1. **Research LangChain caching mechanism**
   - Read `langchain-core` source for `BaseChatModel` caching
   - Check if `_generate` method needs modification
   - Understand cache key generation

2. **Verify current behavior**
   - Test if `set_llm_cache()` already works with ChatMaritaca
   - If it works, just add documentation and examples
   - If not, identify what needs to be implemented

3. **Implement cache support (if needed)**
   - File: `langchain_maritaca/chat_models.py`
   - Ensure `_generate` properly interacts with LangChain cache
   - Handle cache serialization for Maritaca responses

4. **Add unit tests**
   - File: `tests/unit_tests/test_chat_models.py`
   - Test cache hit/miss scenarios
   - Test cache invalidation
   - Test with different cache backends (InMemory, Redis mock)

5. **Add documentation**
   - File: `docs/en/guide/caching.md` and `docs/pt-br/guide/caching.md`
   - Usage examples
   - Performance comparison with/without cache

6. **Update README**
   - Add caching example in usage section

**Files to modify:**
- `langchain_maritaca/chat_models.py`
- `tests/unit_tests/test_chat_models.py`
- `docs/en/guide/caching.md` (new)
- `docs/pt-br/guide/caching.md` (new)
- `mkdocs.yml` (add nav entry)

---

### 2. ~~Configurable Retry Logic~~ ✅ IMPLEMENTED

**Goal:** Expose retry parameters for production resilience customization.

**Implemented Parameters:**
```python
model = ChatMaritaca(
    retry_if_rate_limited=True,   # Auto-retry on HTTP 429
    retry_delay=1.0,              # Initial delay (seconds)
    retry_max_delay=60.0,         # Maximum delay (seconds)
    retry_multiplier=2.0,         # Exponential backoff multiplier
    max_retries=2,                # Maximum retry attempts
)
```

**Features:**
- Exponential backoff with configurable multiplier
- Delay capped at `retry_max_delay`
- Rate limit retry can be disabled with `retry_if_rate_limited=False`
- Validation for all retry parameters
- Works for both sync and async requests

**Status:** ✅ IMPLEMENTED
**Complexity:** Low
**Impact:** Medium - Better resilience in production

---

## MEDIUM PRIORITY

### 3. Enhanced Callbacks

**Goal:** Provide granular callbacks for observability (cost tracking, latency, token streaming).

**Implementation Steps:**

1. **Research LangChain callback system**
   - Study `CallbackManagerForLLMRun`
   - Identify available callback hooks
   - Check what other integrations implement

2. **Implement cost tracking callback**
   - Calculate cost based on token usage and Maritaca pricing
   - Emit cost data via callbacks
   - Create `MaritacaCostCallback` example class

3. **Implement latency monitoring**
   - Track time for each API call
   - Emit latency metrics via callbacks
   - Support percentile calculations

4. **Enhance streaming callbacks**
   - Ensure token-by-token streaming emits proper callbacks
   - Add timing information to stream chunks

5. **Create callback examples**
   - Cost tracking callback
   - Latency logging callback
   - Prometheus metrics callback

6. **Add documentation**
   - Callback usage guide
   - Integration with monitoring tools

**Files to modify:**
- `langchain_maritaca/chat_models.py`
- `langchain_maritaca/callbacks.py` (new, optional)
- `tests/unit_tests/test_callbacks.py` (new)
- `docs/en/guide/callbacks.md` (new)
- `docs/pt-br/guide/callbacks.md` (new)
- `docs/en/examples/monitoring.md` (new)

---

### 4. Token Counter

**Goal:** Implement `get_num_tokens()` for cost estimation before API calls.

**Implementation Steps:**

1. **Research tokenization options**
   - Check if Maritaca publishes their tokenizer
   - Evaluate `tiktoken` as approximation
   - Consider `sentencepiece` for Portuguese

2. **Choose tokenization strategy**
   - Option A: Use tiktoken cl100k_base as approximation
   - Option B: Implement character-based estimation
   - Option C: Call Maritaca API for exact count (if available)

3. **Implement `get_num_tokens()` method**
   - File: `langchain_maritaca/chat_models.py`
   - Handle different input types (str, list of messages)
   - Return token count estimate

4. **Implement `get_num_tokens_from_messages()`**
   - Handle message formatting overhead
   - Account for system/user/assistant prefixes

5. **Add cost estimation utility**
   ```python
   def estimate_cost(self, messages: list, max_output_tokens: int = 1000) -> float:
       input_tokens = self.get_num_tokens_from_messages(messages)
       # Calculate based on Maritaca pricing
   ```

6. **Add tests**
   - Test token counting accuracy
   - Test cost estimation
   - Compare with actual API usage

7. **Add documentation**
   - Usage examples
   - Accuracy disclaimers

**Files to modify:**
- `langchain_maritaca/chat_models.py`
- `pyproject.toml` (add tiktoken dependency, optional)
- `tests/unit_tests/test_token_counter.py` (new)
- `docs/en/guide/cost-estimation.md` (new)

---

## LOW PRIORITY

### 5. Batch Optimization

**Goal:** Use batch API endpoint for improved throughput on multiple requests.

**Implementation Steps:**

1. **Research Maritaca batch API**
   - Check if Maritaca offers batch endpoints
   - Document API differences from single request

2. **If batch API exists:**
   - Implement `_generate_batch` method
   - Override `batch()` method to use batch API
   - Handle batch size limits

3. **If no batch API:**
   - Implement client-side batching with async
   - Use `asyncio.gather` for parallel requests
   - Add rate limiting to avoid API throttling

4. **Add benchmarks**
   - Compare batch vs sequential performance
   - Measure throughput improvements

5. **Add documentation**
   - Batch usage examples
   - Performance tuning guide

**Files to modify:**
- `langchain_maritaca/chat_models.py`
- `tests/unit_tests/test_batch.py` (new)
- `tests/benchmarks/test_batch_performance.py` (new)

---

### 6. Multimodal/Vision Support

**Goal:** Support image inputs when Maritaca API adds vision capabilities.

**Status:** BLOCKED - Waiting for Maritaca API to support image inputs.

**Preparation Steps:**

1. **Monitor Maritaca API updates**
   - Check API documentation periodically
   - Subscribe to Maritaca announcements

2. **Research LangChain multimodal patterns**
   - Study how other integrations handle images
   - Understand `ImageBlock` and `HumanMessageChunk`

3. **When API available:**
   - Implement image content handling
   - Add base64 encoding utilities
   - Support URL and local file inputs

4. **Testing considerations:**
   - Mock image API for unit tests
   - Create integration tests with real images

**Files to modify (when ready):**
- `langchain_maritaca/chat_models.py`
- `tests/unit_tests/test_vision.py` (new)
- `tests/integration_tests/test_vision.py` (new)
- `docs/en/guide/vision.md` (new)

---

## Completed Features

| Feature | Version | Date |
|---------|---------|------|
| Embeddings Support (DeepInfra) | v0.2.2 | Dec 2025 |
| Structured Output | v0.2.2 | Dec 2025 |
| Tool Calling / Function Calling | v0.2.0 | Dec 2025 |
| Coverage Badge | v0.2.3 | Dec 2025 |
| Bilingual Documentation | v0.2.3 | Dec 2025 |
| Configurable Retry Logic | v0.2.3 | Dec 2025 |

---

## Contributing

Want to work on one of these features? Here's how:

1. **Pick a feature** from the roadmap above
2. **Open an issue** to discuss your approach
3. **Fork the repository** and create a feature branch
4. **Follow the implementation steps** outlined above
5. **Submit a pull request** with tests and documentation

For questions, open an issue on GitHub or check the [Contributing Guide](../../CONTRIBUTING.md).
