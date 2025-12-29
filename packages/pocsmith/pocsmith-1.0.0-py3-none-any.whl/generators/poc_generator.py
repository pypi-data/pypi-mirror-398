"""PoC Generator - AI-powered exploit generation"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from pathlib import Path
from typing import Optional

from core.config import (
    MODEL_PATH, BASE_MODEL, DEFAULT_MAX_TOKENS, 
    DEFAULT_TEMPERATURE, DEFAULT_TOP_P, USE_4BIT
)


class PoCGenerator:
    """AI-powered Proof-of-Concept exploit generator"""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.model = None
        self.tokenizer = None
        self._loaded = False
    
    def load_model(self):
        """Load the fine-tuned model"""
        if self._loaded:
            return
        
        print("Loading PoCSmith model...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        
        # Load base model
        if USE_4BIT:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            base_model = AutoModelForCausalLM.from_pretrained(
                BASE_MODEL,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )
        
        # Load LoRA adapters
        self.model = PeftModel.from_pretrained(
            base_model,
            str(self.model_path),
            is_trainable=False,
            device_map={"": 0}
        )
        self.model.eval()
        
        self._loaded = True
        print("Model ready!")
    
    def generate(
        self, 
        instruction: str,
        context: str = "",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P
    ) -> str:
        """
        Generate exploit code
        
        Args:
            instruction: What to generate (e.g., "Generate a PoC for...")
            context: Additional context (CVE details, etc.)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling threshold
            
        Returns:
            Generated exploit code
        """
        if not self._loaded:
            self.load_model()
        
        # Format prompt
        if context:
            prompt = f"""### Instruction:
{instruction}

### Input:
{context}

### Response:
"""
        else:
            prompt = f"""### Instruction:
{instruction}

### Response:
"""
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract response only
        if "### Response:" in result:
            return result.split("### Response:")[1].strip()
        
        return result
    
    def generate_from_cve(
        self, 
        cve_id: str,
        cve_description: str,
        cvss_score: Optional[float] = None,
        affected_software: Optional[list[str]] = None
    ) -> str:
        """Generate PoC from CVE information"""
        
        instruction = f"Generate a Proof-of-Concept (PoC) exploit for {cve_id}."
        
        context = f"Vulnerability Description: {cve_description}"
        if cvss_score:
            context += f"\nCVSS Score: {cvss_score}"
        if affected_software:
            context += f"\nAffected Software: {', '.join(affected_software[:3])}"
        
        return self.generate(instruction, context)
    
    def generate_from_description(
        self,
        vuln_type: str,
        target: Optional[str] = None,
        details: Optional[str] = None
    ) -> str:
        """Generate PoC from vulnerability description"""
        
        instruction = f"Generate a Proof-of-Concept exploit for a {vuln_type}."
        
        context = ""
        if target:
            context += f"Target: {target}\n"
        if details:
            context += f"Details: {details}"
        
        return self.generate(instruction, context.strip())
