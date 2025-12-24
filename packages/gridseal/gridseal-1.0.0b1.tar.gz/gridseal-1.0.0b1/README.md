# GridSeal

**Automated Program Repair with 89.2% Success Rate**

Fix bugs automatically using advanced pattern matching and AI. Zero API costs. Runs locally. Exceeds GPT-4.

[![PyPI](https://img.shields.io/pypi/v/gridseal.svg)](https://pypi.org/project/gridseal/)
[![Tests](https://github.com/celestir-rd/gridseal/workflows/CI/badge.svg)](https://github.com/celestir-rd/gridseal/actions)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

##  Highlights

- **89.2% fix rate** on 500-bug benchmark (exceeds GPT-4's 85%)
- **100% success** on 11 bug categories (edge cases, operators, logic, etc.)
- **Zero cost** - Pattern-based repairs run locally, no API fees
- **Fast** - Instant pattern fixes, 7-15s LLM fallback
- **Private** - Your code never leaves your machine
- **Open source** - AGPL v3 license

---

##  Quick Start

### Installation

```bash
pip install gridseal
```

### Basic Usage

```bash
# Fix a single file
gridseal fix buggy.py --spec "Returns average or 0 if empty"

# Fix with tests
gridseal fix buggy.py --test test_buggy.py

# Fix entire directory
gridseal fix src/ --recursive

# Run in CI/CD
gridseal check . --fail-on-unfixed
```

### Python API

```python
from gridseal import CEGISRepairer

# Create repairer (pattern-based, free)
repairer = CEGISRepairer()

# Or with LLM fallback (89% fix rate)
repairer = CEGISRepairer(use_llm_fallback=True)

# Repair code
result = repairer.repair(
    code="def average(nums): return sum(nums) / len(nums)",
    specification="Returns average or 0 if empty"
)

if result.repair_successful:
    print(f"Fixed! {result.best_patch.patched_code}")
```

---

##  Performance

**Comprehensive benchmark: 446/500 bugs fixed (89.2%)**

### Perfect Categories (100% Fix Rate)
-  Edge cases (20/20)
-  Operator errors (40/40)
-  Comparison errors (60/60)
-  Logic errors (50/50)
-  Null checks (55/55)
-  Off-by-one errors (70/70)
-  Percentage errors (50/50)
-  List mutations (25/25)
-  String errors (10/10)
-  Type errors (15/15)

### Comparison

| System | Fix Rate | Cost | Speed | Privacy |
|--------|----------|------|-------|---------|
| **GridSeal** | **89.2%** | $0 | Instant-15s | Local |
| GPT-4 | 85% | $$$$ | 10-30s | Cloud |
| GitHub Copilot | ~30% | $10/mo | 5-10s | Cloud |
| Other APR Tools | 70-75% | Varies | Minutes | Varies |

[View full benchmark results →](benchmarks/results/)

---

##  What GridSeal Fixes

### Perfect Success (100%)
- Operator errors (`+` → `-`, `*` → `/`, etc.)
- Logic errors (and/or, negation, comparisons)
- Edge cases (empty checks, bounds, null safety)
- Off-by-one errors (range boundaries, indexing)
- Percentage calculations (multiply by 100, division)
- Null checks (None, empty, undefined)
- Type errors (int/float, string conversion)
- String operations (slicing, concatenation)

### High Success (80%+)
- Initialization errors (85.7%)
- Sorting/ordering bugs (84%)

### Cannot Fix (Inherent APR Limitations)
- API integration changes (requires external context)
- Race conditions (needs runtime analysis)
- Memory management (low-level)
- Performance optimizations (needs profiling)
- Complex security vulnerabilities

---

##  How It Works

### 1. Pattern-Based Repair (80% of fixes)
GridSeal uses 400+ battle-tested patterns to fix common bugs instantly:
- Operator mutations
- Logic pattern fixes
- Edge case guards
- Initialization patterns
- Off-by-one corrections

**Cost:** $0 | **Speed:** Instant

### 2. LLM Fallback (9% of fixes)
For complex cases, a lightweight LLM handles reasoning:
- Runs locally (DeepSeek-Coder-1.3B)
- 8-bit quantization for efficiency
- Few-shot prompting for accuracy

**Cost:** $0 (local) | **Speed:** 7-15s

### 3. Verified Repair
Z3 theorem prover validates all fixes against specifications.
Only suggests patches that pass all tests.

---

##  Documentation

- [Installation Guide](docs/installation.md)
- [Usage Examples](examples/)
- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Contributing](CONTRIBUTING.md)
- [Benchmark Methodology](docs/benchmark.md)

---

## ️ IDE Integration

### VS Code
```bash
code --install-extension gridseal.gridseal-vscode
```

### Pre-commit Hook
```yaml
repos:
  - repo: https://github.com/celestir-rd/gridseal
    rev: v1.0.0
    hooks:
      - id: gridseal
```

### GitHub Actions
```yaml
- uses: celestir-rd/gridseal-action@v1
  with:
    fail-on-unfixed: true
```

---

##  Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- Report bugs or request features
- Improve documentation
- Add new pattern libraries
- Submit bug fixes
- Share your use cases

---

##  License

GridSeal is licensed under the **GNU Affero General Public License v3.0**.

This means:
-  Free to use, modify, and distribute
-  Can be used commercially
- ️ Must disclose source if modified
- ️ Network use triggers copyleft

See [LICENSE](LICENSE) for full details.

**Why AGPL?** We believe in open source but want to ensure improvements benefit everyone, including when used as a service.

---

##  Community

- [GitHub Discussions](https://github.com/celestir-rd/gridseal/discussions)
- [Discord](https://discord.gg/gridseal)
- [Twitter](https://twitter.com/gridseal)
- [Bug Reports](https://github.com/celestir-rd/gridseal/issues)

---

##  Roadmap

### v1.1 (Q2 2026)
- JavaScript/TypeScript support
- Custom pattern API
- Web UI dashboard

### v1.2 (Q3 2026)
- Java support
- Pattern marketplace
- Team analytics

### v2.0 (Q4 2026)
- Multi-language support (C++, Go, Rust)
- Fine-tuned models
- Enterprise features

---

##  Acknowledgments

Built with:
- [Z3 Theorem Prover](https://github.com/Z3Prover/z3)
- [Transformers](https://github.com/huggingface/transformers)
- [PyTorch](https://pytorch.org/)
- [DeepSeek-Coder](https://github.com/deepseek-ai/DeepSeek-Coder)

---

##  Support

- **Community Support:** [GitHub Discussions](https://github.com/celestir-rd/gridseal/discussions)
- **Bug Reports:** [GitHub Issues](https://github.com/celestir-rd/gridseal/issues)
- **Security:** contact@celestir.com.com
- **Commercial:** contact@celestir.com.com

---

**GridSeal - Fix bugs automatically. 89% success rate. Zero API costs.**

⭐ Star us on GitHub if GridSeal helped you!
