from _typeshed import Incomplete
from gllm_inference.catalog.catalog import BaseCatalog as BaseCatalog
from gllm_inference.prompt_builder.prompt_builder import PromptBuilder as PromptBuilder

PROMPT_BUILDER_REQUIRED_COLUMNS: Incomplete
logger: Incomplete

class PromptBuilderCatalog(BaseCatalog[PromptBuilder]):
    '''Loads multiple prompt builders from certain sources.

    Attributes:
        components (dict[str, PromptBuilder]): Dictionary of the loaded prompt builders.

    Initialization:
        # Example 1: Load from Google Sheets using client email and private key
        ```python
        catalog = PromptBuilderCatalog.from_gsheets(
            sheet_id="...",
            worksheet_id="...",
            client_email="...",
            private_key="...",
        )
        prompt_builder = catalog.name
        ```

        # Example 2: Load from Google Sheets using credential file
        ```python
        catalog = PromptBuilderCatalog.from_gsheets(
            sheet_id="...",
            worksheet_id="...",
            credential_file_path="...",
        )
        prompt_builder = catalog.name
        ```

        # Example 3: Load from CSV
        ```python
        catalog = PromptBuilderCatalog.from_csv(csv_path="...")
        prompt_builder = catalog.name
        ```

        # Example 4: Load from records/JSON file
        ```python
        records=[
            {
                "name": "answer_question",
                "system": (
                    "You are helpful assistant.\\n"
                    "Answer the following question based on the provided context.\\n"
                    "```{context}```"
                ),
                "user": "{query}",
                "kwargs": json.dumps({
                    "key_defaults": {"context": "<default context>"},
                    "use_jinja": True,
                    "jinja_env": "restricted"
                }),
            },
        ]

        # or load the records from a JSON file
        records = json.load(open("path/to/records.json"))

        catalog = PromptBuilderCatalog.from_records(records=records)
        prompt_builder = catalog.answer_question
        ```

    Template Example:

        For template examples compatible with PromptBuilderCatalog, refer to:

            1. CSV: https://github.com/GDP-ADMIN/gl-sdk/tree/main/libs/gllm-inference/gllm_inference/resources/catalog/prompt_builder_catalog_template.csv
            2. JSON: https://github.com/GDP-ADMIN/gl-sdk/tree/main/libs/gllm-inference/gllm_inference/resources/catalog/prompt_builder_catalog_template.json

    Template Explanation:

        The required columns are:

            1. name (str): The name of the prompt builder.
            2. system (str): The system template of the prompt builder.
            3. user (str): The user template of the prompt builder.
            4. kwargs (json_str): Additional configuration for the prompt builder.

        Important Notes:

            1. At least one of the `system` or `user` columns must be filled.
    '''
