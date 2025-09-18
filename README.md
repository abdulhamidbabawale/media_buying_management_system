# Media Buying Management System

A centralized API-only intelligent media buying management system that manages advertising campaigns across multiple platforms for multiple clients. This system features two levels of intelligence: SKU-level (per-product) and system-wide intelligence that makes hourly optimization decisions.

## 🚀 Key Features

### Core Infrastructure
- **Multi-tenant API architecture** with strict client data isolation
- **JWT authentication** with refresh token rotation (15-minute expiration)
- **Global rate limiting** using Redis (100 requests/minute)
- **MongoDB integration** with Motor async driver
- **Health check endpoints** for monitoring
- **Comprehensive error handling** and logging

### Intelligence Layer
- **EXPLORE/EXPLOIT modes** for campaign optimization
- **Hourly intelligence-driven optimization** with automated decision making
- **Dynamic impression thresholds** based on campaign maturity
- **Budget allocation algorithms** with risk management
- **Performance tracking** and burn rate calculations
- **System-wide learning** with anonymized benchmarks

### Platform Integrations
- **Google Ads API** connector with full campaign management
- **Meta Marketing API** connector with performance tracking
- **Integration middleware** for API orchestration and fallback strategies
- **Data normalization** across platforms
- **Rate limiting** and error handling

### Campaign Management
- **Full CRUD operations** for campaigns, SKUs, and clients
- **Multi-platform campaign creation** and management
- **Budget allocation** and optimization
- **Performance metrics** aggregation and analysis
- **Burn rate calculations** and forecasting

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                SKU INTELLIGENCE LAYER                       │
│       (Hourly decisions: campaigns, budgets, timing)       │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              INTEGRATION MIDDLEWARE                         │
│         (API Orchestration & Data Normalization)           │
└─────────────────┬───────────────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
┌─────▼─────┐           ┌─────▼─────┐
│ REVEALBOT │           │  ADROLL   │
│    API    │           │    API    │
└─────┬─────┘           └─────┬─────┘
      │                       │
┌─────▼─────┐           ┌─────▼─────┐
│   META    │           │  GOOGLE   │
│ PLATFORM  │           │ PLATFORM  │
└───────────┘           └───────────┘
```

## 🛠️ Tech Stack

- **Backend:** FastAPI with async/await
- **Database:** MongoDB with Motor (async driver)
- **Caching/Rate Limiting:** Redis
- **Authentication:** JWT with refresh tokens
- **Testing:** pytest, pytest-asyncio
- **HTTP Client:** httpx for async requests
- **Data Validation:** Pydantic models

## 📊 Data Models

### Core Collections
- **clients** - Client management with industry categorization
- **skus** - Product-level budget and intelligence settings
- **campaigns** - Platform-specific campaign management
- **performance_metrics** - Hourly performance snapshots
- **intelligence_decisions** - Decision logging for analysis
- **system_benchmarks** - Anonymized cross-client learning

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+
- MongoDB
- Redis
- Virtual environment

### Installation
```bash
git clone <repo_url>
cd media_buying_management_system
python -m venv env

# Activate virtual environment
source env/bin/activate  # On Linux/Mac
# .\env\Scripts\activate  # On Windows

pip install -r requirements.txt
```

### Environment Configuration
Create a `.env` file with:
```env
DATABASE_URI=mongodb://localhost:27017/media_buying
DB_NAME=media_buying
JWT_SECRET_KEY=your-secret-key-here
SECRET_KEY=your-secret-key-here
REDIS_HOST=localhost
REDIS_PORT=6379
ENVIRONMENT=development
```

### Running the Application
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login (returns access + refresh tokens)
- `POST /api/v1/auth/refresh` - Refresh access token

### Client Management
- `GET /api/v1/clients/` - List clients (filtered by access)
- `POST /api/v1/clients/` - Create client
- `GET /api/v1/clients/{id}` - Get client details
- `PUT /api/v1/clients/{id}` - Update client

### SKU Management
- `GET /api/v1/skus/` - List SKUs (filtered by client)
- `POST /api/v1/skus/` - Create SKU
- `GET /api/v1/skus/{id}` - Get SKU details
- `PUT /api/v1/skus/{id}` - Update SKU

### Campaign Management
- `GET /api/v1/campaigns/` - List campaigns (filtered by client)
- `POST /api/v1/campaigns/` - Create campaign
- `GET /api/v1/campaigns/{id}` - Get campaign details
- `PUT /api/v1/campaigns/{id}` - Update campaign
- `DELETE /api/v1/campaigns/{id}` - Pause/delete campaign
- `POST /api/v1/campaigns/{id}/pause` - Pause campaign
- `POST /api/v1/campaigns/{id}/activate` - Activate campaign
- `PUT /api/v1/campaigns/{id}/budget` - Update campaign budget

### Performance Metrics
- `GET /api/v1/metrics/campaigns/{campaign_id}` - Campaign performance
- `GET /api/v1/metrics/skus/{sku_id}` - SKU performance aggregation
- `GET /api/v1/metrics/clients/{client_id}` - Client-level metrics
- `GET /api/v1/metrics/burn-rate/{sku_id}` - Burn rate analysis
- `GET /api/v1/metrics/forecasts/{sku_id}` - Budget forecasting
- `GET /api/v1/metrics/platform-breakdown/{sku_id}` - Platform breakdown
- `GET /api/v1/metrics/mode-breakdown/{sku_id}` - Intelligence mode breakdown

### Integration Management
- `POST /api/v1/integrations/platforms/initialize` - Initialize platform connectors
- `GET /api/v1/integrations/platforms/status` - Platform status
- `POST /api/v1/integrations/platforms/validate` - Validate credentials
- `PUT /api/v1/integrations/campaigns/budget` - Update budget via middleware
- `POST /api/v1/integrations/campaigns/create` - Create campaign via middleware
- `GET /api/v1/integrations/campaigns/{id}/performance` - Get performance data

### System Health
- `GET /` - Root endpoint
- `GET /api/v1/health` - Health check with database and Redis status

## 🧠 Intelligence Configuration

### MVP Configuration Parameters
```python
MVP_CONFIG = {
    "min_campaign_budget": 100,  # USD minimum per campaign
    "spend_floor_percentage": 10,  # % of total budget as floor
    "spend_cap_percentage": 50,   # % of total budget as cap
    "explore_budget_percentage": 20,  # % allocated to exploration
    "impression_threshold": 1000,  # Minimum impressions for decisions
    "explore_mode_duration_days": 7,
    "exploit_confidence_threshold": 0.8,
    "min_roas_for_exploit": 2.0,
}
```

### EXPLORE vs EXPLOIT Logic
- **EXPLORE Mode**: Bold budget reallocations for learning (new campaigns, low impressions)
- **EXPLOIT Mode**: Small incremental optimizations (high confidence, good ROAS)

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py
```

### Test Coverage
- Authentication and JWT token management
- Campaign CRUD operations
- SKU intelligence decision making
- Performance metrics and burn rate calculations
- Integration middleware functionality
- Multi-tenant data isolation

## 🔒 Security Features

### Multi-Tenant Isolation
- All database queries include client_id filter
- JWT tokens include client_id claim
- API middleware validates client access on every request
- No cross-client data visibility

### Authentication & Authorization
- JWT tokens with 15-minute expiration
- Refresh token rotation (7-day expiration)
- Rate limiting (100 requests/minute)
- Secure credential management

## 📈 Performance Requirements

### API Response Times
- Authentication endpoints: < 200ms
- CRUD operations: < 500ms
- Performance metrics: < 1s
- Intelligence decisions: < 2s
- Burn rate calculations: < 500ms

### Scalability
- Support 1000+ concurrent API requests
- Handle 10,000+ campaigns per client
- Process hourly optimization for all active campaigns
- MongoDB optimization with proper indexing

## 🚀 Deployment

### Docker Support
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.development.yaml up --build
```

### Environment Variables
- `ENVIRONMENT` - development/production
- `DATABASE_URI` - MongoDB connection string
- `REDIS_HOST` - Redis host
- `JWT_SECRET_KEY` - JWT signing key

## 📋 Development Roadmap

### Completed (Step 1 - Foundation)
- ✅ Multi-tenant API with JWT authentication
- ✅ Google Ads + Meta Marketing integration
- ✅ Basic campaign budget allocation
- ✅ Burn rate calculation and API access
- ✅ Comprehensive test coverage (>80%)

### Next Steps
- 🔄 TikTok Ads API integration
- 🔄 Revealbot and AdRoll integrator connections
- 🔄 System-wide benchmark creation
- 🔄 Advanced A/B testing framework
- 🔄 Portfolio Theory optimization
- 🔄 Predictive eROAS modeling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
