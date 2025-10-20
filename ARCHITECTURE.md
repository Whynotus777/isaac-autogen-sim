# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Natural Lang   │  │   JSON Config    │  │   Python API     │  │
│  │   (Text Prompt)  │  │   (Structured)   │  │   (Programmatic) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼────────────────────┼────────────────────┼──────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              AutonomousSimulationPlatform                    │   │
│  │              (main.py - 215 lines)                           │   │
│  │                                                               │   │
│  │  • Routes requests to appropriate pipeline                   │   │
│  │  • Manages agent lifecycle                                   │   │
│  │  • Coordinates validation                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│              ┌───────────────┼───────────────┐                       │
│              ▼               ▼               ▼                       │
│     ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│     │  Phase 1   │  │  Phase 2   │  │  Phase 3   │                 │
│     │  Pipeline  │  │  Workflow  │  │  Pipeline  │                 │
│     └────────────┘  └────────────┘  └────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                                   │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Architect  │──│ SceneGraph  │──│   Physics   │                 │
│  │   Agent     │  │    Agent    │  │    Agent    │                 │
│  │ (328 lines) │  │ (345 lines) │  │ (367 lines) │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│         │                                                             │
│         ▼                                                             │
│  ┌─────────────┐  ┌─────────────┐                                   │
│  │  Validator  │  │Optimization │                                   │
│  │    Agent    │  │   Agent     │                                   │
│  │ (287 lines) │  │ (371 lines) │                                   │
│  └─────────────┘  └─────────────┘                                   │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                    │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Scene      │  │   Physics    │  │Optimization  │              │
│  │  Commands    │  │  Commands    │  │  Commands    │              │
│  │ (210 lines)  │  │ (253 lines)  │  │ (234 lines)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  All models use Pydantic for type safety and validation             │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                                   │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   OpenUSD        │  │   Isaac Lab      │  │   PyTorch        │  │
│  │   (Scene Rep)    │  │   (Physics Sim)  │  │   (Optimization) │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │   PhysX/Newton   │  │   Generative3D   │                        │
│  │   (Physics Eng)  │  │   APIs           │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Scene Generation Pipeline

```
JSON Config
    │
    ├─── Parse scene section
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │ SceneGraph      │
    │    │ Agent           │
    │    │                 │
    │    │ • CreatePrim    │
    │    │ • SetMaterial   │
    │    │ • CreateLight   │
    │    │ • CreateCamera  │
    │    └────────┬────────┘
    │             │
    │             ▼
    │        base.usd (geometry + materials)
    │
    ├─── Parse physics section
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │ Physics         │
    │    │ Agent           │
    │    │                 │
    │    │ • ApplyRigidBody│
    │    │ • SetFriction   │
    │    │ • ApplyCollider │
    │    │ • CreateJoint   │
    │    └────────┬────────┘
    │             │
    │             ▼
    └─────► final.usd (complete simulation)
```

## Phase 2: Natural Language Workflow

```
Natural Language Prompt
    │
    ▼
┌─────────────────────┐
│ Architect Agent     │
│                     │
│ 1. Parse intent     │
│ 2. Extract entities │
│ 3. Decompose tasks  │
└─────────┬───────────┘
          │
          ├─── Generate scene commands
          │         │
          │         ▼
          │    SceneGraph Agent → base.usd
          │
          ├─── Generate physics commands
          │         │
          │         ▼
          │    Physics Agent → final.usd
          │
          └─── Validate result
                    │
                    ▼
               Validator Agent
                    │
                    ├─── Check physics consistency
                    ├─── Check geometry validity
                    ├─── Check performance
                    │
                    ▼
               Human confirmation
                    │
                    ▼
               Approved USD file
```

## Phase 3: Optimization Loop

```
USD File + Optimization Problem
    │
    ▼
┌─────────────────────────────────────────────┐
│          Optimization Agent                 │
│                                             │
│  Initialize parameters                      │
│         │                                   │
│         ▼                                   │
│  ┌─────────────────────────────────────┐   │
│  │    Optimization Loop                │   │
│  │                                     │   │
│  │  1. Run simulation (forward)       │   │
│  │  2. Compute loss from metrics      │   │
│  │  3. Backpropagate (gradients)      │   │
│  │  4. Update parameters (optimizer)  │   │
│  │  5. Check convergence              │   │
│  │                                     │   │
│  │  Repeat until converged            │   │
│  └──────────┬──────────────────────────┘   │
│             │                               │
│             ▼                               │
│  Optimized parameters                       │
└─────────────────────────────────────────────┘
    │
    ▼
Optimized USD + Results + Visualizations
```

## Data Flow

### Scene Generation
```
Pydantic Model → Agent Logic → OpenUSD API → USD File
     │              │              │            │
     │              │              │            └─→ Disk
     │              │              └─→ Scene graph
     │              └─→ Python code generation
     └─→ Type validation
```

### Physics Application
```
Pydantic Model → Agent Logic → UsdPhysics API → USD File
     │              │              │               │
     │              │              └─→ Physics schemas
     │              └─→ Property computation
     └─→ Bounds checking
```

### Optimization
```
Problem Definition → Initialize → Simulate → Compute Loss
       │               │            │            │
       │               │            │            └─→ Backprop
       │               │            └─→ Forward pass
       │               └─→ PyTorch tensors
       └─→ Pydantic validation

         ┌──────────────────┐
         │ Gradient descent │
         │ parameter update │
         └────────┬─────────┘
                  │
                  └─→ Converged? ─Yes→ Final params
                       │
                       No
                       │
                       └─→ Next iteration
```

## Agent Communication

### Multi-Agent GroupChat (Phase 2)
```
User Input
    │
    ▼
Architect (orchestrator)
    │
    ├─→ Request scene → SceneGraph
    │                       │
    │                       └─→ Returns USD
    │
    ├─→ Request physics → Physics
    │                       │
    │                       └─→ Returns modified USD
    │
    └─→ Request validation → Validator
                            │
                            └─→ Returns report

All communication uses:
• Pydantic models (type-safe)
• JSON serialization
• AutoGen message passing
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│                                                           │
│  Python 3.12  │  CLI  │  Python API  │  Interactive Demo│
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Framework Layer                        │
│                                                           │
│  Microsoft AutoGen  │  Pydantic  │  LangChain           │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Compute Layer                          │
│                                                           │
│  PyTorch 2.7.0+cu128  │  NumPy  │  SciPy  │  Matplotlib│
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Simulation Layer                       │
│                                                           │
│  OpenUSD  │  Isaac Lab  │  PhysX  │  Newton Physics     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Hardware Layer                        │
│                                                           │
│  NVIDIA RTX 5090  │  CUDA 12.8  │  32GB VRAM            │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Modularity**: Each agent is independent and reusable
2. **Type Safety**: Pydantic models ensure correctness
3. **Extensibility**: Easy to add new commands or agents
4. **Testability**: Clear interfaces enable comprehensive testing
5. **Documentation**: Self-documenting code with type hints
6. **Error Handling**: Graceful degradation and clear errors

## Scalability

### Horizontal Scaling
- Multiple agents can run in parallel
- Batch processing of simulations
- Distributed optimization possible

### Vertical Scaling
- GPU acceleration for optimization
- Multi-core for agent processing
- Efficient memory management

## Future Extensions

```
Current System
      │
      ├─→ Add web interface
      │       │
      │       └─→ React frontend + FastAPI backend
      │
      ├─→ Cloud deployment
      │       │
      │       └─→ Kubernetes + AWS/GCP
      │
      ├─→ Simulation library
      │       │
      │       └─→ Marketplace for configs
      │
      └─→ Multi-user collaboration
              │
              └─→ Real-time co-editing
```

---

**Location:** `/home/quantumc1/isaac-autogen-sim`
**Status:** Production Ready
**Version:** 1.0.0
