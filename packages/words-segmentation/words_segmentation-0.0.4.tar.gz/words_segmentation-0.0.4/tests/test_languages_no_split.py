import os
from importlib import reload

import pytest


def test_no_split_removes_language():
    """Test that LANGUAGES_NO_SPLIT removes specified languages."""
    # Set environment variable before importing
    os.environ["LANGUAGES_NO_SPLIT"] = "Chinese"

    # Import the module (will be reloaded in the fixture)
    import words_segmentation.languages as languages_module
    reload(languages_module)

    # Verify Chinese was removed
    assert "Chinese" not in languages_module.LANGUAGE_SPECS
    assert "Japanese" in languages_module.LANGUAGE_SPECS
    assert "SignWriting" in languages_module.LANGUAGE_SPECS
    assert "Default" in languages_module.LANGUAGE_SPECS

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_removes_multiple_languages():
    """Test that LANGUAGES_NO_SPLIT removes multiple languages."""
    os.environ["LANGUAGES_NO_SPLIT"] = "Chinese,Japanese"

    import words_segmentation.languages as languages_module
    reload(languages_module)

    # Verify both were removed
    assert "Chinese" not in languages_module.LANGUAGE_SPECS
    assert "Japanese" not in languages_module.LANGUAGE_SPECS
    assert "SignWriting" in languages_module.LANGUAGE_SPECS
    assert "Default" in languages_module.LANGUAGE_SPECS

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_handles_whitespace():
    """Test that LANGUAGES_NO_SPLIT handles whitespace in language names."""
    os.environ["LANGUAGES_NO_SPLIT"] = " Chinese , Japanese "

    import words_segmentation.languages as languages_module
    reload(languages_module)

    # Verify both were removed despite whitespace
    assert "Chinese" not in languages_module.LANGUAGE_SPECS
    assert "Japanese" not in languages_module.LANGUAGE_SPECS

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_invalid_language_raises_error():
    """Test that specifying an invalid language raises ValueError."""
    os.environ["LANGUAGES_NO_SPLIT"] = "InvalidLanguage"

    import words_segmentation.languages as languages_module

    with pytest.raises(ValueError, match="Language 'InvalidLanguage' specified in LANGUAGES_NO_SPLIT does not exist"):
        reload(languages_module)

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_one_valid_one_invalid_raises_error():
    """Test that having one valid and one invalid language raises ValueError."""
    os.environ["LANGUAGES_NO_SPLIT"] = "Chinese,InvalidLanguage"

    import words_segmentation.languages as languages_module

    with pytest.raises(ValueError, match="Language 'InvalidLanguage' specified in LANGUAGES_NO_SPLIT does not exist"):
        reload(languages_module)

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_cannot_remove_default():
    """Test that attempting to remove 'Default' raises ValueError."""
    os.environ["LANGUAGES_NO_SPLIT"] = "Default"

    import words_segmentation.languages as languages_module

    with pytest.raises(ValueError, match="Cannot remove 'Default' language from LANGUAGE_SPECS"):
        reload(languages_module)

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_empty_string_does_nothing():
    """Test that an empty LANGUAGES_NO_SPLIT doesn't affect LANGUAGE_SPECS."""
    os.environ["LANGUAGES_NO_SPLIT"] = ""

    import words_segmentation.languages as languages_module
    reload(languages_module)

    # Verify all languages are still present
    assert "Chinese" in languages_module.LANGUAGE_SPECS
    assert "Japanese" in languages_module.LANGUAGE_SPECS
    assert "SignWriting" in languages_module.LANGUAGE_SPECS
    assert "Default" in languages_module.LANGUAGE_SPECS

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_whitespace_only_does_nothing():
    """Test that whitespace-only LANGUAGES_NO_SPLIT doesn't affect LANGUAGE_SPECS."""
    os.environ["LANGUAGES_NO_SPLIT"] = "   "

    import words_segmentation.languages as languages_module
    reload(languages_module)

    # Verify all languages are still present
    assert "Chinese" in languages_module.LANGUAGE_SPECS
    assert "Japanese" in languages_module.LANGUAGE_SPECS
    assert "SignWriting" in languages_module.LANGUAGE_SPECS
    assert "Default" in languages_module.LANGUAGE_SPECS

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


def test_no_split_with_empty_comma_separated_values():
    """Test that empty values in comma-separated list are ignored."""
    os.environ["LANGUAGES_NO_SPLIT"] = "Chinese,,Japanese,"

    import words_segmentation.languages as languages_module
    reload(languages_module)

    # Verify both were removed (empty strings ignored)
    assert "Chinese" not in languages_module.LANGUAGE_SPECS
    assert "Japanese" not in languages_module.LANGUAGE_SPECS
    assert "SignWriting" in languages_module.LANGUAGE_SPECS
    assert "Default" in languages_module.LANGUAGE_SPECS

    # Clean up
    del os.environ["LANGUAGES_NO_SPLIT"]
    reload(languages_module)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
