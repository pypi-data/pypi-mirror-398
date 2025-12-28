# EchoIntel Python SDK

Python SDK for integrating with the EchoIntel AI API. Provides forecasting, customer segmentation, inventory optimization, and other AI-powered analytics capabilities.

## Installation

```bash
pip install echointel
```

## Quick Start

### Synchronous Client

```python
from echointel import EchoIntelClient

# Initialize the client
client = EchoIntelClient(
    customer_api_id="your-api-id",
    secret="your-secret"
)

# Forecast revenue
result = client.forecast_revenue({
    "sales": [...],
    "forecast_period": 12
})

print(result)
```

### Async Client

```python
import asyncio
from echointel import AsyncEchoIntelClient

async def main():
    async with AsyncEchoIntelClient(
        customer_api_id="your-api-id",
        secret="your-secret"
    ) as client:
        result = await client.forecast_revenue({
            "sales": [...],
            "forecast_period": 12
        })
        print(result)

asyncio.run(main())
```

## Configuration

The SDK can be configured via constructor arguments or environment variables:

| Constructor Argument | Environment Variable | Default |
|---------------------|---------------------|---------|
| `base_url` | `ECHOINTEL_API_URL` | `https://ai.echosistema.live` |
| `customer_api_id` | `ECHOINTEL_CUSTOMER_API_ID` | - |
| `secret` | `ECHOINTEL_SECRET` | - |
| `admin_secret` | `ECHOINTEL_ADMIN_SECRET` | - |
| `timeout` | `ECHOINTEL_TIMEOUT` | `30` |

### Using Environment Variables

```bash
export ECHOINTEL_CUSTOMER_API_ID="your-api-id"
export ECHOINTEL_SECRET="your-secret"
```

```python
from echointel import EchoIntelClient

# Credentials are automatically loaded from environment
client = EchoIntelClient()
```

## Available Endpoints

### Forecasting
- `forecast_revenue(data)` - Forecast revenue
- `forecast_cost(data)` - Forecast cost
- `forecast_cost_improved(data)` - Improved cost forecasting
- `forecast_units(data)` - Forecast units/quantity
- `forecast_cost_totus(data)` - Totus algorithm forecasting

### Inventory
- `inventory_optimization(data)` - Optimize inventory levels
- `inventory_history_improved(data)` - Analyze inventory history

### Customer Analytics
- `customer_segmentation(data)` - Segment customers
- `customer_features(data)` - Build customer features
- `customer_loyalty(data)` - Calculate loyalty scores
- `customer_rfm(data)` - RFM analysis
- `customer_clv_features(data)` - CLV feature extraction
- `customer_clv_forecast(data)` - CLV forecasting

### Churn Analysis
- `churn_risk(data)` - Predict churn risk
- `churn_label(data)` - Generate churn labels

### NPS
- `nps(data)` - Calculate Net Promoter Score

### Propensity Modeling
- `propensity_buy_product(data)` - Purchase propensity
- `propensity_respond_campaign(data)` - Campaign response propensity
- `propensity_upgrade_plan(data)` - Upgrade propensity

### Recommendations
- `recommend_user_items(data)` - User item recommendations
- `recommend_similar_items(data)` - Similar item recommendations

### Cross-Sell & Upsell
- `cross_sell_matrix(data)` - Cross-sell opportunity matrix
- `upsell_suggestions(data)` - Upsell suggestions

### Dynamic Pricing
- `dynamic_pricing_recommend(data)` - Pricing recommendations

### Sentiment Analysis
- `sentiment_report(data)` - Sentiment report
- `sentiment_realtime(data)` - Real-time sentiment

### Anomaly Detection
- `anomaly_transactions(data)` - Transaction anomalies
- `anomaly_accounts(data)` - Account anomalies
- `anomaly_graph(data)` - Graph-based anomalies

### Credit Risk
- `credit_risk_score(data)` - Credit risk scores
- `credit_risk_explain(data)` - Credit risk explanation

### Marketing Attribution
- `channel_attribution(data)` - Channel attribution
- `uplift_model(data)` - Uplift modeling

### Customer Journey
- `journey_markov(data)` - Markov chain analysis
- `journey_sequences(data)` - Journey sequence analysis

### NLP & Text Processing
- `nlp_analysis(data)` - NLP analysis (Portuguese)
- `nlp_analysis_en(data)` - NLP analysis (English)
- `nlp_excess_inventory_report(data)` - Excess inventory report
- `sanitize_text(data)` - Text sanitization

### Admin Operations (requires admin_secret)
- `create_customer(data)` - Create customer
- `list_customers(include_disabled=False)` - List customers
- `get_customer(customer_id)` - Get customer details
- `update_customer(customer_id, data)` - Update customer
- `delete_customer(customer_id)` - Delete customer

## Error Handling

```python
from echointel import (
    EchoIntelClient,
    EchoIntelException,
    EchoIntelAuthenticationException,
    EchoIntelValidationException,
)

client = EchoIntelClient()

try:
    result = client.forecast_revenue(data)
except EchoIntelAuthenticationException as e:
    print(f"Authentication failed: {e}")
except EchoIntelValidationException as e:
    print(f"Validation error: {e}")
    print(f"Field errors: {e.get_errors()}")
except EchoIntelException as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
```

## Response Objects

The SDK provides typed response classes for structured data:

```python
from echointel.responses import ForecastUnitsResponse

result = client.forecast_units(data)
response = ForecastUnitsResponse.from_dict(result)

print(f"Forecast period: {response.forecast_period}")
for forecast in response.forecasts:
    print(f"Product: {forecast.product_code}")
    print(f"Best algorithm: {forecast.best_algorithm}")
```

## Route Resolver

Use the RouteResolver to work with API routes:

```python
from echointel import RouteResolver

# Get all routes in a category
routes = RouteResolver.resolve(["forecasting"])

# Get specific routes
routes = RouteResolver.resolve(["forecasting.revenue", "customer.rfm"])

# Get all non-admin routes
routes = RouteResolver.resolve(["*"])

# List categories
categories = RouteResolver.categories()

# List endpoints in a category
endpoints = RouteResolver.endpoints("forecasting")
```

## Requirements

- Python 3.10+
- httpx >= 0.24.0
- tenacity >= 8.0.0

## License

MIT
