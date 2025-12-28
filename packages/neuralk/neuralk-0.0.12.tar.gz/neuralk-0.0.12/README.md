<div align="center">

</div>

<div align="center">

[![Neuralk SDK](https://neuralk-ai.github.io/neuralk/_images/cover.png)](https://neuralk.netlify.app)

</div>

<h3 align="center">A Tabular Machine Learning SDK for Industrial Applications</h3>

<p align="center">
  <a href="https://tinyurl.com/neuralk-doc"><strong>[API reference]</strong></a>
</p>    

## 👋 Welcome to the Neuralk SDK

The Neuralk SDK provides a simple and powerful Python interface to our services.
It lets you access our foundation models directly or through advanced, domain-specific workflows.
The SDK automatically performs essential checks on your data, including size and format validation, to ensure optimal performance and reliability.

The Neuralk SDK provides access to our AI platform with two distinct services:

**Expert Use Case** - End-to-end AI solutions with preprocessing and postprocessing adapted to our specialized models. Perfect for production-ready applications.

**NICL (Neural In-Context Learning)** - Direct inference capabilities using our advanced in-context learning models. Ideal for rapid prototyping and direct model interaction.

## ⚙️ Quick-Start Installation

Install the package from PyPI:

```bash
pip install neuralk
```

## 🔬 Development Installation

### Clone the Repository

```bash
git clone https://github.com/Neuralk-AI/neuralk
cd neuralk
```

### Create a Dedicated Environment (recommended)

Neuralk SDK has very light dependecies but we still advice to isolate it in a dedicated virtual environment (e.g., using conda or venv).

```bash
conda create -n neuralk python=3.11
conda activate neuralk
```

### Install the Package

```bash
pip install -e .
```

### Configuring the endpoint

By default, the SDK is configured to use the Neuralk-AI production endpoint. However, depending on your network setup (for example, if requests are forwarded through a proxy) you may need to redirect it to a different endpoint. This can be done with the following configuration line:

```python
from neuralk.utils._configuration import Configuration
Configuration.neuralk_endpoint = "http://localhost:40000"
```

## Examples and tutorials

* [**Neuralk-AI Classifier Workflow Example**](https://neuralk.netlify.app/docs/two_moon_classification)
  A gentle introduction to the framework and how to run your first workflow.

* [**Neuralk-AI Categorization Example**](https://neuralk.netlify.app/docs/categorization)
  A real life example of categorization on a public industrial dataset.


## Citing Neuralk

If you incorporate any part of this repository into your work, please reference it using the following citation:

```bibtex
@article{neuralk2025sdk,
         title={Neuralk: A Foundation Model for Industrial Tabular Data}, 
         author={Neuralk-AI},
         year={2025},
         publisher = {GitHub},
         howpublished = {\url{https://github.com/Neuralk-AI/Neuralk}},
}
```

# Contact

If you have any questions or wish to propose new features please feel free to open an issue or contact us at alex@neuralk-ai.com.  

For collaborations please contact us at antoine@neuralk-ai.com.  
