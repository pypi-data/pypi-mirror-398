# Tunnelify

Tunnelify is a Python library to easily create and manage Cloudflare or Localtunnel tunnels.

# Example

```python
from tunnelify import tunnel

# For Cloudflare
url, proc = tunnel(8000, "cloudflare")
print(f"Cloudflare URL: {url}")

# For Localtunnel (without custom subdomain)
url, _ = tunnel(8000, "localtunnel")
print(f"Localtunnel URL: {url}")

# For Localtunnel with custom subdomain
url, _ = tunnel(8000, "localtunnel", "customsub")
print(f"Custom Localtunnel URL: {url}")
```

# Installation

Just:
`pip install tunnelify`

Tunnelify requires Cloudflared package to work.