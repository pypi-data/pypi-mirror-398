"""Tests for adapter registry."""

import pytest


class TestAdapterConfig:
    """Tests for adapter configuration parsing."""

    def test_parse_legacy_format(self):
        """Test legacy adapter config parsing."""
        from clara.adapters import parse_adapter_config

        config = {
            "adapter": {
                "enabled": True,
                "path": "/path/to/adapter",
                "type": "lora",
            }
        }

        result = parse_adapter_config(config)
        assert result.active == "default"
        assert len(result.available) == 1
        assert result.available[0].path == "/path/to/adapter"

    def test_parse_legacy_disabled(self):
        """Test legacy adapter config when disabled."""
        from clara.adapters import parse_adapter_config

        config = {
            "adapter": {
                "enabled": False,
                "path": "/path/to/adapter",
            }
        }

        result = parse_adapter_config(config)
        assert result.active is None
        assert len(result.available) == 0

    def test_parse_new_format(self):
        """Test new multi-adapter config parsing."""
        from clara.adapters import parse_adapter_config

        config = {
            "adapters": {
                "available": [
                    {"name": "a1", "path": "/a1"},
                    {"name": "a2", "path": "/a2"},
                ],
                "active": "a1",
            }
        }

        result = parse_adapter_config(config)
        assert result.active == "a1"
        assert len(result.available) == 2

    def test_parse_no_adapter(self):
        """Test config with no adapter section."""
        from clara.adapters import parse_adapter_config

        config = {"model": {"hf_id": "test"}}

        result = parse_adapter_config(config)
        assert result.active is None
        assert len(result.available) == 0

    def test_duplicate_names_error(self):
        """Test that duplicate adapter names raise error."""
        from clara.adapters import AdapterConfig, AdapterConfigError, AdaptersConfig

        config = AdaptersConfig(
            available=[
                AdapterConfig(name="dup", path="/a"),
                AdapterConfig(name="dup", path="/b"),
            ]
        )

        with pytest.raises(AdapterConfigError) as exc_info:
            config.validate()

        assert "Duplicate" in str(exc_info.value)

    def test_active_not_in_available(self):
        """Test that active adapter must be in available list."""
        from clara.adapters import AdapterConfig, AdapterConfigError, AdaptersConfig

        config = AdaptersConfig(
            available=[
                AdapterConfig(name="a1", path="/a1"),
            ],
            active="nonexistent",
        )

        with pytest.raises(AdapterConfigError) as exc_info:
            config.validate()

        assert "nonexistent" in str(exc_info.value)


class TestAdapterRegistry:
    """Tests for adapter registry."""

    def test_empty_registry(self):
        """Test empty registry creation."""
        from clara.adapters import AdapterRegistry

        registry = AdapterRegistry()
        assert len(registry) == 0
        assert registry.get_active() is None
        assert registry.list_adapters() == []

    def test_adapter_not_found(self):
        """Test AdapterNotFoundError."""
        from clara.adapters import AdapterNotFoundError, AdapterRegistry

        registry = AdapterRegistry()

        with pytest.raises(AdapterNotFoundError) as exc_info:
            registry.get("nonexistent")

        assert "nonexistent" in str(exc_info.value)
        assert exc_info.value.adapter_name == "nonexistent"
        assert exc_info.value.available == []

    def test_set_active_not_found(self):
        """Test setting active to non-existent adapter."""
        from clara.adapters import AdapterNotFoundError, AdapterRegistry

        registry = AdapterRegistry()

        with pytest.raises(AdapterNotFoundError):
            registry.set_active("nonexistent")

    def test_set_active_none(self):
        """Test setting active to None."""
        from clara.adapters import AdapterRegistry

        registry = AdapterRegistry()
        registry.set_active(None)  # Should not raise
        assert registry.get_active() is None

    def test_contains(self):
        """Test __contains__ method."""
        from clara.adapters import AdapterRegistry

        registry = AdapterRegistry()
        assert "test" not in registry

    def test_from_config_empty(self):
        """Test creating registry from empty config."""
        from clara.adapters import AdapterRegistry

        config = {"model": {"hf_id": "test"}}
        registry = AdapterRegistry.from_config(config)

        assert len(registry) == 0
        assert registry.get_active() is None
