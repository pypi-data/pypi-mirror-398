"""
Template Validation for StackWeaver.

Implements three-stage validation (ADR-004):
- Stage 1: Pre-render validation (variable presence)
- Stage 2: YAML syntax validation
- Stage 3: Docker Compose schema validation
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError, meta


class TemplateValidationError(Exception):
    """Raised when template validation fails."""

    def __init__(self, message: str, missing_variables: list[str] | None = None) -> None:
        """
        Initialize validation error.

        Args:
            message: Error message
            missing_variables: List of missing variable names
        """
        super().__init__(message)
        self.missing_variables = missing_variables or []


@dataclass
class ValidationResult:
    """Result of template validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_variables: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


class Stage1Validator:
    """
    Stage 1: Pre-Render Validation.

    Validates that all required template variables are present in the context
    before rendering begins. This ensures fail-fast behavior.
    """

    def __init__(self, template_dir: Path | str) -> None:
        """
        Initialize Stage 1 validator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)), autoescape=False)

    def validate(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> ValidationResult:
        """
        Validate that all required variables are present.

        Args:
            template_name: Name of the template file
            context: Template rendering context

        Returns:
            ValidationResult with validation status and errors

        Raises:
            TemplateValidationError: If validation fails
        """
        result = ValidationResult(is_valid=True)

        try:
            # Extract required variables from template
            required_vars = self.extract_required_variables(template_name)

            # Check for missing variables
            missing_vars = [var for var in required_vars if var not in context]

            if missing_vars:
                result.missing_variables = missing_vars
                error_msg = self._format_missing_variables_error(template_name, missing_vars)
                result.add_error(error_msg)
                raise TemplateValidationError(error_msg, missing_variables=missing_vars)

        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error in {template_name}: {e}"
            result.add_error(error_msg)
            raise TemplateValidationError(error_msg) from e

        return result

    def extract_required_variables(self, template_name: str) -> set[str]:
        """
        Extract all variables required by a template.

        Args:
            template_name: Name of the template file

        Returns:
            Set of required variable names
        """
        try:
            # Load template source
            if self.env.loader is None:
                raise ValueError("Jinja2 environment has no loader")
            source = self.env.loader.get_source(self.env, template_name)[0]

            # Parse template to AST
            ast = self.env.parse(source)

            # Extract undeclared variables (variables that need to be in context)
            required_vars: set[str] = meta.find_undeclared_variables(ast)

            return required_vars

        except Exception as e:
            raise TemplateValidationError(
                f"Failed to extract variables from {template_name}: {e}"
            ) from e

    def _format_missing_variables_error(self, template_name: str, missing_vars: list[str]) -> str:
        """Format error message for missing variables."""
        var_list = ", ".join(sorted(missing_vars))
        return f"Missing variables for template '{template_name}': [{var_list}]"

    def validate_with_includes(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> ValidationResult:
        """
        Validate template including all included sub-templates.

        Args:
            template_name: Name of the main template file
            context: Template rendering context

        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True)

        # Find all included templates
        included_templates = self._find_included_templates(template_name)

        # Validate main template
        try:
            main_result = self.validate(template_name, context)
            result.errors.extend(main_result.errors)
            result.warnings.extend(main_result.warnings)
            result.missing_variables.extend(main_result.missing_variables)
        except TemplateValidationError as e:
            result.is_valid = False
            result.errors.extend([str(e)])
            result.missing_variables.extend(e.missing_variables)

        # Validate included templates
        for included_template in included_templates:
            try:
                included_result = self.validate(included_template, context)
                result.errors.extend(included_result.errors)
                result.warnings.extend(included_result.warnings)
                result.missing_variables.extend(included_result.missing_variables)
            except TemplateValidationError as e:
                result.is_valid = False
                result.errors.extend([str(e)])
                result.missing_variables.extend(e.missing_variables)

        if result.missing_variables:
            result.is_valid = False

        return result

    def _find_included_templates(self, template_name: str) -> list[str]:
        """
        Find all templates included by the given template.

        Args:
            template_name: Name of the template file

        Returns:
            List of included template names
        """
        included = []
        try:
            if self.env.loader is None:
                raise ValueError("Jinja2 environment has no loader")
            source = self.env.loader.get_source(self.env, template_name)[0]

            # Find {% include 'template.j2' %} patterns
            include_pattern = re.compile(r"{%\s*include\s+['\"]([^'\"]+)['\"]\s*%}")
            matches = include_pattern.findall(source)
            included.extend(matches)

        except Exception:
            pass  # If we can't parse, just return empty list

        return included


class YAMLSyntaxError(TemplateValidationError):
    """Raised when YAML syntax validation fails."""

    def __init__(self, message: str, line: int | None = None, column: int | None = None) -> None:
        """
        Initialize YAML syntax error.

        Args:
            message: Error message
            line: Line number where error occurred
            column: Column number where error occurred
        """
        super().__init__(message)
        self.line = line
        self.column = column


class Stage2Validator:
    """
    Stage 2: YAML Syntax Validation.

    Validates that rendered templates produce syntactically valid YAML.
    """

    def __init__(self, template_dir: Path | str) -> None:
        """
        Initialize Stage 2 validator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)), autoescape=False)

    def validate(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> ValidationResult:
        """
        Validate YAML syntax of rendered template.

        Args:
            template_name: Name of the template file
            context: Template rendering context

        Returns:
            ValidationResult with validation status

        Raises:
            YAMLSyntaxError: If YAML syntax is invalid
        """
        import yaml

        result = ValidationResult(is_valid=True)

        try:
            # Render template
            template = self.env.get_template(template_name)
            rendered_content = template.render(context)

            # Parse YAML
            try:
                yaml.safe_load(rendered_content)
            except yaml.YAMLError as e:
                # Extract line and column if available
                line = getattr(e, "problem_mark", None)
                line_num = line.line + 1 if line else None
                column_num = line.column + 1 if line else None

                error_msg = self._format_yaml_error(template_name, str(e), line_num, column_num)
                result.add_error(error_msg)
                raise YAMLSyntaxError(error_msg, line=line_num, column=column_num) from e

        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error in {template_name}: {e}"
            result.add_error(error_msg)
            raise TemplateValidationError(error_msg) from e

        return result

    def _format_yaml_error(
        self,
        template_name: str,
        error_msg: str,
        line: int | None,
        column: int | None,
    ) -> str:
        """Format YAML error message with line/column information."""
        location = f"line {line}" if line else "unknown location"
        if column:
            location += f", column {column}"

        return f"Invalid YAML in template '{template_name}' at {location}: {error_msg}"


class ComposeSchemaError(TemplateValidationError):
    """Raised when Docker Compose schema validation fails."""

    def __init__(self, message: str, stderr: str = "") -> None:
        """
        Initialize Compose schema error.

        Args:
            message: Error message
            stderr: Standard error output from docker compose
        """
        super().__init__(message)
        self.stderr = stderr


class Stage3Validator:
    """
    Stage 3: Docker Compose Schema Validation.

    Validates that YAML conforms to Docker Compose specification using
    the actual Docker Compose CLI.
    """

    def __init__(self, template_dir: Path | str) -> None:
        """
        Initialize Stage 3 validator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)), autoescape=False)

    def validate(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> ValidationResult:
        """
        Validate Docker Compose schema of rendered template.

        Uses `docker compose config --quiet` to validate the schema.

        Args:
            template_name: Name of the template file
            context: Template rendering context

        Returns:
            ValidationResult with validation status

        Raises:
            ComposeSchemaError: If Docker Compose schema is invalid
        """
        import subprocess
        import tempfile

        result = ValidationResult(is_valid=True)

        # Render template
        try:
            template = self.env.get_template(template_name)
            rendered_content = template.render(context)
        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error in {template_name}: {e}"
            result.add_error(error_msg)
            raise TemplateValidationError(error_msg) from e

        # Write to temporary file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".yml",
                delete=False,
                encoding="utf-8",
            ) as f:
                temp_file = f.name
                f.write(rendered_content)

            # Validate with docker compose config
            process_result = subprocess.run(
                ["docker", "compose", "-f", temp_file, "config", "--quiet"],
                capture_output=True,
                text=True,
            )

            if process_result.returncode != 0:
                # Extract error message from stderr
                stderr = process_result.stderr.strip()
                error_msg = self._format_compose_error(template_name, stderr)
                result.add_error(error_msg)
                raise ComposeSchemaError(error_msg, stderr=stderr)

        finally:
            # Clean up temporary file
            if temp_file and Path(temp_file).exists():
                Path(temp_file).unlink()

        return result

    def _format_compose_error(self, template_name: str, stderr: str) -> str:
        """Format Docker Compose error message."""
        return f"Invalid Docker Compose schema in template '{template_name}': {stderr}"


class TemplateValidator:
    """
    Orchestrates all three stages of template validation.

    Implements ADR-004 three-stage validation:
    1. Pre-render: Check variable presence
    2. Syntax: Validate YAML syntax
    3. Schema: Validate Docker Compose schema
    """

    def __init__(self, template_dir: Path | str) -> None:
        """
        Initialize template validator.

        Args:
            template_dir: Directory containing templates
        """
        self.stage1 = Stage1Validator(template_dir)
        self.stage2 = Stage2Validator(template_dir)
        self.stage3 = Stage3Validator(template_dir)

    def validate_pre_render(
        self,
        template_name: str,
        context: dict[str, Any],
        include_subtemplates: bool = True,
    ) -> ValidationResult:
        """
        Run Stage 1 (pre-render) validation.

        Args:
            template_name: Name of template to validate
            context: Rendering context
            include_subtemplates: Whether to validate included templates

        Returns:
            ValidationResult
        """
        if include_subtemplates:
            return self.stage1.validate_with_includes(template_name, context)
        else:
            try:
                return self.stage1.validate(template_name, context)
            except TemplateValidationError as e:
                result = ValidationResult(is_valid=False)
                result.errors.append(str(e))
                result.missing_variables.extend(e.missing_variables)
                return result

    def validate_yaml_syntax(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> ValidationResult:
        """
        Run Stage 2 (YAML syntax) validation.

        Args:
            template_name: Name of template to validate
            context: Rendering context

        Returns:
            ValidationResult
        """
        try:
            return self.stage2.validate(template_name, context)
        except (TemplateValidationError, YAMLSyntaxError) as e:
            result = ValidationResult(is_valid=False)
            result.errors.append(str(e))
            return result

    def validate_compose_schema(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> ValidationResult:
        """
        Run Stage 3 (Docker Compose schema) validation.

        Args:
            template_name: Name of template to validate
            context: Rendering context

        Returns:
            ValidationResult
        """
        try:
            return self.stage3.validate(template_name, context)
        except (TemplateValidationError, ComposeSchemaError) as e:
            result = ValidationResult(is_valid=False)
            result.errors.append(str(e))
            return result

    def validate_all(
        self,
        template_name: str,
        context: dict[str, Any],
        skip_compose_validation: bool = False,
    ) -> ValidationResult:
        """
        Run all validation stages (Stage 1, 2, and optionally 3).

        Args:
            template_name: Name of template to validate
            context: Rendering context
            skip_compose_validation: Skip Stage 3 (Docker Compose validation)
                                     Useful when Docker is not available

        Returns:
            Aggregated ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Stage 1: Pre-render validation
        stage1_result = self.validate_pre_render(template_name, context)
        result.errors.extend(stage1_result.errors)
        result.warnings.extend(stage1_result.warnings)
        result.missing_variables.extend(stage1_result.missing_variables)

        if not stage1_result.is_valid:
            result.is_valid = False
            return result  # Don't proceed if Stage 1 fails

        # Stage 2: YAML syntax validation
        stage2_result = self.validate_yaml_syntax(template_name, context)
        result.errors.extend(stage2_result.errors)
        result.warnings.extend(stage2_result.warnings)

        if not stage2_result.is_valid:
            result.is_valid = False
            return result  # Don't proceed if Stage 2 fails

        # Stage 3: Docker Compose schema validation (optional)
        if not skip_compose_validation:
            stage3_result = self.validate_compose_schema(template_name, context)
            result.errors.extend(stage3_result.errors)
            result.warnings.extend(stage3_result.warnings)

            if not stage3_result.is_valid:
                result.is_valid = False

        return result
