# Gatsbie Python SDK

Official Python SDK for the [Gatsbie Captcha API](https://gatsbie.io).

## Installation

```bash
pip install gatsbie
```

## Quick Start

```python
import gatsbie

client = gatsbie.Client("gats_your_api_key")

# Solve a Turnstile challenge
response = client.solve_turnstile(
    gatsbie.TurnstileRequest(
        proxy="http://user:pass@proxy:8080",
        target_url="https://example.com",
        site_key="0x4AAAAAAABS7TtLxsNa7Z2e",
    )
)

print(response.solution.token)
```

## Supported Captcha Types

- **Datadome** - Device check and slider
- **reCAPTCHA v3** - Including enterprise
- **Akamai** - Bot management
- **Vercel** - Bot protection
- **Shape** - Antibot
- **Cloudflare Turnstile** - Turnstile challenges
- **Cloudflare WAF** - WAF challenges
- **PerimeterX** - Invisible challenges

## Error Handling

```python
try:
    response = client.solve_turnstile(request)
except gatsbie.APIError as e:
    if e.is_auth_error():
        print("Check your API key")
    elif e.is_insufficient_credits():
        print("Add more credits")
    elif e.is_solve_failed():
        print("Solve failed, try again")
```

## License

MIT
