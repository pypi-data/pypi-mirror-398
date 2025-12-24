from src.lunar_policy.variables import variable, variable_or_default


class TestVariables:
    def test_variable_not_found(self, monkeypatch):
        monkeypatch.delenv('LUNAR_VAR_TEST', raising=False)
        assert variable('TEST') is None

    def test_variable_found(self, monkeypatch):
        monkeypatch.setenv('LUNAR_VAR_TEST', 'value')
        assert variable('TEST') == 'value'

    def test_variable_case_sensitive(self, monkeypatch):
        monkeypatch.setenv('LUNAR_VAR_TEST', 'value')
        assert variable('test') is None

    def test_variable_or_default_not_found(self, monkeypatch):
        monkeypatch.delenv('LUNAR_VAR_TEST', raising=False)
        assert variable_or_default('TEST', 'default') == 'default'

    def test_variable_or_default_found(self, monkeypatch):
        monkeypatch.setenv('LUNAR_VAR_TEST', 'value')
        assert variable_or_default('TEST', 'default') == 'value'

    def test_ignore_non_lunar_var_prefix(self, monkeypatch):
        monkeypatch.setenv('OTHER_VAR_TEST', 'value')
        assert variable('TEST') is None
