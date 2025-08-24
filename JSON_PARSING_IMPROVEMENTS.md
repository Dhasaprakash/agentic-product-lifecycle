# JSON Parsing Improvements and User Model Selection

## 🎯 Overview

This document outlines the improvements made to fix JSON parsing issues and allow users to select LLM models for the Agentic AI Architect system.

## ✅ Completed Improvements

### 1. Enhanced JSON Parsing

#### **Problem Solved**
- LLM responses often included markdown formatting (````json`) or invalid JSON syntax
- System would crash when JSON parsing failed
- No fallback mechanism for handling parsing errors

#### **Solution Implemented**
- **Multi-Strategy JSON Extraction**: 
  - Extract from ````json` code blocks
  - Extract from generic ```` blocks  
  - Pattern matching for JSON objects/arrays
  - Fallback to full content parsing

- **JSON Cleaning**: 
  - Remove trailing commas
  - Quote unquoted keys and values
  - Handle newlines and whitespace

- **Fallback Responses**: 
  - Context-specific default JSON structures
  - Ensures system continues operating even with parsing failures

#### **Code Changes**
- Updated `DesignAgent._parse_json_response()` 
- Updated `CodeGenerationAgent._parse_json_response()`
- Added `_clean_json_string()` and `_get_fallback_json_response()` methods

### 2. Improved LLM Prompts

#### **Problem Solved**
- LLM responses included unnecessary markdown formatting
- Inconsistent JSON structure in responses

#### **Solution Implemented**
- **Clearer Instructions**: "Respond ONLY with valid JSON. Do not include any markdown formatting"
- **Explicit Structure Examples**: Provided exact JSON templates in prompts
- **Context-Specific Prompts**: Tailored prompts for each generation type

### 3. User Model Selection

#### **Problem Solved**
- Users were locked into default LLM models
- No way to choose preferred model through the API

#### **Solution Implemented**
- **Extended API**: Added `llm_model` and `llm_temperature` parameters to `FeatureRequest`
- **New Endpoint**: `/models` - Lists all available LLM models with recommendations
- **Dynamic Configuration**: Workflow uses user-specified model instead of defaults

#### **API Changes**
```json
// POST /workflow/start
{
  "feature_name": "My Feature",
  "feature_description": "Feature description",
  "llm_model": "llama3-8b-8192",    // NEW: User can specify model
  "llm_temperature": 0.7            // NEW: User can specify temperature
}

// GET /models - NEW ENDPOINT
{
  "supported_models": {
    "openai": ["gpt-4o", "gpt-4o-mini", ...],
    "anthropic": ["claude-3-5-sonnet-20241022", ...],
    "groq": ["llama3-8b-8192", ...],
    ...
  },
  "recommendations": {
    "fast_and_cheap": "llama3-8b-8192",
    "balanced": "gpt-4o-mini",
    "high_quality": "gpt-4o"
  }
}
```

## 🔧 Technical Implementation

### Fallback JSON Examples

**Design Agent Fallback**:
```json
{
  "name": "ContextName",
  "description": "Bounded context for ContextName domain",
  "entities": [{"name": "ContextNameEntity", "attributes": ["id", "name"], ...}],
  "value_objects": [{"name": "ContextNameId", ...}],
  "aggregates": [...],
  "domain_services": [...],
  "repositories": [...],
  "factories": [...]
}
```

**Code Generation Agent Fallback**:
```json
{
  "openapi": "3.0.3",
  "info": {"title": "Generated API", "version": "1.0.0"},
  "paths": {"/api/v1/items": {"get": {...}}},
  "components": {"schemas": {"Item": {...}}}
}
```

### Model Selection Flow

1. **User Request** → API receives `llm_model` parameter
2. **Configuration** → Workflow config updated with user model
3. **Agent Initialization** → All agents use the same user-specified model
4. **Consistent Usage** → Design, Code Generation, and Deployment agents all use selected model

## 🚀 Benefits

### Reliability
- ✅ System no longer crashes on JSON parsing errors
- ✅ Fallback responses ensure workflow continuation
- ✅ Better error handling and logging

### Flexibility
- ✅ Users can choose optimal model for their needs
- ✅ Cost optimization (cheap models for testing, premium for production)
- ✅ Performance tuning (fast models vs. high-quality models)

### User Experience
- ✅ Clear model recommendations based on use case
- ✅ API documentation shows available options
- ✅ Consistent model usage throughout workflow

## 🧪 Testing

### JSON Parsing Test
```python
# Test with malformed JSON - should use fallback
test_content = '''
```json
{
    "name": "TestContext",
    "invalid": "json with trailing comma",
}
```
'''
result = agent._parse_json_response(test_content, "TestContext")
# Result: Valid fallback JSON structure
```

### Model Selection Test
```bash
# Check available models
curl http://localhost:8000/models

# Start workflow with specific model
curl -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "Test Feature",
    "feature_description": "Test description", 
    "llm_model": "llama3-8b-8192"
  }'
```

## 🏁 Result

The system is now **significantly more robust** and **user-friendly**:
- No more crashes due to JSON parsing failures
- Users have full control over LLM model selection
- Better error handling and fallback mechanisms
- Improved prompts for cleaner LLM responses

All agents (Design, Code Generation, Deployment) now consistently use the user-selected LLM model with improved error handling and fallback capabilities.
