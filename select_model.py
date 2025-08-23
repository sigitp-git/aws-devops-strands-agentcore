#!/usr/bin/env python3
"""
Model Selector for AWS DevOps Agent
Allows easy switching between different Claude models.
"""

import sys
import os

# Add current directory to path to import agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent import AgentConfig

def main():
    """Main model selection interface."""
    print("\n🤖 AWS DevOps Agent - Model Selector")
    print("=" * 50)
    
    models = AgentConfig.list_models()
    model_keys = list(models.keys())
    
    # Show current selection
    print(f"Current Model: {models[AgentConfig.SELECTED_MODEL]}")
    print(f"Model ID: {AgentConfig.get_model_id()}")
    print()
    
    # Show available models
    print("Available Models:")
    for i, (key, description) in enumerate(models.items(), 1):
        current = " ← CURRENT" if key == AgentConfig.SELECTED_MODEL else ""
        print(f"  {i}. {description}{current}")
    
    print(f"\n  0. Keep current selection")
    
    try:
        choice = input(f"\nSelect model (0-{len(model_keys)}): ").strip()
        
        if choice == '0' or choice == '':
            print(f"✅ Keeping current model: {models[AgentConfig.SELECTED_MODEL]}")
            return
        
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(model_keys):
            selected_key = model_keys[choice_idx]
            AgentConfig.set_model(selected_key)
            print(f"\n✅ Model updated to: {models[selected_key]}")
            print(f"📝 Model ID: {AgentConfig.get_model_id()}")
            print("\n💡 Restart your agent or Streamlit app to use the new model.")
        else:
            print("❌ Invalid selection. No changes made.")
    
    except (ValueError, KeyboardInterrupt):
        print(f"\n✅ No changes made. Current model: {models[AgentConfig.SELECTED_MODEL]}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()