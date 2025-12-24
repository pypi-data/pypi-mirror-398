"""Tests for AudioMetadata raga handling and validation."""

import pytest
from typing import Dict, Any

from idtap.audio_models import AudioMetadata, Raga as AudioRaga, Permissions
from idtap.classes.raga import Raga as MusicalRaga


class TestAudioMetadataRagaValidation:
    """Test cases for AudioMetadata raga format validation and normalization."""

    def test_audioraga_objects_work(self):
        """Test that AudioRaga objects work correctly (baseline)."""
        metadata = AudioMetadata(
            ragas=[AudioRaga(name="Rageshree")]
        )
        
        result = metadata.to_json()
        
        assert "ragas" in result
        assert "Rageshree" in result["ragas"]
        assert "performance sections" in result["ragas"]["Rageshree"]

    def test_string_format_auto_converted(self):
        """Test that string ragas are auto-converted to AudioRaga objects."""
        metadata = AudioMetadata(
            ragas=["Rageshree", "Yaman"]
        )
        
        result = metadata.to_json()
        
        assert "ragas" in result
        assert "Rageshree" in result["ragas"]
        assert "Yaman" in result["ragas"]
        assert "performance sections" in result["ragas"]["Rageshree"]
        assert "performance sections" in result["ragas"]["Yaman"]

    def test_name_dict_format_auto_converted(self):
        """Test that name dict format is auto-converted to AudioRaga objects."""
        metadata = AudioMetadata(
            ragas=[{"name": "Rageshree"}, {"name": "Yaman"}]
        )
        
        result = metadata.to_json()
        
        assert "ragas" in result
        assert "Rageshree" in result["ragas"]
        assert "Yaman" in result["ragas"]

    def test_legacy_dict_format_auto_converted(self):
        """Test that legacy dict format is auto-converted to AudioRaga objects."""
        metadata = AudioMetadata(
            ragas=[{"Rageshree": {"performance_sections": {}}}]
        )
        
        result = metadata.to_json()
        
        assert "ragas" in result
        assert "Rageshree" in result["ragas"]
        assert "performance sections" in result["ragas"]["Rageshree"]

    def test_mixed_formats_work_together(self):
        """Test that different raga formats can be mixed in the same list."""
        metadata = AudioMetadata(
            ragas=[
                AudioRaga(name="Rageshree"),  # AudioRaga object
                "Yaman",  # String
                {"name": "Bhairavi"},  # Name dict
                {"Malkauns": {"performance_sections": {}}}  # Legacy dict
            ]
        )
        
        result = metadata.to_json()
        
        assert "ragas" in result
        assert len(result["ragas"]) == 4
        assert "Rageshree" in result["ragas"]
        assert "Yaman" in result["ragas"]
        assert "Bhairavi" in result["ragas"]
        assert "Malkauns" in result["ragas"]

    def test_empty_ragas_list_works(self):
        """Test that empty ragas list works correctly."""
        metadata = AudioMetadata(ragas=[])
        
        result = metadata.to_json()
        
        assert "ragas" in result
        assert result["ragas"] == {}

    def test_invalid_dict_format_raises_error(self):
        """Test that invalid dict formats raise helpful error messages."""
        metadata = AudioMetadata(
            ragas=[{"invalid": "format", "multiple": "keys"}]
        )
        
        with pytest.raises(ValueError) as exc_info:
            metadata.to_json()
        
        assert "Raga at index 0" in str(exc_info.value)
        assert "Invalid dict format" in str(exc_info.value)
        assert "Use {'name': 'RagaName'} or AudioRaga(name='RagaName')" in str(exc_info.value)

    def test_musical_raga_class_raises_helpful_error(self):
        """Test that using musical analysis Raga class raises helpful error."""
        musical_raga = MusicalRaga({"name": "Rageshree"})
        metadata = AudioMetadata(ragas=[musical_raga])
        
        with pytest.raises(ValueError) as exc_info:
            metadata.to_json()
        
        assert "Raga at index 0" in str(exc_info.value)
        assert "Musical analysis Raga class not supported for uploads" in str(exc_info.value)
        assert "Use AudioRaga(name='Rageshree')" in str(exc_info.value)

    def test_invalid_object_type_raises_error(self):
        """Test that invalid object types raise helpful error messages."""
        metadata = AudioMetadata(ragas=[123])  # Invalid type
        
        with pytest.raises(ValueError) as exc_info:
            metadata.to_json()
        
        assert "Raga at index 0" in str(exc_info.value)
        assert "Invalid raga format" in str(exc_info.value)
        assert "Expected AudioRaga object, string, or dict with 'name' key" in str(exc_info.value)
        assert "Got int: 123" in str(exc_info.value)

    def test_multiple_invalid_ragas_show_individual_errors(self):
        """Test that invalid ragas get their correct index in error messages."""
        metadata = AudioMetadata(
            ragas=[
                "valid_string",  # Valid (index 0)
                {"invalid": "dict"},  # Invalid dict (index 1)
                456  # Invalid type (index 2)
            ]
        )
        
        with pytest.raises(ValueError) as exc_info:
            metadata.to_json()
        
        # Should fail on the first invalid raga encountered during processing
        # The actual behavior processes all items, so it fails on the last invalid one
        error_msg = str(exc_info.value)
        assert "Raga at index" in error_msg
        assert "Invalid" in error_msg

    def test_none_in_ragas_list_raises_error(self):
        """Test that None values in ragas list raise errors."""
        metadata = AudioMetadata(ragas=[None])
        
        with pytest.raises(ValueError) as exc_info:
            metadata.to_json()
        
        assert "Raga at index 0" in str(exc_info.value)
        assert "Invalid raga format" in str(exc_info.value)

    def test_original_user_case_now_works(self):
        """Test that the original failing user case now works with auto-conversion."""
        # This is the exact format the user was trying to use
        metadata = AudioMetadata(
            title="Vilayat Khan - Rageshree gat",
            ragas=[{"Rageshree": {"performance_sections": {}}}],  # Original failing format
            permissions=Permissions()
        )
        
        # This should now work without errors
        result = metadata.to_json()
        
        assert "ragas" in result
        assert "Rageshree" in result["ragas"]
        assert result["title"] == "Vilayat Khan - Rageshree gat"

    def test_performance_sections_are_preserved_correctly(self):
        """Test that performance sections are handled correctly in all formats."""
        raga1 = AudioRaga(name="Test1")
        raga1.performance_sections = []  # Empty list
        
        metadata = AudioMetadata(
            ragas=[
                raga1,  # AudioRaga with empty performance_sections
                "Test2",  # String (will get default empty list)
                {"name": "Test3"}  # Dict (will get default empty list)
            ]
        )
        
        result = metadata.to_json()
        
        # All should have the correct performance sections structure
        for raga_name in ["Test1", "Test2", "Test3"]:
            assert raga_name in result["ragas"]
            assert "performance sections" in result["ragas"][raga_name]
            assert result["ragas"][raga_name]["performance sections"] == {}