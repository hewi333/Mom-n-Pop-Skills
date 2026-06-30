---
name: estimator-engine
description: "Use when calculating service estimates for jobs. Computes pricing based on square footage, ceiling height, service type, travel distance, and severity tiers. Config-driven — plug in your own rate card."
version: "1.0.0"
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [estimator, pricing, small-business, service-quoting]
    related_skills: [crm-lite, quickbooks-online, stripe-payments]
---

# Estimator Engine — Service Pricing Calculator

## Overview
A deterministic pricing engine for a service business. Takes property/job details and returns a structured estimate with line items, ranges, and confidence levels. Designed for agent-mediated use: owners text property details, agent returns instant estimate.

## When to Use
- **Website estimator form** — visitor enters sqft, gets instant price range
- **Referral qualification** — quick ballpark before site visit
- **Agent creates formal estimate** — detailed line items for QuickBooks
- **Insurance claim scoping** — severity tier mapping to pricing multipliers

## Don't Use For
- Dynamic pricing / demand-based surges
- Multi-trade construction estimates
- Recurring subscription pricing

## Configuration

All pricing is **config-driven**. Copy the config block below into a `pricing_config.json`
file or environment variables, then plug in your own rates. The numbers shown are
**EXAMPLES** — replace them with your real rate card.

```python
# Example configuration — REPLACE ALL VALUES with your own rates
PRICING_CONFIG = {
    "regions": {
        "standard": {
            "label": "Standard Region",
            "counties": ["[REGION_1]", "[REGION_2]"]  # list your service areas here
        },
        "premium": {
            "label": "Premium Region",
            "counties": ["[PREMIUM_REGION_1]"]  # e.g., further travel, higher costs
        }
    },
    "residential_commercial": {
        "standard": {
            "tiers": [
                {"max_sqft": 1000, "rate_per_sqft": 1.55, "minimum": 1200, "cigarette_ext_addon": 350},
                {"max_sqft": 1500, "rate_per_sqft": 1.30, "minimum": 0, "cigarette_ext_addon": 450},
                {"max_sqft": 2500, "rate_per_sqft": 1.25, "minimum": 0, "cigarette_ext_addon": 550},
                {"max_sqft": 5000, "rate_per_sqft": 1.20, "minimum": 0, "cigarette_ext_addon": 650},
                {"max_sqft": 10000, "rate_per_sqft": 1.15, "minimum": 0, "cigarette_ext_addon": 750},
                {"max_sqft": 999999, "rate_per_sqft": 1.10, "minimum": 0, "cigarette_ext_addon": 850}
            ],
            "addons": {
                "pet_trauma_per_sqft": 0.35,
                "surface_defense_per_sqft": 0.35,
                "high_rise_flat": 350
            }
        },
        "premium": {
            "tiers": [
                {"max_sqft": 1500, "rate_per_sqft": 1.70, "minimum": 1500, "cigarette_ext_addon": 450},
                {"max_sqft": 2500, "rate_per_sqft": 1.55, "minimum": 0, "cigarette_ext_addon": 550},
                {"max_sqft": 5000, "rate_per_sqft": 1.50, "minimum": 0, "cigarette_ext_addon": 650},
                {"max_sqft": 10000, "rate_per_sqft": 1.45, "minimum": 0, "cigarette_ext_addon": 750},
                {"max_sqft": 999999, "rate_per_sqft": 1.40, "minimum": 0, "cigarette_ext_addon": 850}
            ],
            "addons": {
                "pet_trauma_per_sqft": 0.35,
                "surface_defense_per_sqft": 0.35,
                "high_rise_flat": 350
            }
        }
    },
    "apartments": {
        "standard": {
            "rates": {"1_bed": 900, "2_bed": 1000, "3_bed": 1100},
            "addons": {"pet_trauma_flat": 150, "surface_defense_flat": 100}
        },
        "premium": {
            "rates": {"1_bed": 900, "2_bed": 1000, "3_bed": 1100},
            "premium_surcharge_flat": 500,
            "addons": {"pet_trauma_flat": 150, "surface_defense_flat": 100}
        }
    },
    "estimate_number_prefix": "EST",
    "estimate_valid_days": 30,
    "range_uncertainty_pct": 0.15  # ±15% around calculated total
}
```

> ⚠️ **The numbers above are EXAMPLES.** They show the *structure* of a tiered
> pricing model (per-sqft rates, minimums, add-on surcharges, region differentials).
> Replace every value with your own business's actual rates.

## Pricing Model Structure

### Location Tiers
- **Standard Region:** Your local/primary service area (lower travel cost)
- **Premium Region:** Further service areas with higher travel cost

### Property Types
1. **Residential / Commercial** — priced by square footage tiers
2. **Apartments** — flat rate by bedroom count

### EXAMPLE Pricing (Standard Region)

#### Residential / Commercial — Base Treatment

| Square Footage | Rate (psf) | Ext Add-on (Cigarette >5yrs) |
|---|---|---|
| 1,000 sf or less | $1.55 psf (min $1,200) | +$350 |
| 1,000–1,500 sf | $1.30 psf | +$450 |
| 1,500–2,500 sf | $1.25 psf | +$550 |
| 2,500–5,000 sf | $1.20 psf | +$650 |
| 5,000–10,000 sf | $1.15 psf | +$750 |
| 10,000 sf or more | $1.10 psf | +$850 |

**Add-ons (Standard):**
- Pet/Trauma: +$0.35 psf
- Surface Defense: +$0.35 psf
- High Rise Condo: +$350 per job

#### Apartments — Base Treatment

| Unit Size | Base Price |
|---|---|
| 1 Bedroom | $900 |
| 2 Bedroom | $1,000 |
| 3 Bedroom | $1,100 |

**Add-ons (Standard Apartments):**
- Pet/Trauma: +$150
- Surface Defense: +$100

### EXAMPLE Pricing (Premium Region)

#### Residential / Commercial — Base Treatment

| Square Footage | Rate (psf) | Ext Add-on (Cigarette >5yrs) |
|---|---|---|
| 1,500 sf or less | $1.70 psf (min $1,500) | +$450 |
| 1,500–2,500 sf | $1.55 psf | +$550 |
| 2,500–5,000 sf | $1.50 psf | +$650 |
| 5,000–10,000 sf | $1.45 psf | +$750 |
| 10,000 sf or more | $1.40 psf | +$850 |

**Add-ons (Premium):**
- Pet/Trauma: +$0.35 psf
- Surface Defense: +$0.35 psf
- High Rise Condo: +$350 per job

#### Apartments — Base Treatment

Same base rates as Standard, plus a **Premium Region surcharge** of +$500 to each tier.

**Add-ons (Premium Apartments):**
- Pet/Trauma: +$150
- Surface Defense: +$100

---

### CALCULATION RULES

1. **Determine location:** Standard or Premium (based on configured region mapping)
2. **Determine property type:** Residential/Commercial or Apartment
3. **For Res/Comm:** find sf tier → multiply rate × square footage (apply minimum if applicable)
4. **For Apartments:** use flat rate by bedroom count
5. **Add applicable surcharges:** Pet/Trauma, Surface Defense, Ext (cigarette >5yrs), High Rise
6. **Premium apartments:** add the configured premium surcharge to the flat rate

### Minimums (from pricing tables)
- **Standard Res/Comm ≤1,000 sf:** $1,200 minimum (example)
- **Premium Res/Comm ≤1,500 sf:** $1,500 minimum (example)
- **Apartments:** flat rates already include minimums

## API Interface

### Input Schema
```python
class EstimateRequest:
    property_address: str          # Full address (used to determine region/location)
    property_type: str             # "residential_commercial" or "apartment"
    sqft: int = 0                  # Required for residential_commercial
    bedrooms: int = 0              # Required for apartment (1, 2, or 3)
    is_premium_region: bool = False  # Auto-determined from region config, but can override
    add_ons: List[str] = []        # ["pet_trauma", "surface_defense", "cigarette_ext", "high_rise"]
```

### Output Schema
```python
class EstimateResponse:
    estimate_number: str           # EST-YYYY-NNNN
    line_items: List[LineItem]
    subtotal: float
    total: float
    range_low: float               # -15% for uncertainty
    range_high: float              # +15% for uncertainty
    confidence: str                # high/medium/low
    assumptions: List[str]
    valid_days: int = 30
```

### Line Item Structure
```python
class LineItem:
    description: str
    quantity: float
    unit: str                      # "sf", "each", "job"
    unit_price: float
    total: float
    notes: str
```

## Quick Start

```python
from estimator import estimate_job

# Residential/Commercial example (Standard pricing)
request = {
    "property_address": "123 Main St, [CITY], [STATE] [ZIP]",  # Standard Region
    "property_type": "residential_commercial",
    "sqft": 2500,
    "add_ons": ["pet_trauma"]
}

result = estimate_job(request)
# Returns structured estimate with line items, ranges, total

# Apartment example (Premium Region)
request = {
    "property_address": "456 Ocean Dr, [CITY], [STATE] [ZIP]",  # Premium Region
    "property_type": "apartment",
    "bedrooms": 2,
    "add_ons": ["surface_defense"]
}

result = estimate_job(request)
# Returns structured estimate
```

## Agent Integration Patterns

### Website Estimator Form → Instant Range
```
User: "2500 sqft house, [CITY], pet odor, add surface defense"
Agent: Determines Standard Region, Res/Comm tier 1500-2500 = $1.25/sf
       Base: 2500 × $1.25 = $3,125
       Pet/Trauma: 2500 × $0.35 = $875
       Surface Defense: 2500 × $0.35 = $875
       Total: $4,875 → Returns "Estimated $4,100–$5,600 (est. $4,875)"
```

### Formal Estimate for QuickBooks
```
User: "Create estimate for John Smith, 123 Main St [CITY], 2500 sqft house, pet trauma, surface defense"
Agent: Creates estimate record in CRM, generates QuickBooks estimate with line items, emails PDF
```

### Quick Quote
```
User: "Realtor needs ballpark for 2-bed apartment, cigarette smoke >5yrs"
Agent: Premium Region, Apartment 2-bed = $1,000 + $500 Premium + $150 cigarette
       Total: $1,650 → Returns "$1,400–$1,900" + disclaimer
```

## Common Pitfalls

1. **Region misclassification** — Make sure your region mapping is configured correctly and matches across estimator-engine, website, and CRM
2. **Property type confusion** — Apartments use flat bedroom rates, NOT square footage pricing
3. **Premium apartment surcharge** — Must add the configured premium surcharge to the flat rate for Premium Region apartments
4. **Cigarette >5yrs** — Only applies as "Ext Add-on" flat fee per tier (not per sf)
5. **Minimums** — Check configured minimums for small square footage tiers
6. **High Rise Condo** — Flat fee per job (applies to both Standard and Premium)
7. **Pet/Trauma + Surface Defense** — Both are per-sf for Res/Comm, flat fee for Apartments

## Verification Checklist

- [ ] Region correctly maps to Standard vs Premium (from your config)
- [ ] Property type determines pricing method (sf tiers vs bedroom flat rate)
- [ ] Square footage tier lookup returns correct rate
- [ ] Minimums enforced (from your config)
- [ ] Add-ons calculate correctly (per-sf for Res/Comm, flat for Apartments)
- [ ] Cigarette >5yrs uses tier-based flat fee (not per-sf)
- [ ] Premium apartments add surcharge to flat rate
- [ ] High Rise Condo adds configured flat fee
- [ ] Range ±15% around calculated total
- [ ] Estimate number format: EST-YYYY-NNNN (sequential)
- [ ] Output includes assumptions list for transparency

## One-Shot Recipes

### "Quick ballpark for website (Standard Res/Comm)"
```python
from estimator import quick_quote
quick_quote(property_type="residential_commercial", sqft=2000, is_premium_region=False, add_ons=["pet_trauma"])
# → "Estimated $3,400–$4,600" (2000 × $1.25 = $2,500 + 2000 × $0.35 = $700 + 2000 × $0.35 = $700 = $3,900)
```

### "Full estimate for QuickBooks (Premium Apartment)"
```python
from estimator import formal_estimate
estimate = formal_estimate(
    customer_name="Jane Doe",
    property_address="456 Ocean Dr, [CITY], [STATE] [ZIP]",
    property_type="apartment",
    bedrooms=2,
    is_premium_region=True,
    add_ons=["cigarette_ext", "surface_defense"]
)
# → Creates CRM estimate record, returns QB-ready line items
# Base: $1,000 (2-bed) + $500 (Premium) = $1,500
# Cigarette ext: +$150, Surface Defense: +$100 = $1,750 total
```

### "Batch quote for realtor list"
```python
from estimator import batch_quote
properties = [
    {"address": "456 Palm Ave [CITY], [STATE] [ZIP]", "property_type": "residential_commercial", "sqft": 3200, "add_ons": ["cigarette_ext"]},  # Standard Region
    {"address": "789 Ocean Dr [CITY], [STATE] [ZIP]", "property_type": "apartment", "bedrooms": 2, "add_ons": ["pet_trauma"]},  # Standard Region
    {"address": "1000 Collins Ave [CITY], [STATE] [ZIP]", "property_type": "residential_commercial", "sqft": 2800, "is_premium_region": True, "add_ons": ["high_rise"]},  # Premium Region
]
for prop in properties:
    print(batch_quote(prop))
```