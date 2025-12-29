#!/usr/bin/env python3
"""
Merge LoRA adapters into base model
Creates a single, standalone ExploitGPT model
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import argparse

def merge_lora_model(
    base_model_path: str,
    adapter_path: str,
    output_path: str
):
    """
    Merge LoRA adapters into base model
    
    Args:
        base_model_path: Path to base CodeLlama model
        adapter_path: Path to LoRA adapters
        output_path: Where to save merged model
    """
    
    print("=" * 60)
    print("PoCSmith Model Merger")
    print("=" * 60)
    
    # Load base model on CPU to avoid OOM
    print(f"\n[1/4] Loading base model on CPU: {base_model_path}")
    print("      (This will take 2-3 minutes on CPU)")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,  # Use FP16 for smaller memory
        device_map="cpu",  # Load on CPU to avoid OOM
        trust_remote_code=True
    )
    
    # Load tokenizer
    print(f"[2/4] Loading tokenizer from: {adapter_path}")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    
    # Load and merge adapters
    print(f"[3/4] Loading LoRA adapters: {adapter_path}")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    
    print("[4/4] Merging adapters into base model (CPU)...")
    print("      (This will take 3-5 minutes)")
    merged_model = model.merge_and_unload()
    
    # Save merged model
    print(f"\n✓ Saving merged model to: {output_path}")
    print("  (Saving ~13GB will take 2-3 minutes)")
    merged_model.save_pretrained(output_path, safe_serialization=True, max_shard_size="2GB")
    tokenizer.save_pretrained(output_path)
    
    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)
    print(f"\nYour standalone ExploitGPT model is ready at:")
    print(f"  {output_path}")
    print(f"\nSize: ~13GB")
    print(f"\nYou can now:")
    print(f"  1. Use this model without LoRA/PEFT")
    print(f"  2. Share this single directory")
    print(f"  3. Load with: AutoModelForCausalLM.from_pretrained('{output_path}')")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge ExploitGPT LoRA into standalone model")
    parser.add_argument(
        "--base-model",
        default="codellama/CodeLlama-7b-hf",
        help="Base model (default: codellama/CodeLlama-7b-hf)"
    )
    parser.add_argument(
        "--adapters",
        default="models/exploitgpt-v1",
        help="LoRA adapters path (default: models/exploitgpt-v1)"
    )
    parser.add_argument(
        "--output",
        default="models/exploitgpt-merged",
        help="Output path for merged model (default: models/exploitgpt-merged)"
    )
    
    args = parser.parse_args()
    
    merge_lora_model(
        base_model_path=args.base_model,
        adapter_path=args.adapters,
        output_path=args.output
    )
