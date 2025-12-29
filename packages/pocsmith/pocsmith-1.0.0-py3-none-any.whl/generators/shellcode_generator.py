"""Shellcode Generator - Multi-platform payload generation"""

from typing import Optional
from generators.poc_generator import PoCGenerator


class ShellcodeGenerator:
    """Generate platform-specific shellcode"""
    
    PLATFORMS = {
        "linux_x86": "Linux x86 (32-bit)",
        "linux_x64": "Linux x64 (64-bit)",
        "windows_x86": "Windows x86 (32-bit)",
        "windows_x64": "Windows x64 (64-bit)",
        "arm": "ARM (32-bit)"
    }
    
    PAYLOAD_TYPES = {
        "reverse_shell": "Reverse TCP shell",
        "bind_shell": "Bind TCP shell",
        "exec": "Execute command",
        "download_exec": "Download and execute"
    }
    
    def __init__(self):
        self.generator = PoCGenerator()
    
    @classmethod
    def list_platforms(cls) -> dict:
        """List supported platforms"""
        return cls.PLATFORMS
    
    @classmethod
    def list_payload_types(cls) -> dict:
        """List supported payload types"""
        return cls.PAYLOAD_TYPES
    
    def generate(
        self,
        platform: str,
        payload_type: str,
        lhost: Optional[str] = None,
        lport: Optional[int] = None,
        command: Optional[str] = None
    ) -> str:
        """
        Generate shellcode
        
        Args:
            platform: Target platform (e.g., 'linux_x86')
            payload_type: Type of payload (e.g., 'reverse_shell')
            lhost: Listener host (for reverse/bind shells)
            lport: Listener port
            command: Command to execute (for exec payloads)
            
        Returns:
            Generated shellcode with assembly/hex
        """
        if platform not in self.PLATFORMS:
            raise ValueError(f"Unknown platform: {platform}. Use list_platforms()")
        
        if payload_type not in self.PAYLOAD_TYPES:
            raise ValueError(f"Unknown payload type: {payload_type}. Use list_payload_types()")
        
        # Build instruction
        instruction = f"Generate a {self.PAYLOAD_TYPES[payload_type]} shellcode for {self.PLATFORMS[platform]}."
        
        # Build context
        context_parts = []
        context_parts.append(f"Platform: {self.PLATFORMS[platform]}")
        context_parts.append(f"Payload Type: {self.PAYLOAD_TYPES[payload_type]}")
        
        if payload_type in ["reverse_shell", "bind_shell"]:
            if not lhost or not lport:
                raise ValueError(f"{payload_type} requires lhost and lport")
            context_parts.append(f"Target: {lhost}:{lport}")
        
        if payload_type == "exec" and command:
            context_parts.append(f"Command: {command}")
        
        context = "\n".join(context_parts)
        
        # Generate using AI model
        return self.generator.generate(instruction, context, max_tokens=400)
