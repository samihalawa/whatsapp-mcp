#!/usr/bin/env python3
"""
WhatsApp MCP Server - Validation Script

This script validates your installation and configuration.
Run: python test_setup.py
"""

import sys
import os
import importlib.util

def check_python_version():
    """Check if Python version is 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required. Current:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required = ["mcp", "pydantic", "httpx"]
    missing = []
    
    for package in required:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing.append(package)
            print(f"❌ {package} not installed")
        else:
            print(f"✅ {package} installed")
    
    if missing:
        print(f"\n❌ Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists"""
    if os.path.exists(".env"):
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found (optional)")
        print("   Copy .env.example to .env and configure if needed")
        return True

def check_server_file():
    """Check if main server file exists and is valid"""
    if not os.path.exists("whatsapp_mcp.py"):
        print("❌ whatsapp_mcp.py not found")
        return False
    
    print("✅ whatsapp_mcp.py found")
    
    # Try to import and check syntax
    try:
        with open("whatsapp_mcp.py", "r") as f:
            compile(f.read(), "whatsapp_mcp.py", "exec")
        print("✅ whatsapp_mcp.py syntax valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in whatsapp_mcp.py: {e}")
        return False

def check_whatsapp_server():
    """Check if WhatsApp server is accessible"""
    try:
        import httpx
        api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:3000")
        
        print(f"🔍 Checking WhatsApp server at {api_url}...")
        
        with httpx.Client(timeout=5.0) as client:
            try:
                response = client.get(api_url)
                print(f"✅ WhatsApp server responding (status: {response.status_code})")
                return True
            except httpx.ConnectError:
                print(f"❌ Cannot connect to WhatsApp server at {api_url}")
                print("   Ensure the server is running (docker-compose up -d)")
                return False
            except httpx.TimeoutException:
                print(f"⚠️  WhatsApp server timeout at {api_url}")
                return False
    except ImportError:
        print("⚠️  httpx not installed, skipping server check")
        return True

def main():
    """Run all validation checks"""
    print("=" * 60)
    print("WhatsApp MCP Server - Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Server File", check_server_file),
        ("WhatsApp Server", check_whatsapp_server),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        results.append(check_func())
        print()
    
    print("=" * 60)
    if all(results):
        print("✅ All checks passed! Server ready to use.")
        print("\nNext steps:")
        print("1. Start WhatsApp server: docker-compose up -d")
        print("2. Configure Claude Desktop (see README.md)")
        print("3. Restart Claude Desktop")
        print("4. Test: Ask Claude to 'Login to WhatsApp via QR code'")
    else:
        print("❌ Some checks failed. Fix issues above before using.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
