"""
Test Task 7: Documentation Structure Verification

Verifies that documentation files exist and contain required sections.
"""
import os


def test_federasyon_readme_exists():
    """Verify federasyon/README.md exists."""
    readme_path = os.path.join(
        os.path.dirname(__file__), '..', 'README.md'
    )
    assert os.path.exists(readme_path), "federasyon/README.md does not exist"


def test_federasyon_readme_has_sections():
    """Verify federasyon/README.md contains required sections."""
    readme_path = os.path.join(
        os.path.dirname(__file__), '..', 'README.md'
    )
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verify required sections
    required_sections = [
        'Genel Bakış',
        'Bileşenler',
        'db_fed.py',
        'scorer.py',
        'ranker.py',
        'pipeline.py',
        'Kullanım',
        'Kurallar',
        'Testing',
        'Errors & Troubleshooting',
        'Yapı'
    ]

    for section in required_sections:
        assert section in content, f"Missing section: {section}"


def test_docs_readme_exists():
    """Verify docs/README.md exists."""
    readme_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'docs', 'README.md'
    )
    assert os.path.exists(readme_path), "docs/README.md does not exist"


def test_docs_readme_has_phase3a():
    """Verify docs/README.md contains Phase 3A section."""
    readme_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'docs', 'README.md'
    )
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verify Phase 3A section
    assert 'Phase 3' in content or 'Phase 3A' in content, "Missing Phase 3A section"
    assert 'Data Pipeline' in content, "Missing Data Pipeline reference"


def test_architecture_md_exists():
    """Verify docs/ARCHITECTURE.md exists."""
    arch_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'docs', 'ARCHITECTURE.md'
    )
    assert os.path.exists(arch_path), "docs/ARCHITECTURE.md does not exist"


def test_architecture_md_has_sections():
    """Verify docs/ARCHITECTURE.md contains required sections."""
    arch_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'docs', 'ARCHITECTURE.md'
    )
    with open(arch_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verify required sections
    required_sections = [
        'System Overview',
        'Data Flow',
        'Schema',
        'fed_results',
        'fed_athlete_best'
    ]

    for section in required_sections:
        assert section in content, f"Missing section in ARCHITECTURE.md: {section}"


def test_documentation_encoding():
    """Verify all documentation files use UTF-8 encoding."""
    files_to_check = [
        os.path.join(os.path.dirname(__file__), '..', 'README.md'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'README.md'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'ARCHITECTURE.md'),
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            # Try to read with UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # If it reads successfully, encoding is OK
            assert isinstance(content, str)


def test_turkish_character_support():
    """Verify Turkish characters are present in documentation."""
    readme_path = os.path.join(
        os.path.dirname(__file__), '..', 'README.md'
    )
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for Turkish characters: İ, ş, ç, ğ, ü, ö
    turkish_chars_found = any(c in content for c in 'İşçğüö')
    assert turkish_chars_found, "Turkish characters not found in documentation"
