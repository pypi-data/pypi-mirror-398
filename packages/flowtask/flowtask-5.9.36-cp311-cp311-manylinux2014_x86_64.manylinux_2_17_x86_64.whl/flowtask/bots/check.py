from collections.abc import Callable
from navconfig.logging import config, logging
from parrot.models import AIMessage
from ..exceptions import ComponentError
from ..utils import cPrint
ENABLE_BOT_REVIEWER = config.getboolean('ENABLE_BOT_REVIEWER', fallback=False)

try:
    from .codebot import CodeBot
except ImportError:
    ENABLE_BOT_REVIEWER = False  # noqa
    logging.warning(
        "Unable to import CodeBot for Code Review, install dependencies first."
    )


class CodeReview:
    def __init__(self, task, *args, **kwargs):
        super(CodeReview, self).__init__(*args, **kwargs)
        self.task = task
        self.logger = logging.getLogger('Flowtask.CodeReview')
        self._llm = None
        self.bot: Callable = None
        if ENABLE_BOT_REVIEWER is True:
            self.bot = CodeBot()
            self.bot.configured = False

    def __repr__(self):
        return f"CodeReview({self.task})"

    def format_question(self, name, message, task, error):
        return f"""
        Task with name: **{name}**

        was failed with error: {message}

        Task Definition (in YAML or JSON format):
        ```

        {task}
        ```

        Complete Stack Trace:
        ```
        {error}
        ```
        """

    async def __call__(self, task: str, status: str, message: str, stacktrace: str = None, *args, **kwargs):
        """Calling Bot based on Task Errors/Exceptions."""
        if not self.bot:
            # Bot is not enabled, return Logging
            cPrint("Bot Reviewer is not enabled, please enable it in config.")
        if self.bot.configured is False:
            await self.bot.configure()
            self.bot.configured = True
        # if status == 'Task Not Found':
        #     return
        task_code = self.task.get_task_code()
        question = self.format_question(
            name=task,
            message=message,
            task=task_code,
            error=stacktrace
        )
        try:
            result = await self.bot.ask(
                question=question,
                return_docs=False
            )
            answer = None
            if isinstance(result, AIMessage):
                answer = result.output
            else:
                answer = f"{result.response}"
            # for now, just print the result
            print(f"""
            Code Review Result:
            -------------------

            {answer}
            """)
            try:
                self.task.stat.stats['Review'] = answer
            except (TypeError, KeyError):
                print(result)
        except Exception as exc:
            raise ComponentError(
                f"Unable to get Code Review: {exc}"
            )
