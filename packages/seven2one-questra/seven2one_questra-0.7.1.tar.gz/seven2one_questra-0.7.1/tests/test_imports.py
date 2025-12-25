"""
Tests für das Questra Metapackage.

Das Metapackage dient as Dependency-Aggregator and installiert alle Questra-Komponenten.
Da es den seven2one.questra Namespace nutzt, kann es keine Re-Exports bereitstellen
(würde Namespace Package Mechanismus brechen).

Diese Tests validieren:
1. Alle Sub-Packages sind korrekt importierbar
2. Namespace Package Struktur funktioniert
3. Dependencies sind installiert
"""

import importlib
import sys

import pytest


class TestNamespacePackageStructure:
    """Tests für die Namespace Package Struktur."""

    def test_seven2one_namespace_exists(self):
        """Test: seven2one Namespace existiert."""
        import seven2one

        assert seven2one is not None

    def test_seven2one_questra_namespace_exists(self):
        """Test: seven2one.questra Namespace existiert."""
        import seven2one.questra

        assert seven2one.questra is not None

    def test_namespace_has_no_init(self):
        """Test: Namespace Packages haben kein reguläres __init__.py (PEP 420)."""
        import seven2one.questra

        # Wichtiger: Namespace package sollte __path__ haben (Liste of Pfaden)
        assert hasattr(seven2one.questra, "__path__"), (
            "seven2one.questra sollte __path__ haben (Namespace Package)"
        )

        # __path__ sollte eine Liste/Sequence sein with mehreren Einträgen
        # (ein Eintrag pro installiertem Sub-Package)
        path_list = list(seven2one.questra.__path__)
        assert len(path_list) >= 3, (
            f"seven2one.questra sollte mind. 3 Pfade haben (data, auth, automation), "
            f"hat aber: {len(path_list)}"
        )


class TestSubPackageImports:
    """Tests für Imports from Sub-Packages."""

    def test_authentication_package_importable(self):
        """Test: Authentication Package ist importierbar."""
        from seven2one.questra.authentication import QuestraAuthentication

        assert QuestraAuthentication is not None

    def test_data_package_importable(self):
        """Test: Data Package ist importierbar."""
        from seven2one.questra.data import QuestraData

        assert QuestraData is not None

    def test_automation_package_importable(self):
        """Test: Automation Package ist importierbar."""
        from seven2one.questra.automation import QuestraAutomation

        assert QuestraAutomation is not None

    def test_multiple_imports_from_same_namespace(self):
        """Test: Mehrere Imports from demselben Namespace funktionieren."""
        from seven2one.questra.authentication import (
            OAuth2Authentication,
            QuestraAuthentication,
        )
        from seven2one.questra.data import QuestraData, QuestraDataCore

        assert QuestraAuthentication is not None
        assert OAuth2Authentication is not None
        assert QuestraData is not None
        assert QuestraDataCore is not None

    def test_authentication_main_classes(self):
        """Test: Hauptklassen from Authentication sind importierbar."""
        from seven2one.questra.authentication import (
            OAuth2Authentication,
            OAuth2InteractiveUserCredential,
            OAuth2ServiceCredential,
            QuestraAuthentication,
        )

        assert OAuth2Authentication is not None
        assert OAuth2ServiceCredential is not None
        assert OAuth2InteractiveUserCredential is not None
        assert QuestraAuthentication is not None

    def test_data_main_classes(self):
        """Test: Hauptklassen from Data sind importierbar."""
        from seven2one.questra.data import (
            Inventory,
            Namespace,
            QuestraData,
            QuestraDataCore,
        )

        assert QuestraData is not None
        assert QuestraDataCore is not None
        assert Inventory is not None
        assert Namespace is not None

    def test_data_models_importable(self):
        """Test: Data Models sind importierbar."""
        from seven2one.questra.data import (
            ConflictAction,
            DataType,
            SortOrder,
            StringProperty,
        )

        assert ConflictAction is not None
        assert SortOrder is not None
        assert DataType is not None
        assert StringProperty is not None


class TestExceptionImports:
    """Tests für Exception-Klassen."""

    def test_authentication_exceptions_importable(self):
        """Test: Authentication Exceptions sind importierbar."""
        from seven2one.questra.authentication import (
            AuthenticationError,
            InvalidCredentialsError,
            NotAuthenticatedError,
        )

        assert AuthenticationError is not None
        assert NotAuthenticatedError is not None
        assert InvalidCredentialsError is not None

    def test_data_exceptions_importable(self):
        """Test: Data Exceptions sind importierbar."""
        from seven2one.questra.data import QuestraError, QuestraGraphQLError

        assert QuestraError is not None
        assert QuestraGraphQLError is not None

    def test_exceptions_are_exception_subclasses(self):
        """Test: Exception-Klassen sind tatsächlich Exceptions."""
        from seven2one.questra.authentication import AuthenticationError
        from seven2one.questra.data import QuestraError

        assert issubclass(AuthenticationError, Exception)
        assert issubclass(QuestraError, Exception)


class TestMetaPackageModule:
    """Tests für das questra_meta Modul."""

    def test_questra_meta_exists(self):
        """Test: questra_meta Modul existiert."""
        import questra_meta

        assert questra_meta is not None

    def test_questra_meta_has_version(self):
        """Test: questra_meta hat __version__ Attribut."""
        import questra_meta

        assert hasattr(questra_meta, "__version__")
        assert isinstance(questra_meta.__version__, str)

    def test_version_format(self):
        """Test: Version hat korrektes Format (semver)."""
        import questra_meta

        version = questra_meta.__version__
        parts = version.split(".")
        assert len(parts) >= 2, f"Version '{version}' ist kein gültiges Semver-Format"
        assert parts[0].isdigit(), f"Major-Version ist keine Zahl: {parts[0]}"
        assert parts[1].isdigit(), f"Minor-Version ist keine Zahl: {parts[1]}"


class TestPackageAvailability:
    """Tests für Package-Verfügbarkeit."""

    def test_all_subpackages_in_sys_modules(self):
        """Test: Nach Import sind alle Sub-Packages in sys.modules."""
        # Imports durchführen
        import seven2one.questra.authentication
        import seven2one.questra.automation
        import seven2one.questra.data

        # Prüfen ob in sys.modules
        assert "seven2one.questra.authentication" in sys.modules
        assert "seven2one.questra.data" in sys.modules
        assert "seven2one.questra.automation" in sys.modules

    def test_dynamic_import_works(self):
        """Test: Dynamische Imports funktionieren."""
        packages = [
            "seven2one.questra.authentication",
            "seven2one.questra.data",
            "seven2one.questra.automation",
        ]

        for package_name in packages:
            module = importlib.import_module(package_name)
            assert module is not None


class TestNamespaceIsolation:
    """Tests für Namespace-Isolation."""

    def test_no_cross_contamination(self):
        """Test: Sub-Packages kontaminieren sich nicht gegenseitig."""
        # QuestraData sollte nicht im authentication Namespace sein
        import seven2one.questra.authentication as auth_module
        from seven2one.questra.authentication import QuestraAuthentication
        from seven2one.questra.data import QuestraData

        assert not hasattr(auth_module, "QuestraData")

        # QuestraAuthentication sollte nicht im data Namespace sein
        import seven2one.questra.data as data_module

        assert not hasattr(data_module, "QuestraAuthentication")
