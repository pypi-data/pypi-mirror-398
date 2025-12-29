"""
SAPExtraction Component.

Extract SAP information from invoice images using AI-powered image analysis.
"""
from typing import Optional, Any
from collections.abc import Callable
import asyncio
import pandas as pd
from pydantic import BaseModel, Field
from ..interfaces.LLMClient import LLMClient
from .flow import FlowComponent


class ImageAnalysisResult(BaseModel):
    """Represents the result of an image analysis operation."""
    request_date: Optional[str] = Field(None, description="Date when the analysis was requested")
    vendor_invoice_nbr: Optional[str] = Field(None, description="Vendor invoice number if detected")
    sap_reference_nbr: Optional[str] = Field(None, description="SAP reference number if detected")


DEFAULT_ANALYSIS_PROMPT = """Extract ONLY the following information from the image:
* Request Date (format: YYYY-MM-DD, no day names)
* SAP Reference Nbr
* Vendor Invoice Nbr

If a field is not found, use null.
Return ONLY a valid JSON object, no additional text or explanations.
"""


class SAPExtraction(LLMClient, FlowComponent):
    """
    SAPExtraction Component.

    Overview:
        The SAPExtraction class is a component for extracting SAP information
        from invoice images using AI-powered image analysis with Google Gemini.

       :widths: auto

        | image_column     |   Yes    | Column containing image paths or image bytes                                                     |
        | prompt_file      |   No     | Prompt file name in <program>/prompts/ directory (e.g., 'sap_extraction.txt')                  |
        | analysis_prompt  |   No     | Inline custom analysis prompt. Ignored if prompt_file is provided.                              |
        | model            |   No     | Google Gemini model to use. Default: gemini-2.5-pro                                            |

    Return:
        A Pandas DataFrame with extracted SAP information in separate columns:
        - request_date
        - vendor_invoice_nbr
        - sap_reference_nbr

    Examples:

        Using inline prompt:

        Using prompt file (recommended for long/reusable prompts):

    Input DataFrame Example:
        | id | invoice_image_path          |
        |----|----------------------------|
        | 1  | /path/to/invoice1.pdf      |
        | 2  | /path/to/invoice2.jpg      |

    Output DataFrame Example:
        | id | invoice_image_path     | request_date | vendor_invoice_nbr | sap_reference_nbr |
        |----|------------------------|--------------|-------------------|-------------------|
        | 1  | /path/to/invoice1.pdf  | 2025-01-15   | INV-12345         | SAP-67890         |
        | 2  | /path/to/invoice2.jpg  | 2025-01-16   | INV-12346         | SAP-67891         |

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          SAPExtraction:
          image_column: invoice_image_path
          analysis_prompt: |
          Custom prompt for extracting SAP data...
          model: gemini-2.5-pro
        ```
    """
    _version = "1.0.0"

    def __init__(
        self,
        job: Callable = None,
        loop: asyncio.AbstractEventLoop = None,
        stat: Callable = None,
        **kwargs,
    ):
        # Get custom configurations
        self.image_column: str = kwargs.get('image_column', 'image_path')
        self._prompt_file: str = kwargs.get('prompt_file', None)
        self.analysis_prompt: str = kwargs.get('analysis_prompt', DEFAULT_ANALYSIS_PROMPT)
        model: str = kwargs.get('model', 'gemini-2.5-pro')

        # Pre-configure LLMClient settings for SAP extraction
        kwargs['client'] = 'google'
        kwargs['method'] = 'ask_to_image'
        kwargs['mode'] = 'row_by_row'

        # Configure client parameters (for client initialization)
        # api_key would go here if needed
        kwargs['client_params'] = {}

        # Configure method parameters (for ask_to_image method)
        kwargs['method_params'] = {
            'prompt': self.analysis_prompt,
            'model': model,
            'temperature': 0.1,  # Low temperature for precise extraction
            'structured_output': ImageAnalysisResult
        }

        # Map the image column to the 'image' parameter of ask_to_image
        kwargs['column_mapping'] = {
            'image': self.image_column
        }

        # Temporary output column (will be split into separate columns)
        kwargs['output_column'] = '_sap_extraction_result'

        # Initialize parent classes
        super().__init__(job=job, loop=loop, stat=stat, **kwargs)

    def _generate_arguments(self) -> dict:
        """
        Generate arguments for the LLM client.

        Returns:
            dict: Arguments including structured_output configuration
        """
        return {
            "structured_output": ImageAnalysisResult
        }

    def _map_params(self, row: pd.Series) -> dict:
        """
        Override parent to handle image conversion.

        Converts image paths/strings to bytes or Path objects for the client.
        - If string/Path: convert to bytes by reading the file
        - If BytesIO: convert to bytes by reading the buffer
        - If bytes: pass as-is

        Args:
            row: DataFrame row with image data

        Returns:
            dict: Parameters ready for ask_to_image
        """
        from pathlib import Path
        from io import BytesIO

        # Get base params from parent
        params = super()._map_params(row)

        # Handle image parameter conversion
        if 'image' in params:
            image_value = params['image']

            # Convert string path to Path object
            if isinstance(image_value, str):
                image_path = Path(image_value)

                # Verify file exists
                if not image_path.exists():
                    self._logger.error(f"Image file not found: {image_value}")
                    raise FileNotFoundError(f"Image file not found: {image_value}")

                # Read image as bytes
                with open(image_path, 'rb') as f:
                    params['image'] = f.read()

                self._logger.debug(f"Converted image path to bytes: {image_path.name}")

            # Convert Path object to bytes
            elif isinstance(image_value, Path):
                if not image_value.exists():
                    self._logger.error(f"Image file not found: {image_value}")
                    raise FileNotFoundError(f"Image file not found: {image_value}")

                with open(image_value, 'rb') as f:
                    params['image'] = f.read()

                self._logger.debug(f"Converted Path to bytes: {image_value.name}")

            # Convert BytesIO to bytes
            elif isinstance(image_value, BytesIO):
                # Seek to start to ensure we read from the beginning
                image_value.seek(0)
                params['image'] = image_value.read()
                self._logger.debug("Converted BytesIO to bytes")

            # If already bytes, keep as-is
            elif isinstance(image_value, bytes):
                self._logger.debug("Image already in bytes format")
            else:
                self._logger.warning(f"Unexpected image type: {type(image_value)}")

        return params

    async def start(self, **kwargs):
        """
        Initialize the SAPExtraction component.

        Validates:
        - Input data exists
        - Image column is present in the DataFrame
        - Loads prompt from file if prompt_file is specified

        Returns:
            bool: True if initialization is successful

        Raises:
            ComponentError: If validation fails
        """
        # Call parent start
        await super().start(**kwargs)

        # Load prompt from file if prompt_file is specified
        if self._prompt_file:
            from ..exceptions import ConfigError

            # Find in the taskstorage, the "prompts" directory
            prompt_path = self._taskstore.path.joinpath(self._program, 'prompts')
            if not prompt_path.exists():
                raise ConfigError(
                    f"{self.__name__}: Prompts directory not found: {prompt_path}"
                )

            # Check if prompt file exists
            prompt_file = prompt_path.joinpath(self._prompt_file)
            if not prompt_file.exists():
                raise ConfigError(
                    f"{self.__name__}: Prompt file not found: {prompt_file}"
                )

            # Read the prompt file
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.analysis_prompt = f.read()

            # Update method_params with the loaded prompt
            self.method_params['prompt'] = self.analysis_prompt

            self._logger.info(
                f"Loaded analysis prompt from file: {prompt_file}"
            )

        # Validate image column exists
        if self.image_column not in self.data.columns:
            from ..exceptions import ConfigError
            raise ConfigError(
                f"{self.__name__}: image_column '{self.image_column}' not found in DataFrame. "
                f"Available columns: {', '.join(self.data.columns)}"
            )

        self._logger.info(
            f"SAPExtraction initialized: image_column={self.image_column}, "
            f"model={self.method_params.get('model')}"
        )

        return True

    def _extract_result(self, response: Any) -> Any:
        """
        Override to handle ImageAnalysisResult structured output.

        Args:
            response: Response from the LLM client

        Returns:
            ImageAnalysisResult or dict with extracted fields
        """
        # Try to get the structured output
        if hasattr(response, 'output'):
            result = response.output
        elif hasattr(response, 'content'):
            result = response.content
        else:
            result = response

        # If it's already an ImageAnalysisResult, convert to dict
        if isinstance(result, ImageAnalysisResult):
            return result.model_dump()

        # If it's a dict with the expected fields, return as-is
        if isinstance(result, dict):
            return result

        # Otherwise return the raw result
        return result

    async def run(self, *args, **kwargs):
        """
        Execute the SAPExtraction processing.

        Main flow:
        1. Process images using LLMClient (ask_to_image)
        2. Extract structured data from responses
        3. Split results into separate columns

        Returns:
            pd.DataFrame: Data with extracted SAP information
        """
        # Run parent processing (handles the LLM calls)
        await super().run(*args, **kwargs)

        # Split the structured output into separate columns
        self._split_results_to_columns()

        # Remove temporary result column
        if '_sap_extraction_result' in self.data.columns:
            self.data = self.data.drop(columns=['_sap_extraction_result'])

        self._logger.info(
            f"SAPExtraction completed: processed {len(self.data)} images"
        )

        # Print results (following PositiveBot pattern)
        self._print_data_(self.data, 'SAPExtraction')

        # Set result for next component
        self._result = self.data
        return self._result

    def _split_results_to_columns(self):
        """
        Split the ImageAnalysisResult into separate DataFrame columns.

        Creates columns:
        - request_date
        - vendor_invoice_nbr
        - sap_reference_nbr
        """
        def extract_field(result, field_name):
            """Extract a field from the result dict."""
            if result is None:
                return None
            if isinstance(result, dict):
                return result.get(field_name)
            return None

        # Extract each field into its own column
        self.data['request_date'] = self.data['_sap_extraction_result'].apply(
            lambda x: extract_field(x, 'request_date')
        )
        self.data['vendor_invoice_nbr'] = self.data['_sap_extraction_result'].apply(
            lambda x: extract_field(x, 'vendor_invoice_nbr')
        )
        self.data['sap_reference_nbr'] = self.data['_sap_extraction_result'].apply(
            lambda x: extract_field(x, 'sap_reference_nbr')
        )

    async def close(self):
        """Clean up resources."""
        pass


__all__ = ['SAPExtraction', 'ImageAnalysisResult']
