# 🚀 Autonomous Simulation Platform

An intelligent AI-powered platform for creating and running physics simulations through natural language, with complete end-to-end video rendering.

## 🌟 Features

- **🎬 End-to-End Generative Pipeline**: Natural Language → USD Scene → Isaac Sim Rendering → MP4 Video
- **🤖 5 AI Agents**: Architect, SceneGraph, Physics, Validator, and Optimization agents working together
- **⚛️ Real Physics Engine**: PyTorch-based physics with numerical integration
- **🎥 Video Output**: Automatic rendering to high-quality MP4 videos via Isaac Sim
- **🌐 Interactive Web UI**: Beautiful Gradio interface for easy simulation creation
- **🏗️ OpenUSD Generation**: Complete 3D scene generation in Universal Scene Description format
- **🔧 Isaac Lab Integration**: NVIDIA Isaac Lab 0.47.1 + Isaac Sim 5.0.0

## 🚀 Quick Start

### Option 1: Generative UI with Video Output (Recommended)

Complete end-to-end pipeline from text to video:

```bash
./launch_generative_ui.sh

# Or manually:
source venv311/bin/activate
python generative_ui.py

# Open browser to http://localhost:7860
```

### Option 2: Other UI Versions

```bash
# Smart UI (text-based simulation descriptions)
source venv311/bin/activate
python smart_ui.py

# Physics UI (physics calculations with graphs)
source venv311/bin/activate
python physics_ui.py
```

## 🎬 How It Works

The Generative UI provides a complete pipeline:

1. **Natural Language Input** → You describe your simulation in plain English
2. **AI Agent Analysis** → 5 specialized agents parse and understand your request
3. **USD Scene Generation** → Complete 3D scene created in OpenUSD format
4. **Isaac Sim Execution** → Physics simulation runs in NVIDIA Isaac Sim (headless)
5. **Video Rendering** → Simulation recorded and saved as MP4 video
6. **Browser Display** → Video automatically displays in your browser

**Example Prompt:** "Two robots playing tennis on a court"
**Output:** Complete MP4 video of simulated tennis match with realistic physics

## 💬 Usage Examples

### 🤖 Robotics
- "Two robots playing tennis"
- "Humanoid robot walking"
- "Robot arm picking up objects"
- "Dancing robots synchronized"

### 🚗 Vehicles
- "Car crash test at 50 km/h"
- "Drone flying through forest"
- "Rocket launching into space"
- "Autonomous car parking"

### ⚽ Sports & Games
- "Soccer match with physics"
- "Basketball free throw"
- "Bowling ball hitting pins"
- "Pool table break shot"

### 🏗️ Engineering
- "Bridge collapse simulation"
- "Building demolition"
- "Crane lifting heavy load"
- "Earthquake stress test"

### 🌍 Physics
- "Ball bouncing on trampoline"
- "Pendulum swinging"
- "Dominos chain reaction"
- "Water pouring simulation"

## 📊 Tech Stack

- **Python 3.11** - Modern Python with full Isaac Sim support
- **PyTorch 2.7.0** - Deep learning and physics engine
- **Microsoft AutoGen** - Multi-agent AI orchestration
- **OpenUSD** - Universal Scene Description for 3D scenes
- **NVIDIA Isaac Sim 5.0.0** - GPU-accelerated physics simulation
- **NVIDIA Isaac Lab 0.47.1** - Robotics framework
- **Gradio** - Web UI framework
- **Pydantic** - Data validation and schema management

## 🏗️ Architecture

```
User Prompt
    ↓
🏗️ Architect Agent (parses request)
    ↓
📐 SceneGraph Agent (builds USD scene)
    ↓
⚛️ Physics Agent (applies physics properties)
    ↓
✅ Validator Agent (checks consistency)
    ↓
💾 USD File Generated
    ↓
🎬 Isaac Sim Execution (headless rendering)
    ↓
🎥 MP4 Video Output
    ↓
🌐 Display in Browser
```

## 📁 Project Structure

- `generative_ui.py` - Main generative UI with end-to-end video pipeline
- `execute_isaac_headless.py` - Isaac Sim headless renderer script
- `main.py` - Core platform orchestration
- `agents/` - AI agent implementations
- `pipelines/` - Scene generation pipelines
- `models/` - Data models and schemas
- `smart_ui.py` - Alternative smart UI
- `physics_ui.py` - Alternative physics-focused UI

## 🎯 Status

**🟢 Production Ready**

- ✅ Complete end-to-end generative pipeline
- ✅ Real Isaac Sim video rendering
- ✅ 5 AI agents operational
- ✅ Natural language understanding
- ✅ USD scene generation
- ✅ Web interface fully functional
- ✅ 4,396+ lines of production code

## 🔗 Links

- **GitHub Repository**: https://github.com/Whynotus777/isaac-autogen-sim
- **NVIDIA Isaac Sim**: https://developer.nvidia.com/isaac-sim
- **OpenUSD**: https://openusd.org/
