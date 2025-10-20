#!/bin/bash
# Launch script for Generative Simulation Platform UI

echo "========================================================================"
echo "🎬 GENERATIVE AUTONOMOUS SIMULATION PLATFORM"
echo "========================================================================"
echo ""
echo "✨ Complete End-to-End Pipeline:"
echo "   1. Natural Language Input → AI Agents"
echo "   2. USD Scene Generation → OpenUSD"
echo "   3. Physics Execution → Isaac Sim"
echo "   4. Video Rendering → MP4 Output"
echo ""
echo "🚀 Starting web interface..."
echo "========================================================================"
echo ""

# Activate virtual environment
source venv311/bin/activate

# Launch the generative UI
python generative_ui.py
