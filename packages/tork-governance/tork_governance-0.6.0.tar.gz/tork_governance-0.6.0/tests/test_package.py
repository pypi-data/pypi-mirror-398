"""
Package import tests.

Verifies that the tork package and its modules can be imported correctly.
"""

import pytest


def test_import_tork():
    """Test that the main tork package can be imported."""
    import tork
    
    assert hasattr(tork, "__version__")
    assert tork.__version__ == "0.6.0"


def test_import_core():
    """Test that the core module can be imported."""
    from tork.core import GovernanceEngine
    
    engine = GovernanceEngine()
    assert engine is not None
    assert not engine.is_running()


def test_import_adapters():
    """Test that the adapters module can be imported."""
    from tork.adapters import BaseAdapter
    
    assert BaseAdapter is not None


def test_import_identity():
    """Test that the identity module can be imported."""
    from tork.identity import IdentityManager, JWTHandler
    
    handler = JWTHandler(secret_key="test-secret")
    manager = IdentityManager(handler)
    assert manager is not None
    assert manager.jwt_handler is not None


def test_import_compliance():
    """Test that the compliance module can be imported."""
    from tork.compliance import PolicyValidator
    
    validator = PolicyValidator()
    assert validator is not None
    assert validator.policy_count == 0


def test_import_api():
    """Test that the API module can be imported."""
    from tork.api import create_app
    
    app = create_app()
    assert app is not None
