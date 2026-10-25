
import re
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, ClassificationRule


class ClassificationResult:
    def __init__(
        self,
        category_id: Optional[int] = None,
        category_name: str = "Unclassified",
        subcategory_id: Optional[int] = None,
        subcategory_name: Optional[str] = None,
        confidence: str = "automatic",
    ):
        self.category_id = category_id
        self.category_name = category_name
        self.subcategory_id = subcategory_id
        self.subcategory_name = subcategory_name
        self.confidence = confidence  # automatic, manual, rule_based


# Default keyword-based rules (in-code fallbacks)
DEFAULT_RULES: list[tuple[str, str, str]] = [
    # Food & Dining
    ("ifood", "CONTAINS", "Food"),
    ("i food", "CONTAINS", "Food"),
    ("restaurant", "CONTAINS", "Food"),
    ("pizza", "CONTAINS", "Food"),
    ("subway", "CONTAINS", "Food"),
    ("cafeteria", "CONTAINS", "Food"),
    ("bakery", "CONTAINS", "Food"),
    ("supermarket", "CONTAINS", "Food"),
    ("market", "CONTAINS", "Food"),
    ("butcher shop", "CONTAINS", "Food"),
    ("butcher shop", "CONTAINS", "Food"),
    ("street market", "CONTAINS", "Food"),
    ("large hot dog", "CONTAINS", "Food"),
    ("hamburger", "CONTAINS", "Food"),
    ("hamburger", "CONTAINS", "Food"),
    ("burger", "CONTAINS", "Food"),
    ("ifd", "CONTAINS", "Food"),
    ("sandra", "CONTAINS", "Food"),

    # Transportation   
    ("uber", "CONTAINS", "Transportation"),
    ("uber from Brazil", "CONTAINS", "Transportation"),
    ("99 Pop", "CONTAINS", "Transportation"),
    ("99 taxi", "CONTAINS", "Transportation"),
    ("99 Technology", "CONTAINS", "Transportation"),
    ("99 from Brazil", "CONTAINS", "Transportation"),
    ("taxi", "CONTAINS", "Transportation"),
    ("taxi", "CONTAINS", "Transportation"),
    ("fuel", "CONTAINS", "Transportation"),
    ("fuel", "CONTAINS", "Transportation"),
    ("gasoline", "CONTAINS", "Transportation"),
    ("ethanol", "CONTAINS", "Transportation"),
    ("toll", "CONTAINS", "Transportation"),
    ("toll", "CONTAINS", "Transportation"),
    ("parking", "CONTAINS", "Transportation"),
    ("IPVA", "CONTAINS", "Transportation"),
    ("car insurance", "CONTAINS", "Transportation"),
    ("vehicle maintenance", "CONTAINS", "Transportation"),
    ("vehicle maintenance", "CONTAINS", "Transportation"),
    ("repair shop", "CONTAINS", "Transportation"),
    ("subway", "CONTAINS", "Transportation"),
    ("gas station", "CONTAINS", "Transportation"),
    ("RioCard", "CONTAINS", "Transportation"),
    ("Mais Mobi", "CONTAINS", "Transportation"),
    ("MaisMobi", "CONTAINS", "Transportation"),

    # Entertainment & Leisure
    ("cinema", "CONTAINS", "Entertainment"),
    ("show", "CONTAINS", "Entertainment"),
    ("theater", "CONTAINS", "Entertainment"),
    ("game", "CONTAINS", "Entertainment"),
    ("travel", "CONTAINS", "Entertainment"),
    ("hotel", "CONTAINS", "Entertainment"),
    ("airline ticket", "CONTAINS", "Entertainment"),
    ("airline ticket", "CONTAINS", "Entertainment"),
    ("admission ticket", "CONTAINS", "Entertainment"),
    ("Ticketmaster", "CONTAINS", "Entertainment"),
    ("ciclube", "CONTAINS", "Entertainment"),
    ("cinema", "CONTAINS", "Entertainment"),
    ("Manga Rosa", "CONTAINS", "Entertainment"),
    ("office firm", "CONTAINS", "Entertainment"),
    ("gin", "CONTAINS", "Entertainment"),
    ("deposit", "CONTAINS", "Entertainment"),
    ("bar", "CONTAINS", "Entertainment"),
    ("pub", "CONTAINS", "Entertainment"),

    # Subscriptions
    ("subscription", "CONTAINS", "Subscriptions"),
    ("monthly fee", "CONTAINS", "Subscriptions"),
    ("recurring", "CONTAINS", "Subscriptions"),
    ("Netflix", "CONTAINS", "Subscriptions"),
    ("Prime Video", "CONTAINS", "Subscriptions"),
    ("Amazon Prime", "CONTAINS", "Subscriptions"),
    ("Spotify", "CONTAINS", "Subscriptions"),
    ("YouTube", "CONTAINS", "Subscriptions"),
    ("HBO", "CONTAINS", "Subscriptions"),
    ("Disney", "CONTAINS", "Subscriptions"),
    ("Apple TV", "CONTAINS", "Subscriptions"),
    ("Apple Music", "CONTAINS", "Subscriptions"),
    ("Wellhub", "CONTAINS", "Subscriptions"),
    ("Spotify", "CONTAINS", "Subscriptions"),
    ("responde ai", "CONTAINS", "Subscriptions"),

    # Shopping
    ("Amazon", "CONTAINS", "Shopping"),
    ("Mercado Livre", "CONTAINS", "Shopping"),
    ("Magalu", "CONTAINS", "Shopping"),
    ("Magazine Luiza", "CONTAINS", "Shopping"),
    ("Shopee", "CONTAINS", "Shopping"),
    ("Shein", "CONTAINS", "Shopping"),
    ("clothing", "CONTAINS", "Shopping"),
    ("footwear", "CONTAINS", "Shopping"),
    ("footwear", "CONTAINS", "Shopping"),
    ("electronics", "CONTAINS", "Shopping"),
    ("electronics", "CONTAINS", "Shopping"),

    # Investments
    ("CDB", "CONTAINS", "Investments"),
    ("redemption", "CONTAINS", "Investments"),
    ("investment returns", "CONTAINS", "Investments"),
    ("investment", "CONTAINS", "Investments"),
    ("investment", "CONTAINS", "Investments"),
    ("dividend", "CONTAINS", "Investments"),
]


async def classify_transaction(
    db: AsyncSession,
    description: str,
    amount: Decimal,
    transaction_type: str,
    category_hint: str | None = None,
) -> ClassificationResult:
    # 1. Use the category hint if provided
    if category_hint:
        stmt = select(Category).where(
            Category.name.ilike(f"%{category_hint}%")
        )
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()

        if category:
            return ClassificationResult(
                category_id=category.id,
                category_name=category.name,
                confidence="automatic",
            )

    # 2. Try database rules
    stmt = select(ClassificationRule, Category).join(
        Category,
        ClassificationRule.category_id == Category.id,
    )
    result = await db.execute(stmt)
    db_rules = result.all()

    for rule, cat in db_rules:
        if _matches_rule(description, rule.pattern, rule.rule_type):
            return ClassificationResult(
                category_id=cat.id,
                category_name=cat.name,
                confidence="rule_based",
            )

    # 3. Try default in-code rules
    desc_lower = description.lower()

    for pattern, rule_type, category_name in DEFAULT_RULES:
        if _matches_rule(desc_lower, pattern, rule_type):
            stmt = select(Category).where(
                Category.name == category_name
            )
            result = await db.execute(stmt)
            category = result.scalar_one_or_none()

            if category:
                return ClassificationResult(
                    category_id=category.id,
                    category_name=category.name,
                    confidence="automatic",
                )

    # 4. Fallback: any unclassified transaction -> Others
    stmt = select(Category).where(Category.name == "Others")
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if category:
        return ClassificationResult(
            category_id=category.id,
            category_name=category.name,
            confidence="automatic",
        )

    return ClassificationResult()


def _matches_rule(text: str, pattern: str, rule_type: str) -> bool:
    text_lower = text.lower()
    pattern_lower = pattern.lower()

    if rule_type == "CONTAINS":
        return pattern_lower in text_lower

    elif rule_type == "STARTS_WITH":
        return text_lower.startswith(pattern_lower)

    elif rule_type == "ENDS_WITH":
        return text_lower.endswith(pattern_lower)

    elif rule_type == "EQUALS":
        return text_lower == pattern_lower

    elif rule_type == "REGEX":
        try:
            return bool(
                re.search(pattern, text, re.IGNORECASE)
            )
        except re.error:
            return False

    return False
