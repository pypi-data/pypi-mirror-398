# PoCSmith

**AI-Powered Proof-of-Concept Generator for Security Research**

PoCSmith is an AI model fine-tuned on exploit code and CVE data to assist security researchers in generating proof-of-concept exploits and shellcode for defensive purposes.

Author: Regaan  
---

## Ethical Use Only

This tool is designed exclusively for defensive security research and authorized testing:
- Penetration testing on systems you own or have permission to test
- Security research and vulnerability analysis
- Educational purposes in controlled environments
- NOT for malicious attacks or unauthorized access

Use responsibly. Follow all applicable laws and regulations.

---

## Features

- **AI-Powered Generation** - CodeLlama-7B fine-tuned on 1,472 exploit samples
- **CVE Integration** - Fetch vulnerability data from NVD API
- **Multi-Platform Shellcode** - x86, x64, ARM support
- **Simple CLI** - Easy command-line interface
- **High Quality** - 78.4% token accuracy

---

## Quick Start

### Installation

```bash
git clone https://github.com/noobforanonymous/PoCSmith.git
cd PoCSmith

python3 -m venv venv
source venv/bin/activate

pip install -e .
```

### Usage Examples

```bash
# Generate exploit from CVE
python src/cli/main.py cve CVE-2024-1234

# Generate shellcode
python src/cli/main.py shellcode --platform linux_x64 --type reverse_shell --lhost 10.10.14.5 --lport 4444

# Generate from vulnerability description
python src/cli/main.py generate --vuln "buffer overflow" --target "Apache 2.4"

# List available options
python src/cli/main.py list-platforms
python src/cli/main.py list-payloads
```

---

## Model Details

- **Base Model:** CodeLlama-7B
- **Training:** QLoRA 4-bit quantization
- **Dataset:** 1,472 samples (CVE-Exploit pairs + shellcode)
- **Performance:** 78.4% token accuracy, 30% loss reduction
- **Training Time:** 3h 17min on RTX 4050 (6GB VRAM)

---

## Project Structure

```
PoCSmith/
├── src/
│   ├── parsers/          # CVE parsing
│   ├── generators/       # Exploit & shellcode generation
│   ├── formatters/       # Output formatting
│   ├── cli/              # Command-line interface
│   └── core/             # Configuration
├── models/
│   └── pocsmith-v1/      # Fine-tuned AI model (LoRA adapters)
├── data/                 # Training data
├── docs/                 # Documentation
└── tests/                # Unit tests
```

---

## Documentation

- [Usage Guide](docs/USAGE.md)
- [Setup Instructions](docs/implementation/SETUP.md)
- [Fine-tuning Details](docs/implementation/FINE_TUNING.md)
- [System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)

---

## Requirements

- Python 3.11+
- CUDA-capable GPU (6GB+ VRAM recommended)
- 20GB disk space

### Dependencies

```
torch>=2.0.0
transformers>=4.35.0
peft>=0.7.0
bitsandbytes>=0.41.0
click>=8.1.0
```

---

## Example Output

### Shellcode Generation
```
$ python src/cli/main.py shellcode --platform linux_x86 --type reverse_shell --lhost 10.10.14.5 --lport 4444

PoCSmith v1.0

[*] Generating reverse_shell for linux_x86...
Loading PoCSmith model...
Model ready!

/*
 * Shellcode for Linux/x86
 * - Calls socket() -> connect() -> dup2() -> execve()
 * - Tested on Ubuntu, Debian
 * - Length: 160 bytes
 */
```

---

## Contributing

Contributions are welcome. Please fork the repository, create a feature branch, and submit a pull request.

---

## License

MIT License - See LICENSE file

---

## Disclaimer

FOR EDUCATIONAL AND DEFENSIVE SECURITY RESEARCH ONLY

I am not responsible for misuse of this tool. Users must obtain proper authorization before testing, follow responsible disclosure practices, and comply with all applicable laws.

---

## Acknowledgments

- CodeLlama (Meta AI)
- NVD (NIST)
- Exploit-DB
- Metasploit Framework
- Hugging Face

---

Built for the security research community.

Version 1.0  
By Regaan
