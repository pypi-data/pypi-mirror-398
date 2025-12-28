"""YAML data file parser.

Parses YAML files containing test data items.
SDK-specific fields are stored in evaluation_specs via evaluation_list.
"""

from __future__ import annotations

from typing import Any

import yaml

from command_eval.domain.entities.data_item import DataItem
from command_eval.domain.policies.data_file_load_policy import (
    DataFileParser,
    ParseResult,
)
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.output_config import OutputConfig
from command_eval.domain.value_objects.output_type import OutputType
from command_eval.domain.value_objects.query_source import QuerySource
from command_eval.domain.value_objects.source_type import SourceType


class YamlDataFileParser(DataFileParser):
    """Parser for YAML data files.

    Expected YAML format:
    ```yaml
    output_config:                              # optional result output settings
      type: markdown                            # output format: txt/json/markdown
      output_dir: app/results                   # output directory
      template_file: app/test_data/template.md  # optional custom template

    items:
      - id: test_001                            # optional item ID for result file naming
        query: "What is Python?"                # or query_file: "/path/to/query.txt"
        command: "echo 'test'"
        actual_file: "/tmp/output.txt"
        pre_command:  # optional
          - "cd /tmp"
          - "mkdir -p test"
        query_append_text: "? Please explain."  # optional

        evaluation_list:  # SDK-specific evaluation settings
          - deepeval:
              common_param:  # shared params for all metrics
                expected_file: "expected.md"
              evaluation_type:
                - type: answer_relevancy
                - type: faithfulness
                  retrieval_context:
                    - "doc1"
                    - "doc2"
                - type: g_eval
                  param_file: "metrics/correctness.yml"  # load params from file
                  name: "Override Name"                  # override param_file value

          - ragas:
              common_param:
                reference_file: "expected.md"
              evaluation_type:
                - type: context_precision
                - type: answer_relevancy
    ```

    The param_file feature allows loading metric parameters from external YAML files.
    Parameter precedence (highest to lowest):
    1. Inline params in evaluation_type entry
    2. param_file contents
    3. common_param
    """

    def parse(self, file_path: FilePath) -> ParseResult:
        """Parse a YAML data file and return parse result.

        Args:
            file_path: Path to the YAML file.

        Returns:
            ParseResult containing data items and optional output config.

        Raises:
            ValueError: If the file cannot be parsed or is invalid.
            FileNotFoundError: If the file does not exist.
        """
        try:
            with open(file_path.value, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {file_path.value}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")

        if not data:
            raise ValueError("Empty data file")

        # Parse output_config (optional)
        output_config = self._parse_output_config(data)

        items_data = data.get("items", [])
        if not items_data:
            raise ValueError("No items found in data file")

        items: list[DataItem] = []
        for index, item_data in enumerate(items_data):
            item = self._parse_item(index, item_data)
            items.append(item)

        return ParseResult(items=tuple(items), output_config=output_config)

    def _parse_item(self, index: int, item_data: dict[str, Any]) -> DataItem:
        """Parse a single data item from the YAML data.

        Args:
            index: The index of this item.
            item_data: The raw item data from YAML.

        Returns:
            A DataItem instance.

        Raises:
            ValueError: If required fields are missing.
        """
        # Parse id (optional)
        item_id = item_data.get("id")
        if item_id is not None:
            item_id = str(item_id)

        # Parse query source
        query_source = self._parse_query_source(item_data)

        # Parse command (required)
        command = item_data.get("command")
        if not command:
            raise ValueError(f"Item {index}: 'command' is required")

        # Parse actual file (required) - renamed from output_file
        actual_file_path = item_data.get("actual_file")
        if not actual_file_path:
            raise ValueError(f"Item {index}: 'actual_file' is required")
        actual_file = FilePath(actual_file_path)

        # Parse pre-commands (optional)
        pre_commands = self._parse_pre_commands(item_data)

        # Parse query append text (optional)
        query_append_text = item_data.get("query_append_text")

        # Parse evaluation_list to create EvaluationSpec objects
        evaluation_specs = self._parse_evaluation_list(index, item_data)

        return DataItem(
            index=index,
            id=item_id,
            query_source=query_source,
            command=command,
            actual_file=actual_file,
            pre_commands=pre_commands,
            query_append_text=query_append_text,
            evaluation_specs=evaluation_specs,
        )

    def _parse_query_source(self, item_data: dict[str, Any]) -> QuerySource:
        """Parse query source from item data.

        Args:
            item_data: The raw item data.

        Returns:
            A QuerySource instance.

        Raises:
            ValueError: If query is not specified.
        """
        query_inline = item_data.get("query")
        query_file = item_data.get("query_file")

        if query_inline and query_file:
            raise ValueError("Cannot specify both 'query' and 'query_file'")

        if query_inline:
            return QuerySource(source_type=SourceType.INLINE, value=query_inline)
        elif query_file:
            return QuerySource(source_type=SourceType.FILE, value=query_file)
        else:
            raise ValueError("Either 'query' or 'query_file' is required")

    def _parse_pre_commands(
        self, item_data: dict[str, Any]
    ) -> tuple[str, ...]:
        """Parse pre-commands from item data.

        Supports both 'pre_command' (LLM_Eval compatible) and 'pre_commands'.

        Args:
            item_data: The raw item data.

        Returns:
            A tuple of pre-command strings.
        """
        # Support both 'pre_command' (LLM_Eval style) and 'pre_commands'
        pre_commands = item_data.get("pre_command") or item_data.get("pre_commands", [])
        if not isinstance(pre_commands, list):
            pre_commands = [pre_commands]
        return tuple(str(cmd) for cmd in pre_commands if cmd)

    def _parse_evaluation_list(
        self,
        index: int,
        item_data: dict[str, Any],
    ) -> tuple[EvaluationSpec, ...]:
        """Parse evaluation_list to create EvaluationSpec objects.

        Args:
            index: The index of this item (for error messages).
            item_data: The raw item data.

        Returns:
            A tuple of EvaluationSpec objects.
        """
        evaluation_list = item_data.get("evaluation_list", [])
        if not evaluation_list:
            return ()

        specs: list[EvaluationSpec] = []

        for sdk_entry in evaluation_list:
            if not isinstance(sdk_entry, dict):
                raise ValueError(
                    f"Item {index}: evaluation_list entries must be objects"
                )

            # Each entry should have exactly one SDK key
            sdk_names = list(sdk_entry.keys())
            if len(sdk_names) != 1:
                raise ValueError(
                    f"Item {index}: each evaluation_list entry must have exactly one SDK key"
                )

            sdk_name = sdk_names[0]
            sdk_config = sdk_entry[sdk_name]

            if not isinstance(sdk_config, dict):
                raise ValueError(
                    f"Item {index}: SDK config for '{sdk_name}' must be an object"
                )

            # Parse common_param (optional)
            common_param = sdk_config.get("common_param", {})
            if not isinstance(common_param, dict):
                raise ValueError(
                    f"Item {index}: common_param for '{sdk_name}' must be an object"
                )

            # Parse evaluation_type (required)
            evaluation_types = sdk_config.get("evaluation_type", [])
            if not evaluation_types:
                raise ValueError(
                    f"Item {index}: evaluation_type is required for '{sdk_name}'"
                )

            for eval_type in evaluation_types:
                if not isinstance(eval_type, dict):
                    raise ValueError(
                        f"Item {index}: evaluation_type entries must be objects"
                    )

                metric_type = eval_type.get("type")
                if not metric_type:
                    raise ValueError(
                        f"Item {index}: 'type' is required in evaluation_type for '{sdk_name}'"
                    )

                # Load param_file if specified
                param_file_params: dict[str, Any] = {}
                param_file = eval_type.get("param_file")
                if param_file:
                    param_file_params = self._load_param_file(param_file, index, sdk_name)

                # Merge params with precedence:
                # common_param < param_file < inline params
                merged_params = {**common_param, **param_file_params}
                for key, value in eval_type.items():
                    if key not in ("type", "param_file"):
                        merged_params[key] = value

                spec = EvaluationSpec(
                    sdk=sdk_name,
                    metric=metric_type,
                    params=merged_params,
                )
                specs.append(spec)

        return tuple(specs)

    def _load_param_file(
        self,
        param_file_path: str,
        index: int,
        sdk_name: str,
    ) -> dict[str, Any]:
        """Load parameters from an external YAML file.

        Args:
            param_file_path: Path to the parameter YAML file.
            index: The index of this item (for error messages).
            sdk_name: The SDK name (for error messages).

        Returns:
            A dictionary of parameters from the file.

        Raises:
            ValueError: If the file cannot be loaded or parsed.
        """
        try:
            with open(param_file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ValueError(
                f"Item {index}: param_file not found: {param_file_path} "
                f"for '{sdk_name}'"
            )
        except yaml.YAMLError as e:
            raise ValueError(
                f"Item {index}: invalid YAML in param_file: {param_file_path} "
                f"for '{sdk_name}': {e}"
            )

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise ValueError(
                f"Item {index}: param_file must contain a YAML object: "
                f"{param_file_path} for '{sdk_name}'"
            )

        return data

    def _parse_output_config(
        self,
        data: dict[str, Any],
    ) -> OutputConfig | None:
        """Parse output_config from the YAML root.

        Args:
            data: The raw YAML data.

        Returns:
            OutputConfig if present, None otherwise.

        Raises:
            ValueError: If output_config is invalid.
        """
        output_config_data = data.get("output_config")
        if not output_config_data:
            return None

        if not isinstance(output_config_data, dict):
            raise ValueError("output_config must be an object")

        # Parse type (required)
        type_str = output_config_data.get("type")
        if not type_str:
            raise ValueError("output_config.type is required")

        try:
            output_type = OutputType(type_str)
        except ValueError:
            valid_types = ", ".join(t.value for t in OutputType)
            raise ValueError(
                f"Invalid output_config.type: '{type_str}'. "
                f"Valid types: {valid_types}"
            )

        # Parse output_dir (required)
        output_dir_str = output_config_data.get("output_dir")
        if not output_dir_str:
            raise ValueError("output_config.output_dir is required")
        output_dir = FilePath(output_dir_str)

        # Parse template_file (optional)
        template_file: FilePath | None = None
        template_file_str = output_config_data.get("template_file")
        if template_file_str:
            template_file = FilePath(template_file_str)

        return OutputConfig(
            output_type=output_type,
            output_dir=output_dir,
            template_file=template_file,
        )
