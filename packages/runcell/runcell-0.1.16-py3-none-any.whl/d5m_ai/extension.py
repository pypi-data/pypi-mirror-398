# Load environment variables first, before any imports that might use them
import os
from dotenv import load_dotenv
load_dotenv()

from jupyter_server.extension.application import ExtensionApp
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from .chat import AIChatHandler
from .chat.history import AIChatHistoryListHandler, AIChatHistoryHandler
from tornado import web
from .sandbox.handler import VirtualCellHandler
from .sandbox.shell_exec import ShellExecHandler
from .chat.code_apply import CodeApplyHandler
from .mention.mention_file_handler import MentionFileHandler
from .auth.token_handler import TokenHandler
from .ping.ping_handler import PingProxyHandler, PingLocalHandler
from .empty_display import EmptyDisplayProxyHandler
from .title import TitleGenerationHandler
from .quick_fix import QuickFixApplyHandler

from .completion import CompletionHandler
from .edit import AIEditChatHandler
from .predictive_interaction.cell.dataframe_handler import PredictiveInteractionCellHandler
from .predictive_interaction.cell.viz_handler import VisualizationAnalysisHandler
from .sandbox.fork_kernel import ForkKernelHandler
from .agent import AIJLAgentProxyHandler
from .agent.config import IMAGE_DIR
from .image import get_image_handlers
from .upgrade import UpgradeEnvironmentHandler, UpgradeHandler
from .gitignore_handler import GitIgnoreHandler
from .git_status_handler import GitStatusHandler
from .search_replace_handler import SearchReplaceHandler

# Static file handler for serving image files
class ImageFileHandler(web.StaticFileHandler):
    def set_extra_headers(self, path):
        # Set CORS headers
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        # Set cache control for better performance
        self.set_header("Cache-Control", "public, max-age=3600")

class D5MAIExtensionApp(ExtensionApp):
    name = "d5m_ai"
    extension_id = "d5m_ai"
    extension_name = "D5M AI"
    version = "0.1.0"

    @property
    def handlers(self):
        # Basic handlers
        handlers = [
            (r"/api/d5m_ai/predictive_interaction", PredictiveInteractionCellHandler),
            (r"/api/d5m_ai/visualization_analysis", VisualizationAnalysisHandler),
            (r"/api/d5m_ai/virtualcell", VirtualCellHandler),
            (r"/api/d5m_ai/fork_kernel", ForkKernelHandler),
            (r"/api/d5m_ai/chat", AIChatHandler),
            # (r"/api/d5m_ai/completion", AnthropicCompletionHandler),
            (r"/api/d5m_ai/inline_completion", CompletionHandler),
            (r"/api/d5m_ai/code_apply", CodeApplyHandler),
            (r"/api/d5m_ai/chat/history_list", AIChatHistoryListHandler),
            (r"/api/d5m_ai/chat/history", AIChatHistoryHandler),
            (r"/api/d5m_ai/agent/chat", AIJLAgentProxyHandler),
            (r"/api/d5m_ai/edit/chat", AIEditChatHandler),
            (r"/api/d5m_ai/shell/exec", ShellExecHandler),
            (r"/api/d5m_ai/mention/files", MentionFileHandler),
            (r"/api/d5m_ai/auth/token", TokenHandler),
            (r"/api/d5m_ai/ping", PingProxyHandler),
            (r"/api/d5m_ai/ping_local", PingLocalHandler),
            (r"/api/d5m_ai/empty_display", EmptyDisplayProxyHandler),
            (r"/api/d5m_ai/generate_title", TitleGenerationHandler),
            (r"/api/d5m_ai/quick_fix_apply", QuickFixApplyHandler),
            (r"/api/d5m_ai/upgrade/info", UpgradeEnvironmentHandler),
            (r"/api/d5m_ai/upgrade", UpgradeHandler),
            (r"/api/d5m_ai/gitignore", GitIgnoreHandler),
            (r"/api/d5m_ai/git-status", GitStatusHandler),
            (r"/api/d5m_ai/search_replace", SearchReplaceHandler),
            # Static file handler for the temporary image files
            (r"/d5m-ai/images/(.*)", ImageFileHandler, {"path": IMAGE_DIR}),
        ]
        
        # Add image service handlers
        handlers.extend(get_image_handlers())
        
        return handlers
