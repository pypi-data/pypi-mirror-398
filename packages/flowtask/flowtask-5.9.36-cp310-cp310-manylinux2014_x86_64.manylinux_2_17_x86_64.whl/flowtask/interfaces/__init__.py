"""
Interfaces.

Services and methods covered by Flowtask.
Support interfaces for many options on Task Components.
"""
from .func import FuncSupport
from .mask import MaskSupport
from .databases import DBSupport
from .log import LogSupport, SkipErrors
from .result import ResultSupport
from .cache import CacheSupport
from .stat import StatSupport
from .locale import LocaleSupport
from .template import TemplateSupport
from .http import HTTPService
from .selenium_service import SeleniumService
from .client import ClientInterface
from .db import DBInterface
from .ParrotTool import ParrotTool
from .LLMClient import LLMClient


__all__ = (
    "FuncSupport",
    "MaskSupport",
    "DBSupport",
    "LogSupport",
    "ResultSupport",
    "StatSupport",
    "LocaleSupport",
    "TemplateSupport",
    "SkipErrors",
    # interfaces:
    "DBInterface",
    "ClientInterface",
    "HTTPService",
    "ParrotTool",
    "LLMClient",
)
