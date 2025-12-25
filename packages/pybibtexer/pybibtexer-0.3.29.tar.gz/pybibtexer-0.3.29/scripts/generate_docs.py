from pathlib import Path
from typing import Any


class DocGenerator:
    """Documentation generator class."""

    def __init__(self, package_name: str, source_dir: str, docs_dir: str = "docs"):
        self.package_name = package_name
        self.source_dir = Path(source_dir)
        self.docs_dir = Path(docs_dir)
        self.api_dir = self.docs_dir / "api-auto"

        # Create necessary directories
        self.api_dir.mkdir(parents=True, exist_ok=True)

    def discover_modules(self) -> list[Path]:
        modules = []

        for py_file in self.source_dir.rglob("*.py"):
            # Skip __pycache__ directories and test files
            if "__pycache__" in str(py_file) or "test" in str(py_file).lower():
                continue

            # Skip empty files and __init__.py files (handled separately)
            if py_file.name == "__init__.py":
                continue

            modules.append(py_file)

        return modules

    def get_module_info(self, module_path: Path) -> dict[str, Any]:
        # Calculate relative import path
        relative_path = module_path.relative_to(self.source_dir)
        module_name = str(relative_path).replace("/", ".").replace("\\", ".")
        module_name = module_name[:-3]  # replace(".py", "")

        return {
            "path": module_path,
            "name": module_name,
            "import_path": f"{self.package_name}.{module_name}",
            "doc_path": self.api_dir / f"{module_name}.md",
        }

    def generate_module_doc(self, module_info: dict[str, Any]) -> str:
        module_name = module_info["name"]
        import_path = module_info["import_path"]

        content = [
            f"# {module_name}",
            "",
            f"::: {import_path}",
            "    options:",
            "      show_root_heading: false",
            "      show_submodules: true",
            "      heading_level: 2",
            "      show_source: true",
            "      show_category_heading: true",
            "",
        ]

        return "\n".join(content)

    def generate_api_index(self) -> str:
        modules = self.discover_modules()
        module_infos = [self.get_module_info(module) for module in modules]

        content = [
            "# API Reference",
            "",
            f"This is the complete API reference documentation for the {self.package_name} library.",
            "",
            "## Module List",
            "",
        ]

        # Group modules by directory
        modules_by_dir = {}
        for info in module_infos:
            dir_path = str(Path(info["name"]).parent)
            if dir_path == ".":
                dir_path = "Root Modules"
            if dir_path not in modules_by_dir:
                modules_by_dir[dir_path] = []
            modules_by_dir[dir_path].append(info)

        # Generate directory structure
        for dir_name in sorted(modules_by_dir.keys()):
            content.append(f"### {dir_name}")
            content.append("")

            for info in sorted(modules_by_dir[dir_name], key=lambda x: x["name"]):
                module_name = info["name"]
                doc_file = f"api-auto/{module_name}.md"
                content.append(f"- [{module_name}]({doc_file})")

            content.append("")

        return "\n".join(content)

    def write_file(self, filepath: Path, content: str) -> None:
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        print(f"✓ Generated documentation: {filepath}")

    def generate_all(self) -> None:
        """Generate all documentation."""
        print("Starting API documentation generation...")

        # Generate documentation for individual modules
        modules = self.discover_modules()
        print(f"Found {len(modules)} modules")

        for module_path in modules:
            module_info = self.get_module_info(module_path)
            doc_content = self.generate_module_doc(module_info)
            self.write_file(module_info["doc_path"], doc_content)

        # Generate API index
        api_index_content = self.generate_api_index()
        self.write_file(self.docs_dir / "api-auto.md", api_index_content)

        print("Documentation generation completed!")


if __name__ == "__main__":
    generator = DocGenerator("pybibtexer", "pybibtexer")
    generator.generate_all()
