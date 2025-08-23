# AWS DevOps Agent - Model Selection Guide

This guide covers the dynamic model selection system that allows you to choose from multiple Claude models based on your specific needs.

## Available Models

The AWS DevOps Agent supports 5 different Claude models, each optimized for different use cases:

### 🚀 Claude Sonnet 4
- **Model ID**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **Best For**: Complex DevOps scenarios, advanced reasoning, sophisticated infrastructure planning
- **Characteristics**: Latest and most capable model with enhanced reasoning abilities
- **Use Cases**: 
  - Complex multi-service architecture design
  - Advanced troubleshooting scenarios
  - Comprehensive security analysis
  - Strategic infrastructure planning

### 🧠 Claude 3.7 Sonnet
- **Model ID**: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
- **Best For**: Enhanced reasoning tasks, detailed analysis, comprehensive explanations
- **Characteristics**: Improved reasoning capabilities over 3.5 versions
- **Use Cases**:
  - Infrastructure optimization recommendations
  - Detailed cost analysis
  - Complex CI/CD pipeline design
  - In-depth security assessments

### ⚖️ Claude 3.5 Sonnet v2 (Default)
- **Model ID**: `us.anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Best For**: Balanced performance and speed for most DevOps tasks
- **Characteristics**: Optimal balance of capability and response time
- **Use Cases**:
  - General AWS guidance
  - Standard troubleshooting
  - Configuration assistance
  - Best practices recommendations

### 🛡️ Claude 3.5 Sonnet v1
- **Model ID**: `us.anthropic.claude-3-5-sonnet-20240620-v1:0`
- **Best For**: Stable, proven performance for production environments
- **Characteristics**: Reliable and consistent responses
- **Use Cases**:
  - Production environment guidance
  - Critical system recommendations
  - Compliance and governance advice
  - Risk-averse scenarios

### ⚡ Claude 3.5 Haiku
- **Model ID**: `us.anthropic.claude-3-5-haiku-20241022-v1:0`
- **Best For**: Quick responses, simple queries, efficient processing
- **Characteristics**: Fast and efficient for straightforward tasks
- **Use Cases**:
  - Quick status checks
  - Simple configuration questions
  - Basic troubleshooting
  - Rapid information lookup

## Model Selection Methods

### 1. Standalone Model Selector

The easiest way to select a model:

```bash
python3 select_model.py
```

**Features:**
- Interactive menu with current model display
- Clear descriptions of each model
- Immediate confirmation of selection
- Guidance on when to restart applications

**Example Output:**
```
🤖 AWS DevOps Agent - Model Selector
==================================================
Current Model: Claude 3.5 Sonnet v2 (Balanced Performance)
Model ID: us.anthropic.claude-3-5-sonnet-20241022-v2:0

Available Models:
  1. Claude Sonnet 4 (Latest, Most Capable)
  2. Claude 3.7 Sonnet (Enhanced Reasoning)
  3. Claude 3.5 Sonnet v2 (Balanced Performance) ← CURRENT
  4. Claude 3.5 Sonnet v1 (Stable)
  5. Claude 3.5 Haiku (Fast & Efficient)

  0. Keep current selection

Select model (0-5): 
```

### 2. CLI Agent Integration

Select model before starting the agent:

```bash
python3 agent.py --select-model
```

**Features:**
- Model selection integrated into agent startup
- Selected model used immediately
- No need for separate selection step

### 3. Streamlit Web Interface

Real-time model switching in the web interface:

```bash
./run_streamlit.sh
```

**Features:**
- Dropdown selector in the sidebar under "🤖 Model Selection"
- Real-time model updates (changes take effect immediately)
- Visual feedback with success messages
- Current model display in Session Info

**Interface Elements:**
- **Model Dropdown**: Choose from available models with descriptions
- **Current Model Display**: Shows active model in Session Info
- **Success Notifications**: Confirms model changes
- **Model Description**: Shows current model capabilities

### 4. Help and Status

View available models and usage options:

```bash
python3 agent.py --help
```

**Output:**
```
🤖 AWS DevOps Agent - Usage
========================================
python3 agent.py                 # Run agent with current model
python3 agent.py --select-model  # Interactive model selection
python3 select_model.py          # Standalone model selector

Available Models:
  • Claude Sonnet 4 (Latest, Most Capable)
  • Claude 3.7 Sonnet (Enhanced Reasoning)
  • Claude 3.5 Sonnet v2 (Balanced Performance) (CURRENT)
  • Claude 3.5 Sonnet v1 (Stable)
  • Claude 3.5 Haiku (Fast & Efficient)
```

## Model Selection Best Practices

### Choosing the Right Model

**For Complex Infrastructure Projects:**
- Use **Claude Sonnet 4** for comprehensive architecture design
- Use **Claude 3.7 Sonnet** for detailed analysis and optimization

**For Daily DevOps Tasks:**
- Use **Claude 3.5 Sonnet v2** for balanced performance (recommended default)
- Use **Claude 3.5 Sonnet v1** for production-critical guidance

**For Quick Tasks:**
- Use **Claude 3.5 Haiku** for fast responses to simple questions
- Use **Claude 3.5 Haiku** when response speed is more important than depth

### Performance Considerations

**Response Time vs. Capability:**
- **Haiku**: Fastest responses (~1-2 seconds)
- **Sonnet v1/v2**: Moderate response time (~2-4 seconds)
- **Sonnet 3.7/4**: Slower but more comprehensive (~3-6 seconds)

**Cost Considerations:**
- More capable models may have higher usage costs
- Consider using Haiku for high-volume, simple queries
- Use advanced models for complex, high-value tasks

### Model Switching Strategies

**Development Workflow:**
1. Start with **Claude 3.5 Sonnet v2** for general development
2. Switch to **Claude Sonnet 4** for complex architecture decisions
3. Use **Claude 3.5 Haiku** for quick status checks and simple queries

**Production Support:**
1. Use **Claude 3.5 Sonnet v1** for stable, consistent guidance
2. Switch to **Claude 3.7 Sonnet** for detailed troubleshooting
3. Use **Claude Sonnet 4** for critical incident analysis

## Technical Implementation

### Configuration Class

The model selection system is implemented in the `AgentConfig` class:

```python
class AgentConfig:
    # Available Models
    AVAILABLE_MODELS = {
        'claude-sonnet-4': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
        'claude-3-7-sonnet': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
        'claude-3-5-sonnet-v2': 'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
        'claude-3-5-sonnet-v1': 'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
        'claude-3-5-haiku': 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
    }
    
    # Default model selection
    SELECTED_MODEL = 'claude-3-5-sonnet-v2'
    
    @classmethod
    def get_model_id(cls):
        """Get the currently selected model ID."""
        return cls.AVAILABLE_MODELS.get(cls.SELECTED_MODEL)
    
    @classmethod
    def set_model(cls, model_key):
        """Set the model by key."""
        if model_key in cls.AVAILABLE_MODELS:
            cls.SELECTED_MODEL = model_key
            return True
        return False
```

### Model Display

Both CLI and Streamlit interfaces display:
- Current model ID and description
- Model selection confirmation
- Visual feedback for model changes

**CLI Output:**
```
🤖 Using MODEL_ID: us.anthropic.claude-3-5-sonnet-20241022-v2:0
📝 Model Description: Claude 3.5 Sonnet v2 (Balanced Performance)
```

**Streamlit Display:**
- Session Info shows current model
- Model selector dropdown with descriptions
- Success messages for model changes

## Troubleshooting

### Common Issues

**Model Selection Not Persisting:**
- Restart the agent or Streamlit app after model selection
- Verify the selection was successful with confirmation message

**Model Not Available:**
- Ensure you have access to the selected Claude model in your AWS account
- Check Bedrock model access permissions in your region

**Streamlit Model Selector Not Working:**
- Refresh the browser page
- Check console for any JavaScript errors
- Verify the AgentConfig import is working correctly

### Verification Commands

**Check Current Model:**
```bash
python3 -c "from agent import AgentConfig; print(f'Current: {AgentConfig.SELECTED_MODEL}')"
```

**List Available Models:**
```bash
python3 -c "from agent import AgentConfig; [print(f'{k}: {v}') for k,v in AgentConfig.list_models().items()]"
```

**Test Model Selection:**
```bash
python3 select_model.py
```

## Integration with Other Components

### Memory System
- Model selection works seamlessly with AgentCore Memory
- Memory persists across model changes
- No impact on conversation history

### MCP Gateway
- All models work with MCP tool integration
- Model selection doesn't affect gateway connectivity
- Tools remain available across model switches

### Lambda Functions
- Web search and Prometheus functions work with all models
- No model-specific configuration required
- Consistent tool behavior across models

## Future Enhancements

### Planned Features
- **Automatic Model Selection**: Based on query complexity
- **Model Performance Metrics**: Response time and quality tracking
- **Custom Model Configurations**: User-defined model preferences
- **Model Usage Analytics**: Track model usage patterns

### Configuration Options
- **Per-Session Models**: Different models for different conversation types
- **Context-Aware Selection**: Automatic model switching based on topic
- **Performance Profiles**: Predefined model configurations for different use cases

---

For more information about the AWS DevOps Agent, see the [main documentation](README.md).