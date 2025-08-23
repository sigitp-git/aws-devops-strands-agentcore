#!/usr/bin/env python3
"""
Streamlit Frontend for AWS DevOps Agent
A user-friendly web interface for interacting with the deployed DevOps Agent.
"""

import streamlit as st
import boto3
import json
import os
import sys
import time
import uuid
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_ssm_parameter
from agent import AgentConfig

# Set default AWS region if not already configured
if not os.environ.get('AWS_DEFAULT_REGION'):
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

class StreamlitAgentInterface:
    """Streamlit interface for the DevOps Agent."""
    
    def __init__(self):
        self.region = "us-east-1"
        self.client = boto3.client('bedrock-agentcore', region_name=self.region)
        
    def get_agent_runtime_arn(self):
        """Get the agent runtime ARN from SSM."""
        try:
            arn = get_ssm_parameter("/app/devopsagent/agentcore/runtime_arn")
            return arn
        except Exception as e:
            st.error(f"Failed to get agent runtime ARN: {e}")
            return None
    
    def invoke_agent(self, prompt, session_id=None):
        """Invoke the agent with a prompt."""
        try:
            agent_runtime_arn = self.get_agent_runtime_arn()
            if not agent_runtime_arn:
                return None
            
            if not session_id:
                session_id = f"streamlit-{uuid.uuid4()}-{int(time.time())}"
            
            # Prepare payload
            payload = {
                "prompt": prompt,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Show loading spinner
            with st.spinner('🤖 DevOps Agent is thinking...'):
                # Invoke the agent
                response = self.client.invoke_agent_runtime(
                    agentRuntimeArn=agent_runtime_arn,
                    runtimeSessionId=session_id,
                    payload=json.dumps(payload).encode('utf-8'),
                    qualifier="DEFAULT"
                )
                
                # Parse response
                response_body = response['response'].read()
                response_data = json.loads(response_body)
                
                return response_data
                
        except Exception as e:
            st.error(f"❌ Agent invocation failed: {e}")
            return None

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="AWS DevOps Agent",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Display MODEL_ID information
    current_model_id = AgentConfig.get_model_id()
    print(f"🌐 Streamlit App - Backend MODEL_ID: {current_model_id}")
    print(f"📝 Model Description: {AgentConfig.list_models()[AgentConfig.SELECTED_MODEL]}")
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FF9900;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .agent-message {
        background-color: #F3E5F5;
        border-left: 4px solid #9C27B0;
    }
    .sidebar-content {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🚀 AWS DevOps Agent</h1>', unsafe_allow_html=True)
    st.markdown("**Your intelligent AWS DevOps assistant powered by Amazon Bedrock**")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit-{uuid.uuid4()}-{int(time.time())}"
    if 'agent_interface' not in st.session_state:
        st.session_state.agent_interface = StreamlitAgentInterface()
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Agent Controls")
        
        # Session information
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader("📊 Session Info")
        st.text(f"Session ID: {st.session_state.session_id[:20]}...")
        st.text(f"Region: us-east-1")
        st.text(f"Messages: {len(st.session_state.messages)}")
        current_model_id = AgentConfig.get_model_id()
        st.text(f"Model: {current_model_id.split('.')[-1]}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Model selector
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader("🤖 Model Selection")
        
        # Initialize model selection in session state
        if 'selected_model_key' not in st.session_state:
            st.session_state.selected_model_key = AgentConfig.SELECTED_MODEL
        
        # Model selector dropdown
        model_options = AgentConfig.list_models()
        selected_model = st.selectbox(
            "Choose Claude Model:",
            options=list(model_options.keys()),
            index=list(model_options.keys()).index(st.session_state.selected_model_key),
            format_func=lambda x: model_options[x],
            key="model_selector"
        )
        
        # Update model if changed
        if selected_model != st.session_state.selected_model_key:
            st.session_state.selected_model_key = selected_model
            AgentConfig.set_model(selected_model)
            st.success(f"✅ Model updated to: {model_options[selected_model]}")
            st.rerun()
        
        # Display current model info
        st.info(f"🔧 Current: {model_options[AgentConfig.SELECTED_MODEL]}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick actions
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Actions")
        
        if st.button("🔄 New Session"):
            st.session_state.messages = []
            st.session_state.session_id = f"streamlit-{uuid.uuid4()}-{int(time.time())}"
            st.rerun()
        
        if st.button("📋 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Example prompts
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader("💡 Example Prompts")
        
        example_prompts = [
            "What are AWS best practices for EC2 security?",
            "How do I set up a CI/CD pipeline with CodePipeline?",
            "Help me troubleshoot a CloudFormation stack error",
            "What's the difference between ALB and NLB?",
            "How do I optimize AWS costs for my infrastructure?",
            "Explain AWS Lambda cold starts and how to minimize them"
        ]
        
        for prompt in example_prompts:
            if st.button(f"📝 {prompt[:30]}...", key=f"example_{hash(prompt)}"):
                st.session_state.example_prompt = prompt
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Agent capabilities
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.subheader("🎯 Agent Capabilities")
        st.markdown("""
        - **AWS Services & Infrastructure**
        - **DevOps Best Practices**
        - **CI/CD Pipeline Design**
        - **Infrastructure as Code**
        - **Security & Compliance**
        - **Cost Optimization**
        - **Troubleshooting & Debugging**
        - **Performance Optimization**
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main chat interface
    st.header("💬 Chat with DevOps Agent")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'''
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {message["content"]}
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="chat-message agent-message">
                <strong>🤖 DevOps Agent:</strong><br>
                {message["content"]}
            </div>
            ''', unsafe_allow_html=True)
    
    # Handle example prompt selection
    if hasattr(st.session_state, 'example_prompt'):
        user_input = st.session_state.example_prompt
        delattr(st.session_state, 'example_prompt')
    else:
        user_input = None
    
    # Chat input
    if not user_input:
        user_input = st.chat_input("Ask me anything about AWS DevOps...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message immediately
        st.markdown(f'''
        <div class="chat-message user-message">
            <strong>👤 You:</strong><br>
            {user_input}
        </div>
        ''', unsafe_allow_html=True)
        
        # Get agent response
        response = st.session_state.agent_interface.invoke_agent(
            user_input, 
            st.session_state.session_id
        )
        
        if response:
            if "error" in response:
                agent_message = f"❌ Error: {response['error']}"
            else:
                agent_message = response.get('message', 'No response received')
                
                # Show additional info if available
                if 'tools_used' in response and response['tools_used']:
                    agent_message += f"\n\n🔧 **Tools used:** {', '.join(response['tools_used'])}"
                
                if 'timestamp' in response:
                    agent_message += f"\n\n⏰ **Response time:** {response['timestamp']}"
        else:
            agent_message = "❌ Failed to get response from the agent. Please try again."
        
        # Add agent response to chat history
        st.session_state.messages.append({"role": "agent", "content": agent_message})
        
        # Display agent message
        st.markdown(f'''
        <div class="chat-message agent-message">
            <strong>🤖 DevOps Agent:</strong><br>
            {agent_message}
        </div>
        ''', unsafe_allow_html=True)
        
        # Rerun to update the interface
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>🚀 <strong>AWS DevOps Agent</strong> | Powered by Amazon Bedrock & AgentCore Runtime</p>
        <p>Built with ❤️ using Streamlit | <a href="https://github.com/sigitp-git/aws-devops-strands-agentcore" target="_blank">View on GitHub</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()