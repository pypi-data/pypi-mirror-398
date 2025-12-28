from biz_agent_hub.support_agent import SupportAgent
from biz_agent_hub.scrap_agent import ScrapAgent
from biz_agent_hub.analytics_agent import AnalyticsAgent
from biz_agent_hub.ui_testing_agent import UITestingAgent


class BizAgentHub:
    user_id: str
    api_key: str
    support_agent: SupportAgent
    scrap_agent: ScrapAgent
    analytics_agent: AnalyticsAgent
    ui_testing_agent: UITestingAgent
    def __init__(self, user_id: str, api_key: str) -> None:
        self.user_id = user_id
        self.api_key = api_key
        self.support_agent = SupportAgent(user_id, api_key)
        self.scrap_agent = ScrapAgent(user_id, api_key)
        self.analytics_agent = AnalyticsAgent(user_id, api_key)
        self.ui_testing_agent = UITestingAgent(user_id, api_key)

