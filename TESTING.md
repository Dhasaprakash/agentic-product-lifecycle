# Testing Guide for Agentic AI Architect

This guide explains how to test the Agentic AI Architect system, including the fixes for LangGraph state management, full workflow testing, and real integration verification.

## 🚀 Quick Start

### 1. Setup Environment

First, ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the test configuration file and update it with your credentials:

```bash
cp test_config.env .env
# Edit .env with your actual credentials
```

Required configuration:
- `OPENAI_API_KEY`: Your OpenAI API key for code generation
- `ADO_ORGANIZATION`: Azure DevOps organization name
- `ADO_PROJECT`: Azure DevOps project name  
- `ADO_PAT`: Azure DevOps Personal Access Token

### 3. Run Tests

#### Run All Tests
```bash
python run_tests.py --all
```

#### Run Specific Tests
```bash
# Test only Azure DevOps integration
python run_tests.py --tests ado

# Test workflow state management
python run_tests.py --tests state

# Test OpenAI code generation
python run_tests.py --tests codegen

# Test full workflow
python run_tests.py --tests workflow

# Test multiple components
python run_tests.py --tests ado state workflow
```

## 🧪 Test Components

### 1. Azure DevOps Integration Test (`ado`)

**Purpose**: Verifies real Azure DevOps integration for story creation and management.

**What it tests**:
- Connection to Azure DevOps organization
- Project access validation
- Basic API functionality

**Requirements**:
- Valid Azure DevOps organization and project
- Personal Access Token with appropriate permissions

**Expected Output**:
```
Testing Azure DevOps Integration
==================================================
Testing Azure DevOps connection...
✅ Azure DevOps connection test completed
```

### 2. Workflow State Management Test (`state`)

**Purpose**: Tests LangGraph state management and persistence.

**What it tests**:
- State initialization
- State persistence in memory
- State updates and retrieval
- Error handling

**Requirements**: None (uses in-memory storage)

**Expected Output**:
```
Testing Workflow State Management
==================================================
Testing state initialization...
Testing state persistence...
✅ State persistence test passed
Testing state updates...
✅ State update test passed
✅ All workflow state management tests passed
```

### 3. OpenAI Code Generation Test (`codegen`)

**Purpose**: Tests AI-powered code generation capabilities.

**What it tests**:
- OpenAI API connectivity
- Microservice code generation
- Code validation
- Artifact generation

**Requirements**:
- Valid OpenAI API key
- Internet connectivity

**Expected Output**:
```
Testing OpenAI Code Generation
==================================================
Testing code generation...
Generating test microservice...
✅ Code generation test passed
Generated X code artifacts
```

### 4. Full Workflow Test (`workflow`)

**Purpose**: Tests the complete product lifecycle from ideation to deployment.

**What it tests**:
- End-to-end workflow execution
- All agent interactions
- State transitions
- Artifact generation
- Integration between components

**Requirements**:
- All previous tests should pass
- Sufficient API quota for OpenAI

**Expected Output**:
```
Testing Full Product Lifecycle Workflow
==================================================
Feature Request: User Authentication System
Description: Implement secure user authentication...
Priority: High

Initializing workflow...
Workflow ID: workflow_20241201_143022
Starting workflow execution...

✅ Full workflow completed in X.XX seconds!
Final Status: completed
Current Step: validation
Workflow ID: workflow_20241201_143022

📋 Feature Created: User Authentication System
📚 Epic Created: User Authentication Epic
📝 User Stories Created: X
🏗️  Bounded Contexts: X

📦 Generated Artifacts:
  • DDD Model: X files
  • Generated Code: X files
  • Deployment Config: X files
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` when running tests
**Solution**: Ensure you're running from the project root directory

#### 2. Configuration Errors
**Problem**: Missing environment variables
**Solution**: Check your `.env` file and ensure all required variables are set

#### 3. Azure DevOps Connection Issues
**Problem**: Authentication or permission errors
**Solution**: 
- Verify your Personal Access Token is valid
- Ensure the token has appropriate permissions for the project
- Check organization and project names are correct

#### 4. OpenAI API Errors
**Problem**: Rate limiting or authentication errors
**Solution**:
- Verify your API key is correct
- Check your API quota and billing status
- Ensure you have access to the specified model

#### 5. Workflow State Errors
**Problem**: State management failures
**Solution**: 
- Check that all required dependencies are installed
- Verify LangGraph version compatibility
- Check for memory issues on large workflows

### Debug Mode

Enable detailed logging by setting the log level:

```bash
export LOG_LEVEL=DEBUG
python run_tests.py --tests workflow
```

## 📊 Test Results Interpretation

### Success Indicators

✅ **All Tests Pass**: System is fully functional
- LangGraph state management working correctly
- Azure DevOps integration operational
- OpenAI code generation functional
- Complete workflow execution successful

⚠️ **Some Tests Skipped**: Partial functionality
- Missing configuration for external services
- System continues with limited capabilities

❌ **Tests Failed**: System issues detected
- Check error logs for specific failure reasons
- Verify configuration and dependencies
- Review system logs for additional context

### Performance Metrics

The full workflow test provides execution time metrics:
- **Fast execution** (< 30 seconds): Optimal performance
- **Medium execution** (30-60 seconds): Normal performance
- **Slow execution** (> 60 seconds): May indicate issues

## 🚀 Production Testing

For production deployments, consider additional testing:

### Load Testing
```bash
# Test multiple concurrent workflows
python -c "
import asyncio
from test_full_workflow import test_full_workflow, load_test_config
config = load_test_config()
async def run_concurrent():
    tasks = [test_full_workflow(config) for _ in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f'Completed {len([r for r in results if r])}/5 workflows')
asyncio.run(run_concurrent())
"
```

### Integration Testing
- Test with real Azure DevOps projects
- Verify Kubernetes deployment (if configured)
- Test with production OpenAI models

### Security Testing
- Validate environment variable handling
- Test authentication mechanisms
- Verify API key security

## 📝 Test Customization

### Adding New Tests

1. Create test function in `test_full_workflow.py`
2. Add to test registry in `run_tests.py`
3. Update this documentation

### Custom Test Data

Modify the feature request in `test_full_workflow.py` to test different scenarios:

```python
feature_request = {
    "feature_name": "Your Custom Feature",
    "feature_description": "Custom description...",
    "priority": "Medium",
    # ... other fields
}
```

### Environment-Specific Testing

Create environment-specific test configurations:

```bash
# Development testing
python run_tests.py --config dev_config.env

# Staging testing  
python run_tests.py --config staging_config.env

# Production testing
python run_tests.py --config prod_config.env
```

## 🎯 Next Steps

After successful testing:

1. **Deploy to Development**: Use the system in a development environment
2. **Integration Testing**: Test with real Azure DevOps projects
3. **Performance Optimization**: Monitor and optimize workflow execution
4. **Production Deployment**: Deploy to production with monitoring

## 📞 Support

For testing issues or questions:

1. Check the troubleshooting section above
2. Review system logs for detailed error information
3. Verify all dependencies and configurations
4. Check the main project documentation

---

**Happy Testing! 🚀**
