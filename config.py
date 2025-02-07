import os
from dotenv import load_dotenv

load_dotenv()

class NotionApiKeyConfig:
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")

class DatabaseIdConfig:
    TRAVA_DATABASE_ID = os.getenv("TRAVA_DATABASE_ID")
    DATA_ANALYSIS_DATABASE_ID = os.getenv("DATA_ANALYSIS_DATABASE_ID")
    CENTIC_DATABASE_ID = os.getenv("CENTIC_DATABASE_ID")
    MAZIG_DATABASE_ID = os.getenv("MAZIG_DATABASE_ID")
    TCV_DATABASE_ID  = os.getenv("TCV_DATABASE_ID")
    ORCHAI_DATABASE_ID = os.getenv("ORCHAI_DATABASE_ID")
    THORN_DATABASE_ID = os.getenv("THORN_DATABASE_ID")
    FRONTEND_DATABASE_ID =os.getenv("FRONTEND_DATABASE_ID")
    DESIGN_DATABASE_ID = os.getenv("DESIGN_DATABASE_ID")
    AI_DATABASE_ID = os.getenv("AI_DATABASE_ID")
    BACKEND_DATABASE_ID = os.getenv("BACKEND_DATABASE_ID")
    TRADING_DATABASE_ID = os.getenv("TRADING_DATABASE_ID")
    TRUFY_DATABASE_ID = os.getenv("TRUFY_DATABASE_ID")
    DEVOPS_DATABASE_ID = os.getenv("DEVOPS_DATABASE_ID")
    LOOMIX_DATABASE_ID = os.getenv("LOOMIX_DATABASE_ID")
    STABLE_AI_AGENT_DATABASE_ID = os.getenv("STABLE_AI_AGENT_DATABASE_ID")