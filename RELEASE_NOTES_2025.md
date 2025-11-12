# Release Notes - 2025 Updates

## Version 2025.11.12

### 🎉 Major Features

#### Comprehensive Logging System
- **Added extensive logging throughout the application** for better Docker container monitoring
- All operations now log to stdout with timestamps and log levels (`[INFO]`, `[ERROR]`, `[WARN]`, `[DEBUG]`)
- Startup logging displays full configuration details
- Iteration tracking for both badge and game modes
- Detailed API call logging with request/response information
- Google Sheets operations are fully logged
- State change logging with before/after values
- Discord message send success/failure logging
- Errors logged to stderr for easy filtering

**Benefits:**
- Easy monitoring with `docker logs -f <container-name>`
- Better debugging and troubleshooting
- Clear visibility into what the bot is doing at all times

#### CI/CD Pipeline with GitHub Actions
- **Automated Docker image builds** on every push to `master`/`main`
- **GitHub Container Registry (ghcr.io) integration** - no external secrets needed
- Automatic image tagging:
  - `latest` for default branch
  - Branch names for feature branches
  - Semantic version tags (e.g., `v1.0.0`, `1.0`, `1`)
  - Commit SHA for traceability
- Docker Buildx with GitHub Actions cache for faster builds
- Pull request builds (without pushing)

**Benefits:**
- Zero-configuration CI/CD setup
- Automatic image updates on code changes
- Free container hosting for public repositories
- Better integration with GitHub ecosystem

#### Enhanced Error Handling
- **HTTPS/SSL error handling** for all API calls
- Connection error detection and logging
- Timeout error handling with proper logging
- Request exception handling for all HTTP operations
- Errors logged instead of spamming Discord
- Exponential backoff logging in game mode

**Benefits:**
- More resilient to network issues
- Better error visibility
- Prevents Discord notification spam on transient errors

### 🔧 Improvements

#### Error Handling & Reliability
- Added `requests.exceptions` handling for `SSLError`, `ConnectionError`, `Timeout`, and `RequestException`
- HTTP status code validation with `raise_for_status()`
- Improved error messages with timestamps and context
- Error logging to stderr for easy filtering

#### Configuration & Documentation
- Enhanced startup logging shows all configuration values
- Better visibility into which mode is running (Badge vs Game)
- Configuration validation warnings (e.g., missing WEBHOOK_URL)
- Improved README with GitHub Actions setup instructions

#### Docker Experience
- All logs go to stdout/stderr for proper Docker logging
- Better container monitoring capabilities
- Clear startup banners and status messages

### 📝 Technical Details

#### Logging Format
All logs follow a consistent format:
```
(YYYY-MM-DD HH:MM:SS) [LEVEL] Message
```

Example:
```
(2025-11-12 14:30:45) [INFO] Querying tabletop.events API for badge availability
(2025-11-12 14:30:46) [INFO] Badge availability: 5 of 100 Attendee badges available.
```

#### GitHub Actions Workflow
- **File:** `.github/workflows/docker-build-push.yml`
- **Triggers:** Push to master/main, tags (v*), pull requests, manual dispatch
- **Registry:** `ghcr.io/<username>/bgg-tickets`
- **Authentication:** Uses built-in `GITHUB_TOKEN` (no secrets required)

#### Error Handling Coverage
- `get_game()` - Game API queries
- `get_attendee_badge_availablity()` - Badge API queries
- `send_discord_message()` - Discord webhook calls
- All wrapped with try/except and proper logging

### 🐛 Bug Fixes
- Fixed Discord message spam on API errors
- Improved error recovery in both badge and game modes
- Better handling of missing configuration

### 📚 Documentation Updates
- Added GitHub Actions/CI/CD section to README
- Updated Docker usage examples
- Added logging information
- Improved setup instructions

### 🔄 Migration Notes

#### For Existing Users
1. **Docker Images:** Images are now available at `ghcr.io/<your-username>/bgg-tickets:latest`
2. **Logging:** You can now monitor your container with `docker logs -f <container-name>`
3. **No Breaking Changes:** All existing functionality remains the same, just with better logging

#### For New Users
- Follow the README setup instructions
- No additional secrets needed for GitHub Container Registry
- Enjoy comprehensive logging out of the box

### 🎯 What's Next
- Consider adding structured logging (JSON format) option
- Potential metrics/telemetry integration
- Enhanced retry logic with configurable strategies

---

## Previous Updates (2024)

### Version 2024.11
- Added exponential backoff for error recovery
- Added HTTP timeout configuration
- Fixed timezone handling issues
- Improved error handling in game mode

---

**Full Changelog:** See [GitHub Commits](https://github.com/twoscomp/bgg-tickets/commits/master)

