"""
Test data builders using the Builder pattern
"""

from docgen.models.project import ProjectInfo


class ProjectInfoBuilder:
    """Builder for creating ProjectInfo test instances"""

    def __init__(self):
        self._name = "test-project"
        self._description = "A test project"
        self._version = "1.0.0"
        self._languages = ["python"]
        self._frameworks = []
        self._package_managers = {}
        self._dependencies = []
        self._dev_dependencies = []

    def with_name(self, name: str):
        """Set project name"""
        self._name = name
        return self

    def with_description(self, description: str):
        """Set project description"""
        self._description = description
        return self

    def with_version(self, version: str):
        """Set project version"""
        self._version = version
        return self

    def with_languages(self, languages: list[str]):
        """Set project languages"""
        self._languages = languages
        return self

    def with_frameworks(self, frameworks: list[str]):
        """Set project frameworks"""
        self._frameworks = frameworks
        return self

    def with_package_managers(self, package_managers: dict):
        """Set package managers"""
        self._package_managers = package_managers
        return self

    def build(self) -> ProjectInfo:
        """Build the ProjectInfo instance"""
        return ProjectInfo(
            name=self._name,
            description=self._description,
            version=self._version,
            languages=self._languages,
            frameworks=self._frameworks,
            package_managers=self._package_managers,
            dependencies=self._dependencies,
            dev_dependencies=self._dev_dependencies,
        )
