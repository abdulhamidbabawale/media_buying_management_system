from google.ads.googleads.client import GoogleAdsClient
from google.protobuf.field_mask_pb2 import FieldMask
from google.ads.googleads.errors import GoogleAdsException
from app.schemas.google_ads_schema import Campaign, AdGroup, Ad, Keyword, Budget, CampaignRequest
from app.db.google_ads_queries import get_user_config,save_campaign_to_db,get_campaigns_for_user, get_campaign_by_id
from typing import Dict, Any
import datetime
import uuid
import os

CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

async def get_google_ads_client(client_id: str) -> GoogleAdsClient:
    user_config =await get_user_config(client_id)
    return GoogleAdsClient.load_from_dict(
        {
            "developer_token": DEVELOPER_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": user_config["refresh_token"],
            "login_customer_id": LOGIN_CUSTOMER_ID,
            "use_proto_plus": True,
        },
        version="v21", 
    )

class CampaignService:
    def __init__(self, user_config: dict):
        # Build Google Ads client from user-specific config
        self.client = user_config

    def create_campaign(self, customer_id: str, budget_micros: int, campaign_type: str, name: str):
        try:
            # Budget
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            budget_op = self.client.get_type("CampaignBudgetOperation")
            budget = budget_op.create
            budget.name = f"{name} Budget {uuid.uuid4()}"
            budget.amount_micros = budget_micros
            budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

            budget_response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=customer_id, operations=[budget_op]
            )

            # Campaign
            campaign_service = self.client.get_service("CampaignService")
            campaign_op = self.client.get_type("CampaignOperation")
            campaign = campaign_op.create
            campaign.name = f"{name} {uuid.uuid4()}"
            campaign.advertising_channel_type = getattr(
                self.client.enums.AdvertisingChannelTypeEnum, campaign_type.upper()
            )
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
            campaign.manual_cpc = self.client.get_type("ManualCpc")
            campaign.campaign_budget = budget_response.results[0].resource_name
            campaign.network_settings.target_google_search = True
            campaign.network_settings.target_search_network = True
            campaign.network_settings.target_content_network = True
            campaign.network_settings.target_partner_search_network = False

            start_date = datetime.date.today() + datetime.timedelta(days=1)
            end_date = start_date + datetime.timedelta(weeks=4)
            campaign.start_date = start_date.strftime("%Y%m%d")
            campaign.end_date = end_date.strftime("%Y%m%d")

             # ✅ Required field for compliance
            campaign.contains_eu_political_advertising = (
               self.client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
            )

            campaign_response = campaign_service.mutate_campaigns(
                customer_id=customer_id, operations=[campaign_op]
            )

            return {"campaign_id": campaign_response.results[0].resource_name}

        except GoogleAdsException as ex:
            return {"error": str(ex)}
        

    def create_ad_group(self, customer_id: str, campaign_id: str, name: str):
         ad_group_service = self.client.get_service("AdGroupService")

         ad_group_op = self.client.get_type("AdGroupOperation")
         ad_group = ad_group_op.create
         ad_group.name = f"{name} AdGroup {uuid.uuid4()}"
         ad_group.campaign = campaign_id
         ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
         ad_group.type_ = self.client.enums.AdGroupTypeEnum.SEARCH_STANDARD
         ad_group.cpc_bid_micros = 1000000  # $1.00

         response = ad_group_service.mutate_ad_groups(
             customer_id=customer_id, operations=[ad_group_op]
         )

         return {"ad_group_id": response.results[0].resource_name}
    
    def add_keyword(self, customer_id: str, ad_group_id: str, keyword_text: str, match_type: str = "EXACT"):
         ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
     
         criterion_op = self.client.get_type("AdGroupCriterionOperation")
         criterion = criterion_op.create
         criterion.ad_group = ad_group_id
         criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
         criterion.keyword.text = keyword_text
         criterion.keyword.match_type = getattr(
             self.client.enums.KeywordMatchTypeEnum, match_type.upper()
         )
     
         response = ad_group_criterion_service.mutate_ad_group_criteria(
             customer_id=customer_id, operations=[criterion_op]
         )
     
         return {"keyword_id": response.results[0].resource_name}
    
    def create_responsive_search_ad(self, customer_id: str, ad_group_id: str, headlines: list, descriptions: list, final_url: str):
        if len(headlines) < 3:
           raise ValueError("Google Ads requires at least 3 headlines for a Responsive Search Ad")
        if len(descriptions) < 2:
           raise ValueError("Google Ads requires at least 2 descriptions for a Responsive Search Ad")
    
        ad_group_ad_service = self.client.get_service("AdGroupAdService")

        ad_op = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = ad_op.create
        ad_group_ad.ad_group = ad_group_id
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED  # safer initially

        ad = ad_group_ad.ad
        ad.final_urls.append(final_url)

        # Headlines
        for h in headlines:
            asset = self.client.get_type("AdTextAsset")
            asset.text = h
            ad.responsive_search_ad.headlines.append(asset)

        # Descriptions
        for d in descriptions:
            asset = self.client.get_type("AdTextAsset")
            asset.text = d
            ad.responsive_search_ad.descriptions.append(asset)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id, operations=[ad_op]
        )

        return {"ad_id": response.results[0].resource_name}

    def update_campaign_status(self, customer_id: str, campaign_id: str, status: str):
        """
        Update the status of a campaign.
        status can be one of: 'ENABLED', 'PAUSED', 'REMOVED'
        """
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_op = self.client.get_type("CampaignOperation")

            # Resource name must be in the form: customers/{customer_id}/campaigns/{campaign_id}
            campaign_resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"

            campaign = campaign_op.update
            campaign.resource_name = campaign_resource_name
            campaign.status = getattr(self.client.enums.CampaignStatusEnum, status.upper())

            campaign_op.update_mask.CopyFrom(
                FieldMask(paths=["status"])
            )

            response = campaign_service.mutate_campaigns(
                customer_id=customer_id, operations=[campaign_op]
            )

            return {"message": f"Campaign {campaign_id} updated to {status}", "resource_name": response.results[0].resource_name}

        except GoogleAdsException as ex:
            return {"error": str(ex)}    


class MetricsService:
    def __init__(self, user_config: dict):

        self.client = user_config

    def get_campaign_metrics(self, customer_id: str, campaign_id: str, start_date: str, end_date: str):
        """
        Fetch campaign-level metrics for a date range.
        :param customer_id: Google Ads customer ID
        :param campaign_id: Campaign resource name or ID
        :param start_date: YYYY-MM-DD
        :param end_date: YYYY-MM-DD
        """
        try:

            if not end_date:
                end_date = datetime.date.today().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

            ga_service = self.client.get_service("GoogleAdsService")

            query = f"""
                   SELECT
                       campaign.id,
                       campaign.name,
                       metrics.impressions,
                       metrics.clicks,
                       metrics.ctr,
                       metrics.average_cpc,
                       metrics.cost_micros,
                       metrics.conversions
                   FROM campaign
                   WHERE campaign.id = {campaign_id}
                     AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            """

            response = ga_service.search(customer_id=customer_id, query=query)

            results = []
            for row in response:
                results.append({
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc,
                    "cost_micros": row.metrics.cost_micros,
                    "conversions": row.metrics.conversions,
                })

            return {"metrics": results}

        except GoogleAdsException as ex:
            return {"error": str(ex)}


async def create_google_ads_campaign(req: CampaignRequest,current_client_id):
    user_config = await get_google_ads_client(current_client_id)
    user_config_from_db =await get_user_config(current_client_id)
    customer_id=user_config_from_db["customer_id"]
    service = CampaignService(user_config)

    # Step 1: Create campaign
    campaign_result = service.create_campaign(
        customer_id=customer_id,
        budget_micros=req.budget_micros,
        campaign_type=req.campaign_type,
        name=req.name,
    ) 
    if "error" in campaign_result:
        return {"error": campaign_result["error"]}

    campaign_id = campaign_result["campaign_id"]
    #just the campaign id
    campaign_id_number = campaign_id.split("/")[-1]

    # Step 2: Create ad group
    ad_group_result = service.create_ad_group(
        customer_id=customer_id,
        campaign_id=campaign_id,
        name=req.ad_group_name,
    )
    ad_group_id = ad_group_result["ad_group_id"]

    # Step 3: Add keywords
    keyword_objs = []
    for kw in req.keywords:
        keyword_result = service.add_keyword(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            keyword_text=kw,
            match_type="EXACT",
        )
        keyword_objs.append(
            Keyword(
                criterion_id=keyword_result["keyword_id"],
                keyword_text=kw,
                match_type="EXACT",
                status="ENABLED"
            )
        )

    # Step 4: Create ad
    ad_result = service.create_responsive_search_ad(
        customer_id=customer_id,
        ad_group_id=ad_group_id,
        headlines=req.headlines,
        descriptions=req.descriptions,
        final_url=req.final_url,
    )
    ad_obj = Ad(
        ad_id=ad_result["ad_id"],
        ad_type="RESPONSIVE_SEARCH_AD",
        status="PAUSED",
        headlines=req.headlines,
        descriptions=req.descriptions,
        final_urls=[req.final_url],
    )

    # Build ad group object
    ad_group_obj = AdGroup(
        ad_group_id=ad_group_id,
        ad_group_name=req.ad_group_name,
        status="ENABLED",
        cpc_bid_micros=1000000,
        ads=[ad_obj],
        keywords=keyword_objs,
    )

    # Build campaign object
    campaign_obj = Campaign(
        _id=campaign_id_number,
        client_id=current_client_id,
        google_customer_id=customer_id,
        campaign_id=campaign_id,
        campaign_name=req.name,
        status="PAUSED",
        budget=Budget(amount_micros=req.budget_micros, currency_code="USD"),
        channel=req.campaign_type.upper(),
        created_at=datetime.datetime.utcnow(),
        ad_groups=[ad_group_obj],
    )

    service.update_campaign_status(customer_id,campaign_id_number,'ENABLED')

    return {"campaign_obj": campaign_obj, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "ad_id": ad_result["ad_id"], "keywords": [kw.keyword_text for kw in keyword_objs]}

async def fetch_campaigns(client_id: str) -> list[Dict[str, Any]]:
    campaigns = await get_campaigns_for_user(client_id)
    return campaigns

async def fetch_campaign_by_id(user_id: str, campaign_id: str):
    campaign = await get_campaign_by_id(campaign_id, user_id)
    if not campaign:
        return None
    
    return campaign

