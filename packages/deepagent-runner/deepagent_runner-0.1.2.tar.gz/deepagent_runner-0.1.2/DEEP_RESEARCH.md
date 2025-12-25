# Deep Research với Tavily Search

Kế hoạch triển khai tính năng web research cho DeepAgent Runner sử dụng Tavily API.

## Mục tiêu

Thêm khả năng tìm kiếm và nghiên cứu thông tin từ web cho agent, giúp agent có thể:
- Tìm kiếm thông tin mới nhất từ internet
- Nghiên cứu các chủ đề kỹ thuật, documentation, best practices
- Tìm giải pháp cho các vấn đề coding
- Cập nhật kiến thức về frameworks, libraries mới

## Yêu cầu

### Dependencies
- `tavily-python>=0.3.0` (đã có trong optional dependencies)
- `TAVILY_API_KEY` environment variable

### API Key
- Đăng ký tại: https://www.tavily.com/
- Lấy API key và set trong `.env`: `TAVILY_API_KEY=your-key-here`

## Tool Specification

### Function Signature

```python
@tool
def tavily_research(
    query: str,
    depth: str = "medium",
    max_results: int = 5,
    language: str = "en"
) -> str:
    """
    Tìm kiếm và nghiên cứu thông tin từ web sử dụng Tavily API.
    
    Tool này cho phép agent tìm kiếm thông tin mới nhất từ internet, bao gồm:
    - Documentation và tutorials
    - Best practices và coding patterns
    - Giải pháp cho bugs và errors
    - Thông tin về libraries, frameworks mới
    - Technical articles và blog posts
    
    Args:
        query: Câu hỏi hoặc từ khóa tìm kiếm (ví dụ: "Python async best practices", "React hooks tutorial")
        depth: Độ sâu tìm kiếm - "basic" (nhanh, ít kết quả), "medium" (cân bằng), "advanced" (sâu, nhiều kết quả)
        max_results: Số lượng kết quả tối đa (1-20, mặc định: 5)
        language: Ngôn ngữ kết quả - "en" (English), "vi" (Vietnamese), "es", "fr", etc. (mặc định: "en")
        
    Returns:
        Kết quả tìm kiếm được format với:
        - Tổng quan về chủ đề
        - Danh sách các sources với URLs
        - Nội dung tóm tắt từ các sources
        - Key insights và takeaways
        
    Examples:
        tavily_research("Python async await best practices")
        tavily_research("React hooks tutorial", depth="advanced", max_results=10)
        tavily_research("Lỗi ModuleNotFoundError Python", language="vi")
    """
```

## Implementation Plan

### Phase 1: Tool Implementation

#### 1.1. Tạo tavily_research tool trong `agent.py`

**Location**: `src/deepagent_runner/agent.py`

**Steps**:
1. Import TavilyClient từ `tavily`
2. Tạo function `tavily_research` với decorator `@tool`
3. Validate parameters (depth, max_results, language)
4. Initialize TavilyClient với API key từ environment
5. Gọi Tavily API với parameters
6. Format kết quả thành readable string
7. Handle errors gracefully

**Code Structure**:
```python
from tavily import TavilyClient

# Trong build_agent function, sau execute tool:
@tool
def tavily_research(
    query: str,
    depth: str = "medium",
    max_results: int = 5,
    language: str = "en"
) -> str:
    # Implementation
    pass
```

#### 1.2. Parameter Validation

- `depth`: Chỉ chấp nhận "basic", "medium", "advanced"
- `max_results`: Giới hạn 1-20, default 5
- `language`: Validate language codes (en, vi, es, fr, de, etc.)
- `query`: Không được rỗng, trim whitespace

#### 1.3. Error Handling

- Missing API key: Return friendly error message
- API rate limit: Retry với exponential backoff
- Network errors: Retry hoặc return error message
- Invalid parameters: Return validation error

### Phase 2: Response Formatting

#### 2.1. Format Structure

Kết quả nên được format như sau:

```
📚 Research Results: "{query}"

🔍 Search Parameters:
- Depth: {depth}
- Max Results: {max_results}
- Language: {language}

📊 Summary:
{answer from Tavily}

📝 Sources ({count}):
1. {title}
   URL: {url}
   Content: {content preview}

2. {title}
   URL: {url}
   Content: {content preview}
...

💡 Key Insights:
- {insight 1}
- {insight 2}
- {insight 3}
```

#### 2.2. Content Truncation

- Mỗi source content preview: max 500 characters
- Tổng response: max 8000 characters (để tránh context overflow)
- Nếu quá dài, chỉ hiển thị top N sources

### Phase 3: Integration

#### 3.1. Add to Agent

Trong `build_agent()` function:
```python
tools = [execute_cmd, read_image]

# Conditionally add tavily_research if API key available
if os.getenv("TAVILY_API_KEY"):
    tools.append(tavily_research)

agent = create_deep_agent(
    model=model,
    tools=tools,
    ...
)
```

#### 3.2. Update System Prompt

Thêm hướng dẫn về tavily_research vào `DEFAULT_SYSTEM_PROMPT`:

```
## Web Research

You have access to `tavily_research` tool for finding information from the web:
- Use it to search for documentation, tutorials, best practices
- Use it to find solutions to errors or bugs
- Use it to research new technologies or frameworks
- Use it when you need up-to-date information not in your training data

Parameters:
- query: Search query (required)
- depth: "basic" (fast), "medium" (balanced), "advanced" (thorough)
- max_results: Number of results (1-20, default: 5)
- language: Language code (default: "en")

Examples:
- tavily_research("Python async await tutorial")
- tavily_research("React useState hook best practices", depth="advanced")
- tavily_research("ModuleNotFoundError solution", max_results=10)
```

### Phase 4: Configuration

#### 4.1. Environment Variable

- Check `TAVILY_API_KEY` trong `validate_api_keys()`
- Mark as optional (không bắt buộc)
- Show warning nếu không có (nhưng vẫn chạy được)

#### 4.2. CLI Option

Có thể thêm `--enable-research` flag để enable/disable research tool:
```python
enable_research: bool = typer.Option(
    True,
    "--enable-research/--no-research",
    help="Enable web research capabilities (requires TAVILY_API_KEY)",
)
```

## API Reference

### Tavily Search Parameters

Theo Tavily Python SDK documentation:

```python
tavily_client.search(
    query: str,
    search_depth: str = "basic",  # "basic" | "advanced"
    max_results: int = 5,
    include_answer: bool = True,
    include_raw_content: bool = False,
    include_images: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    topic: Optional[str] = None,  # "general" | "news"
)
```

**Mapping**:
- `depth` → `search_depth` ("basic" → "basic", "medium"/"advanced" → "advanced")
- `max_results` → `max_results`
- `language` → Có thể không được hỗ trợ trực tiếp, cần check API docs

### Response Structure

```python
{
    "query": str,
    "follow_up_questions": List[str],
    "answer": str,  # AI-generated summary
    "response_time": float,
    "results": [
        {
            "title": str,
            "url": str,
            "content": str,
            "score": float,
            "published_date": Optional[str],
        }
    ]
}
```

## Testing Plan

### Unit Tests

1. **Tool Creation**
   - Test tool được tạo khi có API key
   - Test tool không được tạo khi không có API key

2. **Parameter Validation**
   - Test invalid depth values
   - Test max_results out of range
   - Test empty query
   - Test invalid language codes

3. **API Integration**
   - Mock TavilyClient responses
   - Test successful search
   - Test error handling (rate limit, network error)
   - Test response formatting

4. **Response Formatting**
   - Test với 1 result
   - Test với nhiều results
   - Test với response quá dài (truncation)
   - Test với empty results

### Integration Tests

1. **Agent Integration**
   - Test agent có thể gọi tavily_research
   - Test agent sử dụng kết quả để trả lời
   - Test trong REPL session

2. **Error Scenarios**
   - Test với invalid API key
   - Test với network timeout
   - Test với rate limit

## Usage Examples

### Example 1: Basic Research

```
You: How to use async/await in Python?

Agent: [Calls tavily_research("Python async await tutorial")]
Agent: [Displays formatted results]
Agent: Based on the research, here's how to use async/await...
```

### Example 2: Advanced Research

```
You: What are the best practices for React hooks?

Agent: [Calls tavily_research("React hooks best practices", depth="advanced", max_results=10)]
Agent: [Displays comprehensive results]
Agent: Here are the key best practices based on current documentation...
```

### Example 3: Error Research

```
You: I'm getting ModuleNotFoundError, how to fix it?

Agent: [Calls tavily_research("ModuleNotFoundError Python solution")]
Agent: [Displays solutions from multiple sources]
Agent: Here are several ways to fix ModuleNotFoundError...
```

## Security Considerations

1. **API Key Protection**
   - Không log API key
   - Không expose trong error messages
   - Store securely trong environment variables

2. **Rate Limiting**
   - Implement rate limiting để tránh abuse
   - Track API calls per session
   - Warn user nếu gần limit

3. **Content Filtering**
   - Validate URLs trước khi hiển thị
   - Sanitize content để tránh XSS
   - Limit response size

## Performance Considerations

1. **Caching**
   - Cache kết quả search cho cùng query trong session
   - Cache duration: 1 hour
   - Cache key: hash(query + depth + max_results)

2. **Async Execution**
   - Tavily API calls có thể mất vài giây
   - Consider async execution để không block agent
   - Show progress indicator

3. **Response Size**
   - Limit total response size để tránh context overflow
   - Truncate long content
   - Prioritize top results

## Future Enhancements

1. **Search History**
   - Track search queries trong session
   - Suggest similar searches
   - Avoid duplicate searches

2. **Domain Filtering**
   - Allow user to specify trusted domains
   - Filter out untrusted sources
   - Prioritize official documentation

3. **Multi-language Support**
   - Better language parameter handling
   - Auto-detect query language
   - Translate results if needed

4. **Search Context**
   - Include workspace context in search
   - Search for project-specific solutions
   - Filter results by technology stack

## Implementation Checklist

### Phase 1: Core Implementation
- [ ] Install tavily-python dependency
- [ ] Create tavily_research tool function
- [ ] Implement parameter validation
- [ ] Implement Tavily API integration
- [ ] Implement response formatting
- [ ] Add error handling

### Phase 2: Integration
- [ ] Add tool to agent (conditional on API key)
- [ ] Update system prompt with research instructions
- [ ] Update config validation
- [ ] Add to CLI options (optional)

### Phase 3: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test error scenarios
- [ ] Test with real API (staging)

### Phase 4: Documentation
- [ ] Update README.md with research feature
- [ ] Update USAGE.md with examples
- [ ] Add to INSTALL.md configuration section
- [ ] Create example workflows

### Phase 5: Polish
- [ ] Add response caching
- [ ] Optimize response formatting
- [ ] Add rate limiting
- [ ] Performance tuning

## Dependencies

```python
# Required
tavily-python>=0.3.0  # Already in optional dependencies

# Environment
TAVILY_API_KEY  # Required for tool to work
```

## Estimated Timeline

- **Phase 1**: 2-3 hours (core implementation)
- **Phase 2**: 1 hour (integration)
- **Phase 3**: 2 hours (testing)
- **Phase 4**: 1 hour (documentation)
- **Phase 5**: 1-2 hours (polish)

**Total**: ~7-9 hours

## Success Criteria

✅ Tool được tạo và hoạt động với Tavily API
✅ Agent có thể sử dụng tool để research
✅ Results được format rõ ràng và dễ đọc
✅ Error handling graceful
✅ Documentation đầy đủ
✅ Tests pass
✅ Performance acceptable (< 5s per search)

## Notes

- Tavily API có rate limits, cần implement retry logic
- Response có thể rất dài, cần truncation strategy
- Language parameter có thể không được hỗ trợ đầy đủ, cần test
- Consider adding search result caching để giảm API calls

