# OptixLog SDK

Experiment tracking for photonic simulations with automatic MPI support.

## 🚀 Quick Start

```bash
pip install optixlog
```

```python
import optixlog

# Set your API key
export OPTIX_API_KEY="proj_your_key_here"

# Start logging
with optixlog.run("my_experiment", config={"lr": 0.001}) as client:
    # Log metrics
    client.log(step=0, loss=0.5, accuracy=0.9)
    
    # Log plots (one line!)
    import matplotlib.pyplot as plt
    plt.plot([1,2,3], [1,4,9])
    client.log_matplotlib("my_plot", plt.gcf())
```

That's it! View your results at [optixlog.com](https://optixlog.com)

## 📚 Documentation

**→ [Complete API Reference](./API_REFERENCE.md)** - Every function with examples

## ✨ Key Features

- **Zero Boilerplate:** Log matplotlib plots in one line
- **Context Managers:** Clean `with` statement support
- **Input Validation:** Catches NaN/Inf and invalid data
- **Rich Output:** Colored console feedback
- **MPI Support:** Automatic detection and rank 0 logging
- **Batch Operations:** Fast parallel uploads
- **Return Values:** Get URLs and status for everything
- **Query API:** Programmatic access to runs and artifacts

## 🎯 Common Use Cases

### Log Training Metrics
```python
with optixlog.run("training") as client:
    for epoch in range(100):
        client.log(step=epoch, loss=0.5, accuracy=0.9)
```

### Log Matplotlib Plots
```python
# Old way (15+ lines of boilerplate)
plt.savefig("plot.png")
with open("plot.png", "rb") as f:
    img = PIL.Image.open(f)
    client.log_image("plot", img)
os.remove("plot.png")

# New way (one line!)
client.log_matplotlib("plot", plt.gcf())
```

### Log Field Data
```python
import numpy as np
field = np.random.rand(100, 100)
client.log_array_as_image("field", field, cmap='hot')
```

### Log Multiple Metrics
```python
metrics = [{"step": i, "loss": losses[i]} for i in range(1000)]
result = client.log_batch(metrics)  # Fast batch upload!
```

### Query Previous Runs
```python
runs = optixlog.list_runs(client, project_name="MyProject")
for run in runs:
    artifacts = optixlog.get_artifacts(client, run.run_id)
    print(f"{run.name}: {len(artifacts)} artifacts")
```

## 🔧 Installation

### From PyPI
```bash
pip install optixlog
```

### From Source
```bash
git clone https://github.com/yourusername/optixlog-sdk.git
cd optixlog-sdk
pip install -e .
```

## 🔑 Setup

1. Get your API key from [optixlog.com](https://optixlog.com)
2. Set environment variable:
```bash
export OPTIX_API_KEY="proj_your_key_here"
```

3. Optionally set default project:
```bash
export OPTIX_PROJECT="MyProject"
```

## 📖 Full Documentation

→ **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete reference with:
- All functions and parameters
- Return types and error handling
- Real-world examples
- Best practices
- MPI support details

## 🎓 Examples

See [DEMO.py](./DEMO.py) for a comprehensive demonstration of all features.

## 🛠️ Requirements

- Python 3.8+
- requests
- numpy
- matplotlib
- pillow
- rich

## 🚀 What's New in v0.1.0

- ✨ **One-line plot logging:** `log_matplotlib()`
- ✨ **Context managers:** `with optixlog.run()`
- ✨ **Helper functions:** `log_plot()`, `log_array_as_image()`
- ✨ **Input validation:** Catches NaN/Inf automatically
- ✨ **Return values:** Every method returns status + URL
- ✨ **Batch operations:** `log_batch()`, `log_images_batch()`
- ✨ **Query API:** List and download runs programmatically
- ✨ **Rich output:** Beautiful colored console feedback

See [CHANGELOG.md](./CHANGELOG.md) for full details.

## 🤝 CLI Integration

The OptixLog CLI is included with the SDK! Install it with:

```bash
pip install optixlog
```

Then use the CLI commands:

```bash
optixlog init  # Initialize configuration
optixlog login  # Set your API key
optixlog add-logging script.py  # Auto-instrument code
optixlog runs  # List runs
optixlog projects  # List projects
optixlog metrics <run_id>  # View metrics
```

Both `optixlog` and `ox` commands are available (they're aliases).

See the [CLI Documentation](https://docs.optixlog.com/cli) for complete command reference.

## 📊 Dashboard

View all your experiments at [optixlog.com](https://optixlog.com)

## 📝 License

MIT License - see LICENSE file for details

## 🐛 Support

- Documentation: [API_REFERENCE.md](./API_REFERENCE.md)
- Demo: [DEMO.py](./DEMO.py)
- Issues: Report bugs or request features

---

**Version:** 0.1.0  
Made with ⚡ for photonic simulation tracking
