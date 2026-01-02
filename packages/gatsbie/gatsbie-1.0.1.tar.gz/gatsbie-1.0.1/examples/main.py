"""Example usage of the Gatsbie SDK."""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gatsbie


def main():
    # Get API key from environment
    api_key = os.environ.get("GATSBIE_API_KEY")
    if not api_key:
        print("GATSBIE_API_KEY environment variable is required")
        sys.exit(1)

    # Create client with default options
    client = gatsbie.Client(api_key)

    # Or with custom options:
    # client = gatsbie.Client(
    #     api_key,
    #     timeout=60.0,
    #     base_url="https://custom.api.url",
    # )

    # Check API health
    health = client.health()
    print(f"API Status: {health.status}\n")

    # Example: Solve Turnstile challenge
    solve_turnstile_example(client)

    # Example: Solve Datadome challenge
    # solve_datadome_example(client)

    # Example: Solve reCAPTCHA v3 challenge
    # solve_recaptcha_v3_example(client)

    # Example: Solve Akamai challenge
    # solve_akamai_example(client)


def solve_turnstile_example(client: gatsbie.Client):
    print("Solving Turnstile challenge...")

    try:
        resp = client.solve_turnstile(
            gatsbie.TurnstileRequest(
                proxy="http://user:pass@proxy.example.com:8080",
                target_url="https://example.com/protected-page",
                site_key="0x4AAAAAAABS7TtLxsNa7Z2e",
            )
        )

        print(f"Success! Task ID: {resp.task_id}")
        print(f"Token: {resp.solution.token[:50]}...")
        print(f"User-Agent: {resp.solution.user_agent}")
        print(f"Cost: {resp.cost:.4f} credits")
        print(f"Solve Time: {resp.solve_time:.2f} ms\n")

    except gatsbie.APIError as e:
        handle_error(e)


def solve_datadome_example(client: gatsbie.Client):
    print("Solving Datadome device check...")

    try:
        resp = client.solve_datadome(
            gatsbie.DatadomeRequest(
                proxy="http://user:pass@proxy.example.com:8080",
                target_url="https://www.cma-cgm.com/",
                target_method="GET",
            )
        )

        print(f"Success! Task ID: {resp.task_id}")
        print(f"Datadome Cookie: {resp.solution.datadome[:50]}...")
        print(f"User-Agent: {resp.solution.user_agent}")
        print(f"Cost: {resp.cost:.4f} credits")
        print(f"Solve Time: {resp.solve_time:.2f} ms\n")

    except gatsbie.APIError as e:
        handle_error(e)


def solve_recaptcha_v3_example(client: gatsbie.Client):
    print("Solving reCAPTCHA v3...")

    try:
        resp = client.solve_recaptcha_v3(
            gatsbie.RecaptchaV3Request(
                proxy="http://user:pass@proxy.example.com:8080",
                target_url="https://2captcha.com/demo/recaptcha-v3",
                site_key="6Lcyqq8oAAAAAJE7eVJ3aZp_hnJcI6LgGdYD8lge",
                action="demo_action",
                title="Google reCAPTCHA V3 demo: Sample Form with Google reCAPTCHA V3",
                enterprise=False,
            )
        )

        print(f"Success! Task ID: {resp.task_id}")
        print(f"Token: {resp.solution.token[:50]}...")
        print(f"User-Agent: {resp.solution.user_agent}")
        print(f"Cost: {resp.cost:.4f} credits")
        print(f"Solve Time: {resp.solve_time:.2f} ms\n")

    except gatsbie.APIError as e:
        handle_error(e)


def solve_akamai_example(client: gatsbie.Client):
    print("Solving Akamai challenge...")

    try:
        resp = client.solve_akamai(
            gatsbie.AkamaiRequest(
                proxy="http://user:pass@proxy.example.com:8080",
                target_url="https://shop.lululemon.com/",
                akamai_js_url="https://shop.lululemon.com/WGlx/lc_w/w/vez/w0HNXw/EmubktLXh3Npr6Nab5/TXUGYQ/Lh9aC2xK/H34",
            )
        )

        print(f"Success! Task ID: {resp.task_id}")
        print(f"_abck: {resp.solution.abck[:50]}...")
        print(f"bm_sz: {resp.solution.bm_sz[:50]}...")
        print(f"User-Agent: {resp.solution.user_agent}")
        print(f"Cost: {resp.cost:.4f} credits")
        print(f"Solve Time: {resp.solve_time:.2f} ms\n")

    except gatsbie.APIError as e:
        handle_error(e)


def handle_error(err: gatsbie.APIError):
    print(f"API Error [{err.code}]: {err.message}")
    if err.details:
        print(f"Details: {err.details}")

    # Handle specific error types
    if err.is_auth_error():
        print("Check your API key")
    elif err.is_insufficient_credits():
        print("Please add more credits to your account")
    elif err.is_solve_failed():
        print("The captcha could not be solved, try again")


if __name__ == "__main__":
    main()
