"""JSON data file parser.

Parses JSON files containing test data items.
SDK-specific fields are stored in evaluation_specs via evaluation_list.
"""

from __future__ import annotations

import json
from typing import Any

from command_eval.domain.entities.data_item import DataItem
from command_eval.domain.policies.data_file_load_policy import DataFileParser
from command_eval.domain.value_objects.evaluation_spec import EvaluationSpec
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.query_source import QuerySource
from command_eval.domain.value_objects.source_type import SourceType


class JsonDataFileParser(DataFileParser):
    """Parser for JSON data files.

    Expected JSON format:
    ```json
    {
      "items": [
        {
          "query": "What is Python?",
          "command": "echo 'test'",
          "actual_file": "/tmp/output.txt",
          "pre_commands": ["cd /tmp", "mkdir -p test"],
          "query_append_text": "? Please explain.",
          "evaluation_list": [
            {
              "deepeval": {
                "common_param": {
                  "expected_file": "expected.md"
                },
                "evaluation_type": [
                  {"type": "answer_relevancy"},
                  {"type": "faithfulness", "retrieval_context": ["doc1", "doc2"]}
                ]
              }
            }
          ]
        }
      ]
    }
    ```

    Alternative using file-based query:
    ```json
    {
      "items": [
        {
          "query_file": "/path/to/query.txt",
          "command": "echo 'test'",
          "actual_file": "/tmp/output.txt",
          "evaluation_list": [...]
        }
      ]
    }
    ```
    """

    def parse(self, file_path: FilePath) -> tuple[DataItem, ...]:
        """Parse a JSON data file and return data items.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Tuple of data items.

        Raises:
            ValueError: If the file cannot be parsed or is invalid.
            FileNotFoundError: If the file does not exist.
        """
        try:
            with open(file_path.value, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {file_path.value}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        if data is None:
            raise ValueError("Empty data file")

        items_data = data.get("items", [])
        if not items_data:
            raise ValueError("No items found in data file")

        items: list[DataItem] = []
        for index, item_data in enumerate(items_data):
            item = self._parse_item(index, item_data)
            items.append(item)

        return tuple(items)

    def _parse_item(self, index: int, item_data: dict[str, Any]) -> DataItem:
        """Parse a single data item from the JSON data.

        Args:
            index: The index of this item.
            item_data: The raw item data from JSON.

        Returns:
            A DataItem instance.

        Raises:
            ValueError: If required fields are missing.
        """
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

        Args:
            item_data: The raw item data.

        Returns:
            A tuple of pre-command strings.
        """
        pre_commands = item_data.get("pre_commands", [])
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

                # Merge common_param with type-specific params
                # Type-specific params override common_param
                merged_params = {**common_param}
                for key, value in eval_type.items():
                    if key != "type":
                        merged_params[key] = value

                spec = EvaluationSpec(
                    sdk=sdk_name,
                    metric=metric_type,
                    params=merged_params,
                )
                specs.append(spec)

        return tuple(specs)
