"""
PoCSmith Core Configuration
"""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "models/pocsmith-v1"
BASE_MODEL = "codellama/CodeLlama-7b-hf"
OUTPUT_DIR = PROJECT_ROOT / "output"

# NVD API
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_RATE_LIMIT = 5  # requests per 30 seconds
NVD_TIMEOUT = 10  # seconds

# Model Generation Settings
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
USE_4BIT = True  # 4-bit quantization for memory efficiency

# Output Settings
SAVE_BY_DEFAULT = False  # Don't auto-save, let user decide
VERBOSE = True

# Ethical Warning
ETHICAL_WARNING = """
ETHICAL USE ONLY 
This tool is for defensive security research and authorized testing only.
- Only use on systems you own or have permission to test
- Do not use for malicious purposes
- Follow responsible disclosure practices
- Comply with all local laws and regulations
"""
