from collections.abc import Callable
from pathlib import Path
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..interfaces.ParrotBot import ParrotBot
from .flow import FlowComponent
from ..exceptions import ComponentError, ConfigError
import re
from parrot.bots.product import ProductReport, ProductInfoTool
from parrot.tools.products import ProductResponse
from asyncdb import AsyncDB
from querysource.conf import default_dsn
from parrot.models.responses import AgentResponse, AIMessage
from parrot.models.basic import CompletionUsage
from pathlib import Path
import shutil
class ProductReportBot(ParrotBot, FlowComponent):
    """
    ProductReportBot Component

    **Overview**

    The ProductReportBot class is a component for generating comprehensive product reports using AI-Parrot's ProductReport agent.
    It supports both single product and program-wide report generation with customizable report types (PDF, PPT, PODCAST).

    **Features:**
    - Generate reports for individual products or entire programs
    - Support for multiple report formats (PDF, PowerPoint, Podcast)
    - Integration with FlowTask's prompt system
    - Automatic database storage of generated reports
    - Configurable LLM settings

       :widths: auto

    |   type                     |   Yes    | Type of operation: "program" for all products in a tenant, "single" for specific products. |
    |   program_slug             |   Yes    | The program/tenant identifier (e.g., 'hisense', 'google').                                  |
    |   output_column            |   Yes    | Column name for saving the generated product reports.                                        |
    |   models                   |   No     | List of specific product models to process (required when type="single").                   |
    |   report_types             |   No     | List of report types to generate: ["PDF", "PPT", "PODCAST"] (default: all).                |
    |   llm_config               |   No     | LLM configuration dictionary with llm, model, temperature, etc.                             |

    **Returns**

    A pandas DataFrame containing the generated product reports with file paths and metadata.

    **Example:**

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          ProductReportBot:
          type: program
          program_slug: hisense
          output_column: product_reports
          report_types: ["PDF", "PPT", "PODCAST"]
          destination: "/custom/path/for/reports"  # Optional: custom directory for all generated files
          llm_config:
          llm: openai
          model: gpt-4o
          temperature: 0.0
        ```
    """
    _version = "1.0.0"

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        # Extract ProductReportBot specific parameters
        self.type: str = kwargs.get('type', 'program')  # 'program' or 'single'
        self.program_slug: str = kwargs.get('program_slug')
        self.models: List[str] = kwargs.get('models', [])
        self.report_types: List[str] = kwargs.get('report_types', ['PDF', 'PPT', 'PODCAST'])
        self.llm_config: Dict[str, Any] = kwargs.get('llm_config', {})
        self.model_column: str = kwargs.get('model_column', 'model')  # Column name for model in DataFrame
        self.destination: str = kwargs.get('destination', None)  # Custom destination directory
        
        # ParrotBot attributes (needed for proper initialization)
        self._bot_name = kwargs.get('bot_name', 'ProductReportBot')
        self._prompt_file = kwargs.get('prompt_file', 'product_info.txt')
        self._rating_column: str = kwargs.get('rating_column', 'rating')
        self._eval_column: str = kwargs.get('eval_column', 'evaluation')
        self._desc_column: str = kwargs.get('description_column', 'description')
        self.output_column: str = kwargs.get('output_column')
        self._survey_mode: bool = kwargs.get('survey', False)
        # System Prompt (initial value, will be overwritten by file content in start())
        self.system_prompt = "Product Report: "
        self._bot: Any = None
        
        # Validate required parameters (only basic validation in __init__)
        if not self.program_slug:
            raise ConfigError("ProductReportBot: program_slug is required")
        
        if self.type not in ['program', 'single']:
            raise ConfigError("ProductReportBot: type must be 'program' or 'single'")
        
        # Initialize parent classes (ParrotBot first, then FlowComponent)
        super().__init__(
            loop=loop, job=job, stat=stat, **kwargs
        )
        
        # LLM configuration - merge llm_config with defaults and assign to self.llm
        # (Must be after super().__init__() in case parent classes initialize llm)
        default_llm_config = {
            'llm': 'google',
            'model': 'gemini-2.5-flash',
            'temperature': 0.0,
        }
        self.llm = {**default_llm_config, **self.llm_config}
        
        # Set default goal for product report generation
        self._goal: str = 'Generate comprehensive product reports with detailed analysis, specifications, and insights'
        
        # ProductReport agent instance
        self._product_report_agent: Optional[ProductReport] = None

    async def start(self, **kwargs):
        """
        Start the ProductReportBot component.
        
        Initializes the ProductReport agent with the specified configuration.
        """
        # Call ParrotBot's start method to handle prompt loading
        await super().start(**kwargs)
        
        if self.previous:
            self.data = self.input
            # Extract models from DataFrame if type is single and no models list provided
            if self.type == "single" and not self.models and hasattr(self, 'data') and self.data is not None:
                if self.model_column in self.data.columns:
                    # Extract unique models from DataFrame
                    self.models = self.data[self.model_column].dropna().unique().tolist()
                    self._logger.info(f"Extracted {len(self.models)} models from DataFrame column '{self.model_column}': {self.models}")
                else:
                    raise ComponentError(
                        f"ProductReportBot: Column '{self.model_column}' not found in input DataFrame. Available columns: {list(self.data.columns)}"
                    )
        else:
            # For type="program", we don't need input data
            if self.type == "single":
                # Validate that we have models when no input data
                if not self.models:
                    raise ComponentError(
                        f"{self._bot_name.lower()}: models list is required when type='single' and no input data provided"
                    )
        
        if not self.output_column:
            raise ConfigError(
                f"{self._bot_name.lower()}: output_column is required"
            )
        
        # Initialize ProductReport agent (for report generation tools only)
        await self._initialize_product_report_agent()
        

        
        return True

    def _load_prompt_from_taskstore(self, prompt_filename: str, subdirectory: str = None) -> str:
        """
        Load prompt file from taskstore per-program directory.

        Args:
            prompt_filename: Name of the prompt file (e.g., 'product_info.txt')
            subdirectory: Optional subdirectory within prompts/ (e.g., 'product_report_bot')

        Returns:
            Content of the prompt file

        Raises:
            ConfigError: If prompt file not found
        """
        prompts_path = self._taskstore.path.joinpath(self._program, 'prompts')

        # If subdirectory specified, look there first
        if subdirectory:
            prompt_file = prompts_path / subdirectory / prompt_filename
            if not prompt_file.exists():
                # Fallback: try root prompts directory
                prompt_file = prompts_path / prompt_filename
        else:
            prompt_file = prompts_path / prompt_filename

        if not prompt_file.exists():
            raise ConfigError(
                f"ProductReportBot: Prompt file not found: {prompt_file}\n"
                f"Expected location: {self._program}/prompts/{subdirectory + '/' if subdirectory else ''}{prompt_filename}"
            )

        try:
            content = prompt_file.read_text(encoding='utf-8')
            self._logger.info(f"Loaded prompt from taskstore: {prompt_file}")
            return content
        except Exception as err:
            raise ConfigError(
                f"ProductReportBot: Failed to read prompt file '{prompt_file}': {err}"
            ) from err

    async def _initialize_product_report_agent(self):
        """Initialize the ProductReport agent with configuration."""
        try:
            # Default LLM configuration
            default_llm_config = {
                'llm': 'openai',
                'model': 'gpt-4o',
                'temperature': 0.0,
                'max_tokens': 8192
            }

            # Merge with provided configuration
            final_llm_config = {**default_llm_config, **self.llm_config}

            # Use system_prompt if available, otherwise use a default
            system_prompt = getattr(self, 'system_prompt', None)
            if not system_prompt:
                system_prompt = """
                You are an AI assistant specialized in generating comprehensive product reports.
                Your task is to analyze product information and create detailed reports including:
                - Product specifications and features
                - Market analysis and positioning
                - Customer insights and reviews
                - Competitive analysis
                - Recommendations and conclusions

                Provide a thorough, professional analysis based on the product data provided.
                """

            # Create ProductReport agent with correct parameters
            self._product_report_agent = ProductReport(
                name='ProductReportBot',
                agent_id='product_report_bot',
                use_llm=final_llm_config['llm'],  # Use 'use_llm' not 'llm'
                llm=final_llm_config['model'],   # This is the model name
                system_prompt=system_prompt,
                static_dir=self._taskstore.path  # Pass taskstore path as base for SQL files
            )

            # Set additional configuration if needed
            self._product_report_agent.temperature = final_llm_config['temperature']
            self._product_report_agent.max_tokens = final_llm_config['max_tokens']

            # Configure the agent with error handling for database issues
            try:
                await self._product_report_agent.configure()
            except Exception as db_err:
                # If database configuration fails (e.g., missing bot_class column),
                # log the warning but continue - the agent can still work
                self._logger.warning(
                    f"Database configuration failed for ProductReport agent: {db_err}. "
                    f"Continuing without database registration."
                )
                # Still need to configure LLM even if database fails
                try:
                    self._product_report_agent.configure_llm()
                    self._logger.info("LLM configured successfully despite database error")
                except Exception as llm_err:
                    raise ComponentError(f"Failed to configure LLM: {llm_err}") from llm_err

        except Exception as err:
            raise ComponentError(
                f"ProductReportBot: Error initializing ProductReport agent: {err}"
            ) from err

    async def run(self):
        """
        Run the ProductReportBot component.
        
        Executes the appropriate method based on the type parameter.
        """
        try:
            if self.type == 'program':
                result = await self.program_reports()
            elif self.type == 'single':
                result = await self.single_reports()
            else:
                raise ComponentError(f"ProductReportBot: Unknown type '{self.type}'")
            
            self._result = result
            self.add_metric("NUMROWS", len(result.index))
            self.add_metric("NUMCOLS", len(result.columns))
            
            if self._debug is True:
                self._print_data_("ProductReportBot Result", self._result)
            
            return self._result
            
        except Exception as e:
            self._logger.error(f"ProductReportBot: Error in run: {str(e)}")
            raise

    async def program_reports(self) -> pd.DataFrame:
        """
        Generate reports for all products in a program/tenant.
        
        Returns:
            pd.DataFrame: DataFrame with generated reports for all products
        """
        self._logger.info(f"Generating reports for all products in program: {self.program_slug}")
        
        try:
            # Use the ProductReport agent to generate reports for all products
            responses = await self._product_report_agent.create_product_report(self.program_slug)
            
            # Convert responses to DataFrame
            if not responses:
                self._logger.warning(f"No products found for program: {self.program_slug}")
                return pd.DataFrame()
            
            # Convert ProductResponse objects to dictionary format
            reports_data = []
            for response in responses:
                report_dict = {
                    'model': response.model,
                    'program_slug': self.program_slug,
                    'agent_id': response.agent_id,
                    'agent_name': response.agent_name,
                    'status': response.status,
                    'transcript': response.transcript,
                    'pdf_path': response.pdf_path,
                    'document_path': response.document_path,
                    'podcast_path': response.podcast_path,
                    'script_path': response.script_path,
                    'created_at': response.created_at,
                    'files': response.files
                }
                reports_data.append(report_dict)
            
            df = pd.DataFrame(reports_data)
            self._logger.info(f"Generated {len(df)} product reports for program: {self.program_slug}")
            
            return df
            
        except Exception as e:
            self._logger.error(f"Error generating program reports: {str(e)}")
            raise ComponentError(f"Failed to generate program reports: {str(e)}")

    async def single_reports(self) -> pd.DataFrame:
        """
        Generate reports for specific products.
        
        Returns:
            pd.DataFrame: DataFrame with generated reports for specified products
        """
        self._logger.info(f"Generating reports for specific models: {self.models}")
        
        if not self.models:
            self._logger.warning("No models to process")
            return pd.DataFrame()
        
        try:
            reports_data = []
            
            # Process each model
            for model in self.models:
                self._logger.info(f"Processing model: {model}")
                
                try:
                    # Generate report for single product
                    response = await self._generate_single_product_report(model, self.program_slug)
                    
                    if response:
                        report_dict = {
                            'model': model,
                            'program_slug': self.program_slug,
                            'agent_id': response.agent_id,
                            'agent_name': response.agent_name,
                            'status': response.status,
                            'transcript': response.transcript,
                            'pdf_path': response.pdf_path,
                            'document_path': response.document_path,
                            'podcast_path': response.podcast_path,
                            'script_path': response.script_path,
                            'created_at': response.created_at,
                            'files': response.files
                        }
                        reports_data.append(report_dict)
                        
                except Exception as e:
                    self._logger.error(f"Error processing model {model}: {str(e)}")
                    # Add error entry
                    error_dict = {
                        'model': model,
                        'program_slug': self.program_slug,
                        'agent_id': 'product_report_bot',
                        'agent_name': 'ProductReportBot',
                        'status': 'error',
                        'transcript': None,
                        'pdf_path': None,
                        'document_path': None,
                        'podcast_path': None,
                        'script_path': None,
                        'created_at': pd.Timestamp.now(),
                        'files': [],
                        'error': str(e)
                    }
                    reports_data.append(error_dict)
            
            df = pd.DataFrame(reports_data)
            self._logger.info(f"Generated {len(df)} product reports for models: {self.models}")
            
            return df
            
        except Exception as e:
            self._logger.error(f"Error generating single reports: {str(e)}")
            raise ComponentError(f"Failed to generate single reports: {str(e)}")

    async def _generate_single_product_report(self, model: str, program_slug: str) -> Optional[ProductResponse]:
        try:
            async with self._product_report_agent:
                # ========= PREFETCH DEL TOOL + DEBUG =========
                # Configure ProductInfoTool to use taskstore directory
                taskstore_base = self._taskstore.path
                info_tool = ProductInfoTool(static_dir=taskstore_base)
                info = await info_tool._execute(model=model, program_slug=program_slug)
                info_dict = info.model_dump() if hasattr(info, "model_dump") else dict(info)

                # 🔎 DEBUG CLAVE AQUÍ (lo que me pediste):
                self._logger.debug("Tool ProductInfo result (model=%s): %s", model, info_dict)
                if 'picture_url' not in info_dict:
                    self._logger.error("ProductInfo sin 'picture_url' (model=%s). Keys=%s", model, list(info_dict.keys()))

                # ========= FORMATO DE PROMPT CON VARIABLES (sin duplicar 'model') =========
                # Load prompt from taskstore instead of hardcoded parrot location
                prompt_content = self._load_prompt_from_taskstore("product_info.txt")

                # Evitar conflicto: str.format() got multiple values for keyword argument 'model'
                ctx = {**info_dict}
                ctx.pop('model', None)         # elimina 'model' del tool si existe
                ctx['model'] = model            # usa el 'model' actual
                ctx['program_slug'] = program_slug

                # (opcional) fallback seguro ante placeholders faltantes
                class SafeDict(dict):
                    def __missing__(self, key):
                        return "{" + key + "}"

                self._logger.debug("Prompt format context keys: %s", list(ctx.keys()))
                formatted_prompt = prompt_content.format_map(SafeDict(ctx))


                # ========= INVOCACIÓN DEL AGENTE =========
                ai_message = await self._product_report_agent.invoke(question=formatted_prompt)

                proper_ai_message = AIMessage(
                    input=formatted_prompt,
                    output=ai_message.output,
                    model=self.llm['model'],
                    provider=self.llm['llm'],
                    usage=CompletionUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                    response=ai_message.output
                )
                response = AgentResponse(
                    user_id="1",
                    agent_id=self._product_report_agent.agent_id,
                    agent_name=self._product_report_agent.name,
                    status="success",
                    response=proper_ai_message,
                    data=ai_message.output,
                    output=ai_message.output,
                    created_at=datetime.now(),
                    model=model,
                    program_slug=program_slug
                )

            final_output = response.output or ""
            # ========= “CINTURÓN Y TIRANTES”: fuerza la URL real en el markdown =========
            def _force_image(md: str, url: str) -> str:
                if not url:
                    return md
                if re.search(r'!\[Product Image\]\((.*?)\)', md, flags=re.IGNORECASE):
                    return re.sub(r'!\[Product Image\]\((.*?)\)', f'![Product Image]({url})', md, flags=re.IGNORECASE)
                return md.replace("**Product Image:**", f"**Product Image:** ![Product Image]({url})")

            final_output = _force_image(final_output, info_dict.get('picture_url'))

            # 🔎 DEBUG de la imagen que va a PDF/PPT
            m = re.search(r'!\[[^\]]*\]\(([^)]+)\)', final_output)
            self._logger.debug("Image URL en markdown final (model=%s): %s", model, (m.group(1) if m else None))

            # (opcional) guarda el markdown final para inspección:
            try:
                debug_dir = self._get_output_directory("documents")
                debug_md = debug_dir / f"{model}_final.md"
                debug_md.write_text(final_output)
                self._logger.info("Saved debug markdown for %s: %s", model, debug_md)
            except Exception as _:
                pass
            
            # Generate requested report types
            report_paths = {}
            
            if 'PDF' in self.report_types:
                # TEMP FIX: Replace problematic characters in model name for file naming
                safe_model = model.replace("/", "_").replace("\\", "_").replace(":", "_")
                pdf = await self._product_report_agent.pdf_report(
                    title=f'AI-Generated Product Report - {model}',
                    content=final_output,
                    filename_prefix=f'product_report_{safe_model}'
                )
                original_pdf_path = pdf.result.get('file_path')
                
                # Move to custom destination if specified
                if self.destination:
                    custom_pdf_dir = self._get_output_directory("documents") 
                    original_pdf = Path(original_pdf_path)
                    new_pdf_path = custom_pdf_dir / original_pdf.name
                    shutil.move(str(original_pdf), str(new_pdf_path))
                    report_paths['pdf_path'] = str(new_pdf_path)
                    
                    # Also move the debug HTML file
                    debug_html_path = original_pdf.parent / f"{original_pdf.stem}_debug.html"
                    if debug_html_path.exists():
                        new_html_path = custom_pdf_dir / debug_html_path.name
                        shutil.move(str(debug_html_path), str(new_html_path))
                        self._logger.info(f"HTML debug file moved for {model}: {new_html_path}")
                else:
                    report_paths['pdf_path'] = str(original_pdf_path)
                    
                self._logger.info(f"PDF generated for {model}: {report_paths['pdf_path']}")
            
            if 'PPT' in self.report_types:
                # TEMP FIX: Replace problematic characters in model name for file naming
                safe_model = model.replace("/", "_").replace("\\", "_").replace(":", "_")
                ppt = await self._product_report_agent.generate_presentation(
                    content=final_output,
                    filename_prefix=f'product_presentation_{safe_model}',
                    pptx_template="corporate_template.pptx",
                    title=f'Product Report - {model}',
                    company=program_slug.title(),
                    presenter='AI Assistant'
                )
                original_ppt_path = ppt.result.get('file_path')
                
                # Move to custom destination if specified
                if self.destination:
                    custom_ppt_dir = self._get_output_directory("documents")  # Changed to "documents"
                    original_ppt = Path(original_ppt_path)
                    new_ppt_path = custom_ppt_dir / original_ppt.name
                    shutil.move(str(original_ppt), str(new_ppt_path))
                    report_paths['document_path'] = str(new_ppt_path)
                else:
                    report_paths['document_path'] = str(original_ppt_path)
                    
                self._logger.info(f"PowerPoint generated for {model}: {report_paths['document_path']}")
            
            if 'PODCAST' in self.report_types:
                try:
                    # Load podcast instructions from taskstore (in product_report_bot subdirectory)
                    try:
                        podcast_instructions = self._load_prompt_from_taskstore(
                            'product_conversation.txt',
                            subdirectory='product_report_bot'
                        )
                    except ConfigError as prompt_err:
                        self._logger.warning(f"Podcast instructions not found in taskstore: {prompt_err}")
                        podcast_instructions = None

                    if podcast_instructions:
                        # Call speech_report with content from taskstore
                        podcast = await self._product_report_agent.speech_report(
                            report=final_output,
                            max_lines=self._product_report_agent.speech_length,
                            num_speakers=self._product_report_agent.num_speakers,
                            podcast_instructions=podcast_instructions  # Pass content, not filename
                        )
                    else:
                        podcast = None
                        self._logger.info(f"Podcast skipped for {model} - instructions not found in taskstore")
                except Exception as e:
                    self._logger.warning(f"Podcast generation failed for {model}: {e}")
                    podcast = None
                if podcast:
                    # Rename podcast files to include model name
                    original_podcast_path = podcast.get('podcast_path')
                    original_script_path = podcast.get('script_path')
                    
                    if original_podcast_path:
                        original_podcast = Path(original_podcast_path)
                        # TEMP FIX: Replace problematic characters in model name for file naming
                        safe_model = model.replace("/", "_").replace("\\", "_").replace(":", "_")
                        new_podcast_name = f"product_podcast_{safe_model}_{original_podcast.stem.split('_')[-1]}{original_podcast.suffix}"
                        
                        # Move to custom destination if specified
                        if self.destination:
                            custom_podcast_dir = self._get_output_directory("podcasts")
                            new_podcast_path = custom_podcast_dir / new_podcast_name
                            shutil.move(str(original_podcast), str(new_podcast_path))
                        else:
                            new_podcast_path = original_podcast.parent / new_podcast_name
                            original_podcast.rename(new_podcast_path)
                            
                        report_paths['podcast_path'] = str(new_podcast_path)
                        self._logger.info(f"Podcast renamed for {model}: {new_podcast_path}")
                    else:
                        report_paths['podcast_path'] = None
                    
                    if original_script_path:
                        original_script = Path(original_script_path)
                        # TEMP FIX: Replace problematic characters in model name for file naming
                        safe_model = model.replace("/", "_").replace("\\", "_").replace(":", "_")
                        new_script_name = f"product_script_{safe_model}_{original_script.stem.split('_')[-1]}{original_script.suffix}"
                        
                        # Move to custom destination if specified
                        if self.destination:
                            custom_scripts_dir = self._get_output_directory("documents")
                            new_script_path = custom_scripts_dir / new_script_name
                            shutil.move(str(original_script), str(new_script_path))
                        else:
                            new_script_path = original_script.parent / new_script_name
                            original_script.rename(new_script_path)
                            
                        report_paths['script_path'] = str(new_script_path)
                        self._logger.info(f"Script renamed for {model}: {new_script_path}")
                    else:
                        report_paths['script_path'] = None
                else:
                    report_paths['podcast_path'] = None
                    report_paths['script_path'] = None
                    self._logger.info(f"Podcast skipped for {model} - conversation prompt not found")
            
            # Update response with file paths
            response.transcript = final_output
            response.pdf_path = report_paths.get('pdf_path')
            response.document_path = report_paths.get('document_path')
            response.podcast_path = report_paths.get('podcast_path')
            response.script_path = report_paths.get('script_path')
            
            # Save to database
            await self._save_to_database(response, model, program_slug)
            
            return response
            
        except Exception as e:
            self._logger.error(f"Error generating report for {model}: {str(e)}")
            raise

    def _get_output_directory(self, report_type: str) -> Path:
        """
        Get the output directory for reports. If destination is specified, use it.
        Otherwise, use the taskstore directory per program.

        Args:
            report_type: Type of report (documents, podcasts, generated_scripts)

        Returns:
            Path to the output directory
        """
        if self.destination:
            custom_dir = Path(self.destination) / report_type
        else:
            # Use taskstore per-program directory instead of flowtask static folder
            custom_dir = self._taskstore.path.joinpath(self._program, 'outputs', report_type)

        # Create directory if it doesn't exist
        custom_dir.mkdir(parents=True, exist_ok=True)
        return custom_dir

    async def _save_to_database(self, response, model: str, program_slug: str):
        """
        Save the generated report to the database.
        
        Args:
            response: AgentResponse object
            model: Product model
            program_slug: Program identifier
        """
        try:
            # Convert AgentResponse to Dict and prepare for database
            response_dict = response.model_dump()

            # Remove fields that shouldn't be in the database
            fields_to_remove = ['session_id', 'user_id', 'turn_id', 'images', 'response', 'question', 'media', 'documents']
            for field in fields_to_remove:
                response_dict.pop(field, None)
            
           
            db = AsyncDB('pg', dsn=default_dsn)
            async with await db.connection() as conn:
                ProductResponse.Meta.connection = conn
                ProductResponse.Meta.schema = program_slug
                
                product_response = ProductResponse(**response_dict)
                product_response.model = model
                product_response.agent_id = self._product_report_agent.agent_id
                product_response.agent_name = self._product_report_agent.name
                
                # Use PostgreSQL UPSERT (ON CONFLICT) for reliable insert/update
                try:
                    # First try regular save
                    await product_response.save()
                    self._logger.info(f"Saved new product response for {model} to database")
                except Exception as save_err:
                    if "duplicate key" in str(save_err):
                        # Use raw SQL for upsert since ORM update might not work as expected
                        self._logger.info(f"Record exists, using UPSERT for {model}")
                        
                        upsert_sql = f"""
                        INSERT INTO {program_slug}.products_informations 
                        (model, agent_id, agent_name, status, output, transcript, script_path, podcast_path, pdf_path, document_path, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (model, agent_id) 
                        DO UPDATE SET 
                            status = EXCLUDED.status,
                            output = EXCLUDED.output,
                            transcript = EXCLUDED.transcript,
                            script_path = EXCLUDED.script_path,
                            podcast_path = EXCLUDED.podcast_path,
                            pdf_path = EXCLUDED.pdf_path,
                            document_path = EXCLUDED.document_path,
                            created_at = EXCLUDED.created_at
                        """
                        
                        await conn.execute(upsert_sql, 
                            product_response.model,
                            product_response.agent_id, 
                            product_response.agent_name,
                            product_response.status,
                            product_response.output,
                            product_response.transcript,
                            product_response.script_path,
                            product_response.podcast_path,
                            product_response.pdf_path,
                            product_response.document_path,
                            product_response.created_at
                        )
                        self._logger.info(f"UPSERTED product response for {model} in database")
                    else:
                        raise save_err
                
        except Exception as e:
            self._logger.error(f"Error saving to database for {model}: {str(e)}")
            # Don't raise the error, just log it to avoid breaking the main flow

    async def close(self):
        """Cierra recursos del ProductReportBot (sesiones HTTP, clientes, etc.)."""
        agent = self._product_report_agent
        if not agent:
            return True

        # 1) Intenta salir del contexto del agente si lo soporta
        aexit = getattr(agent, "__aexit__", None)
        if callable(aexit):
            try:
                res = aexit(None, None, None)
                try:
                    await res   # si es coroutine
                except TypeError:
                    pass        # si es síncrono, no pasa nada
            except Exception as e:
                self._logger.debug(f"__aexit__ del agente falló/omitido: {e}")

        # 2) Intenta cerrar el propio agente con aclose()/close() si existen
        for closer_name in ("aclose", "close"):
            closer = getattr(agent, closer_name, None)
            if callable(closer):
                try:
                    res = closer()
                    try:
                        await res   # asíncrono
                    except TypeError:
                        pass        # síncrono
                except Exception as e:
                    self._logger.debug(f"No se pudo {closer_name} el agente: {e}")
                break

        # 3) Cierra clientes/sesiones comunes colgadas (aiohttp/httpx, etc.)
        for attr in ("session", "_session", "client", "_client", "http", "_http", "httpx_client"):
            obj = getattr(agent, attr, None)
            if not obj:
                continue
            for closer_name in ("aclose", "close"):
                closer = getattr(obj, closer_name, None)
                if callable(closer):
                    try:
                        res = closer()
                        try:
                            await res   # asíncrono
                        except TypeError:
                            pass        # síncrono
                    except Exception as e:
                        self._logger.debug(f"No se pudo cerrar {attr} con {closer_name}: {e}")
                    break

        return True


    def _print_data_(self, title: str, data_df: pd.DataFrame):
        """
        Print the data and its corresponding column types for a given DataFrame.
        
        Args:
            title: The title to print before the data
            data_df: The DataFrame to print and inspect
        """
        self._logger.info(f"Generated report data for {title}")
        if len(data_df) > 0:
            self._logger.debug(f"DataFrame shape: {data_df.shape}, columns: {list(data_df.columns)}")
        else:
            self._logger.warning(f"No data generated for {title}")