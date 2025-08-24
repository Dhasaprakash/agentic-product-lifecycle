# Agentic AI Architect System

An intelligent system that orchestrates multiple AI agents to automate the entire product development lifecycle from ideation to deployment using **LangGraph + MCP**.

## 🎯 **Overview**

This system orchestrates multiple AI agents to automate:
- **Ideation → Requirements**: Generate Epics/Stories with Definition of Done
- **Design & Architecture**: Create DDD models using Context Mapper
- **Code Generation**: Build production-ready Spring Boot microservices
- **Deployment**: Deploy to Kubernetes using Helm charts

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ideation      │───▶│   Requirements  │───▶│   Code Gen      │───▶│   Deployment    │
│     Agent       │    │     Agent       │    │     Agent       │    │     Agent       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Core Components**

- **LangGraph Orchestration**: Intelligent workflow management with state transitions
- **MCP Integration**: Tool calling and external service integration
- **Azure DevOps Integration**: Automated story creation and management
- **DDD Design**: Context Mapper DSL for bounded contexts
- **Spring Boot Generation**: Production-ready microservices with clean architecture
- **Kubernetes Deployment**: Helm charts and deployment automation

## 🚀 **Quick Start Guide**

### **1. Environment Setup**

#### **Option A: Using Virtual Environment (Recommended)**
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### **Option B: Using System Python**
```bash
# Install dependencies directly
python3 -m pip install -r requirements.txt
```

### **2. Configuration**

Set environment variables (optional for demo mode):
```bash
# Set OpenAI API key for full functionality
export OPENAI_API_KEY="your-openai-api-key-here"

# Azure DevOps configuration (optional for demo)
export ADO_ORGANIZATION="your-organization-name"
export ADO_PROJECT="your-project-name"
export ADO_PAT="your-personal-access-token"
```

### **3. Run the Application**

#### **Start the Server**
```bash
# Run the simplified version (no external dependencies required)
python3 main_simple.py
```

The application will start at `http://localhost:8000`

#### **Verify Installation**
```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

### **4. Execute a Complete Workflow**

#### **Step 1: Start a New Workflow**
```bash
curl -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "User Authentication System",
    "feature_description": "Implement secure user authentication with OAuth2",
    "priority": "High"
  }'
```

**Response:**
```json
{
  "workflow_id": "workflow_0",
  "status": "started",
  "message": "Workflow started for feature: User Authentication System"
}
```

#### **Step 2: Monitor Workflow Progress**
```bash
# Check workflow status
curl http://localhost:8000/workflow/workflow_0/status

# List all workflows
curl http://localhost:8000/workflows
```

#### **Step 3: Approve the Workflow**
When the workflow reaches the approval step:
```bash
# Approve to continue
curl -X POST http://localhost:8000/workflow/workflow_0/approve

# Or reject if needed
curl -X POST http://localhost:8000/workflow/workflow_0/reject \
  -H "Content-Type: application/json" \
  -d '{"reason": "Need more details"}'
```

#### **Step 4: View Generated Artifacts**
```bash
# Get all artifacts
curl http://localhost:8000/workflow/workflow_0/artifacts
```

## 🔄 **Workflow Stages**

The system automatically progresses through these stages:

1. **🚀 Ideation** (2s) → Generates epics, user stories, bounded contexts
2. **⏸️ Human Approval** → Waits for your decision
3. **📋 Requirements** (2s) → Creates ADO stories (mocked)
4. **🏗️ Design** (2s) → Generates DDD models and architecture diagrams
5. **💻 Code Generation** (3s) → Creates OpenAPI specs and Spring Boot services
6. **🚀 Deployment** (2s) → Generates Kubernetes manifests and Helm charts

## 🌐 **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System information |
| `/health` | GET | Health check |
| `/workflow/start` | POST | Start new workflow |
| `/workflow/{id}/status` | GET | Get workflow status |
| `/workflow/{id}/approve` | POST | Approve workflow |
| `/workflow/{id}/reject` | POST | Reject workflow |
| `/workflow/{id}/artifacts` | GET | Get generated artifacts |
| `/workflows` | GET | List all workflows |

## 🎯 **Demo Workflow Example**

### **Complete Feature Development Workflow**

```bash
# 1. Start workflow for a new feature
WORKFLOW_ID=$(curl -s -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "E-commerce Shopping Cart",
    "feature_description": "Implement shopping cart functionality with inventory management",
    "priority": "High"
  }' | jq -r '.workflow_id')

echo "Started workflow: $WORKFLOW_ID"

# 2. Wait for approval step (check status every 5 seconds)
while true; do
  STATUS=$(curl -s "http://localhost:8000/workflow/$WORKFLOW_ID/status" | jq -r '.status')
  echo "Current status: $STATUS"
  
  if [ "$STATUS" = "waiting_approval" ]; then
    echo "Workflow waiting for approval. Approving now..."
    break
  elif [ "$STATUS" = "completed" ]; then
    echo "Workflow completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Workflow failed!"
    break
  fi
  
  sleep 5
done

# 3. Approve the workflow
curl -X POST "http://localhost:8000/workflow/$WORKFLOW_ID/approve"

# 4. Wait for completion
while true; do
  STATUS=$(curl -s "http://localhost:8000/workflow/$WORKFLOW_ID/status" | jq -r '.status')
  echo "Current status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo "Workflow completed successfully!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Workflow failed!"
    break
  fi
  
  sleep 5
done

# 5. View final artifacts
echo "Final artifacts:"
curl -s "http://localhost:8000/workflow/$WORKFLOW_ID/artifacts" | jq '.'
```

## 📁 **Project Structure**

```
agentic-product-lifecycle/
├── agents/                 # LangGraph agents
│   ├── ideation.py        # Ideation agent
│   ├── requirements.py     # Requirements agent
│   ├── design.py          # Design agent
│   ├── codegen.py         # Code generation agent
│   └── deployment.py      # Deployment agent
├── workflows/              # LangGraph workflows
│   └── lifecycle.py       # Main workflow orchestration
├── templates/              # Code generation templates
│   ├── spring-boot/       # Spring Boot templates
│   ├── helm/              # Helm chart templates
│   └── context-mapper/    # Context Mapper DSL templates
├── services/               # External service integrations
│   ├── ado_client.py      # Azure DevOps client
│   ├── mcp_client.py      # MCP client
│   └── kubernetes.py      # Kubernetes client
├── models/                 # Data models
│   └── domain.py          # Domain models
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
├── build.gradle           # Java dependencies
├── main.py                # Main application entry point
└── main_simple.py         # Simplified demo version
```

## 🔄 **Workflow Details**

### **1. Ideation Agent**
- Analyzes feature ideas using LLM intelligence
- Generates user stories with acceptance criteria
- Creates Definition of Done (DoD)
- Identifies initial bounded contexts

### **2. Requirements Agent**
- Pushes stories to Azure DevOps
- Manages epic/story relationships
- Tracks requirements status
- Validates story readiness for development

### **3. Design Agent**
- Creates DDD bounded contexts
- Generates Context Mapper DSL
- Produces architecture diagrams (PlantUML)
- Applies domain modeling best practices

### **4. Code Generation Agent**
- Generates OpenAPI 3.0 specifications
- Scaffolds Spring Boot microservices
- Implements clean architecture patterns
- Creates comprehensive test suites

### **5. Deployment Agent**
- Generates Docker images
- Creates Helm charts
- Deploys to Kubernetes
- Manages deployment lifecycle

## 🧪 **Testing**

```bash
# Run Python tests
pytest

# Run Java tests
./gradlew test

# Run integration tests
./gradlew integrationTest
```

## 🚢 **Deployment**

```bash
# Deploy to Kubernetes
helm install my-service ./helm/my-service

# Check deployment status
kubectl get pods -l app=my-service
```

## 📊 **Monitoring**

- **Azure DevOps**: Story tracking and progress
- **Kubernetes**: Pod status and logs
- **Application**: Health checks and metrics

## 🔧 **Troubleshooting**

### **Common Issues**

1. **ModuleNotFoundError: No module named 'fastapi'**
   ```bash
   # Solution: Install dependencies
   pip install -r requirements.txt
   ```

2. **Port 8000 already in use**
   ```bash
   # Solution: Kill existing process or change port
   lsof -ti:8000 | xargs kill -9
   ```

3. **Permission denied**
   ```bash
   # Solution: Use virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   ```
4. **check if we have all the dependencies installed and then run the main application:**
```bash
source .venv/bin/activate && pip list | grep -E "(fastapi|langgraph|langchain|azure-devops|kubernetes)"
```

5. **If youinstall them first:**
```bash
source .venv/bin/activate && pip install -r requirements.txt
```
6. **Ifrun the main application (not the mock version) to use the real integrations:**
```bash
   source .venv/bin/activate && python3 main.py
   ```
7. **check if it's running:**
```bash
curl -s http://localhost:8000/ | jq
curl http://localhost:8000/health | jq
```
8. **check process running**
   ```bash
   ps aux | grep python | grep -v grep
   lsof -ti:8000 | xargs kill -9
   ```
9. **start workflow**
  ```bash
  curl -X POST http://localhost:8000/workflow/start -H "Content-Type: application/json" -d '{"feature_name": "Real Integration Test", "feature_description": "Testing real Azure DevOps and OpenAI integrations", "priority": "High", "business_context": "Testing the full system capabilities"}' | jq
  ```



### **Logs and Debugging**

The application provides detailed logging:
- **Startup logs**: System initialization and configuration
- **Workflow logs**: Progress through each stage
- **Error logs**: Detailed error information for debugging

## 🚀 **Next Steps**

After running the demo workflow:

1. **Explore the API Documentation** at `http://localhost:8000/docs`
2. **Test Different Feature Types** with various priorities and descriptions
3. **Monitor Workflow Execution** in real-time
4. **Extend the System** with real integrations (ADO, Kubernetes, etc.)

## 📚 **Architecture Overview**

The system consists of:

- **FastAPI Backend**: RESTful API for workflow management
- **LangGraph Workflows**: Intelligent orchestration of AI agents
- **Mocked Agents**: Simulated AI agents for each lifecycle stage
- **Workflow Engine**: Orchestrates the complete development process
- **Artifact Storage**: In-memory storage for generated deliverables

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Ready to automate your product development? Start with the demo workflow above! 🚀**
