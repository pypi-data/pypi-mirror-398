# Short-Lived Token Rotation

## What It Does

JFrog tokens with longer expiration times take longer to validate. This feature automatically swaps your long-lived base token for short-lived tokens (with shorter expiration) to speed up validation.

**Result:** Faster authentication without changing your base token configuration.

## Basic Behavior

**Without rotation (default):**
- Your base token is used directly for every request

**With rotation enabled:**
- A short-lived token is generated from your base token
- This short-lived token is used for requests (faster validation)
- Tokens auto-refresh in the background before expiration
- If refresh fails, falls back to base token - a request is never blocked for any reason

## Configuration

### Enable Token Rotation

```bash
export JF_USE_SHORT_TOKEN_ROTATION=TRUE
```

### Optional: Cache Base Token Retrieval

```bash
export JF_ACCESS_TOKEN_RELOAD_INTERVAL_SECONDS=60
```

**What it does:** Caches the base token for the specified number of seconds. By default, the base token is fetched per-request.

**When to use:**
- Set it: Base token is cached (faster, but won't pick up token changes during the interval)
- Don't set it: Base token is re-read on every call (slower, but picks up changes immediately)

**Note:** This is separate from rotation - you can use base token caching with or without rotation enabled.

### Tune Rotation Behavior (Advanced)

**`JF_SHORT_TOKEN_ROTATION_INTERVAL_SECONDS`** (default: 1500 = 25 minutes)
How long each short-lived token is used before a refresh is triggered.

**`JF_SHORT_TOKEN_ROTATION_GRACE_PERIOD_SECONDS`** (default: 1500 = 25 minutes)
Grace period on top of the rotation interval. Short-lived tokens have an expiry of (interval + grace period), allowing them to remain usable during background refresh.

**`JF_SHORT_TOKEN_ROTATION_GENERATION_TIMEOUT_SECONDS`** (default: 20 seconds)
Timeout for generating new tokens.
