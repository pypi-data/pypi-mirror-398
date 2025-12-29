"""Rule merging service for combining rulesets."""

from daimyo.domain import Category, CategoryKey, RuleSet
from daimyo.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RuleMergingService:
    """Service for merging rulesets according to Daimyo's merging rules.

    Commandments: Additive merging (all parent + all child)
    Suggestions: Override by default, append with + prefix
    """

    def merge_commandments(self, parent: RuleSet, child: RuleSet) -> RuleSet:
        """Merge commandments additively.

        All parent rules + all child rules. If a category exists in both,
        rules are combined. Child's 'when' description overrides parent's.

        :param parent: Parent ruleset
        :type parent: RuleSet
        :param child: Child ruleset
        :type child: RuleSet
        :returns: Merged ruleset with all commandments
        :rtype: RuleSet
        """
        result = RuleSet()

        for cat_key, category in parent.categories.items():
            result.add_category(category.copy())

        for cat_key, child_category in child.categories.items():
            if cat_key in result.categories:
                existing = result.categories[cat_key]
                existing.rules.extend(child_category.rules)
                existing.when = child_category.when
                logger.debug(
                    f"Extended commandment category '{cat_key}' (now {len(existing.rules)} rules)"
                )
            else:
                result.add_category(child_category.copy())
                logger.debug(f"Added new commandment category '{cat_key}'")

        logger.debug(
            f"Merged commandments: {len(result.categories)} categories, "
            f"{sum(len(c.rules) for c in result.categories.values())} total rules"
        )
        return result

    def merge_suggestions(self, parent: RuleSet, child: RuleSet) -> RuleSet:
        """Merge suggestions with override/append logic.

        Rules:
        1. If child category key starts with '+', append to parent
        2. Otherwise, child completely overrides parent for that category
        3. Categories only in parent are kept
        4. Categories only in child are added

        :param parent: Parent ruleset
        :type parent: RuleSet
        :param child: Child ruleset
        :type child: RuleSet
        :returns: Merged ruleset with combined suggestions
        :rtype: RuleSet
        """
        result = RuleSet()

        for cat_key, category in parent.categories.items():
            result.add_category(category.copy())

        for cat_key, child_category in child.categories.items():
            cat_str = str(cat_key)

            if cat_str.startswith("+"):
                actual_key = CategoryKey.from_string(cat_str[1:])

                if actual_key in result.categories:
                    existing = result.categories[actual_key]
                    existing.rules.extend(child_category.rules)
                    existing.when = child_category.when
                    logger.debug(
                        f"Appended to suggestion category '{actual_key}' "
                        f"(now {len(existing.rules)} rules)"
                    )
                else:
                    new_category = Category(
                        key=actual_key, when=child_category.when, rules=child_category.rules.copy()
                    )
                    result.add_category(new_category)
                    logger.debug(
                        f"Added new suggestion category '{actual_key}' (no parent to append to)"
                    )
            else:
                result.categories[cat_key] = child_category.copy()
                logger.debug(f"Overrode suggestion category '{cat_key}'")

        logger.debug(
            f"Merged suggestions: {len(result.categories)} categories, "
            f"{sum(len(c.rules) for c in result.categories.values())} total rules"
        )
        return result

    def filter_categories(self, ruleset: RuleSet, category_filters: list[str]) -> RuleSet:
        """Filter ruleset to only include matching categories.

        Uses prefix matching: filter "python.web" matches "python.web",
        "python.web.api", "python.web.testing", etc.

        :param ruleset: The ruleset to filter
        :type ruleset: RuleSet
        :param category_filters: List of category prefixes to match
        :type category_filters: List[str]
        :returns: New ruleset with only matching categories
        :rtype: RuleSet
        """
        if not category_filters:
            return ruleset

        result = RuleSet()
        matched_keys = set()

        for filter_str in category_filters:
            filter_key = CategoryKey.from_string(filter_str)

            for cat_key, category in ruleset.categories.items():
                if cat_key.matches_prefix(filter_key) or cat_key == filter_key:
                    if cat_key not in matched_keys:
                        result.add_category(category.copy())
                        matched_keys.add(cat_key)

        logger.debug(
            f"Filtered {len(ruleset.categories)} categories to "
            f"{len(result.categories)} using filters: {category_filters}"
        )
        return result


__all__ = ["RuleMergingService"]
