from pygeai.core.models import UsageLimit


class UsageLimitMapper:

    @classmethod
    def map_to_usage_limit(cls, data: dict) -> UsageLimit:
        return UsageLimit(
            hard_limit=data.get('hardLimit'),
            usage_limit_id=data.get('id'),
            related_entity_name=data.get('relatedEntityName'),
            remaining_usage=data.get('remainingUsage'),
            renewal_status=data.get('renewalStatus'),
            soft_limit=data.get('softLimit'),
            status=data.get('status'),
            subscription_type=data.get('subscriptionType'),
            usage_unit=data.get('usageUnit'),
            used_amount=data.get('usedAmount'),
            valid_from=data.get('validFrom'),
            valid_until=data.get('validUntil'),
        )
