# Changelog

All notable changes to ACTO will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2025-12-21

### 🚀 Fleet Management System

This release introduces a comprehensive fleet management system for monitoring and organizing your robot fleet.

#### Added

- **Fleet Dashboard**
  - Device overview with proof counts, task history, and activity status
  - Device status indicators (Active, Idle, Inactive based on activity)
  - List and grid view options
  - Search and filter functionality

- **Device Details Modal**
  - Complete activity logs with timestamps
  - Task history overview
  - Health metrics visualization (when available)
  - First and last activity timestamps

- **Device Groups**
  - Create groups with name and description (e.g., "Warehouse A", "Production Line")
  - Assign/unassign devices to groups
  - Filter device list by group
  - Edit and delete groups

- **Device Customization**
  - Rename devices with custom names
  - Custom name badge indicator in device list

- **Health Monitoring**
  - CPU, Memory, Battery, Disk usage tracking
  - Network status and signal strength
  - Temperature and uptime monitoring
  - All metrics are optional (devices only report what they support)
  - Historical health data storage (30 days default)
  - Color-coded health bars (green/yellow/red)

- **Database Persistence**
  - New `fleet_devices` table for custom names and metadata
  - New `fleet_groups` table for group management
  - New `fleet_health` table for health history
  - Automatic schema migration

- **API Endpoints**
  - `GET /v1/fleet` - Fleet overview with devices and groups
  - `GET /v1/fleet/devices/{id}` - Device details with logs
  - `PATCH /v1/fleet/devices/{id}/name` - Rename device
  - `POST /v1/fleet/devices/{id}/health` - Report health metrics
  - `GET /v1/fleet/devices/{id}/health` - Get latest health
  - `GET /v1/fleet/groups` - List all groups
  - `POST /v1/fleet/groups` - Create new group
  - `PATCH /v1/fleet/groups/{id}` - Update group
  - `DELETE /v1/fleet/groups/{id}` - Delete group
  - `POST /v1/fleet/groups/{id}/assign` - Assign devices
  - `POST /v1/fleet/groups/{id}/unassign` - Remove devices

- **New Files**
  - `acto/fleet/__init__.py` - Fleet module export
  - `acto/fleet/models.py` - Database models (DeviceRecord, DeviceGroupRecord, DeviceHealthRecord)
  - `acto/fleet/store.py` - FleetStore with all database operations
  - Updated `acto_server/routers/fleet.py` - Complete API router
  - Updated `static/js/fleet.js` - Frontend module with all features
  - Updated `static/css/fleet.css` - Fleet styles and modals

- **Documentation**
  - Fleet Management section in Dashboard docs
  - Updated README.md with Fleet features
  - Complete API documentation in docs/API.md

#### Technical

- All fleet data tied to user's wallet via JWT authentication
- Health metrics history with automatic cleanup (30 days)
- Responsive design for mobile and desktop

---

## [0.7.4] - 2025-12-21

### 📊 Advanced Statistics & Analytics Dashboard

This release introduces comprehensive analytics features with interactive charts and data export capabilities.

#### Added

- **Interactive Charts (Chart.js)**
  - Activity line chart showing proof submissions over time with gradient fill
  - Request heatmap displaying API usage by hour and day of week
  - Endpoint distribution doughnut chart with color-coded segments
  - Top endpoints horizontal bar chart with HTTP method colors

- **Analytics Dashboard Components**
  - Summary cards (5 KPIs: Proofs, Verifications, Success Rate, API Requests, Active Keys)
  - Endpoint usage details table with visual usage bars
  - Responsive charts grid layout

- **Time Range Selection**
  - Quick filters: 7 days, 30 days, 90 days
  - Custom date range picker with start/end date inputs
  - Automatic chart refresh on period change

- **Data Export**
  - CSV export with summary, timeline, and endpoint data
  - JSON export with full structured data
  - Timestamped filenames for easy organization

- **New Files**
  - `static/js/charts.js` - Chart.js integration and chart creation functions
  - `static/css/analytics.css` - Analytics-specific styling (toolbar, charts, heatmap, tables)

#### Changed

- Extended `wallet-stats.js` with aggregated key statistics, advanced chart rendering, and export functions
- Updated `dashboard.html` with new analytics section and Chart.js CDN

#### Technical

- Chart.js v4.4.1 CDN for core charting functionality
- chartjs-chart-matrix plugin for heatmap visualization
- Consistent color palette across all chart types
- Loading states with spinners for async chart rendering

---

## [0.7.3] - 2025-12-21

### 🔧 Dashboard Key Management Fixes

This release fixes critical issues with API key management in the dashboard.

#### Fixed

- **Key Actions via Event Delegation** - Rename, toggle, and delete buttons now work reliably using event delegation instead of inline onclick handlers with JSON.stringify (prevents HTML attribute parsing issues)
- **Delete Keys Permanently** - Delete button now permanently removes keys from the database instead of just deactivating them
- **Toggle vs Delete Distinction** - Toggle (on/off switch) deactivates keys but keeps them visible; Delete removes them completely
- **Key Statistics Loading** - Fixed 401 errors when viewing key statistics (requires `ACTO_JWT_SECRET_KEY` environment variable on Vercel)

#### Changed

- Improved success checking for delete operations
- Keys list now loads with `include_inactive=true` to show toggled-off keys

#### Important

- **Vercel Users**: Set `ACTO_JWT_SECRET_KEY` environment variable with a fixed secret to prevent JWT validation issues across serverless instances

---

## [0.7.2] - 2025-12-21

### 🏗️ Modular Codebase Refactoring

This release focuses on code organization and maintainability by splitting the codebase into logical, reusable modules.

#### Added

- **Modular JavaScript Architecture** (`static/js/`)
  - `core.js` - Global state, API helpers, alerts, tab navigation
  - `wallet.js` - Wallet connection, multi-wallet support, authentication
  - `clipboard.js` - Copy-to-clipboard functionality
  - `modals.js` - Rename and delete confirmation dialogs
  - `keys.js` - API key CRUD, filtering, pagination, bulk actions
  - `wallet-stats.js` - Wallet statistics and activity charts
  - `playground.js` - API playground endpoint testing

- **Modular CSS Architecture** (`static/css/`)
  - `base.css` - CSS variables, reset, container, cards
  - `buttons.css` - All button variants (primary, secondary, danger, toggle, copy)
  - `forms.css` - Input fields, select, textarea styling
  - `alerts.css` - Notification alerts, status badges
  - `modals.css` - Wallet, rename, delete modal styles
  - `keys.css` - Key list, search, filter, pagination
  - `stats.css` - Statistics grid, activity charts, breakdowns
  - `playground.css` - API playground, response display
  - `fleet.css` - Fleet device management
  - `balance.css` - Insufficient balance screen
  - `responsive.css` - Mobile and tablet adaptations

- **Backend Router Modules** (`acto_server/routers/`)
  - `auth.py` - Wallet authentication, JWT endpoints
  - `keys.py` - API key management endpoints
  - `proofs.py` - Proof submission, verification, search
  - `access.py` - Token gating, access control
  - `stats.py` - Wallet statistics endpoints
  - `fleet.py` - Fleet management endpoints

#### Changed

- Dashboard now loads modular JS/CSS instead of monolithic files
- Better separation of concerns for easier maintenance
- Improved code reusability across modules
- Smaller file sizes for faster development iteration

#### Benefits

- ✅ Better maintainability - each module has clear responsibility
- ✅ Easier development - changes in one area don't affect others
- ✅ Reusability - modules can be imported individually
- ✅ Readability - smaller files are easier to understand
- ✅ Team collaboration - fewer merge conflicts

---

## [0.7.1] - 2025-12-21

### 🔧 Fleet Improvements

#### Changed
- Fleet data now uses JWT authentication (wallet-based) instead of API key
- Moved fleet code to separate `fleet.js` module for better code organization
- New `/v1/fleet` endpoint that returns fleet data tied to wallet session

#### Fixed
- Fleet tab now correctly loads devices without requiring an API key

---

## [0.7.0] - 2025-12-21

### 🚀 Fleet Management & Helius RPC Integration

#### Added

- **Fleet Tab**: New dashboard section to monitor your robot fleet
  - Overview statistics (active devices, total devices, proofs, tasks)
  - Device list with individual stats
  - Online/offline status indicators
  - Last activity timestamps
- **Helius RPC Support**: Better rate limits for Solana token balance checks
  - Set `ACTO_HELIUS_API_KEY` for automatic Helius integration
  - Falls back to public RPC if not configured
- **Site Logo**: Added ACTO logo to dashboard header

#### Changed

- Token balance check now happens at wallet connection (not just API calls)
- Insufficient balance shows dedicated screen with clear messaging
- Improved RPC configuration flexibility

#### Fixed

- Fixed token mint address consistency across configuration files
- Fixed Pydantic settings property issue for RPC URL

---

## [0.6.0] - 2025-12-20

### 🎉 Major Release: Dashboard 2.0 & Multi-Wallet Support

This release brings a completely revamped dashboard experience with multi-wallet support, an interactive API playground, and comprehensive wallet statistics.

### Added

#### Dashboard Features
- **Multi-Wallet Support**: Connect with Phantom, Solflare, Backpack, Glow, or Coinbase Wallet
- **API Playground**: Test API endpoints directly in your browser with live responses
- **Wallet Statistics Dashboard**: 
  - Proofs submitted counter
  - Total verifications with success rate
  - Activity timeline (last 30 days)
  - Breakdown by robot and task type
- **API Key Management**: Create, view, and delete API keys with usage statistics
- **Session Persistence**: Auto-reconnect wallet on page reload

#### API Endpoints
- `POST /v1/proofs/search` - Search and filter proofs with pagination
  - Filter by task_id, robot_id, run_id, signer_public_key
  - Date range filtering (created_after, created_before)
  - Full-text search across metadata
  - Configurable sorting and pagination
- `POST /v1/verify/batch` - Batch verify multiple proofs in a single request
  - Reduces network latency for bulk operations
  - Returns individual results with summary statistics
- `GET /v1/stats/wallet/{address}` - Get comprehensive wallet statistics
  - Proof submission counts
  - Verification statistics with success rates
  - Activity timeline
  - Breakdown by robot and task

### Changed
- Improved error handling with user-friendly messages
- Better session management with JWT token persistence
- Updated documentation with new endpoint examples

### Fixed
- Fixed infinite loop in documentation JS module
- Fixed race condition causing spurious authentication errors
- Fixed API key not being removed from localStorage when deleted
- Fixed verification statistics not counting correctly (endpoint key mismatch)
- Fixed auto-logout issue when switching dashboard tabs

---

## [0.5.23] - 2025-12-19

### Added
- Proof Search & Filter API endpoint
- Batch Verification API endpoint
- Wallet Statistics API endpoint

---

## [0.5.22] - 2025-12-18

### Added
- Initial dashboard with wallet connection
- API key creation and management
- Basic proof submission and verification

---

## [0.4.0] - 2025-12-01

### Added
- OAuth2/JWT authentication support
- Role-Based Access Control (RBAC)
- Audit logging with multiple backends
- Encryption at rest (AES-128)
- TLS/SSL support
- Secrets management (Vault, AWS)
- PII detection and masking
- Signing key rotation

---

## [0.3.0] - 2025-11-15

### Added
- Interactive CLI mode
- Shell completion (bash, zsh, fish, PowerShell)
- Configuration file support
- Async/await operations
- Context managers for registry
- Jupyter notebook examples

---

## [0.2.0] - 2025-11-01

### Added
- Token gating module (Solana SPL)
- Proof anchoring (Solana Memo)
- Pipeline system
- API key authentication
- Rate limiting middleware
- Reputation scoring
- Prometheus metrics

---

## [0.1.0] - 2025-10-15

### Added
- Initial release
- Proof creation and verification
- SQLite registry
- FastAPI server
- CLI tools

