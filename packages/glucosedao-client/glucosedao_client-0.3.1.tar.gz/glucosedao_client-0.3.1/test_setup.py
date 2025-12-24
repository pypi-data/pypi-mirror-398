"""Test script for glucosedao_client setup."""
import sys


def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from glucosedao_client import (
            GluRPCClient,
            GluRPCConfig,
            AsyncGluRPCClient,
            create_gradio_app,
            launch_app,
            start_server,
            stop_server,
            is_server_running,
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_client_creation():
    """Test that we can create a client."""
    print("\nTesting client creation...")
    
    try:
        from glucosedao_client import GluRPCClient, GluRPCConfig
        
        config = GluRPCConfig(
            base_url="http://localhost:8000",
            api_key=None
        )
        client = GluRPCClient(config)
        
        print(f"✅ Client created with base_url: {client.config.base_url}")
        
        client.close()
        return True
    except Exception as e:
        print(f"❌ Client creation failed: {e}")
        return False


def test_gradio_app_creation():
    """Test that we can create the Gradio app."""
    print("\nTesting Gradio app creation...")
    
    try:
        from glucosedao_client import create_gradio_app
        
        app = create_gradio_app()
        print("✅ Gradio app created successfully")
        return True
    except Exception as e:
        print(f"❌ Gradio app creation failed: {e}")
        print(f"   This is expected if gradio is not installed")
        return False


def test_server_utilities():
    """Test server utility functions."""
    print("\nTesting server utilities...")
    
    try:
        from glucosedao_client import is_server_running
        
        # This should return False if no server is running
        result = is_server_running("http://localhost:9999")
        print(f"✅ is_server_running works (returned {result})")
        return True
    except Exception as e:
        print(f"❌ Server utilities test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("GluRPC Client Setup Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Client Creation", test_client_creation()))
    results.append(("Gradio App", test_gradio_app_creation()))
    results.append(("Server Utilities", test_server_utilities()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. This might be expected if dependencies aren't installed.")
        print("   Run 'uv sync' to install all dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

