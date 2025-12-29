"""Tests for FabricAdvisor core functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sparkwise.core.advisor import FabricAdvisor


class TestFabricAdvisor:
    """Test suite for FabricAdvisor class."""
    
    @patch('sparkwise.core.advisor.SparkSession')
    def test_advisor_initialization(self, mock_spark):
        """Test that advisor initializes correctly with SparkSession."""
        mock_session = Mock()
        mock_spark.builder.getOrCreate.return_value = mock_session
        
        advisor = FabricAdvisor()
        
        assert advisor.spark == mock_session
        assert advisor.conf is not None
    
    @patch('sparkwise.core.advisor.SparkSession')
    def test_quick_check_executes(self, mock_spark):
        """Test that quick_check runs without errors."""
        mock_session = Mock()
        mock_spark.builder.getOrCreate.return_value = mock_session
        
        advisor = FabricAdvisor()
        
        # Should not raise any exceptions
        try:
            advisor.quick_check()
        except Exception as e:
            pytest.fail(f"quick_check() raised {e}")
    
    @patch('sparkwise.core.advisor.SparkSession')
    def test_analyze_returns_dict(self, mock_spark):
        """Test that analyze returns a dictionary with expected keys."""
        mock_session = Mock()
        mock_spark.builder.getOrCreate.return_value = mock_session
        
        advisor = FabricAdvisor()
        result = advisor.analyze()
        
        assert isinstance(result, dict)
        assert "native_execution" in result
        assert "pooling" in result
        assert "skew" in result
        assert "delta" in result
        assert "runtime" in result


class TestNativeExecutionChecker:
    """Test suite for NativeExecutionChecker."""
    
    @patch('sparkwise.core.native_check.SparkSession')
    def test_check_returns_dict(self, mock_spark):
        """Test that check returns properly structured dict."""
        from sparkwise.core.native_check import NativeExecutionChecker
        
        mock_session = Mock()
        checker = NativeExecutionChecker(mock_session)
        result = checker.check()
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "native_enabled" in result
        assert "issues" in result
        assert "recommendations" in result


class TestPoolingChecker:
    """Test suite for PoolingChecker."""
    
    @patch('sparkwise.core.pool_check.SparkSession')
    def test_check_returns_dict(self, mock_spark):
        """Test that check returns properly structured dict."""
        from sparkwise.core.pool_check import PoolingChecker
        
        mock_session = Mock()
        checker = PoolingChecker(mock_session)
        result = checker.check()
        
        assert isinstance(result, dict)
        assert "executor_count" in result
        assert "can_use_starter" in result
        assert "recommendations" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
