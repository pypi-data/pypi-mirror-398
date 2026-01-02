import pytest
import pandas as pd
import numpy as np
from misata.formulas import FormulaEngine

class TestFormulaSecurity:
    """Security tests for formula evaluation."""
    
    def setup_method(self):
        self.tables = {
            "users": pd.DataFrame({
                "id": [1, 2, 3],
                "age": [25, 30, 35]
            })
        }
        self.engine = FormulaEngine(self.tables)
        self.df = self.tables["users"]

    def test_blocks_import(self):
        """Test that __import__ is blocked."""
        # Try to import os and run system command
        formula = "__import__('os').system('echo pwned')"
        
        with pytest.raises(ValueError, match="Function '__import__' not defined"):
            self.engine.evaluate(self.df, formula)

    def test_blocks_builtin_functions(self):
        """Test that builtin functions like open() are blocked."""
        # Try to open a file
        formula = "open('/etc/passwd').read()"
        
        with pytest.raises(ValueError, match="Function 'open' not defined"):
            self.engine.evaluate(self.df, formula)
            
    def test_blocks_eval(self):
        """Test that nested eval is blocked."""
        formula = "eval('2 + 2')"
        with pytest.raises(ValueError, match="Function 'eval' not defined"):
            self.engine.evaluate(self.df, formula)

    def test_blocks_non_whitelisted_numpy(self):
        """Test that non-whitelisted numpy functions are blocked."""
        # np.load is dangerous
        formula = "np.load('malicious.npy')"
        
        with pytest.raises(ValueError) as excinfo:
            self.engine.evaluate(self.df, formula)
        
        # simpleeval might raise different errors depending on implementation
        # But it should fail. Our custom SafeNumpy raises NameNotDefined which wraps into ValueError
        assert "not allowed" in str(excinfo.value) or "not defined" in str(excinfo.value)

    def test_allows_whitelisted_numpy(self):
        """Test that whitelisted numpy functions work."""
        formula = "np.where(age > 30, 1, 0)"
        result = self.engine.evaluate(self.df, formula)
        
        expected = np.array([0, 0, 1])
        np.testing.assert_array_equal(result, expected)

    def test_allows_basic_math(self):
        """Test that basic math still works."""
        formula = "age * 2"
        result = self.engine.evaluate(self.df, formula)
        
        expected = np.array([50, 60, 70])
        np.testing.assert_array_equal(result, expected)
