# VoiceStudio

<div align="center">

**Your Complete Voice Adaptation Workspace**

[![PyPI version](https://badge.fury.io/py/voicestudio.svg)](https://badge.fury.io/py/voicestudio)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://img.shields.io/badge/docs-passing-brightgreen.svg)](https://latentforge.github.io/VoiceStudio)

[**Installation**](#installation) | [**Quick Start**](#quick-start) | [**Documentation**](https://latentforge.github.io/VoiceStudio) | [**Papers**](#publications)

</div>

---

## 🎯 Overview

VoiceStudio is a unified toolkit for **text-style prompted speech synthesis**, enabling instant voice adaptation and editing through natural language descriptions. Built on cutting-edge research in voice style prompting, LoRA adaptation, and language-audio models.

**Key Features:**
- 🎨 **Text-Style Prompting**: Control voice characteristics with natural language
- ⚡ **Instant Adaptation**: Real-time LoRA generation for any TTS model
- ✂️ **Voice Editing**: Modify existing voices with simple instructions
- 🔧 **Architecture Agnostic**: Works with multiple TTS architectures
- 🚀 **Production Ready**: Optimized for both research and deployment

---

## 🆕 What's New

**v0.1.0** (2025)
- 🔍 Speaker consistency analysis tools
- 🎨 BOS token P-tuning
- 📊 Attention visualization

---

## 🚀 Installation

### From PyPI (Recommended)

```bash
uv add voicestudio[all]
```

### From Source

```bash
uv add git+https://github.com/LatentForge/voicestudio.git
```

### Requirements

- Python 3.8+
- PyTorch 2.0+
- CUDA 11.8+ (for GPU acceleration)

---

## 📚 Advanced Usage

### Custom TTS Model Integration

VoiceStudio supports any TTS model through a simple adapter interface:

```python
from voicestudio import TTSAdapter, LoRAGenerator

# Wrap your TTS model
class MyTTSAdapter(TTSAdapter):
    def __init__(self, model):
        self.model = model
    
    def get_lora_target_modules(self):
        return ["attention.q_proj", "attention.v_proj"]
    
    def forward(self, text, lora_weights=None):
        if lora_weights:
            self.apply_lora(lora_weights)
        return self.model(text)

# Use with VoiceStudio
adapter = MyTTSAdapter(my_tts_model)
generator = LoRAGenerator.from_pretrained("voicestudio/t2a-lora-base")

lora = generator("professional news anchor voice")
audio = adapter(text="Breaking news tonight...", lora_weights=lora)
```

### Multi-Speaker Voice Blending

```python
from voicestudio import VoiceBlender

blender = VoiceBlender()

# Blend multiple voice characteristics
blended_lora = blender.blend([
    ("warm and friendly", 0.6),
    ("professional and clear", 0.4)
])

audio = tts_model.synthesize(text, lora=blended_lora)
```

### Fine-tuning on Custom Data

```python
from voicestudio import LoRAGenerator
from voicestudio.training import Trainer

# Load pre-trained generator
generator = LoRAGenerator.from_pretrained("voicestudio/t2a-lora-base")

# Fine-tune on your data
trainer = Trainer(
    model=generator,
    train_dataset=your_dataset,
    output_dir="./checkpoints"
)

trainer.train()
```

---

## 📊 Supported Models

VoiceStudio works with various TTS architectures:

| Model | Status | Notes |
|-------|--------|-------|
| VITS | ✅ Supported | Fully tested |
| FastSpeech2 | ✅ Supported | Fully tested |
| Tacotron2 | ✅ Supported | Requires adapter |
| VALL-E | 🔄 Experimental | Work in progress |
| Bark | 🔄 Experimental | Coming soon |
| YourTTS | ✅ Supported | Community contributed |

**Add your own model**: See our [Integration Guide](docs/integration.md)

---

```bibtex
@inproceedings{voicestudio2027lam,
  title={T2A-LoRA2: Text-Guided Voice Editing with Language-Audio Models},
  author={Your Name},
  booktitle={ICML},
  year={2027}
}
```

---

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas we need help with:**
- 🔧 Additional TTS model adapters
- 📚 Documentation improvements
- 🐛 Bug fixes and testing
- 🌍 Multi-language support
- 🎨 New voice editing techniques

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **CLAP**: Microsoft & LAION-AI for CLAP model
- **LoRA**: Microsoft for LoRA technique
- **HuggingFace**: For transformers library and model hub
- **LatentForge Team**: For research support and infrastructure

---

## 🌟 Citation

If you use VoiceStudio in your research, please cite:

```bibtex
@software{voicestudio2026,
  title={VoiceStudio: A Unified Toolkit for Voice Style Adaptation},
  author={Your Name},
  year={2026},
  url={https://github.com/LatentForge/voicestudio}
}
```

---

<div align="center">

**Made with ❤️ by the LatentForge Team**

[⭐ Star us on GitHub](https://github.com/LatentForge/voicestudio) | [📖 Read the Docs](https://latentforge.github.io/VoiceStudio) | [🤗 HuggingFace](https://huggingface.co/LatentForge)

</div>
