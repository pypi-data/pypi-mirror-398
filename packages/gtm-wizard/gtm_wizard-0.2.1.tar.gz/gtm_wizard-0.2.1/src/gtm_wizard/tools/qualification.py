"""Lead qualification tools for GTM Wizard.

These tools provide frameworks for lead qualification, not absolute answers.
Users should adapt the logic based on their specific:
- ICP (Ideal Customer Profile)
- Sales capacity and motion
- Historical conversion data
- Market context
"""

from typing import Any, TypedDict


class RoleTierData(TypedDict):
    """Type definition for role tier data."""

    titles: list[str]
    tier: int
    label: str
    points: int


class SizeData(TypedDict):
    """Type definition for company size data."""

    points: int
    label: str


# Default role tiers - users should customize based on their ICP
DEFAULT_ROLE_TIERS: dict[str, RoleTierData] = {
    "c_level": {
        "titles": ["ceo", "cfo", "coo", "cmo", "cro", "cto", "chief"],
        "tier": 1,
        "label": "C-Level Executive",
        "points": 30,
    },
    "vp": {
        "titles": ["vp", "vice president", "svp", "evp"],
        "tier": 2,
        "label": "VP Level",
        "points": 25,
    },
    "director": {
        "titles": ["director", "head of", "senior director"],
        "tier": 3,
        "label": "Director Level",
        "points": 20,
    },
    "manager": {
        "titles": ["manager", "senior manager", "team lead"],
        "tier": 4,
        "label": "Manager Level",
        "points": 15,
    },
    "individual": {
        "titles": ["analyst", "specialist", "coordinator", "associate"],
        "tier": 5,
        "label": "Individual Contributor",
        "points": 5,
    },
}

# Personal email domains to flag
PERSONAL_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

# Education-related patterns
EDUCATION_PATTERNS = [".edu", "student", "intern", "university"]


def score_lead(
    role_title: str | None = None,
    industry: str | None = None,
    company_size: str | None = None,
    intent_signals: list[str] | None = None,
    custom_factors: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Calculate a lead score with transparent breakdown.

    This provides a STARTING FRAMEWORK. You should:
    1. Adjust weights based on your conversion data
    2. Add/remove factors relevant to your ICP
    3. Calibrate thresholds to your sales capacity

    Returns a score breakdown, not just a number.
    """
    breakdown = []
    total_score = 0
    max_possible = 0

    # Role scoring
    role_score = 0
    role_tier = "Unknown"
    if role_title:
        role_lower = role_title.lower()
        for _tier_name, tier_data in DEFAULT_ROLE_TIERS.items():
            if any(t in role_lower for t in tier_data["titles"]):
                role_score = tier_data["points"]
                role_tier = tier_data["label"]
                break
        if role_score == 0:
            role_score = 10  # Default for unrecognized roles
            role_tier = "Unclassified"

    breakdown.append(
        {
            "factor": "Role/Title",
            "value": role_title or "Not provided",
            "classification": role_tier,
            "points": role_score,
            "max_points": 30,
            "reasoning": "Higher seniority = more decision-making authority. "
            "Adjust weights if your product targets specific levels.",
        }
    )
    total_score += role_score
    max_possible += 30

    # Industry scoring (requires user configuration)
    industry_score = 10  # Default middle score
    industry_tier = "Not configured"
    breakdown.append(
        {
            "factor": "Industry",
            "value": industry or "Not provided",
            "classification": industry_tier,
            "points": industry_score,
            "max_points": 25,
            "reasoning": "Industry scoring requires YOUR configuration. "
            "Define which industries are Tier 1/2/3 for your product.",
            "action_required": "Configure industry tiers based on your ICP",
        }
    )
    total_score += industry_score
    max_possible += 25

    # Company size scoring
    size_score = 0
    size_map: dict[str, SizeData] = {
        "enterprise": {"points": 20, "label": "Enterprise (1000+)"},
        "mid-market": {"points": 15, "label": "Mid-Market (100-999)"},
        "smb": {"points": 10, "label": "SMB (10-99)"},
        "startup": {"points": 5, "label": "Startup (<10)"},
    }
    if company_size:
        size_lower = company_size.lower()
        for size_key, size_data in size_map.items():
            if size_key in size_lower:
                size_score = size_data["points"]
                break
        if size_score == 0:
            size_score = 10  # Default

    breakdown.append(
        {
            "factor": "Company Size",
            "value": company_size or "Not provided",
            "points": size_score,
            "max_points": 20,
            "reasoning": "Size scoring depends on YOUR target. Enterprise products "
            "score large companies higher; PLG products might score SMB higher.",
        }
    )
    total_score += size_score
    max_possible += 20

    # Intent signals
    intent_score = 0
    if intent_signals:
        # Each signal adds points (diminishing returns)
        intent_score = min(len(intent_signals) * 5, 20)

    breakdown.append(
        {
            "factor": "Intent Signals",
            "value": intent_signals or [],
            "points": intent_score,
            "max_points": 20,
            "reasoning": "More intent signals = higher engagement. "
            "Weight signals differently based on your funnel data.",
        }
    )
    total_score += intent_score
    max_possible += 20

    # Custom factors
    if custom_factors:
        for factor_name, factor_points in custom_factors.items():
            breakdown.append(
                {
                    "factor": f"Custom: {factor_name}",
                    "points": factor_points,
                    "max_points": factor_points,  # Custom factors are user-defined
                    "reasoning": "User-defined scoring factor",
                }
            )
            total_score += factor_points
            max_possible += abs(factor_points)

    # Calculate percentage and tier
    if max_possible > 0:
        percentage = round((total_score / max_possible) * 100)
    else:
        percentage = 0

    # Tier assignment (these thresholds should be calibrated to YOUR data)
    if percentage >= 70:
        tier = "A"
        tier_description = "High priority - strong fit signals"
    elif percentage >= 50:
        tier = "B"
        tier_description = "Medium priority - moderate fit signals"
    elif percentage >= 30:
        tier = "C"
        tier_description = "Low priority - weak fit signals"
    else:
        tier = "D"
        tier_description = "Very low priority - poor fit signals"

    return {
        "total_score": total_score,
        "max_possible": max_possible,
        "percentage": percentage,
        "tier": tier,
        "tier_description": tier_description,
        "breakdown": breakdown,
        "calibration_note": "These thresholds (70/50/30) are starting points. "
        "Calibrate based on your actual conversion rates by tier.",
        "next_steps": [
            "Compare tier distribution to your sales capacity",
            "Track conversion rates by tier to validate scoring",
            "Adjust weights based on what actually predicts conversion",
        ],
    }


def classify_role(job_title: str) -> dict[str, Any]:
    """Classify a job title into decision-making tiers.

    This classification helps prioritize outreach based on likely
    decision-making authority. Adapt based on your product and motion.
    """
    if not job_title:
        return {
            "tier": 0,
            "label": "Unknown",
            "confidence": "low",
            "reasoning": "No job title provided",
        }

    title_lower = job_title.lower()

    # Check each tier
    for tier_name, tier_data in DEFAULT_ROLE_TIERS.items():
        if any(t in title_lower for t in tier_data["titles"]):
            return {
                "original_title": job_title,
                "tier": tier_data["tier"],
                "label": tier_data["label"],
                "points": tier_data["points"],
                "confidence": "high" if len(job_title) > 3 else "medium",
                "reasoning": f"Title contains '{tier_name}' indicators",
                "customization_note": "Role importance varies by product. "
                "A product for developers might weight ICs higher.",
            }

    # Unclassified
    return {
        "original_title": job_title,
        "tier": 5,
        "label": "Unclassified",
        "points": 10,
        "confidence": "low",
        "reasoning": f"Title '{job_title}' doesn't match known patterns",
        "action": "Consider adding this title pattern to your classification",
    }


def classify_industry(
    industry: str,
    tier_1_industries: list[str] | None = None,
    tier_2_industries: list[str] | None = None,
    tier_3_industries: list[str] | None = None,
) -> dict[str, Any]:
    """Classify an industry into fit tiers.

    Industry classification is highly product-specific. You MUST provide
    your own tier definitions for meaningful results.
    """
    if not industry:
        return {
            "tier": 0,
            "label": "Unknown",
            "reasoning": "No industry provided",
        }

    industry_lower = industry.lower()

    # Check user-provided tiers
    if tier_1_industries:
        for t1 in tier_1_industries:
            if t1.lower() in industry_lower or industry_lower in t1.lower():
                return {
                    "original_industry": industry,
                    "tier": 1,
                    "label": "Primary Target",
                    "points": 25,
                    "reasoning": f"Matches Tier 1 industry: {t1}",
                }

    if tier_2_industries:
        for t2 in tier_2_industries:
            if t2.lower() in industry_lower or industry_lower in t2.lower():
                return {
                    "original_industry": industry,
                    "tier": 2,
                    "label": "Secondary Target",
                    "points": 15,
                    "reasoning": f"Matches Tier 2 industry: {t2}",
                }

    if tier_3_industries:
        for t3 in tier_3_industries:
            if t3.lower() in industry_lower or industry_lower in t3.lower():
                return {
                    "original_industry": industry,
                    "tier": 3,
                    "label": "Tertiary Target",
                    "points": 10,
                    "reasoning": f"Matches Tier 3 industry: {t3}",
                }

    # No tier configuration provided or no match
    return {
        "original_industry": industry,
        "tier": 0,
        "label": "Unclassified",
        "points": 5,
        "reasoning": "Industry not in configured tiers",
        "action_required": "Define your industry tiers based on your ICP. "
        "Which industries have the best product-market fit?",
        "questions_to_answer": [
            "Which industries have you closed the most deals in?",
            "Which industries have the shortest sales cycles?",
            "Which industries have the highest retention?",
        ],
    }


def determine_routing(
    score: int,
    tier: str,
    company_size: str | None = None,
    has_intent_signals: bool = False,
    custom_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Determine the appropriate routing track for a lead.

    Routing should match lead quality to your sales capacity.
    High-quality leads → human touch. Lower quality → automation.
    """
    # Default routing logic (adapt to your team structure)
    if tier == "A" or (tier == "B" and has_intent_signals):
        track = "high_touch"
        track_description = "Route to sales rep for personalized outreach"
        suggested_actions = [
            "Assign to named account owner",
            "Trigger personalized sequence",
            "Add to priority follow-up queue",
        ]
    elif tier == "B":
        track = "medium_touch"
        track_description = "Automated sequence with human oversight"
        suggested_actions = [
            "Enroll in nurture sequence",
            "Monitor for engagement signals",
            "Escalate to sales if engagement detected",
        ]
    elif tier == "C":
        track = "low_touch"
        track_description = "Automated nurture only"
        suggested_actions = [
            "Add to long-term nurture",
            "Include in marketing campaigns",
            "Re-score periodically for changes",
        ]
    else:
        track = "nurture_only"
        track_description = "Marketing nurture, no sales touch"
        suggested_actions = [
            "Add to general newsletter",
            "May re-engage if circumstances change",
        ]

    # Company size override (large companies often warrant more attention)
    size_override = None
    if company_size:
        size_lower = company_size.lower()
        if "enterprise" in size_lower and track != "high_touch":
            size_override = "Consider upgrading to high_touch for enterprise accounts"

    return {
        "recommended_track": track,
        "track_description": track_description,
        "suggested_actions": suggested_actions,
        "size_override_note": size_override,
        "inputs_used": {
            "score": score,
            "tier": tier,
            "company_size": company_size,
            "has_intent_signals": has_intent_signals,
        },
        "customization_note": "Routing tracks should match YOUR sales motion. "
        "Adjust based on team capacity and deal economics.",
        "questions_to_consider": [
            "How many leads can your sales team handle personally?",
            "What's the cost of a sales touch vs. expected deal value?",
            "Are there segments that convert well with pure automation?",
        ],
    }


def check_disqualification(
    email: str | None = None,
    company_name: str | None = None,
    job_title: str | None = None,
    competitors: list[str] | None = None,
    excluded_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Check for disqualifying factors.

    Disqualification saves time by filtering leads that won't convert.
    But be careful not to over-filter and miss opportunities.
    """
    flags = []
    is_disqualified = False
    disqualification_reason = None

    # Check email domain
    if email:
        email_lower = email.lower()
        domain = email_lower.split("@")[-1] if "@" in email_lower else ""

        # Personal email check
        if any(pd in domain for pd in PERSONAL_EMAIL_DOMAINS):
            flags.append(
                {
                    "type": "personal_email",
                    "value": domain,
                    "severity": "medium",
                    "recommendation": "Personal emails are often lower quality, "
                    "but not always disqualifying. Consider your motion.",
                }
            )

        # Student/edu check
        if any(ep in domain for ep in EDUCATION_PATTERNS):
            flags.append(
                {
                    "type": "education_domain",
                    "value": domain,
                    "severity": "medium",
                    "recommendation": "Education domains may be students or academics. "
                    "Disqualify unless education is a target market.",
                }
            )

        # Custom excluded domains
        if excluded_domains:
            if any(ed.lower() in domain for ed in excluded_domains):
                flags.append(
                    {
                        "type": "excluded_domain",
                        "value": domain,
                        "severity": "high",
                        "recommendation": "Domain is on your exclusion list.",
                    }
                )
                is_disqualified = True
                disqualification_reason = f"Domain '{domain}' is excluded"

    # Competitor check
    if company_name and competitors:
        company_lower = company_name.lower()
        for competitor in competitors:
            if competitor.lower() in company_lower:
                flags.append(
                    {
                        "type": "competitor",
                        "value": company_name,
                        "matched": competitor,
                        "severity": "high",
                        "recommendation": "Lead works at a competitor. "
                        "Typically disqualified from outreach.",
                    }
                )
                is_disqualified = True
                disqualification_reason = f"Works at competitor: {competitor}"
                break

    # Job title red flags
    if job_title:
        title_lower = job_title.lower()
        if any(s in title_lower for s in ["student", "intern"]):
            flags.append(
                {
                    "type": "student_title",
                    "value": job_title,
                    "severity": "medium",
                    "recommendation": "Students/interns rarely have buying authority. "
                    "Consider excluding unless your product targets them.",
                }
            )

    return {
        "is_disqualified": is_disqualified,
        "disqualification_reason": disqualification_reason,
        "flags": flags,
        "flag_count": len(flags),
        "recommendation": "Review flags and decide based on your policies. "
        "Not all flags require disqualification.",
        "customization_note": "Disqualification rules should be based on YOUR data. "
        "Track which flags actually predict non-conversion.",
    }
