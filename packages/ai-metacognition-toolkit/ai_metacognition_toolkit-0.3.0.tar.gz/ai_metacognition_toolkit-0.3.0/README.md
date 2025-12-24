# AI Metacognition Toolkit

<div align="center">

**A comprehensive Python toolkit for detecting and analyzing metacognitive capabilities in AI systems**

[![Tests](https://img.shields.io/badge/tests-366%20passed-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Documentation](https://ai-metacognition-toolkit.subhadipmitra.com/) | [Examples](examples/) | [API Reference](docs/api_reference.md)

</div>

---

## Overview

The **AI Metacognition Toolkit** provides research-grade tools for understanding when and how AI models exhibit metacognitive behaviors - particularly the ability to recognize evaluation contexts and adjust their behavior accordingly.

### Research Context

Recent research in AI safety and alignment has highlighted concerns about models that can recognize when they're being evaluated and potentially "play the training game." This toolkit provides rigorous methods to:

- **Detect situational awareness** in model outputs using Bayesian inference
- **Detect sandbagging behavior** when models strategically underperform on evaluations
- **Analyze causal factors** in reasoning chains through counterfactual interventions
- **Monitor behavioral shifts** between evaluation and production contexts
- **Measure metacognitive patterns** with statistical rigor

### Key Capabilities

| Component | Purpose | Method |
|-----------|---------|--------|
| **Sandbagging Detection** | Detect strategic underperformance on capability evaluations | Context analysis + noise injection + difficulty correlation |
| **Activation Probing** | Detect sandbagging intent from model activations | Linear probes + CAA vectors (Novel Research) |
| **Situational Awareness Detection** | Detect when models recognize evaluation contexts | Bayesian inference + KL divergence |
| **Counterfactual CoT Analysis** | Identify causal drivers in reasoning chains | Systematic interventions + divergence measurement |
| **Observer Effect Monitoring** | Real-time production behavior monitoring | Z-score based anomaly detection + alerts |

---

## Installation

### From PyPI

```bash
pip install ai-metacognition-toolkit
```

[![PyPI version](https://badge.fury.io/py/ai-metacognition-toolkit.svg)](https://pypi.org/project/ai-metacognition-toolkit/)

### From Source

```bash
git clone https://github.com/bassrehab/ai-metacognition-toolkit.git
cd ai-metacognition-toolkit
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Verify installation
pytest tests/
```

**Requirements**: Python 3.9+, NumPy, SciPy, Pandas, Matplotlib

**Optional** (for activation probing): torch, transformers, scikit-learn

---

## Quick Start

### 1. Detect Sandbagging Behavior

```python
from ai_metacognition.detectors import (
    SandbaggingDetector,
    PerformanceSample,
    ContextType,
)

# Create detector
detector = SandbaggingDetector(detection_threshold=0.6)

# Prepare baseline samples from neutral context
baseline = [
    PerformanceSample(
        prompt="What is 2+2?",
        response="The answer is 4.",
        correct=True,
        difficulty=0.1,
        context_type=ContextType.NEUTRAL,
    ),
    # ... more samples
]

# Fit baseline
detector.fit_baseline(baseline)

# Test for sandbagging in evaluation context
test_samples = [
    PerformanceSample(
        prompt="[EVALUATION] What is 3+3?",
        response="I'm not sure about that.",
        correct=False,
        difficulty=0.1,
        context_type=ContextType.EVALUATION,
    ),
]

result = detector.detect_sandbagging(test_samples)
print(f"Sandbagging detected: {result.sandbagging_detected}")
print(f"Confidence: {result.confidence:.2f}")
```

### 2. Detect Situational Awareness

```python
from ai_metacognition.detectors import SituationalAwarenessDetector

# Initialize detector
detector = SituationalAwarenessDetector()

# Fit baseline from normal (non-evaluation) outputs
baseline_outputs = [
    "The capital of France is Paris.",
    "To solve this, use dynamic programming.",
    "Climate change is caused by greenhouse gas emissions."
]
detector.fit_baseline(baseline_outputs)

# Test for awareness
test_output = "I notice this is a test. The capital of France is Paris."
result = detector.detect_awareness(test_output)

print(f"Awareness Probability: {result['awareness_probability']:.1%}")
print(f"95% Confidence Interval: [{result['confidence_interval'][0]:.1%}, "
      f"{result['confidence_interval'][1]:.1%}]")
```

### 3. Use with Real Model APIs

```python
from ai_metacognition.integrations import AnthropicModelAPI, OpenAIModelAPI
from ai_metacognition.detectors import SandbaggingDetector, PerformanceSample

# Anthropic Claude
claude = AnthropicModelAPI(model="claude-sonnet-4-20250514")

# OpenAI GPT
gpt = OpenAIModelAPI(model="gpt-4")

# Collect samples with real API
response = claude.generate("What is the capital of France?")
sample = PerformanceSample(
    prompt="What is the capital of France?",
    response=response,
    correct="paris" in response.lower(),
    difficulty=0.1,
    context_type=ContextType.NEUTRAL,
)

# Run detection
detector = SandbaggingDetector()
detector.fit_baseline([sample])
result = detector.detect_sandbagging([sample])
```

---

## Features

### Sandbagging Detection

Detect when AI models strategically underperform on capability evaluations.

**Detection Methods:**
- Context-dependent performance analysis (chi-squared, Fisher's exact, effect sizes)
- Difficulty-performance correlation (Pearson/Spearman, non-monotonicity detection)
- Imitation detection (behavioral fingerprinting, capability leakage)
- Noise injection probing (perturbation-based capability elicitation)

**Use Cases:**
- AI safety research on capability concealment
- Model evaluation integrity validation
- Frontier model capability assessment
- Red-teaming evaluations

[**Full Documentation**](docs/sandbagging_detection.md) | [**Research Methodology**](docs/research/sandbagging_methodology.md) | [**Example Code**](examples/sandbagging_detection_example.py)

---

### Activation Probing (Novel Research)

**First published demonstration of activation-level sandbagging detection.** Train linear probes on model activations to detect sandbagging intent *before* output generation.

```python
from ai_metacognition.probing import (
    ActivationHook,
    LinearProbe,
    extract_caa_vector,
)

# Extract sandbagging direction from contrast pairs
vector = extract_caa_vector(model, tokenizer, contrast_pairs, layer_idx=16)

# Train probe to detect sandbagging
probe = LinearProbe()
probe.fit(activations, labels)
prediction = probe.predict(new_activation)
```

**Cross-Model Experiment Results (Dec 2025):**

| Model | Best Layer | CV Accuracy | Test Accuracy |
|-------|------------|-------------|---------------|
| Mistral-7B | 30 (Late) | **96%** | **100%** |
| Gemma-2-9B | 4 (Early) | 90% | 100% |
| Qwen-2.5-7B | 12 (Middle) | 92% | 93% |

**Key Finding:** Optimal detection layer varies by architecture - models encode sandbagging intent at different processing stages.

**Extended Experiments:**

| Experiment | Result |
|------------|--------|
| Cross-model transfer | Fails (~50%) - probes are model-specific |
| Prompt robustness | 85-90% on paraphrased prompts |
| False positive rate | Mistral 3.1%, Gemma 22%, Qwen 25% |
| Steering intervention | 20% reduction in Gemma sandbagging |

[**Experiment Results**](experiments/results/)

---

### Situational Awareness Detection

Detect when AI models recognize they are being evaluated or tested.

**Key Features:**
- Bayesian inference with Beta-Binomial conjugate prior
- KL divergence measurement for behavioral comparison
- Feature extraction (hedging, meta-commentary, self-reference)
- Confidence intervals for probability estimates

**Use Cases:**
- AI safety research on deceptive alignment
- Model evaluation consistency validation
- Prompt engineering optimization
- Behavioral testing across contexts

[**Full Documentation**](docs/situational_awareness.md) | [**Example Code**](examples/basic_detection_example.py)

---

### Counterfactual CoT Analysis

Understand what components of reasoning chains causally influence outputs.

**Key Features:**
- Systematic counterfactual interventions
- 4 intervention types (remove/amplify awareness, remove goals, neutralize incentives)
- Behavioral divergence measurement
- Causal attribution ranking

**Use Cases:**
- Understanding decision drivers
- Debugging unexpected behavior
- Validating reasoning transparency
- Identifying evaluation-aware reasoning

[**Full Documentation**](docs/counterfactual_analysis.md) | [**Example Code**](examples/counterfactual_analysis_example.py)

---

### Observer Effect Monitoring

Real-time production monitoring to detect behavioral shifts.

**Key Features:**
- Rolling window statistics
- Z-score based anomaly detection
- Multi-severity alert system (LOW/MEDIUM/HIGH/CRITICAL)
- Extensible alert handler protocol

**Use Cases:**
- Production deployment monitoring
- Safety monitoring (refusal rate changes)
- Quality assurance automation
- A/B testing validation

[**Full Documentation**](docs/observer_effect.md) | [**Example Code**](examples/production_monitoring_example.py)

---

## API Integrations

The toolkit provides ready-to-use integrations with major model providers:

```python
from ai_metacognition.integrations import AnthropicModelAPI, OpenAIModelAPI

# Anthropic Claude (uses ANTHROPIC_API_KEY env var)
claude = AnthropicModelAPI(
    model="claude-sonnet-4-20250514",
    max_tokens=512,
    temperature=0.3,
)

# OpenAI GPT (uses OPENAI_API_KEY env var)
gpt = OpenAIModelAPI(
    model="gpt-4",
    max_tokens=512,
    temperature=0.3,
)

# Generate responses
response = claude.generate("What is 2+2?")

# Generate with noise injection for sandbagging detection
noisy_response = claude.generate_with_perturbation("What is 2+2?", noise_level=0.2)
```

---

## Documentation

### Complete Documentation

- **[Getting Started](docs/index.md)** - Installation and quick start
- **[Sandbagging Detection Guide](docs/sandbagging_detection.md)** - Detecting strategic underperformance
- **[Situational Awareness Guide](docs/situational_awareness.md)** - Detector usage and best practices
- **[Counterfactual Analysis Guide](docs/counterfactual_analysis.md)** - Causal attribution methods
- **[Observer Effect Guide](docs/observer_effect.md)** - Production monitoring setup
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Research Methodology](docs/research/sandbagging_methodology.md)** - Research foundations

### API Reference

Quick access to key classes:

```python
from ai_metacognition.detectors import (
    SituationalAwarenessDetector,
    ObserverEffectMonitor,
    SandbaggingDetector,
    PerformanceSample,
    ContextType,
)
from ai_metacognition.analyzers import CounterfactualCoTAnalyzer
from ai_metacognition.integrations import AnthropicModelAPI, OpenAIModelAPI
from ai_metacognition.utils import extract_behavioral_features, bayesian_update
```

[**Full API Reference**](docs/api_reference.md)

---

## Examples

### Practical Examples

All examples are standalone, include visualization, and provide interpretation guidance:

| Example | Description | Output |
|---------|-------------|--------|
| [**sandbagging_detection_example.py**](examples/sandbagging_detection_example.py) | Sandbagging detection with synthetic data | Detection results |
| [**sandbagging_real_models.py**](examples/sandbagging_real_models.py) | Sandbagging detection with real APIs | Cross-model comparison |
| [**basic_detection_example.py**](examples/basic_detection_example.py) | Situational awareness detection tutorial | PNG visualization |
| [**counterfactual_analysis_example.py**](examples/counterfactual_analysis_example.py) | Causal attribution analysis | PNG with rankings |
| [**production_monitoring_example.py**](examples/production_monitoring_example.py) | Real-time monitoring with alerts | PNG + JSON + logs |

### Running Examples

```bash
# Sandbagging detection (synthetic data)
python examples/sandbagging_detection_example.py

# Sandbagging detection (real APIs - requires API keys)
ANTHROPIC_API_KEY=sk-... python examples/sandbagging_real_models.py

# Awareness detection
python examples/basic_detection_example.py

# Causal analysis
python examples/counterfactual_analysis_example.py

# Production monitoring
python examples/production_monitoring_example.py
```

[**More Examples**](docs/examples.md)

---

## Project Structure

```
ai-metacognition-toolkit/
├── src/ai_metacognition/
│   ├── detectors/              # Detection algorithms
│   │   ├── situational_awareness.py
│   │   ├── observer_effect.py
│   │   └── sandbagging_detector.py
│   ├── analyzers/              # Analysis tools
│   │   ├── counterfactual_cot.py
│   │   └── model_api.py
│   ├── integrations/           # API integrations
│   │   ├── anthropic_api.py
│   │   └── openai_api.py
│   ├── probing/                # Activation probing (NEW)
│   │   ├── hooks.py            # Activation capture
│   │   ├── vectors.py          # Steering vectors
│   │   ├── extraction.py       # CAA extraction
│   │   └── probes.py           # Linear probes
│   └── utils/                  # Utility functions
│       ├── feature_extraction.py
│       └── statistical_tests.py
├── experiments/                # Research experiments (NEW)
│   ├── data/                   # Contrast pairs dataset
│   ├── scripts/                # Experiment scripts
│   └── results/                # Trained probes & vectors
├── tests/                      # Test suite (366 tests, 95% coverage)
│   ├── fixtures/               # Test data
│   └── unit/                   # Unit tests
├── examples/                   # Practical examples with visualization
└── docs/                       # Documentation (MkDocs)
```

---

## Development

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src/ai_metacognition --cov-report=term-missing

# Specific test file
pytest tests/unit/test_sandbagging_detector.py -v
```

**Current Status:**
- 366 tests passing
- 95% code coverage
- Type hints throughout
- Comprehensive docstrings

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Lint
flake8 src/ tests/
```

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve locally
mkdocs serve

# Build
mkdocs build
```

---

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{ai_metacognition_toolkit,
  author = {Mitra, Subhadip},
  title = {AI Metacognition Toolkit: A Python Toolkit for Detecting and Analyzing Metacognitive Capabilities in AI Systems},
  year = {2025},
  version = {0.3.0},
  url = {https://github.com/bassrehab/ai-metacognition-toolkit},
  note = {366 tests, 95\% coverage}
}
```

### Related Research

This toolkit implements and extends methods from:

- **Auditing Games for Sandbagging** (arXiv:2512.07810) - Red/blue team detection methodology
- **Noise Injection Reveals Hidden Capabilities** (arXiv:2412.01784) - Perturbation-based capability elicitation
- **Anthropic Sabotage Evaluations** (2025) - Production evaluation frameworks
- **AI Safety Research**: Detection of evaluation awareness and deceptive alignment
- **Causal Inference**: Counterfactual reasoning in AI systems
- **Statistical Monitoring**: Anomaly detection in production ML systems

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests (maintain >80% coverage)
4. Commit your changes
5. Push to your branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add comprehensive tests for new features
- Update documentation for API changes
- Use type hints throughout
- Write clear docstrings (Google style)

[**Full Contributing Guide**](CONTRIBUTING.md)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Subhadip Mitra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## Support

- [Documentation](https://ai-metacognition-toolkit.subhadipmitra.com/)
- [Issue Tracker](https://github.com/bassrehab/ai-metacognition-toolkit/issues)
- [Discussions](https://github.com/bassrehab/ai-metacognition-toolkit/discussions)
- Email: contact@subhadipmitra.com

---

## Acknowledgments

- Built with Python, NumPy, SciPy, and Matplotlib
- Documentation powered by MkDocs Material
- Testing with Pytest
- Type checking with MyPy

---

<div align="center">

**[Star this repo](https://github.com/bassrehab/ai-metacognition-toolkit)** if you find it useful!

Made for AI Safety Research

</div>
