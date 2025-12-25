import datetime
from typing import (TYPE_CHECKING, Any, Dict, List, Optional, Type, TypeVar,
                    Union, cast)

import attr
from dateutil.parser import isoparse

from ..models.organization_addon_billing_period import \
    OrganizationAddonBillingPeriod
from ..models.organization_flags_item import OrganizationFlagsItem
from ..models.organization_invoice_billing_period import \
    OrganizationInvoiceBillingPeriod
from ..models.organization_plan import OrganizationPlan
from ..models.organization_support_tier import OrganizationSupportTier
from ..models.organization_supported_regions_item import \
    OrganizationSupportedRegionsItem
from ..types import UNSET, Unset

if TYPE_CHECKING:
  from ..models.aws_info import AwsInfo
  from ..models.billing_info import BillingInfo
  from ..models.device_configuration_document import \
      DeviceConfigurationDocument
  from ..models.google_info import GoogleInfo
  from ..models.google_storage_info import GoogleStorageInfo
  from ..models.overview_settings import OverviewSettings
  from ..models.pagerduty_info import PagerdutyInfo
  from ..models.rtc_info import RtcInfo
  from ..models.slack_info import SlackInfo
  from ..models.stripe_info import StripeInfo
  from ..models.teleop_high_ping_reconnect_behaviors import \
      TeleopHighPingReconnectBehaviors
  from ..models.user_teleop_configuration import UserTeleopConfiguration
  from ..models.webhooks_info import WebhooksInfo




T = TypeVar("T", bound="Organization")

@attr.s(auto_attribs=True)
class Organization:
    """
    Attributes:
        plan (OrganizationPlan):
        name (str):
        industry (str):
        website (str):
        address_line_1 (str):
        address_line_2 (str):
        city (str):
        state (str):
        postal_code (str):
        country (str):
        addon_billing_period (OrganizationAddonBillingPeriod):
        invoice_billing_period (OrganizationInvoiceBillingPeriod):
        terms_modal_v2_enabled (bool):
        themes (List[Any]):
        description (Union[Unset, None, str]):
        enabled (Union[Unset, bool]):
        pagerduty_info (Union[Unset, PagerdutyInfo]):
        teleop_high_ping_reconnect_behaviors (Union[Unset, TeleopHighPingReconnectBehaviors]):
        slack_info (Union[Unset, SlackInfo]):
        google_info (Union[Unset, GoogleInfo]):
        webhooks_info (Union[Unset, WebhooksInfo]):
        aws_info (Union[Unset, AwsInfo]):
        google_storage_info (Union[Unset, GoogleStorageInfo]):
        stripe_info (Union[Unset, StripeInfo]):
        rtc_info (Union[Unset, RtcInfo]):
        teleop_configuration (Union[Unset, UserTeleopConfiguration]):
        data_export_enabled (Union[Unset, None, datetime.datetime]):
        advanced_configuration_enabled (Union[Unset, None, datetime.datetime]):
        customer_portal_enabled (Union[Unset, None, datetime.datetime]):
        stripe_billing_enabled (Union[Unset, bool]):
        stripe_subscription_enabled (Union[Unset, bool]):
        mission_planning_enabled (Union[Unset, bool]):
        billing_info (Union[Unset, BillingInfo]):
        s_3_export_enabled (Union[Unset, bool]):
        blob_data_enabled (Union[Unset, bool]):
        white_label_enabled (Union[Unset, bool]):
        viewer_3_d_enabled (Union[Unset, bool]):
        adapters_enabled (Union[Unset, bool]):
        white_label_css (Union[Unset, None, str]):
        demo_mode_enabled (Union[Unset, bool]):
        teleop_share_enabled (Union[Unset, bool]):
        bill_estimate_enabled (Union[Unset, bool]):
        data_retention_enabled (Union[Unset, None, datetime.datetime]):
        days_data_retained (Union[Unset, int]):
        max_chunk_request_limit (Union[Unset, int]):
        limit_metadatas (Union[Unset, bool]):
        online_sensitivity (Union[Unset, int]):
        support_enabled (Union[Unset, None, datetime.datetime]):
        support_tier (Union[Unset, OrganizationSupportTier]):
        trial_period_end (Optional[datetime.datetime]):
        external_id (Union[Unset, str]):
        chargebee_id (Optional[str]):
        default_group_category (Optional[str]):
        external_twilio_config (Optional[str]):
        totango_id (Optional[str]):
        hubspot_id (Optional[str]):
        custom_tos (Union[Unset, bool]):
        teleop_enabled (Union[Unset, None, datetime.datetime]):
        observability_enabled (Union[Unset, None, datetime.datetime]):
        share_enabled (Union[Unset, None, datetime.datetime]):
        annotations_enabled (Union[Unset, None, datetime.datetime]):
        diagnostics_enabled (Union[Unset, None, datetime.datetime]):
        ssh_enabled (Union[Unset, None, datetime.datetime]):
        spot_enabled (Union[Unset, None, datetime.datetime]):
        file_storage_enabled (Union[Unset, bool]):
        role_viewer_enabled (Union[Unset, bool]):
        teams_enabled (Union[Unset, bool]):
        schedules_enabled (Union[Unset, bool]):
        beta_ui (Union[Unset, bool]):
        realtime_v2_enabled (Union[Unset, bool]):
        paging_enabled (Union[Unset, bool]):
        stateful_events_enabled (Union[Unset, bool]):
        billing_enabled (Union[Unset, bool]):
        sms_followers_enabled (Union[Unset, bool]):
        event_action_interval_enabled (Union[Unset, bool]):
        task_summaries_enabled (Union[Unset, bool]):
        default_device_config (Union[Unset, DeviceConfigurationDocument]):
        default_stream_throttle_hz (Union[Unset, None, float]):
        outage_banner_enabled (Union[Unset, bool]):
        new_header_enabled (Union[Unset, bool]):
        explorations_enabled (Union[Unset, bool]):
        customer_success_ai_enabled (Union[Unset, bool]):
        custom_analytics_enabled (Union[Unset, bool]):
        fleet_analytics_enabled (Union[Unset, bool]):
        navigator_enabled (Union[Unset, bool]):
        list_view_enabled (Union[Unset, bool]):
        map_view_enabled (Union[Unset, bool]):
        node_graph_page_enabled (Union[Unset, bool]):
        flags (Union[Unset, List[OrganizationFlagsItem]]):
        overview_settings (Union[Unset, OverviewSettings]):
        snowflake_warehouse_name (Optional[str]):
        snowflake_schema_name (Union[Unset, None, str]):
        supported_regions (Union[Unset, List[OrganizationSupportedRegionsItem]]):
        enable_sso_oidc (Union[Unset, bool]):
        inactivity_logout_enabled (Union[Unset, bool]):
        sms_opt_in_enabled (Union[Unset, bool]):
        inactivity_timeout (Union[Unset, float]):
        allow_custom_email_configuration (Union[Unset, bool]):
        portal_base_url (Union[Unset, None, str]):
        ingestion_enabled (Union[Unset, bool]):
        timescale_enabled (Optional[datetime.datetime]):
        clickhouse_enabled (Optional[datetime.datetime]):
        clickhouse_query_enabled (Union[Unset, bool]):
        drop_experimental_query_data (Union[Unset, bool]):
        event_queries_enabled (Union[Unset, bool]):
        snowflake_row_level_security_enabled (Union[Unset, bool]):
        clickhouse_analytics_enabled (Union[Unset, bool]):
        cached_events_enabled (Union[Unset, bool]):
        user_tag_settings_enabled (Union[Unset, bool]):
        bulk_provisioning_enabled (Union[Unset, bool]):
        device_configuration_templates_enabled (Union[Unset, bool]):
        observability_v1_enabled (Union[Unset, bool]):
        analytics_v1_enabled (Union[Unset, bool]):
        custom_roles_enabled (Union[Unset, bool]):
        mixed_module_mode_enabled (Union[Unset, bool]):
        google_storage_export_enabled (Union[Unset, bool]):
        custom_modules_enabled (Union[Unset, bool]):
        native_scene_module_enabled (Union[Unset, bool]):
        ai_insights_enabled (Union[Unset, bool]):
        ai_enabled (Union[Unset, bool]):
        teleop_3_preview_button (Union[Unset, bool]):
        use_dynamic_presence (Union[Unset, bool]):
        show_get_started_on_overview (Union[Unset, bool]):
        sidebar_hidden_sections (Union[Unset, List[str]]):
        design_fleet_manager_white_listed_users (Union[Unset, None, str]):
        design_fleet_manager_view_name (Union[Unset, None, str]):
        optional_help_link (Union[Unset, None, str]):
        teleop_joy_enabled (Union[Unset, bool]):
        show_overview_filters (Union[Unset, bool]):
        local_mode_enabled (Union[Unset, bool]):
        embed_view_enabled (Union[Unset, bool]):
        investigations_enabled (Union[Unset, bool]):
        investigations_beta_enabled (Union[Unset, bool]):
        v_2_custom_modules_enabled (Union[Unset, bool]):
        v_2_overview_enabled (Union[Unset, bool]):
        sidebar_v2_enabled (Union[Unset, bool]):
        alarm_console_enabled (Union[Unset, bool]):
        multiple_primary_teleop_enabled (Union[Unset, bool]):
        ros_2_streams_enabled (Union[Unset, bool]):
        commands_module_enabled (Union[Unset, bool]):
        theme_customizer_enabled (Union[Unset, bool]):
        id (Union[Unset, str]):
        created_at (Union[Unset, datetime.datetime]):
        updated_at (Union[Unset, datetime.datetime]):
    """

    plan: OrganizationPlan
    name: str
    industry: str
    website: str
    address_line_1: str
    address_line_2: str
    city: str
    state: str
    postal_code: str
    country: str
    addon_billing_period: OrganizationAddonBillingPeriod
    invoice_billing_period: OrganizationInvoiceBillingPeriod
    terms_modal_v2_enabled: bool
    themes: List[Any]
    trial_period_end: Optional[datetime.datetime]
    chargebee_id: Optional[str]
    default_group_category: Optional[str]
    external_twilio_config: Optional[str]
    totango_id: Optional[str]
    hubspot_id: Optional[str]
    snowflake_warehouse_name: Optional[str]
    timescale_enabled: Optional[datetime.datetime]
    clickhouse_enabled: Optional[datetime.datetime]
    description: Union[Unset, None, str] = UNSET
    enabled: Union[Unset, bool] = UNSET
    pagerduty_info: Union[Unset, 'PagerdutyInfo'] = UNSET
    teleop_high_ping_reconnect_behaviors: Union[Unset, 'TeleopHighPingReconnectBehaviors'] = UNSET
    slack_info: Union[Unset, 'SlackInfo'] = UNSET
    google_info: Union[Unset, 'GoogleInfo'] = UNSET
    webhooks_info: Union[Unset, 'WebhooksInfo'] = UNSET
    aws_info: Union[Unset, 'AwsInfo'] = UNSET
    google_storage_info: Union[Unset, 'GoogleStorageInfo'] = UNSET
    stripe_info: Union[Unset, 'StripeInfo'] = UNSET
    rtc_info: Union[Unset, 'RtcInfo'] = UNSET
    teleop_configuration: Union[Unset, 'UserTeleopConfiguration'] = UNSET
    data_export_enabled: Union[Unset, None, datetime.datetime] = UNSET
    advanced_configuration_enabled: Union[Unset, None, datetime.datetime] = UNSET
    customer_portal_enabled: Union[Unset, None, datetime.datetime] = UNSET
    stripe_billing_enabled: Union[Unset, bool] = UNSET
    stripe_subscription_enabled: Union[Unset, bool] = UNSET
    mission_planning_enabled: Union[Unset, bool] = UNSET
    billing_info: Union[Unset, 'BillingInfo'] = UNSET
    s_3_export_enabled: Union[Unset, bool] = UNSET
    blob_data_enabled: Union[Unset, bool] = UNSET
    white_label_enabled: Union[Unset, bool] = UNSET
    viewer_3_d_enabled: Union[Unset, bool] = UNSET
    adapters_enabled: Union[Unset, bool] = UNSET
    white_label_css: Union[Unset, None, str] = UNSET
    demo_mode_enabled: Union[Unset, bool] = UNSET
    teleop_share_enabled: Union[Unset, bool] = UNSET
    bill_estimate_enabled: Union[Unset, bool] = UNSET
    data_retention_enabled: Union[Unset, None, datetime.datetime] = UNSET
    days_data_retained: Union[Unset, int] = UNSET
    max_chunk_request_limit: Union[Unset, int] = UNSET
    limit_metadatas: Union[Unset, bool] = UNSET
    online_sensitivity: Union[Unset, int] = UNSET
    support_enabled: Union[Unset, None, datetime.datetime] = UNSET
    support_tier: Union[Unset, OrganizationSupportTier] = UNSET
    external_id: Union[Unset, str] = UNSET
    custom_tos: Union[Unset, bool] = UNSET
    teleop_enabled: Union[Unset, None, datetime.datetime] = UNSET
    observability_enabled: Union[Unset, None, datetime.datetime] = UNSET
    share_enabled: Union[Unset, None, datetime.datetime] = UNSET
    annotations_enabled: Union[Unset, None, datetime.datetime] = UNSET
    diagnostics_enabled: Union[Unset, None, datetime.datetime] = UNSET
    ssh_enabled: Union[Unset, None, datetime.datetime] = UNSET
    spot_enabled: Union[Unset, None, datetime.datetime] = UNSET
    file_storage_enabled: Union[Unset, bool] = UNSET
    role_viewer_enabled: Union[Unset, bool] = UNSET
    teams_enabled: Union[Unset, bool] = UNSET
    schedules_enabled: Union[Unset, bool] = UNSET
    beta_ui: Union[Unset, bool] = UNSET
    realtime_v2_enabled: Union[Unset, bool] = UNSET
    paging_enabled: Union[Unset, bool] = UNSET
    stateful_events_enabled: Union[Unset, bool] = UNSET
    billing_enabled: Union[Unset, bool] = UNSET
    sms_followers_enabled: Union[Unset, bool] = UNSET
    event_action_interval_enabled: Union[Unset, bool] = UNSET
    task_summaries_enabled: Union[Unset, bool] = UNSET
    default_device_config: Union[Unset, 'DeviceConfigurationDocument'] = UNSET
    default_stream_throttle_hz: Union[Unset, None, float] = UNSET
    outage_banner_enabled: Union[Unset, bool] = UNSET
    new_header_enabled: Union[Unset, bool] = UNSET
    explorations_enabled: Union[Unset, bool] = UNSET
    customer_success_ai_enabled: Union[Unset, bool] = UNSET
    custom_analytics_enabled: Union[Unset, bool] = UNSET
    fleet_analytics_enabled: Union[Unset, bool] = UNSET
    navigator_enabled: Union[Unset, bool] = UNSET
    list_view_enabled: Union[Unset, bool] = UNSET
    map_view_enabled: Union[Unset, bool] = UNSET
    node_graph_page_enabled: Union[Unset, bool] = UNSET
    flags: Union[Unset, List[OrganizationFlagsItem]] = UNSET
    overview_settings: Union[Unset, 'OverviewSettings'] = UNSET
    snowflake_schema_name: Union[Unset, None, str] = UNSET
    supported_regions: Union[Unset, List[OrganizationSupportedRegionsItem]] = UNSET
    enable_sso_oidc: Union[Unset, bool] = UNSET
    inactivity_logout_enabled: Union[Unset, bool] = UNSET
    sms_opt_in_enabled: Union[Unset, bool] = UNSET
    inactivity_timeout: Union[Unset, float] = UNSET
    allow_custom_email_configuration: Union[Unset, bool] = UNSET
    portal_base_url: Union[Unset, None, str] = UNSET
    ingestion_enabled: Union[Unset, bool] = UNSET
    clickhouse_query_enabled: Union[Unset, bool] = UNSET
    drop_experimental_query_data: Union[Unset, bool] = UNSET
    event_queries_enabled: Union[Unset, bool] = UNSET
    snowflake_row_level_security_enabled: Union[Unset, bool] = UNSET
    clickhouse_analytics_enabled: Union[Unset, bool] = UNSET
    cached_events_enabled: Union[Unset, bool] = UNSET
    user_tag_settings_enabled: Union[Unset, bool] = UNSET
    bulk_provisioning_enabled: Union[Unset, bool] = UNSET
    device_configuration_templates_enabled: Union[Unset, bool] = UNSET
    observability_v1_enabled: Union[Unset, bool] = UNSET
    analytics_v1_enabled: Union[Unset, bool] = UNSET
    custom_roles_enabled: Union[Unset, bool] = UNSET
    mixed_module_mode_enabled: Union[Unset, bool] = UNSET
    google_storage_export_enabled: Union[Unset, bool] = UNSET
    custom_modules_enabled: Union[Unset, bool] = UNSET
    native_scene_module_enabled: Union[Unset, bool] = UNSET
    ai_insights_enabled: Union[Unset, bool] = UNSET
    ai_enabled: Union[Unset, bool] = UNSET
    teleop_3_preview_button: Union[Unset, bool] = UNSET
    use_dynamic_presence: Union[Unset, bool] = UNSET
    show_get_started_on_overview: Union[Unset, bool] = UNSET
    sidebar_hidden_sections: Union[Unset, List[str]] = UNSET
    design_fleet_manager_white_listed_users: Union[Unset, None, str] = UNSET
    design_fleet_manager_view_name: Union[Unset, None, str] = UNSET
    optional_help_link: Union[Unset, None, str] = UNSET
    teleop_joy_enabled: Union[Unset, bool] = UNSET
    show_overview_filters: Union[Unset, bool] = UNSET
    local_mode_enabled: Union[Unset, bool] = UNSET
    embed_view_enabled: Union[Unset, bool] = UNSET
    investigations_enabled: Union[Unset, bool] = UNSET
    investigations_beta_enabled: Union[Unset, bool] = UNSET
    v_2_custom_modules_enabled: Union[Unset, bool] = UNSET
    v_2_overview_enabled: Union[Unset, bool] = UNSET
    sidebar_v2_enabled: Union[Unset, bool] = UNSET
    alarm_console_enabled: Union[Unset, bool] = UNSET
    multiple_primary_teleop_enabled: Union[Unset, bool] = UNSET
    ros_2_streams_enabled: Union[Unset, bool] = UNSET
    commands_module_enabled: Union[Unset, bool] = UNSET
    theme_customizer_enabled: Union[Unset, bool] = UNSET
    id: Union[Unset, str] = UNSET
    created_at: Union[Unset, datetime.datetime] = UNSET
    updated_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)


    def to_dict(self) -> Dict[str, Any]:
        plan = self.plan.value

        name = self.name
        industry = self.industry
        website = self.website
        address_line_1 = self.address_line_1
        address_line_2 = self.address_line_2
        city = self.city
        state = self.state
        postal_code = self.postal_code
        country = self.country
        addon_billing_period = self.addon_billing_period.value

        invoice_billing_period = self.invoice_billing_period.value

        terms_modal_v2_enabled = self.terms_modal_v2_enabled
        themes = self.themes




        description = self.description
        enabled = self.enabled
        pagerduty_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.pagerduty_info, Unset):
            pagerduty_info = self.pagerduty_info.to_dict()

        teleop_high_ping_reconnect_behaviors: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.teleop_high_ping_reconnect_behaviors, Unset):
            teleop_high_ping_reconnect_behaviors = self.teleop_high_ping_reconnect_behaviors.to_dict()

        slack_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.slack_info, Unset):
            slack_info = self.slack_info.to_dict()

        google_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.google_info, Unset):
            google_info = self.google_info.to_dict()

        webhooks_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.webhooks_info, Unset):
            webhooks_info = self.webhooks_info.to_dict()

        aws_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.aws_info, Unset):
            aws_info = self.aws_info.to_dict()

        google_storage_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.google_storage_info, Unset):
            google_storage_info = self.google_storage_info.to_dict()

        stripe_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.stripe_info, Unset):
            stripe_info = self.stripe_info.to_dict()

        rtc_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.rtc_info, Unset):
            rtc_info = self.rtc_info.to_dict()

        teleop_configuration: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.teleop_configuration, Unset):
            teleop_configuration = self.teleop_configuration.to_dict()

        data_export_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.data_export_enabled, Unset):
            data_export_enabled = self.data_export_enabled.isoformat() if self.data_export_enabled else None

        advanced_configuration_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.advanced_configuration_enabled, Unset):
            advanced_configuration_enabled = self.advanced_configuration_enabled.isoformat() if self.advanced_configuration_enabled else None

        customer_portal_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.customer_portal_enabled, Unset):
            customer_portal_enabled = self.customer_portal_enabled.isoformat() if self.customer_portal_enabled else None

        stripe_billing_enabled = self.stripe_billing_enabled
        stripe_subscription_enabled = self.stripe_subscription_enabled
        mission_planning_enabled = self.mission_planning_enabled
        billing_info: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.billing_info, Unset):
            billing_info = self.billing_info.to_dict()

        s_3_export_enabled = self.s_3_export_enabled
        blob_data_enabled = self.blob_data_enabled
        white_label_enabled = self.white_label_enabled
        viewer_3_d_enabled = self.viewer_3_d_enabled
        adapters_enabled = self.adapters_enabled
        white_label_css = self.white_label_css
        demo_mode_enabled = self.demo_mode_enabled
        teleop_share_enabled = self.teleop_share_enabled
        bill_estimate_enabled = self.bill_estimate_enabled
        data_retention_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.data_retention_enabled, Unset):
            data_retention_enabled = self.data_retention_enabled.isoformat() if self.data_retention_enabled else None

        days_data_retained = self.days_data_retained
        max_chunk_request_limit = self.max_chunk_request_limit
        limit_metadatas = self.limit_metadatas
        online_sensitivity = self.online_sensitivity
        support_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.support_enabled, Unset):
            support_enabled = self.support_enabled.isoformat() if self.support_enabled else None

        support_tier: Union[Unset, str] = UNSET
        if not isinstance(self.support_tier, Unset):
            support_tier = self.support_tier.value

        trial_period_end = self.trial_period_end.isoformat() if self.trial_period_end else None

        external_id = self.external_id
        chargebee_id = self.chargebee_id
        default_group_category = self.default_group_category
        external_twilio_config = self.external_twilio_config
        totango_id = self.totango_id
        hubspot_id = self.hubspot_id
        custom_tos = self.custom_tos
        teleop_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.teleop_enabled, Unset):
            teleop_enabled = self.teleop_enabled.isoformat() if self.teleop_enabled else None

        observability_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.observability_enabled, Unset):
            observability_enabled = self.observability_enabled.isoformat() if self.observability_enabled else None

        share_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.share_enabled, Unset):
            share_enabled = self.share_enabled.isoformat() if self.share_enabled else None

        annotations_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.annotations_enabled, Unset):
            annotations_enabled = self.annotations_enabled.isoformat() if self.annotations_enabled else None

        diagnostics_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.diagnostics_enabled, Unset):
            diagnostics_enabled = self.diagnostics_enabled.isoformat() if self.diagnostics_enabled else None

        ssh_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.ssh_enabled, Unset):
            ssh_enabled = self.ssh_enabled.isoformat() if self.ssh_enabled else None

        spot_enabled: Union[Unset, None, str] = UNSET
        if not isinstance(self.spot_enabled, Unset):
            spot_enabled = self.spot_enabled.isoformat() if self.spot_enabled else None

        file_storage_enabled = self.file_storage_enabled
        role_viewer_enabled = self.role_viewer_enabled
        teams_enabled = self.teams_enabled
        schedules_enabled = self.schedules_enabled
        beta_ui = self.beta_ui
        realtime_v2_enabled = self.realtime_v2_enabled
        paging_enabled = self.paging_enabled
        stateful_events_enabled = self.stateful_events_enabled
        billing_enabled = self.billing_enabled
        sms_followers_enabled = self.sms_followers_enabled
        event_action_interval_enabled = self.event_action_interval_enabled
        task_summaries_enabled = self.task_summaries_enabled
        default_device_config: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.default_device_config, Unset):
            default_device_config = self.default_device_config.to_dict()

        default_stream_throttle_hz = self.default_stream_throttle_hz
        outage_banner_enabled = self.outage_banner_enabled
        new_header_enabled = self.new_header_enabled
        explorations_enabled = self.explorations_enabled
        customer_success_ai_enabled = self.customer_success_ai_enabled
        custom_analytics_enabled = self.custom_analytics_enabled
        fleet_analytics_enabled = self.fleet_analytics_enabled
        navigator_enabled = self.navigator_enabled
        list_view_enabled = self.list_view_enabled
        map_view_enabled = self.map_view_enabled
        node_graph_page_enabled = self.node_graph_page_enabled
        flags: Union[Unset, List[str]] = UNSET
        if not isinstance(self.flags, Unset):
            flags = []
            for flags_item_data in self.flags:
                flags_item = flags_item_data.value

                flags.append(flags_item)




        overview_settings: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.overview_settings, Unset):
            overview_settings = self.overview_settings.to_dict()

        snowflake_warehouse_name = self.snowflake_warehouse_name
        snowflake_schema_name = self.snowflake_schema_name
        supported_regions: Union[Unset, List[str]] = UNSET
        if not isinstance(self.supported_regions, Unset):
            supported_regions = []
            for supported_regions_item_data in self.supported_regions:
                supported_regions_item = supported_regions_item_data.value

                supported_regions.append(supported_regions_item)




        enable_sso_oidc = self.enable_sso_oidc
        inactivity_logout_enabled = self.inactivity_logout_enabled
        sms_opt_in_enabled = self.sms_opt_in_enabled
        inactivity_timeout = self.inactivity_timeout
        allow_custom_email_configuration = self.allow_custom_email_configuration
        portal_base_url = self.portal_base_url
        ingestion_enabled = self.ingestion_enabled
        timescale_enabled = self.timescale_enabled.isoformat() if self.timescale_enabled else None

        clickhouse_enabled = self.clickhouse_enabled.isoformat() if self.clickhouse_enabled else None

        clickhouse_query_enabled = self.clickhouse_query_enabled
        drop_experimental_query_data = self.drop_experimental_query_data
        event_queries_enabled = self.event_queries_enabled
        snowflake_row_level_security_enabled = self.snowflake_row_level_security_enabled
        clickhouse_analytics_enabled = self.clickhouse_analytics_enabled
        cached_events_enabled = self.cached_events_enabled
        user_tag_settings_enabled = self.user_tag_settings_enabled
        bulk_provisioning_enabled = self.bulk_provisioning_enabled
        device_configuration_templates_enabled = self.device_configuration_templates_enabled
        observability_v1_enabled = self.observability_v1_enabled
        analytics_v1_enabled = self.analytics_v1_enabled
        custom_roles_enabled = self.custom_roles_enabled
        mixed_module_mode_enabled = self.mixed_module_mode_enabled
        google_storage_export_enabled = self.google_storage_export_enabled
        custom_modules_enabled = self.custom_modules_enabled
        native_scene_module_enabled = self.native_scene_module_enabled
        ai_insights_enabled = self.ai_insights_enabled
        ai_enabled = self.ai_enabled
        teleop_3_preview_button = self.teleop_3_preview_button
        use_dynamic_presence = self.use_dynamic_presence
        show_get_started_on_overview = self.show_get_started_on_overview
        sidebar_hidden_sections: Union[Unset, List[str]] = UNSET
        if not isinstance(self.sidebar_hidden_sections, Unset):
            sidebar_hidden_sections = self.sidebar_hidden_sections




        design_fleet_manager_white_listed_users = self.design_fleet_manager_white_listed_users
        design_fleet_manager_view_name = self.design_fleet_manager_view_name
        optional_help_link = self.optional_help_link
        teleop_joy_enabled = self.teleop_joy_enabled
        show_overview_filters = self.show_overview_filters
        local_mode_enabled = self.local_mode_enabled
        embed_view_enabled = self.embed_view_enabled
        investigations_enabled = self.investigations_enabled
        investigations_beta_enabled = self.investigations_beta_enabled
        v_2_custom_modules_enabled = self.v_2_custom_modules_enabled
        v_2_overview_enabled = self.v_2_overview_enabled
        sidebar_v2_enabled = self.sidebar_v2_enabled
        alarm_console_enabled = self.alarm_console_enabled
        multiple_primary_teleop_enabled = self.multiple_primary_teleop_enabled
        ros_2_streams_enabled = self.ros_2_streams_enabled
        commands_module_enabled = self.commands_module_enabled
        theme_customizer_enabled = self.theme_customizer_enabled
        id = self.id
        created_at: Union[Unset, str] = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Union[Unset, str] = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()


        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "plan": plan,
            "name": name,
            "industry": industry,
            "website": website,
            "addressLine1": address_line_1,
            "addressLine2": address_line_2,
            "city": city,
            "state": state,
            "postalCode": postal_code,
            "country": country,
            "addonBillingPeriod": addon_billing_period,
            "invoiceBillingPeriod": invoice_billing_period,
            "termsModalV2Enabled": terms_modal_v2_enabled,
            "themes": themes,
            "trialPeriodEnd": trial_period_end,
            "chargebeeId": chargebee_id,
            "defaultGroupCategory": default_group_category,
            "externalTwilioConfig": external_twilio_config,
            "totangoId": totango_id,
            "hubspotId": hubspot_id,
            "snowflakeWarehouseName": snowflake_warehouse_name,
            "timescaleEnabled": timescale_enabled,
            "clickhouseEnabled": clickhouse_enabled,
        })
        if description is not UNSET:
            field_dict["description"] = description
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if pagerduty_info is not UNSET:
            field_dict["pagerdutyInfo"] = pagerduty_info
        if teleop_high_ping_reconnect_behaviors is not UNSET:
            field_dict["teleopHighPingReconnectBehaviors"] = teleop_high_ping_reconnect_behaviors
        if slack_info is not UNSET:
            field_dict["slackInfo"] = slack_info
        if google_info is not UNSET:
            field_dict["googleInfo"] = google_info
        if webhooks_info is not UNSET:
            field_dict["webhooksInfo"] = webhooks_info
        if aws_info is not UNSET:
            field_dict["awsInfo"] = aws_info
        if google_storage_info is not UNSET:
            field_dict["googleStorageInfo"] = google_storage_info
        if stripe_info is not UNSET:
            field_dict["stripeInfo"] = stripe_info
        if rtc_info is not UNSET:
            field_dict["rtcInfo"] = rtc_info
        if teleop_configuration is not UNSET:
            field_dict["teleopConfiguration"] = teleop_configuration
        if data_export_enabled is not UNSET:
            field_dict["dataExportEnabled"] = data_export_enabled
        if advanced_configuration_enabled is not UNSET:
            field_dict["advancedConfigurationEnabled"] = advanced_configuration_enabled
        if customer_portal_enabled is not UNSET:
            field_dict["customerPortalEnabled"] = customer_portal_enabled
        if stripe_billing_enabled is not UNSET:
            field_dict["stripeBillingEnabled"] = stripe_billing_enabled
        if stripe_subscription_enabled is not UNSET:
            field_dict["stripeSubscriptionEnabled"] = stripe_subscription_enabled
        if mission_planning_enabled is not UNSET:
            field_dict["missionPlanningEnabled"] = mission_planning_enabled
        if billing_info is not UNSET:
            field_dict["billingInfo"] = billing_info
        if s_3_export_enabled is not UNSET:
            field_dict["s3ExportEnabled"] = s_3_export_enabled
        if blob_data_enabled is not UNSET:
            field_dict["blobDataEnabled"] = blob_data_enabled
        if white_label_enabled is not UNSET:
            field_dict["whiteLabelEnabled"] = white_label_enabled
        if viewer_3_d_enabled is not UNSET:
            field_dict["viewer3dEnabled"] = viewer_3_d_enabled
        if adapters_enabled is not UNSET:
            field_dict["adaptersEnabled"] = adapters_enabled
        if white_label_css is not UNSET:
            field_dict["whiteLabelCSS"] = white_label_css
        if demo_mode_enabled is not UNSET:
            field_dict["demoModeEnabled"] = demo_mode_enabled
        if teleop_share_enabled is not UNSET:
            field_dict["teleopShareEnabled"] = teleop_share_enabled
        if bill_estimate_enabled is not UNSET:
            field_dict["billEstimateEnabled"] = bill_estimate_enabled
        if data_retention_enabled is not UNSET:
            field_dict["dataRetentionEnabled"] = data_retention_enabled
        if days_data_retained is not UNSET:
            field_dict["daysDataRetained"] = days_data_retained
        if max_chunk_request_limit is not UNSET:
            field_dict["maxChunkRequestLimit"] = max_chunk_request_limit
        if limit_metadatas is not UNSET:
            field_dict["limitMetadatas"] = limit_metadatas
        if online_sensitivity is not UNSET:
            field_dict["onlineSensitivity"] = online_sensitivity
        if support_enabled is not UNSET:
            field_dict["supportEnabled"] = support_enabled
        if support_tier is not UNSET:
            field_dict["supportTier"] = support_tier
        if external_id is not UNSET:
            field_dict["externalId"] = external_id
        if custom_tos is not UNSET:
            field_dict["customTos"] = custom_tos
        if teleop_enabled is not UNSET:
            field_dict["teleopEnabled"] = teleop_enabled
        if observability_enabled is not UNSET:
            field_dict["observabilityEnabled"] = observability_enabled
        if share_enabled is not UNSET:
            field_dict["shareEnabled"] = share_enabled
        if annotations_enabled is not UNSET:
            field_dict["annotationsEnabled"] = annotations_enabled
        if diagnostics_enabled is not UNSET:
            field_dict["diagnosticsEnabled"] = diagnostics_enabled
        if ssh_enabled is not UNSET:
            field_dict["sshEnabled"] = ssh_enabled
        if spot_enabled is not UNSET:
            field_dict["spotEnabled"] = spot_enabled
        if file_storage_enabled is not UNSET:
            field_dict["fileStorageEnabled"] = file_storage_enabled
        if role_viewer_enabled is not UNSET:
            field_dict["roleViewerEnabled"] = role_viewer_enabled
        if teams_enabled is not UNSET:
            field_dict["teamsEnabled"] = teams_enabled
        if schedules_enabled is not UNSET:
            field_dict["schedulesEnabled"] = schedules_enabled
        if beta_ui is not UNSET:
            field_dict["betaUI"] = beta_ui
        if realtime_v2_enabled is not UNSET:
            field_dict["realtimeV2Enabled"] = realtime_v2_enabled
        if paging_enabled is not UNSET:
            field_dict["pagingEnabled"] = paging_enabled
        if stateful_events_enabled is not UNSET:
            field_dict["statefulEventsEnabled"] = stateful_events_enabled
        if billing_enabled is not UNSET:
            field_dict["billingEnabled"] = billing_enabled
        if sms_followers_enabled is not UNSET:
            field_dict["smsFollowersEnabled"] = sms_followers_enabled
        if event_action_interval_enabled is not UNSET:
            field_dict["eventActionIntervalEnabled"] = event_action_interval_enabled
        if task_summaries_enabled is not UNSET:
            field_dict["taskSummariesEnabled"] = task_summaries_enabled
        if default_device_config is not UNSET:
            field_dict["defaultDeviceConfig"] = default_device_config
        if default_stream_throttle_hz is not UNSET:
            field_dict["defaultStreamThrottleHz"] = default_stream_throttle_hz
        if outage_banner_enabled is not UNSET:
            field_dict["outageBannerEnabled"] = outage_banner_enabled
        if new_header_enabled is not UNSET:
            field_dict["newHeaderEnabled"] = new_header_enabled
        if explorations_enabled is not UNSET:
            field_dict["explorationsEnabled"] = explorations_enabled
        if customer_success_ai_enabled is not UNSET:
            field_dict["customerSuccessAIEnabled"] = customer_success_ai_enabled
        if custom_analytics_enabled is not UNSET:
            field_dict["customAnalyticsEnabled"] = custom_analytics_enabled
        if fleet_analytics_enabled is not UNSET:
            field_dict["fleetAnalyticsEnabled"] = fleet_analytics_enabled
        if navigator_enabled is not UNSET:
            field_dict["navigatorEnabled"] = navigator_enabled
        if list_view_enabled is not UNSET:
            field_dict["listViewEnabled"] = list_view_enabled
        if map_view_enabled is not UNSET:
            field_dict["mapViewEnabled"] = map_view_enabled
        if node_graph_page_enabled is not UNSET:
            field_dict["nodeGraphPageEnabled"] = node_graph_page_enabled
        if flags is not UNSET:
            field_dict["flags"] = flags
        if overview_settings is not UNSET:
            field_dict["overviewSettings"] = overview_settings
        if snowflake_schema_name is not UNSET:
            field_dict["snowflakeSchemaName"] = snowflake_schema_name
        if supported_regions is not UNSET:
            field_dict["supportedRegions"] = supported_regions
        if enable_sso_oidc is not UNSET:
            field_dict["enableSsoOidc"] = enable_sso_oidc
        if inactivity_logout_enabled is not UNSET:
            field_dict["inactivityLogoutEnabled"] = inactivity_logout_enabled
        if sms_opt_in_enabled is not UNSET:
            field_dict["smsOptInEnabled"] = sms_opt_in_enabled
        if inactivity_timeout is not UNSET:
            field_dict["inactivityTimeout"] = inactivity_timeout
        if allow_custom_email_configuration is not UNSET:
            field_dict["allowCustomEmailConfiguration"] = allow_custom_email_configuration
        if portal_base_url is not UNSET:
            field_dict["portalBaseUrl"] = portal_base_url
        if ingestion_enabled is not UNSET:
            field_dict["ingestionEnabled"] = ingestion_enabled
        if clickhouse_query_enabled is not UNSET:
            field_dict["clickhouseQueryEnabled"] = clickhouse_query_enabled
        if drop_experimental_query_data is not UNSET:
            field_dict["dropExperimentalQueryData"] = drop_experimental_query_data
        if event_queries_enabled is not UNSET:
            field_dict["eventQueriesEnabled"] = event_queries_enabled
        if snowflake_row_level_security_enabled is not UNSET:
            field_dict["snowflakeRowLevelSecurityEnabled"] = snowflake_row_level_security_enabled
        if clickhouse_analytics_enabled is not UNSET:
            field_dict["clickhouseAnalyticsEnabled"] = clickhouse_analytics_enabled
        if cached_events_enabled is not UNSET:
            field_dict["cachedEventsEnabled"] = cached_events_enabled
        if user_tag_settings_enabled is not UNSET:
            field_dict["userTagSettingsEnabled"] = user_tag_settings_enabled
        if bulk_provisioning_enabled is not UNSET:
            field_dict["bulkProvisioningEnabled"] = bulk_provisioning_enabled
        if device_configuration_templates_enabled is not UNSET:
            field_dict["deviceConfigurationTemplatesEnabled"] = device_configuration_templates_enabled
        if observability_v1_enabled is not UNSET:
            field_dict["observabilityV1Enabled"] = observability_v1_enabled
        if analytics_v1_enabled is not UNSET:
            field_dict["analyticsV1Enabled"] = analytics_v1_enabled
        if custom_roles_enabled is not UNSET:
            field_dict["customRolesEnabled"] = custom_roles_enabled
        if mixed_module_mode_enabled is not UNSET:
            field_dict["mixedModuleModeEnabled"] = mixed_module_mode_enabled
        if google_storage_export_enabled is not UNSET:
            field_dict["googleStorageExportEnabled"] = google_storage_export_enabled
        if custom_modules_enabled is not UNSET:
            field_dict["customModulesEnabled"] = custom_modules_enabled
        if native_scene_module_enabled is not UNSET:
            field_dict["nativeSceneModuleEnabled"] = native_scene_module_enabled
        if ai_insights_enabled is not UNSET:
            field_dict["aiInsightsEnabled"] = ai_insights_enabled
        if ai_enabled is not UNSET:
            field_dict["aiEnabled"] = ai_enabled
        if teleop_3_preview_button is not UNSET:
            field_dict["teleop3PreviewButton"] = teleop_3_preview_button
        if use_dynamic_presence is not UNSET:
            field_dict["useDynamicPresence"] = use_dynamic_presence
        if show_get_started_on_overview is not UNSET:
            field_dict["showGetStartedOnOverview"] = show_get_started_on_overview
        if sidebar_hidden_sections is not UNSET:
            field_dict["sidebarHiddenSections"] = sidebar_hidden_sections
        if design_fleet_manager_white_listed_users is not UNSET:
            field_dict["designFleetManagerWhiteListedUsers"] = design_fleet_manager_white_listed_users
        if design_fleet_manager_view_name is not UNSET:
            field_dict["designFleetManagerViewName"] = design_fleet_manager_view_name
        if optional_help_link is not UNSET:
            field_dict["optionalHelpLink"] = optional_help_link
        if teleop_joy_enabled is not UNSET:
            field_dict["teleopJoyEnabled"] = teleop_joy_enabled
        if show_overview_filters is not UNSET:
            field_dict["showOverviewFilters"] = show_overview_filters
        if local_mode_enabled is not UNSET:
            field_dict["localModeEnabled"] = local_mode_enabled
        if embed_view_enabled is not UNSET:
            field_dict["embedViewEnabled"] = embed_view_enabled
        if investigations_enabled is not UNSET:
            field_dict["investigationsEnabled"] = investigations_enabled
        if investigations_beta_enabled is not UNSET:
            field_dict["investigationsBetaEnabled"] = investigations_beta_enabled
        if v_2_custom_modules_enabled is not UNSET:
            field_dict["v2CustomModulesEnabled"] = v_2_custom_modules_enabled
        if v_2_overview_enabled is not UNSET:
            field_dict["v2OverviewEnabled"] = v_2_overview_enabled
        if sidebar_v2_enabled is not UNSET:
            field_dict["sidebarV2Enabled"] = sidebar_v2_enabled
        if alarm_console_enabled is not UNSET:
            field_dict["alarmConsoleEnabled"] = alarm_console_enabled
        if multiple_primary_teleop_enabled is not UNSET:
            field_dict["multiplePrimaryTeleopEnabled"] = multiple_primary_teleop_enabled
        if ros_2_streams_enabled is not UNSET:
            field_dict["ros2StreamsEnabled"] = ros_2_streams_enabled
        if commands_module_enabled is not UNSET:
            field_dict["commandsModuleEnabled"] = commands_module_enabled
        if theme_customizer_enabled is not UNSET:
            field_dict["themeCustomizerEnabled"] = theme_customizer_enabled
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict



    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.aws_info import AwsInfo
        from ..models.billing_info import BillingInfo
        from ..models.device_configuration_document import \
            DeviceConfigurationDocument
        from ..models.google_info import GoogleInfo
        from ..models.google_storage_info import GoogleStorageInfo
        from ..models.overview_settings import OverviewSettings
        from ..models.pagerduty_info import PagerdutyInfo
        from ..models.rtc_info import RtcInfo
        from ..models.slack_info import SlackInfo
        from ..models.stripe_info import StripeInfo
        from ..models.teleop_high_ping_reconnect_behaviors import \
            TeleopHighPingReconnectBehaviors
        from ..models.user_teleop_configuration import UserTeleopConfiguration
        from ..models.webhooks_info import WebhooksInfo
        d = src_dict.copy()
        plan = OrganizationPlan(d.pop("plan"))




        name = d.pop("name")

        industry = d.pop("industry")

        website = d.pop("website")

        address_line_1 = d.pop("addressLine1")

        address_line_2 = d.pop("addressLine2")

        city = d.pop("city")

        state = d.pop("state")

        postal_code = d.pop("postalCode")

        country = d.pop("country")

        addon_billing_period = OrganizationAddonBillingPeriod(d.pop("addonBillingPeriod"))




        invoice_billing_period = OrganizationInvoiceBillingPeriod(d.pop("invoiceBillingPeriod"))




        terms_modal_v2_enabled = d.pop("termsModalV2Enabled")

        themes = cast(List[Any], d.pop("themes"))


        description = d.pop("description", UNSET)

        enabled = d.pop("enabled", UNSET)

        _pagerduty_info = d.pop("pagerdutyInfo", UNSET)
        pagerduty_info: Union[Unset, PagerdutyInfo]
        if isinstance(_pagerduty_info,  Unset):
            pagerduty_info = UNSET
        else:
            pagerduty_info = PagerdutyInfo.from_dict(_pagerduty_info)




        _teleop_high_ping_reconnect_behaviors = d.pop("teleopHighPingReconnectBehaviors", UNSET)
        teleop_high_ping_reconnect_behaviors: Union[Unset, TeleopHighPingReconnectBehaviors]
        if isinstance(_teleop_high_ping_reconnect_behaviors,  Unset):
            teleop_high_ping_reconnect_behaviors = UNSET
        else:
            teleop_high_ping_reconnect_behaviors = TeleopHighPingReconnectBehaviors.from_dict(_teleop_high_ping_reconnect_behaviors)




        _slack_info = d.pop("slackInfo", UNSET)
        slack_info: Union[Unset, SlackInfo]
        if isinstance(_slack_info,  Unset):
            slack_info = UNSET
        else:
            slack_info = SlackInfo.from_dict(_slack_info)




        _google_info = d.pop("googleInfo", UNSET)
        google_info: Union[Unset, GoogleInfo]
        if isinstance(_google_info,  Unset):
            google_info = UNSET
        else:
            google_info = GoogleInfo.from_dict(_google_info)




        _webhooks_info = d.pop("webhooksInfo", UNSET)
        webhooks_info: Union[Unset, WebhooksInfo]
        if isinstance(_webhooks_info,  Unset):
            webhooks_info = UNSET
        else:
            webhooks_info = WebhooksInfo.from_dict(_webhooks_info)




        _aws_info = d.pop("awsInfo", UNSET)
        aws_info: Union[Unset, AwsInfo]
        if isinstance(_aws_info,  Unset):
            aws_info = UNSET
        else:
            aws_info = AwsInfo.from_dict(_aws_info)




        _google_storage_info = d.pop("googleStorageInfo", UNSET)
        google_storage_info: Union[Unset, GoogleStorageInfo]
        if isinstance(_google_storage_info,  Unset):
            google_storage_info = UNSET
        else:
            google_storage_info = GoogleStorageInfo.from_dict(_google_storage_info)




        _stripe_info = d.pop("stripeInfo", UNSET)
        stripe_info: Union[Unset, StripeInfo]
        if isinstance(_stripe_info,  Unset):
            stripe_info = UNSET
        else:
            stripe_info = StripeInfo.from_dict(_stripe_info)




        _rtc_info = d.pop("rtcInfo", UNSET)
        rtc_info: Union[Unset, RtcInfo]
        if isinstance(_rtc_info,  Unset):
            rtc_info = UNSET
        else:
            rtc_info = RtcInfo.from_dict(_rtc_info)




        _teleop_configuration = d.pop("teleopConfiguration", UNSET)
        teleop_configuration: Union[Unset, UserTeleopConfiguration]
        if isinstance(_teleop_configuration,  Unset):
            teleop_configuration = UNSET
        else:
            teleop_configuration = UserTeleopConfiguration.from_dict(_teleop_configuration)




        _data_export_enabled = d.pop("dataExportEnabled", UNSET)
        data_export_enabled: Union[Unset, None, datetime.datetime]
        if _data_export_enabled is None:
            data_export_enabled = None
        elif isinstance(_data_export_enabled,  Unset):
            data_export_enabled = UNSET
        else:
            data_export_enabled = isoparse(_data_export_enabled)




        _advanced_configuration_enabled = d.pop("advancedConfigurationEnabled", UNSET)
        advanced_configuration_enabled: Union[Unset, None, datetime.datetime]
        if _advanced_configuration_enabled is None:
            advanced_configuration_enabled = None
        elif isinstance(_advanced_configuration_enabled,  Unset):
            advanced_configuration_enabled = UNSET
        else:
            advanced_configuration_enabled = isoparse(_advanced_configuration_enabled)




        _customer_portal_enabled = d.pop("customerPortalEnabled", UNSET)
        customer_portal_enabled: Union[Unset, None, datetime.datetime]
        if _customer_portal_enabled is None:
            customer_portal_enabled = None
        elif isinstance(_customer_portal_enabled,  Unset):
            customer_portal_enabled = UNSET
        else:
            customer_portal_enabled = isoparse(_customer_portal_enabled)




        stripe_billing_enabled = d.pop("stripeBillingEnabled", UNSET)

        stripe_subscription_enabled = d.pop("stripeSubscriptionEnabled", UNSET)

        mission_planning_enabled = d.pop("missionPlanningEnabled", UNSET)

        _billing_info = d.pop("billingInfo", UNSET)
        billing_info: Union[Unset, BillingInfo]
        if isinstance(_billing_info,  Unset):
            billing_info = UNSET
        else:
            billing_info = BillingInfo.from_dict(_billing_info)




        s_3_export_enabled = d.pop("s3ExportEnabled", UNSET)

        blob_data_enabled = d.pop("blobDataEnabled", UNSET)

        white_label_enabled = d.pop("whiteLabelEnabled", UNSET)

        viewer_3_d_enabled = d.pop("viewer3dEnabled", UNSET)

        adapters_enabled = d.pop("adaptersEnabled", UNSET)

        white_label_css = d.pop("whiteLabelCSS", UNSET)

        demo_mode_enabled = d.pop("demoModeEnabled", UNSET)

        teleop_share_enabled = d.pop("teleopShareEnabled", UNSET)

        bill_estimate_enabled = d.pop("billEstimateEnabled", UNSET)

        _data_retention_enabled = d.pop("dataRetentionEnabled", UNSET)
        data_retention_enabled: Union[Unset, None, datetime.datetime]
        if _data_retention_enabled is None:
            data_retention_enabled = None
        elif isinstance(_data_retention_enabled,  Unset):
            data_retention_enabled = UNSET
        else:
            data_retention_enabled = isoparse(_data_retention_enabled)




        days_data_retained = d.pop("daysDataRetained", UNSET)

        max_chunk_request_limit = d.pop("maxChunkRequestLimit", UNSET)

        limit_metadatas = d.pop("limitMetadatas", UNSET)

        online_sensitivity = d.pop("onlineSensitivity", UNSET)

        _support_enabled = d.pop("supportEnabled", UNSET)
        support_enabled: Union[Unset, None, datetime.datetime]
        if _support_enabled is None:
            support_enabled = None
        elif isinstance(_support_enabled,  Unset):
            support_enabled = UNSET
        else:
            support_enabled = isoparse(_support_enabled)




        _support_tier = d.pop("supportTier", UNSET)
        support_tier: Union[Unset, OrganizationSupportTier]
        if isinstance(_support_tier,  Unset):
            support_tier = UNSET
        else:
            support_tier = OrganizationSupportTier(_support_tier)




        _trial_period_end = d.pop("trialPeriodEnd")
        trial_period_end: Optional[datetime.datetime]
        if _trial_period_end is None:
            trial_period_end = None
        else:
            trial_period_end = isoparse(_trial_period_end)




        external_id = d.pop("externalId", UNSET)

        chargebee_id = d.pop("chargebeeId")

        default_group_category = d.pop("defaultGroupCategory")

        external_twilio_config = d.pop("externalTwilioConfig")

        totango_id = d.pop("totangoId")

        hubspot_id = d.pop("hubspotId")

        custom_tos = d.pop("customTos", UNSET)

        _teleop_enabled = d.pop("teleopEnabled", UNSET)
        teleop_enabled: Union[Unset, None, datetime.datetime]
        if _teleop_enabled is None:
            teleop_enabled = None
        elif isinstance(_teleop_enabled,  Unset):
            teleop_enabled = UNSET
        else:
            teleop_enabled = isoparse(_teleop_enabled)




        _observability_enabled = d.pop("observabilityEnabled", UNSET)
        observability_enabled: Union[Unset, None, datetime.datetime]
        if _observability_enabled is None:
            observability_enabled = None
        elif isinstance(_observability_enabled,  Unset):
            observability_enabled = UNSET
        else:
            observability_enabled = isoparse(_observability_enabled)




        _share_enabled = d.pop("shareEnabled", UNSET)
        share_enabled: Union[Unset, None, datetime.datetime]
        if _share_enabled is None:
            share_enabled = None
        elif isinstance(_share_enabled,  Unset):
            share_enabled = UNSET
        else:
            share_enabled = isoparse(_share_enabled)




        _annotations_enabled = d.pop("annotationsEnabled", UNSET)
        annotations_enabled: Union[Unset, None, datetime.datetime]
        if _annotations_enabled is None:
            annotations_enabled = None
        elif isinstance(_annotations_enabled,  Unset):
            annotations_enabled = UNSET
        else:
            annotations_enabled = isoparse(_annotations_enabled)




        _diagnostics_enabled = d.pop("diagnosticsEnabled", UNSET)
        diagnostics_enabled: Union[Unset, None, datetime.datetime]
        if _diagnostics_enabled is None:
            diagnostics_enabled = None
        elif isinstance(_diagnostics_enabled,  Unset):
            diagnostics_enabled = UNSET
        else:
            diagnostics_enabled = isoparse(_diagnostics_enabled)




        _ssh_enabled = d.pop("sshEnabled", UNSET)
        ssh_enabled: Union[Unset, None, datetime.datetime]
        if _ssh_enabled is None:
            ssh_enabled = None
        elif isinstance(_ssh_enabled,  Unset):
            ssh_enabled = UNSET
        else:
            ssh_enabled = isoparse(_ssh_enabled)




        _spot_enabled = d.pop("spotEnabled", UNSET)
        spot_enabled: Union[Unset, None, datetime.datetime]
        if _spot_enabled is None:
            spot_enabled = None
        elif isinstance(_spot_enabled,  Unset):
            spot_enabled = UNSET
        else:
            spot_enabled = isoparse(_spot_enabled)




        file_storage_enabled = d.pop("fileStorageEnabled", UNSET)

        role_viewer_enabled = d.pop("roleViewerEnabled", UNSET)

        teams_enabled = d.pop("teamsEnabled", UNSET)

        schedules_enabled = d.pop("schedulesEnabled", UNSET)

        beta_ui = d.pop("betaUI", UNSET)

        realtime_v2_enabled = d.pop("realtimeV2Enabled", UNSET)

        paging_enabled = d.pop("pagingEnabled", UNSET)

        stateful_events_enabled = d.pop("statefulEventsEnabled", UNSET)

        billing_enabled = d.pop("billingEnabled", UNSET)

        sms_followers_enabled = d.pop("smsFollowersEnabled", UNSET)

        event_action_interval_enabled = d.pop("eventActionIntervalEnabled", UNSET)

        task_summaries_enabled = d.pop("taskSummariesEnabled", UNSET)

        _default_device_config = d.pop("defaultDeviceConfig", UNSET)
        default_device_config: Union[Unset, DeviceConfigurationDocument]
        if isinstance(_default_device_config,  Unset):
            default_device_config = UNSET
        else:
            default_device_config = DeviceConfigurationDocument.from_dict(_default_device_config)




        default_stream_throttle_hz = d.pop("defaultStreamThrottleHz", UNSET)

        outage_banner_enabled = d.pop("outageBannerEnabled", UNSET)

        new_header_enabled = d.pop("newHeaderEnabled", UNSET)

        explorations_enabled = d.pop("explorationsEnabled", UNSET)

        customer_success_ai_enabled = d.pop("customerSuccessAIEnabled", UNSET)

        custom_analytics_enabled = d.pop("customAnalyticsEnabled", UNSET)

        fleet_analytics_enabled = d.pop("fleetAnalyticsEnabled", UNSET)

        navigator_enabled = d.pop("navigatorEnabled", UNSET)

        list_view_enabled = d.pop("listViewEnabled", UNSET)

        map_view_enabled = d.pop("mapViewEnabled", UNSET)

        node_graph_page_enabled = d.pop("nodeGraphPageEnabled", UNSET)

        flags = []
        _flags = d.pop("flags", UNSET)
        for flags_item_data in (_flags or []):
            flags_item = OrganizationFlagsItem(flags_item_data)



            flags.append(flags_item)


        _overview_settings = d.pop("overviewSettings", UNSET)
        overview_settings: Union[Unset, OverviewSettings]
        if isinstance(_overview_settings,  Unset):
            overview_settings = UNSET
        else:
            overview_settings = OverviewSettings.from_dict(_overview_settings)




        snowflake_warehouse_name = d.pop("snowflakeWarehouseName")

        snowflake_schema_name = d.pop("snowflakeSchemaName", UNSET)

        supported_regions = []
        _supported_regions = d.pop("supportedRegions", UNSET)
        for supported_regions_item_data in (_supported_regions or []):
            supported_regions_item = OrganizationSupportedRegionsItem(supported_regions_item_data)



            supported_regions.append(supported_regions_item)


        enable_sso_oidc = d.pop("enableSsoOidc", UNSET)

        inactivity_logout_enabled = d.pop("inactivityLogoutEnabled", UNSET)

        sms_opt_in_enabled = d.pop("smsOptInEnabled", UNSET)

        inactivity_timeout = d.pop("inactivityTimeout", UNSET)

        allow_custom_email_configuration = d.pop("allowCustomEmailConfiguration", UNSET)

        portal_base_url = d.pop("portalBaseUrl", UNSET)

        ingestion_enabled = d.pop("ingestionEnabled", UNSET)

        _timescale_enabled = d.pop("timescaleEnabled")
        timescale_enabled: Optional[datetime.datetime]
        if _timescale_enabled is None:
            timescale_enabled = None
        else:
            timescale_enabled = isoparse(_timescale_enabled)




        _clickhouse_enabled = d.pop("clickhouseEnabled")
        clickhouse_enabled: Optional[datetime.datetime]
        if _clickhouse_enabled is None:
            clickhouse_enabled = None
        else:
            clickhouse_enabled = isoparse(_clickhouse_enabled)




        clickhouse_query_enabled = d.pop("clickhouseQueryEnabled", UNSET)

        drop_experimental_query_data = d.pop("dropExperimentalQueryData", UNSET)

        event_queries_enabled = d.pop("eventQueriesEnabled", UNSET)

        snowflake_row_level_security_enabled = d.pop("snowflakeRowLevelSecurityEnabled", UNSET)

        clickhouse_analytics_enabled = d.pop("clickhouseAnalyticsEnabled", UNSET)

        cached_events_enabled = d.pop("cachedEventsEnabled", UNSET)

        user_tag_settings_enabled = d.pop("userTagSettingsEnabled", UNSET)

        bulk_provisioning_enabled = d.pop("bulkProvisioningEnabled", UNSET)

        device_configuration_templates_enabled = d.pop("deviceConfigurationTemplatesEnabled", UNSET)

        observability_v1_enabled = d.pop("observabilityV1Enabled", UNSET)

        analytics_v1_enabled = d.pop("analyticsV1Enabled", UNSET)

        custom_roles_enabled = d.pop("customRolesEnabled", UNSET)

        mixed_module_mode_enabled = d.pop("mixedModuleModeEnabled", UNSET)

        google_storage_export_enabled = d.pop("googleStorageExportEnabled", UNSET)

        custom_modules_enabled = d.pop("customModulesEnabled", UNSET)

        native_scene_module_enabled = d.pop("nativeSceneModuleEnabled", UNSET)

        ai_insights_enabled = d.pop("aiInsightsEnabled", UNSET)

        ai_enabled = d.pop("aiEnabled", UNSET)

        teleop_3_preview_button = d.pop("teleop3PreviewButton", UNSET)

        use_dynamic_presence = d.pop("useDynamicPresence", UNSET)

        show_get_started_on_overview = d.pop("showGetStartedOnOverview", UNSET)

        sidebar_hidden_sections = cast(List[str], d.pop("sidebarHiddenSections", UNSET))


        design_fleet_manager_white_listed_users = d.pop("designFleetManagerWhiteListedUsers", UNSET)

        design_fleet_manager_view_name = d.pop("designFleetManagerViewName", UNSET)

        optional_help_link = d.pop("optionalHelpLink", UNSET)

        teleop_joy_enabled = d.pop("teleopJoyEnabled", UNSET)

        show_overview_filters = d.pop("showOverviewFilters", UNSET)

        local_mode_enabled = d.pop("localModeEnabled", UNSET)

        embed_view_enabled = d.pop("embedViewEnabled", UNSET)

        investigations_enabled = d.pop("investigationsEnabled", UNSET)

        investigations_beta_enabled = d.pop("investigationsBetaEnabled", UNSET)

        v_2_custom_modules_enabled = d.pop("v2CustomModulesEnabled", UNSET)

        v_2_overview_enabled = d.pop("v2OverviewEnabled", UNSET)

        sidebar_v2_enabled = d.pop("sidebarV2Enabled", UNSET)

        alarm_console_enabled = d.pop("alarmConsoleEnabled", UNSET)

        multiple_primary_teleop_enabled = d.pop("multiplePrimaryTeleopEnabled", UNSET)

        ros_2_streams_enabled = d.pop("ros2StreamsEnabled", UNSET)

        commands_module_enabled = d.pop("commandsModuleEnabled", UNSET)

        theme_customizer_enabled = d.pop("themeCustomizerEnabled", UNSET)

        id = d.pop("id", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: Union[Unset, datetime.datetime]
        if isinstance(_created_at,  Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)




        _updated_at = d.pop("updatedAt", UNSET)
        updated_at: Union[Unset, datetime.datetime]
        if isinstance(_updated_at,  Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)




        organization = cls(
            plan=plan,
            name=name,
            industry=industry,
            website=website,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            addon_billing_period=addon_billing_period,
            invoice_billing_period=invoice_billing_period,
            terms_modal_v2_enabled=terms_modal_v2_enabled,
            themes=themes,
            description=description,
            enabled=enabled,
            pagerduty_info=pagerduty_info,
            teleop_high_ping_reconnect_behaviors=teleop_high_ping_reconnect_behaviors,
            slack_info=slack_info,
            google_info=google_info,
            webhooks_info=webhooks_info,
            aws_info=aws_info,
            google_storage_info=google_storage_info,
            stripe_info=stripe_info,
            rtc_info=rtc_info,
            teleop_configuration=teleop_configuration,
            data_export_enabled=data_export_enabled,
            advanced_configuration_enabled=advanced_configuration_enabled,
            customer_portal_enabled=customer_portal_enabled,
            stripe_billing_enabled=stripe_billing_enabled,
            stripe_subscription_enabled=stripe_subscription_enabled,
            mission_planning_enabled=mission_planning_enabled,
            billing_info=billing_info,
            s_3_export_enabled=s_3_export_enabled,
            blob_data_enabled=blob_data_enabled,
            white_label_enabled=white_label_enabled,
            viewer_3_d_enabled=viewer_3_d_enabled,
            adapters_enabled=adapters_enabled,
            white_label_css=white_label_css,
            demo_mode_enabled=demo_mode_enabled,
            teleop_share_enabled=teleop_share_enabled,
            bill_estimate_enabled=bill_estimate_enabled,
            data_retention_enabled=data_retention_enabled,
            days_data_retained=days_data_retained,
            max_chunk_request_limit=max_chunk_request_limit,
            limit_metadatas=limit_metadatas,
            online_sensitivity=online_sensitivity,
            support_enabled=support_enabled,
            support_tier=support_tier,
            trial_period_end=trial_period_end,
            external_id=external_id,
            chargebee_id=chargebee_id,
            default_group_category=default_group_category,
            external_twilio_config=external_twilio_config,
            totango_id=totango_id,
            hubspot_id=hubspot_id,
            custom_tos=custom_tos,
            teleop_enabled=teleop_enabled,
            observability_enabled=observability_enabled,
            share_enabled=share_enabled,
            annotations_enabled=annotations_enabled,
            diagnostics_enabled=diagnostics_enabled,
            ssh_enabled=ssh_enabled,
            spot_enabled=spot_enabled,
            file_storage_enabled=file_storage_enabled,
            role_viewer_enabled=role_viewer_enabled,
            teams_enabled=teams_enabled,
            schedules_enabled=schedules_enabled,
            beta_ui=beta_ui,
            realtime_v2_enabled=realtime_v2_enabled,
            paging_enabled=paging_enabled,
            stateful_events_enabled=stateful_events_enabled,
            billing_enabled=billing_enabled,
            sms_followers_enabled=sms_followers_enabled,
            event_action_interval_enabled=event_action_interval_enabled,
            task_summaries_enabled=task_summaries_enabled,
            default_device_config=default_device_config,
            default_stream_throttle_hz=default_stream_throttle_hz,
            outage_banner_enabled=outage_banner_enabled,
            new_header_enabled=new_header_enabled,
            explorations_enabled=explorations_enabled,
            customer_success_ai_enabled=customer_success_ai_enabled,
            custom_analytics_enabled=custom_analytics_enabled,
            fleet_analytics_enabled=fleet_analytics_enabled,
            navigator_enabled=navigator_enabled,
            list_view_enabled=list_view_enabled,
            map_view_enabled=map_view_enabled,
            node_graph_page_enabled=node_graph_page_enabled,
            flags=flags,
            overview_settings=overview_settings,
            snowflake_warehouse_name=snowflake_warehouse_name,
            snowflake_schema_name=snowflake_schema_name,
            supported_regions=supported_regions,
            enable_sso_oidc=enable_sso_oidc,
            inactivity_logout_enabled=inactivity_logout_enabled,
            sms_opt_in_enabled=sms_opt_in_enabled,
            inactivity_timeout=inactivity_timeout,
            allow_custom_email_configuration=allow_custom_email_configuration,
            portal_base_url=portal_base_url,
            ingestion_enabled=ingestion_enabled,
            timescale_enabled=timescale_enabled,
            clickhouse_enabled=clickhouse_enabled,
            clickhouse_query_enabled=clickhouse_query_enabled,
            drop_experimental_query_data=drop_experimental_query_data,
            event_queries_enabled=event_queries_enabled,
            snowflake_row_level_security_enabled=snowflake_row_level_security_enabled,
            clickhouse_analytics_enabled=clickhouse_analytics_enabled,
            cached_events_enabled=cached_events_enabled,
            user_tag_settings_enabled=user_tag_settings_enabled,
            bulk_provisioning_enabled=bulk_provisioning_enabled,
            device_configuration_templates_enabled=device_configuration_templates_enabled,
            observability_v1_enabled=observability_v1_enabled,
            analytics_v1_enabled=analytics_v1_enabled,
            custom_roles_enabled=custom_roles_enabled,
            mixed_module_mode_enabled=mixed_module_mode_enabled,
            google_storage_export_enabled=google_storage_export_enabled,
            custom_modules_enabled=custom_modules_enabled,
            native_scene_module_enabled=native_scene_module_enabled,
            ai_insights_enabled=ai_insights_enabled,
            ai_enabled=ai_enabled,
            teleop_3_preview_button=teleop_3_preview_button,
            use_dynamic_presence=use_dynamic_presence,
            show_get_started_on_overview=show_get_started_on_overview,
            sidebar_hidden_sections=sidebar_hidden_sections,
            design_fleet_manager_white_listed_users=design_fleet_manager_white_listed_users,
            design_fleet_manager_view_name=design_fleet_manager_view_name,
            optional_help_link=optional_help_link,
            teleop_joy_enabled=teleop_joy_enabled,
            show_overview_filters=show_overview_filters,
            local_mode_enabled=local_mode_enabled,
            embed_view_enabled=embed_view_enabled,
            investigations_enabled=investigations_enabled,
            investigations_beta_enabled=investigations_beta_enabled,
            v_2_custom_modules_enabled=v_2_custom_modules_enabled,
            v_2_overview_enabled=v_2_overview_enabled,
            sidebar_v2_enabled=sidebar_v2_enabled,
            alarm_console_enabled=alarm_console_enabled,
            multiple_primary_teleop_enabled=multiple_primary_teleop_enabled,
            ros_2_streams_enabled=ros_2_streams_enabled,
            commands_module_enabled=commands_module_enabled,
            theme_customizer_enabled=theme_customizer_enabled,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        organization.additional_properties = d
        return organization

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
