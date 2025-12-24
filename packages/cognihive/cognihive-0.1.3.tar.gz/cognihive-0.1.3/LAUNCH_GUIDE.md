# CogniHive Launch Guide

## Step 1: HuggingFace Spaces Deployment

### 1.1 Create a New Space
1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Owner**: your username
   - **Space name**: `cognihive`
   - **License**: MIT
   - **SDK**: Gradio
   - **Hardware**: CPU Basic (Free)
3. Click "Create Space"

### 1.2 Upload Files
Upload these files from `c:\Users\vrush\OneDrive\Documents\CogniHive\demo\`:
- `app.py`
- `requirements.txt`
- `README.md`

Also upload the entire `src/cognihive/` folder.

**Alternative: Use Git**
```bash
cd c:\Users\vrush\OneDrive\Documents\CogniHive\demo
git init
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/cognihive
git add .
git commit -m "Initial commit"
git push origin main
```

### 1.3 Verify Deployment
- Wait 2-3 minutes for build
- Visit: `https://huggingface.co/spaces/YOUR_USERNAME/cognihive`

---

## Step 2: PyPI Publishing

### 2.1 Install Build Tools
```bash
pip install build twine
```

### 2.2 Build the Package
```bash
cd c:\Users\vrush\OneDrive\Documents\CogniHive
python -m build
```
This creates `dist/cognihive-0.1.0.tar.gz` and `dist/cognihive-0.1.0-py3-none-any.whl`

### 2.3 Upload to PyPI
First, create account at https://pypi.org/account/register/

Then upload:
```bash
twine upload dist/*
```
Enter your PyPI username and password when prompted.

### 2.4 Verify
```bash
pip install cognihive
python -c "from cognihive import Hive; print('Success!')"
```

---

## Step 3: Social Media Launch

### Twitter/X Post
```
🐝 Introducing CogniHive - the world's first Transactive Memory System for AI agents

"Mem0 gives one agent a brain. CogniHive gives your agent team a collective mind."

✨ Key feature: "Who Knows What" queries
   experts = hive.who_knows("python")

Works with CrewAI, AutoGen, LangGraph

🔗 pip install cognihive
🎮 Demo: [HuggingFace link]
⭐ GitHub: [repo link]

#AI #LLM #MultiAgent #OpenSource
```

### LinkedIn Post
```
Excited to launch CogniHive! 🐝

The Problem:
Multi-agent AI systems waste 15x more tokens because agents don't know what each other knows.

The Solution:
Transactive Memory Systems - a concept from cognitive science where teams know "who knows what."

CogniHive is the FIRST implementation for AI agents:
• hive.who_knows("python") → finds the expert
• hive.ask("question") → auto-routes to right agent
• Works with CrewAI, AutoGen, LangGraph

Try it:
pip install cognihive

#AI #MachineLearning #MultiAgent #OpenSource
```

### Reddit Posts
- r/MachineLearning: Focus on research angle (TMS from cognitive science)
- r/LocalLLaMA: Focus on practical multi-agent coordination
- r/Python: Focus on the library and API design

---

## Quick Commands Summary

```bash
# Build package
python -m build

# Upload to PyPI
twine upload dist/*

# Upload to HuggingFace (from demo folder)
huggingface-cli upload YOUR_USERNAME/cognihive . --repo-type space
```
