#!/usr/bin/env python3
"""
Language detector verification script
Run with: python -m docgen.language_detector or install package first
"""
from pathlib import Path

from docgen.language_detector import LanguageDetector
from docgen.models import DetectedLanguage


def main():
    print("Verifying LanguageDetector changes...")
    detector = LanguageDetector(project_root)
    languages = detector.detect_languages()

    print(f"Detected {len(languages)} languages.")

    for lang in languages:
        print(f"\nLanguage: {lang.name}")
        print(f"  Type: {type(lang)}")
        print(f"  Package Manager: {lang.package_manager}")
        print(f"  Extensions: {lang.source_extensions}")
        print(f"  RAG Patterns: {lang.get_rag_patterns()}")

        if not isinstance(lang, DetectedLanguage):
            print("  ERROR: Not an instance of DetectedLanguage")
            sys.exit(1)

        if lang.name == "python" and not any(ext == ".py" for ext in lang.source_extensions):
            print("  ERROR: Python should have .py extension")
            sys.exit(1)

    print("\nVerification successful!")


if __name__ == "__main__":
    main()
