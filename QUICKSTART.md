# Quick Start Guide

Get up and running with the Autonomous Simulation Design Platform in minutes!

## Prerequisites

- Python 3.12 (current) or Python 3.11 (for full Isaac Sim support)
- NVIDIA GPU with CUDA 12.8+ (for GPU acceleration)
- Git

## Installation (5 minutes)

### 1. Clone and Setup

```bash
cd /home/quantumc1/isaac-autogen-sim
source venv/bin/activate  # Virtual environment already created
```

### 2. Install Dependencies

```bash
# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Minimum required in `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

## Quick Test (30 seconds)

### Run the Demo

```bash
# Interactive demo menu
python demo.py

# Or run specific phases:
python demo.py --phase 3  # Optimization demo (works without Isaac Sim)
```

### Run Examples

```bash
# Example 1: Generate from natural language
python main.py --prompt "A ball rolling down a ramp"

# Example 2: Use configuration file
python main.py --config examples/falling_block.json

# Example 3: Run built-in example
python main.py --example
```

## What Works Right Now

✅ **Without Isaac Sim** (Python 3.12 - Current Setup):
- Natural language → Simulation configuration
- All agent coordination
- Optimization algorithms (with mock physics)
- Visualization and logging
- USD file generation (using usd-core)

⏸️ **Requires Isaac Sim** (Python 3.11):
- Actual physics simulation
- Real-time gradient computation
- Full USD scene rendering
- Isaac Lab integration

## Project Structure

```
isaac-autogen-sim/
├── agents/           # 5 AI agents (Scene, Physics, Architect, Validator, Optimization)
├── models/           # Pydantic data schemas
├── pipelines/        # Phase 1-3 workflows
├── examples/         # Example configs and optimization problems
├── main.py           # Main CLI
├── demo.py           # Interactive demo
└── tests/            # Unit and integration tests
```

## Common Commands

```bash
# Run tests
pytest tests/ -v

# Count lines of code
find . -name "*.py" -not -path "./venv/*" | xargs wc -l

# Check project status
cat PROJECT_STATUS.md

# View examples
ls examples/

# See all options
python main.py --help
python demo.py --help
```

## Next Steps

### 1. Try Different Prompts

```python
# In Python
from main import AutonomousSimulationPlatform

platform = AutonomousSimulationPlatform()

# Natural language examples
platform.create_from_prompt("A pendulum swinging")
platform.create_from_prompt("Two balls colliding")
platform.create_from_prompt("A robot arm stacking blocks")
```

### 2. Create Custom Configurations

Edit `examples/falling_block.json` or create your own:

```json
{
  "name": "my_simulation",
  "scene": {
    "scene_name": "my_scene",
    "commands": [...]
  },
  "physics": {
    "configuration_name": "my_physics",
    "commands": [...]
  }
}
```

### 3. Run Optimization

```bash
# Edit examples/optimization_throw_ball.json
# Then run:
python -c "
from pipelines.phase3_pipeline import Phase3Pipeline
from models.optimization_commands import OptimizationProblem
import json

pipeline = Phase3Pipeline()
with open('examples/optimization_throw_ball.json') as f:
    problem = OptimizationProblem(**json.load(f))

result = pipeline.run('output/test.usd', problem)
print(f'Final loss: {result.final_loss}')
"
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_models.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=models --cov=pipelines
```

## Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Issue: OpenAI API Error

```bash
# Check your .env file
cat .env | grep OPENAI_API_KEY

# Make sure the key is set correctly
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: CUDA not available

```python
# Check PyTorch CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Getting Help

- **Documentation**: See `README.md` for full docs
- **Status**: See `PROJECT_STATUS.md` for current state
- **Examples**: Check `examples/` directory
- **Issues**: If you find bugs, check the code or ask!

## Performance Tips

1. **Use GPU**: Optimization runs much faster on GPU
   ```python
   # Check device
   import torch
   print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
   ```

2. **Reduce Iterations**: For testing, lower max_iterations
   ```json
   "termination": {
     "max_iterations": 20  // Instead of 100
   }
   ```

3. **Batch Processing**: Process multiple simulations in parallel
   ```python
   from concurrent.futures import ThreadPoolExecutor

   prompts = ["sim1", "sim2", "sim3"]
   with ThreadPoolExecutor(max_workers=3) as executor:
       results = executor.map(platform.create_from_prompt, prompts)
   ```

## What's Next?

1. ✅ **Phase 1 & 2**: Fully functional
2. ✅ **Phase 3**: Implemented with mock physics
3. ⏸️ **Isaac Sim Integration**: Requires Python 3.11 setup
4. 📋 **Web Interface**: Future work
5. 📋 **Cloud Deployment**: Future work

---

**Ready to create your first simulation?**

```bash
python main.py --prompt "Create something amazing!"
```
