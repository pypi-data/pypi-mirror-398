#!/usr/bin/env python3
"""
Test Script for Orca Platform Package
=======================================

This script tests the basic functionality of the installed package.
"""

import asyncio
from orca import (
    OrcaHandler, 
    ChatMessage, 
    Variable, 
    Memory,
    ForceToolsHelper,
    create_success_response,
    __version__
)

def test_basic_imports():
    """Test basic package imports."""
    print("🧪 Testing basic imports...")
    
    try:
        from orca import OrcaHandler, ChatMessage, Variable, Memory
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Basic imports failed: {e}")
        return False

def test_version():
    """Test package version."""
    print(f"📦 Package version: {__version__}")
    return True

def test_models():
    """Test data models."""
    print("🔧 Testing data models...")
    
    try:
        # Test Variable model
        var = Variable(name="TEST_VAR", value="test_value")
        print(f"✅ Variable model: {var.name} = {var.value}")
        
        # Test ChatMessage model
        message = ChatMessage(
            thread_id="test123",
            model="gpt-4",
            message="Hello, world!",
            conversation_id=1,
            response_uuid="uuid123",
            message_uuid="msg123",
            channel="test",
            file_type="",
            file_url="",
            variables=[var],
            url="http://test.com",
            url_update="",
            url_upload="",
            force_tools=["code", "search"],
            sleep_time=100,
            system_message=None,
            memory=Memory(),
            project_system_message=None,
            first_message=False,
            project_id="",
            project_files=None
        )
        print(f"✅ ChatMessage model: {message.message}")
        
        # Test ForceToolsHelper
        tools = ForceToolsHelper(message.force_tools)
        if tools.has('code') and tools.has('search'):
            print(f"✅ ForceToolsHelper: has code and search tools")
        
        return True
    except Exception as e:
        print(f"❌ Data models test failed: {e}")
        return False

def test_response_handler():
    """Test response handler."""
    print("📝 Testing response handler...")
    
    try:
        response = create_success_response(
            response_uuid="uuid123",
            thread_id="thread456"
        )
        print(f"✅ Response created: {response.status} - {response.message}")
        return True
    except Exception as e:
        print(f"❌ Response handler test failed: {e}")
        return False

def test_orca_handler():
    """Test OrcaHandler initialization."""
    print("🤖 Testing OrcaHandler...")
    
    try:
        handler = OrcaHandler()
        print("✅ OrcaHandler created successfully")
        
        # Test that required methods exist
        required_methods = ['stream_chunk', 'complete_response', 'send_error']
        for method in required_methods:
            if hasattr(handler, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ OrcaHandler test failed: {e}")
        return False

def test_web_imports():
    """Test web framework imports."""
    print("🌐 Testing web imports...")
    
    try:
        from orca.web import create_orca_app, add_standard_endpoints
        print("✅ Web imports successful")
        return True
    except ImportError as e:
        print(f"❌ Web imports failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Orca Platform Package Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Version", test_version),
        ("Data Models", test_models),
        ("Response Handler", test_response_handler),
        ("OrcaHandler", test_orca_handler),
        ("Web Imports", test_web_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Package is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

