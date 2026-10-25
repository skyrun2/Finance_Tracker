import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClassificationRule


async def classify_transaction(
    description: str,
    amount: float,
    db: AsyncSession,
) -> Optional[str]:
    result = await db.execute(
        select(ClassificationRule)
        .where(ClassificationRule.is_active == True)
        .order_by(ClassificationRule.priority)
    )
    rules = result.scalars().all()

    for rule in rules:
        match = False
        if rule.rule_type == "CONTAINS":
            match = rule.pattern.lower() in description.lower()
        elif rule.rule_type == "REGEX":
            match = bool(re.search(rule.pattern, description, re.IGNORECASE))
        elif rule.rule_type == "EQUALS":
            match = description.lower() == rule.pattern.lower()
        elif rule.rule_type == "STARTS_WITH":
            match = description.lower().startswith(rule.pattern.lower())
        elif rule.rule_type == "ENDS_WITH":
            match = description.lower().endswith(rule.pattern.lower())

        if match:
            return rule.category_id

    return None
