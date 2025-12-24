"""
Tests for core functionality
"""

import pytest
from polerisk.core import hello_polerisk


def test_hello_polerisk():
    """Test the hello_polerisk function"""
    result = hello_polerisk()
    assert result == "Hello from polerisk!"
    assert isinstance(result, str)

