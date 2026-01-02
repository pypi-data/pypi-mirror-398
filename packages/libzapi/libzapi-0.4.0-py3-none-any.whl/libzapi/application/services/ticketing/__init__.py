import libzapi.infrastructure.api_clients.ticketing as api
from libzapi.application.services.ticketing.account_settings_service import AccountSettingsService
from libzapi.application.services.ticketing.attachments_service import AttachmentsService
from libzapi.application.services.ticketing.automations_service import AutomationsService
from libzapi.application.services.ticketing.brand_agents_service import BrandAgentsService
from libzapi.application.services.ticketing.brands_service import BrandsService
from libzapi.application.services.ticketing.email_notifications_service import EmailNotificationService
from libzapi.application.services.ticketing.groups_service import GroupsService
from libzapi.application.services.ticketing.macro_service import MacroService
from libzapi.application.services.ticketing.organizations_service import OrganizationsService
from libzapi.application.services.ticketing.requests_service import RequestsService
from libzapi.application.services.ticketing.schedule_service import ScheduleService
from libzapi.application.services.ticketing.sessions_service import SessionsService
from libzapi.application.services.ticketing.sla_policies_service import SlaPoliciesService
from libzapi.application.services.ticketing.support_addresses_service import SupportAddressesService
from libzapi.application.services.ticketing.suspended_tickets_service import SuspendedTicketsService
from libzapi.application.services.ticketing.tickets_service import TickestService
from libzapi.application.services.ticketing.ticket_audits_service import TicketAuditsService
from libzapi.application.services.ticketing.ticket_fields_service import TicketFieldsService
from libzapi.application.services.ticketing.ticket_forms_service import TicketFormsService
from libzapi.application.services.ticketing.ticket_metrics_service import TicketMetricsService
from libzapi.application.services.ticketing.ticket_trigger_categories_service import TicketTriggerCategoriesService
from libzapi.application.services.ticketing.ticket_trigger_service import TicketTriggerService
from libzapi.application.services.ticketing.users_service import UsersService
from libzapi.application.services.ticketing.user_fields_service import UserFieldsService
from libzapi.application.services.ticketing.views_service import ViewsService
from libzapi.application.services.ticketing.workspace_service import WorkspaceService
from libzapi.infrastructure.http.auth import oauth_headers, api_token_headers
from libzapi.infrastructure.http.client import HttpClient


class Ticketing:
    def __init__(
        self, base_url: str, oauth_token: str | None = None, email: str | None = None, api_token: str | None = None
    ):
        if oauth_token:
            headers = oauth_headers(oauth_token)
        elif email and api_token:
            headers = api_token_headers(email, api_token)
        else:
            raise ValueError("Provide oauth_token or email+api_token")

        http = HttpClient(base_url, headers=headers)

        # Initialize services
        self.account_settings = AccountSettingsService(api.AccountSettingsApiClient(http))
        self.attachments = AttachmentsService(api.AttachmentApiClient(http))
        self.automations = AutomationsService(api.AutomationApiClient(http))
        self.brands = BrandsService(api.BrandApiClient(http))
        self.brand_agents = BrandAgentsService(api.BrandAgentApiClient(http))
        self.email_notifications = EmailNotificationService(api.EmailNotificationApiClient(http))
        self.groups = GroupsService(api.GroupApiClient(http))
        self.macros = MacroService(api.MacroApiClient(http))
        self.organizations = OrganizationsService(api.OrganizationApiClient(http))
        self.requests = RequestsService(api.RequestApiClient(http))
        self.schedules = ScheduleService(api.ScheduleApiClient(http))
        self.sessions = SessionsService(api.SessionApiClient(http))
        self.sla_policies = SlaPoliciesService(api.SlaPolicyApiClient(http))
        self.support_addresses = SupportAddressesService(api.SupportAddressApiClient(http))
        self.suspended_tickets = SuspendedTicketsService(api.SuspendedTicketApiClient(http))
        self.tickets = TickestService(api.TicketApiClient(http))
        self.ticket_audits = TicketAuditsService(api.TicketAuditApiClient(http))
        self.ticket_fields = TicketFieldsService(api.TicketFieldApiClient(http))
        self.ticket_forms = TicketFormsService(api.TicketFormApiClient(http))
        self.ticket_metrics = TicketMetricsService(api.TicketMetricApiClient(http))
        self.ticket_metric_events = api.TicketMetricEventApiClient(http)
        self.ticket_triggers = TicketTriggerService(api.TicketTriggerApiClient(http))
        self.ticket_trigger_categories = TicketTriggerCategoriesService(api.TicketTriggerCategoryApiClient(http))
        self.users = UsersService(api.UserApiClient(http))
        self.user_fields = UserFieldsService(api.UserFieldApiClient(http))
        self.views = ViewsService(api.ViewApiClient(http))
        self.workspaces = WorkspaceService(api.WorkspaceApiClient(http))
