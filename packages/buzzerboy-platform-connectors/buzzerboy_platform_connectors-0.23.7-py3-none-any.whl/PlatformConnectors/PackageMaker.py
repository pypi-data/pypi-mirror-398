"""
Buzzerboy Platform Connectors - Package Automation Module

This module provides automated package management and build functionality for Python
projects. It handles version management, changelog generation, and package.json creation
for semantic-release workflows.

Key Features:
    - Automated version incrementing from pyproject.toml
    - Changelog generation from git commit history  
    - Package.json creation for semantic-release
    - Automated setup.py configuration
    - Requirements handling and manifest management

Example:
    Basic usage::

        from PlatformConnectors.PackageMaker import PackageAutomation
        
        # Auto package with version increment
        package = PackageAutomation.auto_package()
        
        # Manual setup with existing package
        package = PackageAutomation('/path/to/project')
        package.increment_version()
        package.generate_package_json()

Author:
    Buzzerboy Inc

Version:
    0.8.6
"""

from setuptools import setup, find_packages
import os, toml, json, subprocess

class PackageAutomation:
    """
    Automated package management and build system.
    
    This class provides comprehensive package automation functionality including
    version management, changelog generation, and build configuration. It reads
    project metadata from pyproject.toml and automates common packaging tasks.
    
    Attributes:
        filepath (str): Project directory path.
        project (dict): Project metadata from pyproject.toml.
        name (str): Package name.
        version (str): Current package version.
        description (str): Package description.
        author (str): Package author name.
        license (str): Package license identifier.
    
    Example:
        ::
        
            # Initialize with current directory
            automation = PackageAutomation()
            
            # Initialize with specific path
            automation = PackageAutomation('/path/to/project')
            
            # Access project metadata
            print(f"Package: {automation.name} v{automation.version}")
    """

    def __init__(self, filepath=None):
        """
        Initialize PackageAutomation with project metadata.
        
        Args:
            filepath (str, optional): Project directory path. If not provided,
                                    uses the directory containing this module.
        
        Raises:
            FileNotFoundError: If pyproject.toml is not found.
            toml.TomlDecodeError: If pyproject.toml contains invalid TOML.
            KeyError: If required project metadata is missing.
        """

        if filepath:
            self.filepath = filepath
        else:
            self.filepath = os.path.dirname(os.path.abspath(__file__))

        # Read pyproject.toml and gather project metadata
        with open(os.path.join(self.filepath, 'pyproject.toml'), 'r') as f:
            pyproject_data = toml.load(f)

        self.project = pyproject_data.get('project', {})
        self.name = self.project.get('name', 'unknown')
        self.version = self.project.get('version', '0.0.1')
        self.description = self.project.get('description', '')
        self.author = self.project.get('authors', [{}])[0].get('name', '')
        self.license = self.project.get('license', {}).get('file', 'MIT')

    def generate_package_json(self):
        """
        Generate package.json for semantic-release automation.
        
        Creates a package.json file with semantic-release configuration and
        project metadata. This enables automated version management and
        release processes in CI/CD pipelines.
        
        The generated package.json includes:
            - Project metadata (name, version, description, author)
            - Semantic-release dependencies and plugins
            - Release configuration for main branch
        
        Example:
            ::
            
                automation = PackageAutomation()
                automation.generate_package_json()
                # Creates package.json with semantic-release config
        
        Note:
            The package.json is created in the project root directory and
            overwrites any existing package.json file.
        """
        package_json = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "main": "index.js",
            "scripts": {
                "semantic-release": "semantic-release"
            },
            "devDependencies": {
                "@semantic-release/changelog": "*",
                "@semantic-release/commit-analyzer": "*",
                "@semantic-release/git": "*",
                "@semantic-release/gitlab": "*",
                "@semantic-release/github": "*",            
                "@semantic-release/release-notes-generator": "*",
                "semantic-release": "*"
            },
            "release": {
                "branches": ["main"]
            },
            "author": self.author,
            "license": self.license
        }

        with open('package.json', 'w') as f:
            json.dump(package_json, f, indent=2)

    def increment_version(self):
        """
        Automatically increment the package version.
        
        Increments the patch version number and updates pyproject.toml.
        When patch version reaches 10, it resets to 0 and increments
        the minor version.
        
        Version Format: MAJOR.MINOR.PATCH
        
        Example:
            ::
            
                # Current version: 1.2.3
                automation.increment_version()
                # New version: 1.2.4
                
                # Current version: 1.2.9  
                automation.increment_version()
                # New version: 1.3.0
        
        Note:
            This method modifies the pyproject.toml file and updates the
            instance's version attribute.
        """
        # Increment version
        major, minor, patch = self.version.split('.')
        patch = int(patch) + 1

        if patch >= 10:
            patch = 0
            minor = int(minor) + 1

        self.version = f'{major}.{minor}.{patch}'
        self.project['version'] = self.version

        # Read the entire pyproject.toml file
        with open('pyproject.toml', 'r') as f:
            pyproject_data = toml.load(f)

        # Update only the version property in the [project] section
        pyproject_data['project']['version'] = self.version

        # Write the updated content back to the file
        with open('pyproject.toml', 'w') as f:
            toml.dump(pyproject_data, f)

    def generate_changelog_from_git_log(self):
        """
        Generate CHANGELOG.md from git commit history.
        
        Parses git log to create a structured changelog grouped by versions.
        Merge commits trigger minor version increments, creating natural
        version boundaries in the changelog.
        
        The generated changelog includes:
            - Versions in descending order (newest first)
            - Commit messages grouped by version
            - Automatic version detection from merge commits
        
        Example:
            ::
            
                automation = PackageAutomation()
                automation.generate_changelog_from_git_log()
                # Creates/updates CHANGELOG.md
        
        Output Format:
            The changelog follows this structure::
            
                ## Version X.Y.Z
                - Commit message 1
                - Commit message 2
                
                ## Version X.Y.Z-1
                - Previous commit 1
                - Previous commit 2
        
        Note:
            This method overwrites any existing CHANGELOG.md file and
            requires the project to be in a git repository.
        """
        # Get the git log
        git_log = subprocess.check_output(['git', 'log', '--pretty=format:%s']).decode('utf-8')
        commits = git_log.split('\n')

        # reverse commits array with last line being first line, and first line being last line
        commits = commits[::-1]

        # Group commits by version
        changelog = {}
        current_version = self.version
        for commit in commits:
            if 'Merge' in commit:
                # Increment minor version for PR merge commits
                major, minor, patch = current_version.split('.')
                minor = int(minor) + 1
                current_version = f'{major}.{minor}.{patch}'
                self.version = f'{major}.{minor}.{patch}'
                changelog[current_version] = []
            if current_version not in changelog:
                changelog[current_version] = []
            changelog[current_version].append(commit)

        # Write the changelog to CHANGELOG.md
        with open('CHANGELOG.md', 'w') as f:
            for version, changes in sorted(changelog.items(), reverse=True):
                f.write(f'## Version {version}\n')
                for change in changes:
                    f.write(f'- {change}\n')
                f.write('\n')

    def cleanUpMarkdown(self):
        """
        Clean up generated markdown files by removing unwanted content.
        
        Removes lines starting with "// filepath:" from CHANGELOG.md to
        clean up automatically generated content that shouldn't be in
        the final changelog.
        
        Example:
            ::
            
                automation = PackageAutomation()
                automation.cleanUpMarkdown()
                # Removes filepath comments from CHANGELOG.md
        
        Note:
            This method modifies CHANGELOG.md in place, removing any lines
            that start with "// filepath:" which may be added by automated
            tools or IDEs.
        """
        # Remove lines starting with "// filepath:" from CHANGELOG.md
        with open('CHANGELOG.md', 'r') as f:
            lines = f.readlines()
        
        with open('CHANGELOG.md', 'w') as f:
            for line in lines:
                if not line.startswith('// filepath:'):
                    f.write(line)


    @staticmethod
    def auto_package(filepath=None):
        """
        Perform complete automated package management workflow.
        
        This static method executes the full automation workflow including
        changelog generation, version incrementing, and package.json creation.
        
        Args:
            filepath (str, optional): Project directory path. If not provided,
                                    uses the current directory.
        
        Returns:
            PackageAutomation: Configured automation instance.
        
        Example:
            ::
            
                # Complete automation workflow
                package = PackageAutomation.auto_package()
                
                # Automation for specific project
                package = PackageAutomation.auto_package('/path/to/project')
        
        Workflow Steps:
            1. Generate changelog from git history
            2. Clean up markdown formatting
            3. Increment version number
            4. Generate package.json for semantic-release
        
        Note:
            This method requires the project to be in a git repository and
            have a valid pyproject.toml file.
        """
        autoPackage = PackageAutomation(filepath=filepath)

        # Generate changelog from git log
        autoPackage.generate_changelog_from_git_log()
        autoPackage.cleanUpMarkdown()

        # Increment version
        autoPackage.increment_version()

        # Generate package.json
        autoPackage.generate_package_json()

        return autoPackage


    def parse_requirements(self, filename):
        """
        Parse requirements.txt file and return list of dependencies.
        
        Reads a requirements file and extracts package dependencies,
        filtering out comments and empty lines.
        
        Args:
            filename (str): Name of the requirements file to parse.
        
        Returns:
            list: List of package requirement strings.
        
        Example:
            ::
            
                # requirements.txt contains:
                # django>=4.0
                # requests
                # # This is a comment
                
                automation = PackageAutomation()
                deps = automation.parse_requirements('requirements.txt')
                # Returns: ['django>=4.0', 'requests']
        
        Note:
            Lines starting with '#' are treated as comments and ignored.
            Empty lines are also filtered out.
        """
        absolute_path = os.path.join(self.filepath, filename)
        with open(absolute_path, 'r') as file:
            lines = file.readlines()
            return [line.strip() for line in lines if line.strip() and not line.startswith('#')]

    def ensure_manifest_includes_requirements(self):
        """
        Ensure MANIFEST.in includes requirements.txt for package distribution.
        
        Checks if MANIFEST.in exists and includes the requirements.txt file.
        If not, adds the include directive to ensure requirements are bundled
        with the package distribution.
        
        Example:
            ::
            
                automation = PackageAutomation()
                automation.ensure_manifest_includes_requirements()
                # Ensures MANIFEST.in contains: include requirements.txt
        
        Note:
            This method creates MANIFEST.in if it doesn't exist, or appends
            the requirements include if missing from an existing file.
        """
        manifest_file = 'MANIFEST.in'
        requirements_line = 'include requirements.txt\n'
        if os.path.exists(manifest_file):
            with open(manifest_file, 'r') as file:
                lines = file.readlines()
            if requirements_line not in lines:
                with open(manifest_file, 'a') as file:
                    file.write(requirements_line)
        else:
            with open(manifest_file, 'w') as file:
                file.write(requirements_line)


    @staticmethod
    def auto_setup(package):
        """
        Automated setup.py configuration using PackageAutomation instance.
        
        Configures and executes setuptools setup() with project metadata
        from pyproject.toml and automatic requirements handling.
        
        Args:
            package (PackageAutomation): Configured PackageAutomation instance.
        
        Example:
            ::
            
                # Complete automated setup
                package = PackageAutomation()
                PackageAutomation.auto_setup(package)
        
        Configuration Includes:
            - Project metadata from pyproject.toml
            - Automatic package discovery
            - Requirements parsing from requirements.txt
            - MANIFEST.in setup for package distribution
        
        Note:
            This method calls setuptools.setup() and should be used in
            setup.py files for package distribution.
        """

        # Ensure MANIFEST.in includes requirements.txt
        package.ensure_manifest_includes_requirements()


        # Read pyproject.toml
        pyproject = toml.load('pyproject.toml')
        project = pyproject['project']


        setup(
            name=project['name'],
            version=project['version'],
            author=project['authors'][0]['name'],
            author_email=project['authors'][0]['email'],
            description=project['description'],
            long_description=open('README.md').read(),
            long_description_content_type='text/markdown',
            url=project['urls']['Homepage'],
            packages=find_packages(),
            classifiers=project['classifiers'],
            python_requires=project['requires-python'],
            install_requires=package.parse_requirements("requirements.txt"),
            license=project['license']
        )


