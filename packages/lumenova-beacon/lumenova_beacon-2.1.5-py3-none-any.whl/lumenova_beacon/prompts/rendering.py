"""Prompt template rendering and compilation.

This module handles all template-related operations including:
- Jinja2-style variable substitution ({{var}})
- Template compilation with variable injection
- Conversion to Python template format
"""

from __future__ import annotations

import re

from typing import Any

from lumenova_beacon.exceptions import PromptCompilationError
from lumenova_beacon.prompts.types import PromptType


# Precompiled regex patterns for better performance
_JINJA2_VAR_PATTERN = re.compile(r'\{\{\s*(\w+)\s*\}\}')
_REMAINING_VAR_PATTERN = re.compile(r'\{\{[^}]+\}\}')


class PromptRenderer:
    """Handles prompt template rendering and compilation.

    This class provides static methods for rendering Jinja2-style templates,
    compiling prompts with variables, and converting templates to different formats.
    """

    @staticmethod
    def render_template(template: str, variables: dict[str, Any]) -> str:
        """Render a single template string with Jinja2-style variables.

        Args:
            template: Template string with {{variable}} syntax
            variables: Dictionary of variables

        Returns:
            Rendered string

        Raises:
            Exception: If rendering fails or variables are missing

        Examples:
            >>> PromptRenderer.render_template('Hello {{name}}!', {'name': 'Alice'})
            'Hello Alice!'
        """
        try:
            # Simple Jinja2-style replacement using regex
            result = template
            for key, value in variables.items():
                # Use precompiled pattern with dynamic key
                pattern = re.compile(r'\{\{\s*' + re.escape(key) + r'\s*\}\}')
                result = pattern.sub(str(value), result)

            # Check for remaining unreplaced variables using precompiled pattern
            remaining = _REMAINING_VAR_PATTERN.findall(result)
            if remaining:
                missing_vars = [v.strip('{}').strip() for v in remaining]
                raise ValueError(f'Missing variables: {", ".join(missing_vars)}')

            return result
        except Exception as e:
            raise Exception(f'Template rendering failed: {e}') from e

    @staticmethod
    def compile_text_prompt(template: str, variables: dict[str, Any]) -> str:
        """Compile a text prompt with variables.

        Args:
            template: Template string with {{variable}} syntax
            variables: Dictionary of variables to substitute

        Returns:
            Rendered string

        Raises:
            PromptCompilationError: If compilation fails
        """
        try:
            return PromptRenderer.render_template(template, variables)
        except Exception as e:
            raise PromptCompilationError(f'Failed to compile text prompt: {e}') from e

    @staticmethod
    def compile_chat_prompt(
        messages: list[dict[str, str]], variables: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Compile a chat prompt with variables.

        Args:
            messages: List of message dictionaries with role and content
            variables: Dictionary of variables to substitute

        Returns:
            List of message dictionaries with rendered content

        Raises:
            PromptCompilationError: If compilation fails
        """
        try:
            return [
                {
                    'role': msg['role'],
                    'content': PromptRenderer.render_template(msg['content'], variables),
                }
                for msg in messages
            ]
        except Exception as e:
            raise PromptCompilationError(f'Failed to compile chat prompt: {e}') from e

    @staticmethod
    def compile_prompt(
        prompt_type: PromptType, content: dict[str, Any], variables: dict[str, Any]
    ) -> str | list[dict[str, str]]:
        """Compile a prompt with variable substitution.

        Args:
            prompt_type: Type of prompt (TEXT or CHAT)
            content: Prompt content (template or messages)
            variables: Dictionary of variables to substitute

        Returns:
            - For text prompts: Rendered string
            - For chat prompts: List of message dictionaries

        Raises:
            PromptCompilationError: If compilation fails

        Examples:
            Text prompt:
            >>> content = {'template': 'Hello {{name}}!'}
            >>> PromptRenderer.compile_prompt(PromptType.TEXT, content, {'name': 'Bob'})
            'Hello Bob!'

            Chat prompt:
            >>> content = {'messages': [{'role': 'user', 'content': 'Hi {{name}}'}]}
            >>> PromptRenderer.compile_prompt(PromptType.CHAT, content, {'name': 'Alice'})
            [{'role': 'user', 'content': 'Hi Alice'}]
        """
        try:
            if prompt_type == PromptType.TEXT:
                template = content.get('template', '')
                return PromptRenderer.compile_text_prompt(template, variables)
            else:  # CHAT
                messages = content.get('messages', [])
                return PromptRenderer.compile_chat_prompt(messages, variables)
        except PromptCompilationError:
            raise
        except Exception as e:
            raise PromptCompilationError(f'Failed to compile prompt: {e}') from e

    @staticmethod
    def to_template_text(template: str) -> str:
        """Convert Jinja2 text template to Python f-string format.

        Converts {{variable}} to {variable} for use with Python f-strings.

        Args:
            template: Jinja2 template string

        Returns:
            Python-compatible template string

        Examples:
            >>> PromptRenderer.to_template_text('Hello {{name}}!')
            'Hello {name}!'
        """
        # Convert {{var}} to {var} using precompiled pattern
        return _JINJA2_VAR_PATTERN.sub(r'{\1}', template)

    @staticmethod
    def to_template_chat(messages: list[dict[str, str]]) -> list[dict[str, str]]:
        """Convert Jinja2 chat messages to Python f-string format.

        Converts {{variable}} to {variable} in all message contents.

        Args:
            messages: List of message dictionaries with role and content

        Returns:
            List of messages with converted templates

        Examples:
            >>> messages = [{'role': 'user', 'content': 'Hi {{name}}'}]
            >>> PromptRenderer.to_template_chat(messages)
            [{'role': 'user', 'content': 'Hi {name}'}]
        """
        # Convert messages using precompiled pattern
        return [
            {
                'role': msg['role'],
                'content': _JINJA2_VAR_PATTERN.sub(r'{\1}', msg['content']),
            }
            for msg in messages
        ]

    @staticmethod
    def to_template(prompt_type: PromptType, content: dict[str, Any]) -> str | list[dict[str, str]]:
        """Convert Jinja2 template to Python f-string format.

        Converts {{variable}} to {variable} for use with Python f-strings.
        Works for both TEXT and CHAT prompts.

        Args:
            prompt_type: Type of prompt (TEXT or CHAT)
            content: Prompt content (template or messages)

        Returns:
            - For TEXT prompts: Python-compatible template string
            - For CHAT prompts: List of messages with converted templates

        Examples:
            Text prompt:
            >>> content = {'template': 'Hello {{name}}!'}
            >>> template = PromptRenderer.to_template(PromptType.TEXT, content)
            >>> name = 'Charlie'
            >>> result = eval(f'f"{template}"')

            Chat prompt:
            >>> content = {'messages': [{'role': 'system', 'content': 'You are {{role}}'}]}
            >>> messages = PromptRenderer.to_template(PromptType.CHAT, content)
            >>> # Returns: [{'role': 'system', 'content': 'You are {role}'}]
        """
        if prompt_type == PromptType.TEXT:
            template = content.get('template', '')
            return PromptRenderer.to_template_text(template)
        else:  # CHAT
            messages = content.get('messages', [])
            return PromptRenderer.to_template_chat(messages)

    @staticmethod
    def extract_variables(template: str) -> list[str]:
        """Extract variable names from a Jinja2 template.

        Args:
            template: Template string with {{variable}} syntax

        Returns:
            List of unique variable names

        Examples:
            >>> PromptRenderer.extract_variables('Hello {{name}}, welcome to {{company}}!')
            ['name', 'company']
        """
        return list(set(_JINJA2_VAR_PATTERN.findall(template)))

    @staticmethod
    def extract_variables_from_messages(messages: list[dict[str, str]]) -> list[str]:
        """Extract all variable names from chat messages.

        Args:
            messages: List of message dictionaries

        Returns:
            List of unique variable names across all messages

        Examples:
            >>> messages = [
            ...     {'role': 'system', 'content': 'You are {{role}}'},
            ...     {'role': 'user', 'content': 'Help with {{topic}}'}
            ... ]
            >>> PromptRenderer.extract_variables_from_messages(messages)
            ['role', 'topic']
        """
        all_vars = []
        for msg in messages:
            vars_in_content = PromptRenderer.extract_variables(msg['content'])
            all_vars.extend(vars_in_content)
        return list(set(all_vars))
