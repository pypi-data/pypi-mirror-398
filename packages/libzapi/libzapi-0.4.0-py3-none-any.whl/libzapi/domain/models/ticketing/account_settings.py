"""
For references, see https://developer.zendesk.com/api-reference/ticketing/account-configuration/account_settings/
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Branding:
    header_color: str
    page_background_color: str
    tab_background_color: str
    text_color: str
    header_logo_url: str | None
    favicon_url: str | None


@dataclass(frozen=True, slots=True)
class Apps:
    use: bool
    create_private: bool
    create_public: bool


@dataclass(frozen=True, slots=True)
class SuspendedTicketNotification:
    frequency: int
    email_list: str


@dataclass(frozen=True, slots=True)
class Tickets:
    agent_ticket_deletion: bool
    list_newest_comments_first: bool
    collaboration: bool
    private_attachments: bool
    email_attachments: bool
    agent_collision: bool
    tagging: bool
    list_empty_views: bool
    comments_public_by_default: bool
    is_first_comment_private_enabled: bool
    maximum_personal_views_to_list: int
    status_hold: bool
    markdown_ticket_comments: bool
    rich_text_comments: bool
    default_to_draft_mode: bool
    emoji_autocompletion: bool
    has_color_text: bool
    assign_tickets_upon_solve: bool
    allow_group_reset: bool
    assign_default_organization: bool
    messaging_transcript_public: bool
    app_shortcuts_context_panel_enabled: bool
    auto_translation_enabled: bool
    agent_invitation_enabled: bool
    chat_sla_enablement: bool
    modern_ticket_reassignment: bool
    show_modern_ticket_reassignment: bool
    default_solved_ticket_reassignment_strategy: str
    accepted_new_collaboration_tos: bool
    follower_and_email_cc_collaborations: bool
    auto_updated_ccs_followers_rules: bool
    agent_can_change_requester: bool
    comment_email_ccs_allowed: bool
    ticket_followers_allowed: bool
    ticket_auto_tagging: bool
    end_user_attachments: bool
    copy_original_assignee_and_group_to_followup: bool
    ccs_requester_excluded_public_comments: bool
    bcc_archive_address: str
    suspended_ticket_notification: SuspendedTicketNotification
    light_agent_email_ccs_allowed: bool
    agent_email_ccs_become_followers: bool
    using_skill_based_routing: bool
    custom_statuses_enabled: bool
    modify_closed_tickets_customer_setting: bool
    help_center_enabled: bool
    display_fcp_setting: bool
    ocb_messaging_enabled: bool
    native_messaging_enabled: bool
    bcc_archiving_available: bool
    bcc_archiving_enabled: bool
    ticket_tags_via_widget_enabled: bool
    trial: bool
    part_of_new_collaboration_eap_and_accepted_tos: bool
    accepted_tos_but_new_collaboration_disabled: bool
    third_party_end_user_public_comments_setting: bool
    cc_blacklist: str
    collaborators_settable_in_help_center: bool
    ticket_tags_via_widget: str
    ocb_enabled: str
    reengagement: bool
    third_party_end_user_public_comments: bool
    lockdown_enabled: bool
    email_comments_public: bool
    render_custom_uri_hyperlinks: str
    ticket_id_sequence: int
    follower_subject_template: str
    follower_email_template: str
    ticket_email_ccs_suspension_threshold: int
    messaging_enabled: bool
    ccs_followers_rules_update_required: bool
    ccs_followers_no_rollback: bool
    sunco_private_attachments_enabled: bool
    only_allowed_attachment_file_types: str
    only_allowed_attachment_file_types_agreement: str
    attachment_public_expiration: bool
    attachment_public_duration: int


@dataclass(frozen=True, slots=True)
class Agents:
    agent_workspace: bool
    focus_mode: bool
    aw_self_serve_migration_enabled: bool
    aw_auto_activation_timestamp: bool
    aw_auto_activation_timestamp: str | None
    aw_auto_activation_status: int
    aw_prevent_opt_out: bool
    agent_as_a_requester: str
    idle_timeout_enabled: bool
    agent_home: bool
    split_view_enabled: bool
    split_view_tos_accepted: bool
    dark_mode_agent_workspace: bool
    dark_mode_terms_and_conditions_accepted: bool
    example_eap_tos_accepted: bool
    example_eap_enabled: bool
    it_asset_management_eap_tos_accepted: bool
    it_asset_management_eap_enabled: bool


@dataclass(frozen=True, slots=True)
class Groups:
    check_group_name_uniqueness: bool


@dataclass(frozen=True, slots=True)
class Chat:
    enabled: bool
    integrated: bool
    available: bool
    maximum_request_count: int
    welcome_message: str
    ctm_auto_activation_timestamp: datetime
    ctm_auto_activation_status: int
    ctm_prevent_opt_out: bool
    ctm_segment: int
    ctm_operating_hours_migration_status: int
    ctm_chat_triggers_migration_status: int
    ctm_chat_triggers_llm_migration_status: int
    ctm_default_setup_csat_status: int
    ctm_pre_chat_form_migration_status: int
    ctm_offline_form_migration_status: int
    ctm_visitor_ip_banned_migration_status: int
    ctm_goals_migration_status: int
    ctm_chat_routing_migration_status: int
    ctm_device_metadata_migration_status: int
    ctm_reporting_migration_status: int
    ctm_chat_api_migration_status: int
    ctm_mobile_sdk_migration_status: int
    ctm_default_setup_end_session_status: int
    ctm_default_setup_auto_release_status: int
    ctm_default_setup_wait_time_status: int


@dataclass(frozen=True, slots=True)
class Voice:
    enabled: bool
    logging: bool
    outbound_enabled: bool
    agent_confirmation_when_forwarding: bool
    agent_wrap_up_after_calls: bool
    maximum_queue_size: int
    maximum_queue_wait_time: int
    only_during_business_hours: bool
    recordings_public: bool
    uk_mobile_forwarding: bool
    voice_ai_enabled: bool
    voice_ai_display_transcript: bool
    voice_zendesk_qa_enabled: bool
    knowledge_suggestions_enabled: bool
    knowledge_suggestions_group_ids: list[int]
    voice_transcriptions_pii_redaction: bool
    voice_transcriptions_pci_redaction: bool
    voice_transcriptions_boosted_keywords_enabled: bool
    voice_transcriptions_boosted_keywords: str


@dataclass(frozen=True, slots=True)
class Twitter:
    shorten_url: str


@dataclass(frozen=True, slots=True)
class GoogleApps:
    has_google_apps: bool
    has_google_apps_admin: bool


@dataclass(frozen=True, slots=True)
class User:
    tagging: bool
    time_zone_selection: bool
    language_selection: bool
    multiple_organizations: bool
    agent_created_welcome_emails: bool
    end_user_phone_number_validation: bool
    have_gravatars_enabled: bool


@dataclass(frozen=True, slots=True)
class Screencast:
    enabled_for_tickets: bool
    host: str | None
    tickets_recorder_id: int | None


@dataclass(frozen=True, slots=True)
class Lotus:
    prefer_lotus: bool
    reporting: bool
    pod_id: int


@dataclass(frozen=True, slots=True)
class Statistics:
    forum: bool
    search: bool
    rule_usage: bool


@dataclass(frozen=True, slots=True)
class Billing:
    backend: str


@dataclass(frozen=True, slots=True)
class ActiveFeatures:
    on_hold_status: bool
    user_tagging: bool
    ticket_tagging: bool
    topic_suggestion: bool
    voice: bool
    business_hours: bool
    facebook_login: bool
    google_login: bool
    twitter_login: bool
    forum_analytics: bool
    agent_forwarding: bool
    chat: bool
    chat_about_my_ticket: bool
    customer_satisfaction: bool
    satisfaction_prediction: bool
    automatic_answers: bool
    csat_reason_code: bool
    screencasts: bool
    markdown: bool
    bcc_archiving: bool
    allow_ccs: bool
    organization_access_enabled: bool
    audit_logs_gdpr: bool
    access_logs_enabled: bool
    explore: bool
    explore_on_support_ent_plan: bool
    explore_on_support_pro_plan: bool
    good_data_and_explore: bool
    good_data_only: bool
    explore_forbidden: bool
    explore_not_set: bool
    sandbox: bool
    suspended_ticket_notification: bool
    twitter: bool
    facebook: bool
    dynamic_contents: bool
    light_agents: bool
    ticket_forms: bool
    user_org_fields: bool
    is_abusive: bool
    rich_content_in_emails: bool
    custom_object_nav_enabled: bool
    release_control_enabled: bool
    data_masking_configured_in_roles: bool
    approvals_activated: bool
    has_ever_used_approvals: bool
    benchmark_opt_out: bool
    custom_dkim_domain: bool
    allow_email_template_customization: bool
    custom_objects_activated: bool


@dataclass(frozen=True, slots=True)
class TicketForm:
    ticket_forms_instructions: str
    raw_ticket_forms_instructions: str


@dataclass(frozen=True, slots=True)
class Brands:
    default_brand_id: int
    require_brand_on_new_tickets: bool
    end_user_across_brand_requests: bool
    new_agent_brand_association_behavior: str
    end_user_upgrade_brand_association_behavior: str


@dataclass(frozen=True, slots=True)
class Api:
    accepted_api_agreement: bool
    api_password_access: str
    api_password_access_end_users: bool
    api_token_access: str


@dataclass(frozen=True, slots=True)
class Rule:
    macro_most_used: bool
    macro_order: str
    skill_based_filtered_views: list[int]
    using_skill_based_routing: bool
    enable_macro_suggestions: bool


@dataclass(frozen=True, slots=True)
class Limits:
    attachment_size: int


@dataclass(frozen=True, slots=True)
class Onboarding:
    checklist_onboarding_version: int
    onboarding_segments: str | None
    product_sign_up: str | None


@dataclass(frozen=True, slots=True)
class CrossSell:
    show_chat_tooltip: bool
    xsell_source: str | None


@dataclass(frozen=True, slots=True)
class Hosts:
    name: str
    url: str


@dataclass(frozen=True, slots=True)
class Cdn:
    cdn_provider: str
    fallback_cdn_provider: str
    hosts: list[Hosts]


@dataclass(frozen=True, slots=True)
class Metrics:
    account_size: str


@dataclass(frozen=True, slots=True)
class Localization:
    locale_ids: list[int]
    time_zone: str
    iana_time_zone: str
    default_locale_identifier: str
    uses_12_hour_clock: bool


@dataclass(frozen=True, slots=True)
class Knowledge:
    default_search_filters_brands: str
    default_search_filters_categories: str
    default_search_filters_external_content_sources: str
    default_search_filters_locales: str
    default_search_filters_sections: str
    search_articles: bool
    search_community_posts: bool
    search_external_content: bool
    require_article_templates: bool
    generative_answers: bool


@dataclass(frozen=True, slots=True)
class Routing:
    enabled: bool
    autorouting_tag: str
    max_email_capacity: int
    max_messaging_capacity: int
    reassignment_messaging_enabled: bool
    reassignment_messaging_timeout: int
    reassignment_talk_timeout: int
    skills_enabled: bool
    skills_timeout_enabled: bool
    skills_timeout_support: int
    skills_timeout_messaging: int
    skills_timeout_talk: int
    reassignment_reopened_tickets_enabled: bool
    reassignment_reopened_tickets_support_enabled: bool
    reassignment_reopened_tickets_messaging_enabled: bool
    reassignment_reopened_tickets_support_statuses: list[str]
    reassignment_reopened_tickets_messaging_statuses: list[str]
    reassignment_agent_status_change_enabled: bool
    reassignment_agent_status_change_support_enabled: bool
    reassignment_agent_status_change_messaging_enabled: bool
    reassignment_agent_status_change_support_agent_statuses: list[str]
    reassignment_agent_status_change_support_ticket_priorities: list[str]
    reassignment_agent_status_change_messaging_agent_statuses: list[str]
    reassignment_agent_status_change_messaging_ticket_priorities: list[str]
    reassignment_through_queues_enabled: bool
    messaging_activity_routing_enabled: bool
    auto_activation: int
    auto_open_email_enabled: bool
    auto_accept_messaging_enabled: bool
    focus_mode_enabled: bool
    assignment_method: str
    ticket_sorting_prioritize_sla: bool
    transform_to_email_enabled: bool


@dataclass(frozen=True, slots=True)
class Deletion:
    user_auto_delete_soft_deleted_retention: int
    user_auto_delete_max_deletions_per_hour: int
    user_auto_delete_batch_size: int
    user_auto_delete_account_prioritisation: int


@dataclass(frozen=True, slots=True)
class Reminders:
    message: str
    tags: list[str] = field(default_factory=list)
    timeout: Optional[int] = None
    ticket_status_id: Optional[int] = None


@dataclass(frozen=True, slots=True)
class DefaultLocalizedMessages:
    pre_solved_message_1: str
    pre_solved_message_2: str
    solved_message: str


@dataclass(frozen=True, slots=True)
class MessagingInactivity:
    timeout: int
    enabled: bool
    ticket_status_id: int
    end_session: bool
    reminders: list[Reminders]
    default_localized_messages: DefaultLocalizedMessages


@dataclass(frozen=True, slots=True)
class DeviceMetadata:
    enabled: bool
    hide_ip: bool
    hide_location: bool


@dataclass(frozen=True, slots=True)
class Messaging:
    messaging_end_session: bool


@dataclass(frozen=True, slots=True)
class ItAssetManagement:
    enabled: bool


@dataclass(frozen=True, slots=True)
class Email:
    accept_wildcard_emails: bool
    custom_dkim_domain: bool
    email_status: bool
    email_sender_authentication: bool
    email_sender_authentication_profile: str
    email_template_photos: bool
    email_template_selection: bool
    gmail_actions: bool
    html_mail_template: str
    modern_email_template: bool
    no_mail_delimiter: bool
    personalized_replies: bool
    rich_content_in_emails: bool
    send_gmail_messages_via_gmail: bool
    text_mail_template: str


@dataclass(frozen=True, slots=True)
class AutomaticAnswers:
    threshold: str


@dataclass(frozen=True, slots=True)
class SideConversations:
    email_channel: bool
    msteams_channel: bool
    slack_channel: bool
    tickets_channel: bool
    show_in_context_panel: bool


@dataclass(frozen=True, slots=True)
class Ai:
    macro_content_suggestions_title_gen_enabled: bool


@dataclass(frozen=True, slots=True)
class Settings:
    branding: Branding
    apps: Apps
    tickets: Tickets
    agents: Agents
    groups: Groups
    chat: Chat
    voice: Voice
    twitter: Twitter
    google_apps: GoogleApps
    user: User
    screencast: Screencast
    lotus: Lotus
    statistics: Statistics
    billing: Billing
    active_features: ActiveFeatures
    ticket_form: TicketForm
    brands: Brands
    api: Api
    rule: Rule
    limits: Limits
    onboarding: Onboarding
    cross_sell: CrossSell
    cdn: Cdn
    metrics: Metrics
    localization: Localization
    knowledge: Knowledge
    routing: Routing
    deletion: Deletion
    messaging_inactivity: MessagingInactivity
    device_metadata: DeviceMetadata
    messaging: Messaging
    it_asset_management: ItAssetManagement
    email: Email
    automatic_answers: AutomaticAnswers
    side_conversations: SideConversations
    ai: Ai
