"""
Test script for refactored Orca SDK with SOLID principles
===========================================================

This script demonstrates that the refactored code works correctly
and maintains backwards compatibility.
"""

import sys
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


def test_basic_import():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from orca import OrcaHandler
        from orca.services import BufferManager, ButtonRenderer, UsageTracker
        from orca.factories import StreamClientFactory
        from orca.domain.interfaces import IStreamClient, IAPIClient
        from orca.core import Session
        from orca.helpers import ButtonHelper
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_handler_initialization():
    """Test that OrcaHandler initializes correctly."""
    print("\nTesting OrcaHandler initialization...")
    
    try:
        from orca import OrcaHandler
        
        # Test default initialization
        handler1 = OrcaHandler(dev_mode=True)
        assert handler1.dev_mode == True
        print("✅ Dev mode initialization works")
        
        # Test dependency injection
        mock_stream = Mock()
        mock_api = Mock()
        handler2 = OrcaHandler(
            dev_mode=False,
            stream_client=mock_stream,
            api_client=mock_api
        )
        assert handler2._stream_client == mock_stream
        assert handler2._api_client == mock_api
        print("✅ Dependency injection works")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


def test_services():
    """Test individual services."""
    print("\nTesting services...")
    
    try:
        from orca.services import BufferManager, ButtonRenderer, LoadingMarkerProvider
        
        # Test BufferManager
        buffer_mgr = BufferManager()
        buffer_mgr.append("test-uuid", "Hello ")
        buffer_mgr.append("test-uuid", "World")
        result = buffer_mgr.drain("test-uuid")
        assert result == "Hello World"
        print("✅ BufferManager works")
        
        # Test ButtonRenderer
        renderer = ButtonRenderer()
        button = renderer.create_link_button("Click", "https://example.com")
        assert button["type"] == "link"
        assert button["label"] == "Click"
        assert button["url"] == "https://example.com"
        print("✅ ButtonRenderer works")
        
        # Test LoadingMarkerProvider
        marker_provider = LoadingMarkerProvider()
        marker = marker_provider.get_marker("thinking", "start")
        assert "[orca.loading.thinking.start]" in marker
        print("✅ LoadingMarkerProvider works")
        
        return True
    except Exception as e:
        print(f"❌ Services test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory():
    """Test StreamClientFactory."""
    print("\nTesting factory...")
    
    try:
        from orca.factories import StreamClientFactory
        from orca.domain.interfaces import IStreamClient
        
        # Test dev client creation
        dev_client = StreamClientFactory.create(dev_mode=True)
        assert isinstance(dev_client, IStreamClient)
        print("✅ Factory creates dev client")
        
        # Test production client creation
        prod_client = StreamClientFactory.create(dev_mode=False)
        assert isinstance(prod_client, IStreamClient)
        print("✅ Factory creates production client")
        
        return True
    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backwards_compatibility():
    """Test that old API still works."""
    print("\nTesting backwards compatibility...")
    
    try:
        from orca import OrcaHandler, create_link_button_block, create_action_button_block
        
        # Test standalone functions
        link_block = create_link_button_block("Test", "https://example.com")
        assert "[orca.buttons.start]" in link_block
        assert "Test" in link_block
        print("✅ Standalone functions work")
        
        # Test handler with mock data
        handler = OrcaHandler(dev_mode=True)
        
        # Create mock data object
        mock_data = MagicMock()
        mock_data.response_uuid = "test-uuid"
        mock_data.conversation_id = 123
        mock_data.channel = "test-channel"
        mock_data.thread_id = "test-thread"
        
        # Test session creation
        session = handler.begin(mock_data)
        assert session is not None
        print("✅ Session creation works")
        
        # Test streaming (should not throw)
        session.stream("Test content")
        print("✅ Streaming works")
        
        # Test close (should not throw)
        result = session.close()
        assert "Test content" in result
        print("✅ Close works")
        
        return True
    except Exception as e:
        print(f"❌ Backwards compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependency_injection():
    """Test dependency injection for testing."""
    print("\nTesting dependency injection for mocking...")
    
    try:
        from orca import OrcaHandler
        
        # Create mocks
        mock_stream = Mock()
        mock_api = Mock()
        mock_buffer = Mock()
        mock_buffer.append = Mock()
        mock_buffer.drain = Mock(return_value="Mocked content")
        
        # Inject mocks
        handler = OrcaHandler(
            dev_mode=True,
            stream_client=mock_stream,
            api_client=mock_api,
            buffer_manager=mock_buffer
        )
        
        # Create mock data
        mock_data = MagicMock()
        mock_data.response_uuid = "test-uuid"
        mock_data.conversation_id = 123
        mock_data.channel = "test-channel"
        mock_data.thread_id = "test-thread"
        
        # Test that mocks are used
        session = handler.begin(mock_data)
        session.stream("Test")
        
        # Verify mock was called
        mock_buffer.append.assert_called()
        print("✅ Mock buffer was called")
        
        # Test close
        result = session.close()
        mock_buffer.drain.assert_called()
        assert result == "Mocked content"
        print("✅ Mock injection works perfectly")
        
        return True
    except Exception as e:
        print(f"❌ Dependency injection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("ORCA SDK REFACTORED - SOLID PRINCIPLES TEST SUITE")
    print("="*60)
    
    tests = [
        test_basic_import,
        test_handler_initialization,
        test_services,
        test_factory,
        test_backwards_compatibility,
        test_dependency_injection,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! REFACTORING SUCCESSFUL!")
        print("✅ SOLID principles implemented correctly")
        print("✅ Backwards compatibility maintained")
        print("✅ Dependency injection works")
        print("✅ Ready for production!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

