"""Domain ontology for the Customer Support CBR system.

Defines the concept hierarchy:

    CustomerSupportIssue  (root)
    ├── ORDER
    │   ├── cancel_order
    │   ├── change_order
    │   ├── place_order
    │   └── track_order
    ├── ACCOUNT
    │   ├── create_account
    │   ├── delete_account
    │   ├── edit_account
    │   └── switch_account
    ├── SHIPPING_ADDRESS
    │   ├── change_shipping_address
    │   └── set_up_shipping_address
    ├── PAYMENT
    │   ├── check_payment_methods
    │   └── payment_issue
    ├── REFUND
    │   ├── check_refund_policy
    │   ├── get_refund
    │   └── track_refund
    ├── CANCELLATION_FEE
    │   └── check_cancellation_fee
    ├── CONTACT
    │   ├── contact_customer_service
    │   └── contact_human_agent
    ├── FEEDBACK
    │   ├── complaint
    │   └── review
    ├── INVOICE
    │   ├── check_invoice
    │   └── get_invoice
    ├── NEWSLETTER
    │   └── newsletter_subscription
    └── DELIVERY
        ├── delivery_options
        └── delivery_period

Also defines:
    SIMILARITY_WEIGHTS      Weights for the composite similarity score.
    TREE_DISTANCE_SCORES    Maps tree-hop distance to a normalised [0,1] score.
    CATEGORY_DESCRIPTIONS   Human-readable descriptions for each category
                            (used when seeding the knowledge graph).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Core ontology tree: category → list[intent]
# ---------------------------------------------------------------------------

ROOT = "CustomerSupportIssue"

ONTOLOGY: dict[str, list[str]] = {
    "ORDER": [
        "cancel_order",
        "change_order",
        "place_order",
        "track_order",
    ],
    "ACCOUNT": [
        "create_account",
        "delete_account",
        "edit_account",
        "switch_account",
    ],
    "SHIPPING_ADDRESS": [
        "change_shipping_address",
        "set_up_shipping_address",
    ],
    "PAYMENT": [
        "check_payment_methods",
        "payment_issue",
    ],
    "REFUND": [
        "check_refund_policy",
        "get_refund",
        "track_refund",
    ],
    "CANCELLATION_FEE": [
        "check_cancellation_fee",
    ],
    "CONTACT": [
        "contact_customer_service",
        "contact_human_agent",
    ],
    "FEEDBACK": [
        "complaint",
        "review",
    ],
    "INVOICE": [
        "check_invoice",
        "get_invoice",
    ],
    "NEWSLETTER": [
        "newsletter_subscription",
    ],
    "DELIVERY": [
        "delivery_options",
        "delivery_period",
    ],
}

# ---------------------------------------------------------------------------
# Category descriptions (stored in the KG for documentation / future NLU)
# ---------------------------------------------------------------------------

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "ORDER": "Issues related to placing, changing, cancelling or tracking orders.",
    "ACCOUNT": "Issues related to creating, editing, switching or deleting a customer account.",
    "SHIPPING_ADDRESS": "Issues related to setting up or modifying a shipping address.",
    "PAYMENT": "Issues related to payment methods or payment failures.",
    "REFUND": "Issues related to initiating, tracking or understanding refunds.",
    "CANCELLATION_FEE": "Questions about fees charged when cancelling an order or service.",
    "CONTACT": "Requests to reach a customer service agent or human support.",
    "FEEDBACK": "Customer feedback including complaints and product/service reviews.",
    "INVOICE": "Issues related to retrieving or validating invoices.",
    "NEWSLETTER": "Enquiries about newsletter subscription or unsubscription.",
    "DELIVERY": "Questions about delivery options, estimated delivery periods.",
}

INTENT_DESCRIPTIONS: dict[str, str] = {
    "cancel_order": "Customer wants to cancel an existing order.",
    "change_order": "Customer wants to modify the details of an existing order.",
    "place_order": "Customer wants to place a new order.",
    "track_order": "Customer wants to know the current status or location of their order.",
    "create_account": "Customer wants to register a new account.",
    "delete_account": "Customer wants to permanently remove their account.",
    "edit_account": "Customer wants to update their account details (email, name, address, etc.).",
    "switch_account": "Customer wants to log in or move to a different account.",
    "change_shipping_address": "Customer wants to update the delivery address for an order.",
    "set_up_shipping_address": "Customer wants to add a new shipping address to their profile.",
    "check_payment_methods": "Customer wants to know which payment methods are accepted.",
    "payment_issue": "Customer is experiencing a problem with a payment or charge.",
    "check_refund_policy": "Customer wants to understand the refund policy.",
    "get_refund": "Customer wants to initiate a refund for an order or charge.",
    "track_refund": "Customer wants to know the status of an in-progress refund.",
    "check_cancellation_fee": "Customer wants to know if a cancellation fee applies.",
    "contact_customer_service": "Customer wants to contact the support team.",
    "contact_human_agent": "Customer explicitly requests to speak with a human agent.",
    "complaint": "Customer is lodging a formal complaint.",
    "review": "Customer wants to leave a review or rating.",
    "check_invoice": "Customer wants to verify or view an invoice.",
    "get_invoice": "Customer needs a copy of an invoice.",
    "newsletter_subscription": "Customer wants to subscribe or unsubscribe from a newsletter.",
    "delivery_options": "Customer wants to know the available delivery options.",
    "delivery_period": "Customer wants to know how long delivery will take.",
}

# ---------------------------------------------------------------------------
# Derived look-ups (built once at import time)
# ---------------------------------------------------------------------------

# intent → parent category
INTENT_TO_CATEGORY: dict[str, str] = {
    intent: category
    for category, intents in ONTOLOGY.items()
    for intent in intents
}

# All known categories and intents as flat sets
ALL_CATEGORIES: frozenset[str] = frozenset(ONTOLOGY.keys())
ALL_INTENTS: frozenset[str] = frozenset(INTENT_TO_CATEGORY.keys())

# ---------------------------------------------------------------------------
# Composite similarity configuration
# ---------------------------------------------------------------------------

# Weights applied to the three similarity components.
# Must sum to 1.0.
SIMILARITY_WEIGHTS: dict[str, float] = {
    "text":     0.60,   # spaCy cosine / Jaccard text similarity
    "intent":   0.25,   # ontology tree-distance intent similarity
    "category": 0.15,   # category exact-match similarity
}

# Maps tree-hop distance to a normalised similarity score.
#
# Hops are counted on the undirected concept tree:
#   distance 0  → same concept               → score 1.0
#   distance 2  → sibling intents            → score 0.6
#               (intent → category → intent)
#   distance 4  → cross-category intents     → score 0.2
#               (intent → cat → root → cat → intent)
#   unknown     → no ontology info available → score 0.0
TREE_DISTANCE_SCORES: dict[int, float] = {
    0: 1.0,
    2: 0.6,
    4: 0.2,
}
