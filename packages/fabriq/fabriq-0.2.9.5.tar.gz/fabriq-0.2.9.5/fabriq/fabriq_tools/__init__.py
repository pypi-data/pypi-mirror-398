from fabriq.fabriq_tools.clinical_trials import ClinicalTrialsTool
from fabriq.fabriq_tools.travel_tool import TravelTool
from fabriq.fabriq_tools.web_search import WebSearchTool
from fabriq.fabriq_tools.wiki import WikipediaTool
from fabriq.fabriq_tools.wolfram import WolframAlphaTool
from fabriq.fabriq_tools.yahoo_finance_news import YFinanceNews
from fabriq.fabriq_tools.youtube import YoutubeSearch
from fabriq.fabriq_tools.datetime_tool import DateTimeTool
from fabriq.fabriq_tools.code_analysis import CodeAnalysisTool
from fabriq.fabriq_tools.translator import Translator

def get_tool_by_name(tool_name: str):
    """Return the tool class based on the tool name."""
    tools_mapping = {
        "ClinicalTrialsTool": ClinicalTrialsTool,
        "TravelTool": TravelTool,
        "WebSearchTool": WebSearchTool,
        "WikipediaTool": WikipediaTool,
        "WolframAlphaTool": WolframAlphaTool,
        "YFinanceNews": YFinanceNews,
        "YoutubeSearch": YoutubeSearch,
        "DateTimeTool": DateTimeTool,
        "CodeAnalysisTool": CodeAnalysisTool,
        "Translator": Translator,
    }
    return tools_mapping.get(tool_name, None)

def list_available_tools():
    """Return a list of available tool names."""
    return [
        "ClinicalTrialsTool",
        "TravelTool",
        "WebSearchTool",
        "WikipediaTool",
        "WolframAlphaTool",
        "YFinanceNews",
        "YoutubeSearch",
        "DateTimeTool",
        "CodeAnalysisTool",
        "Translator"
    ]