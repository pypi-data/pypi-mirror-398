# Private Captcha for Python

[![PyPI version](https://img.shields.io/pypi/v/private-captcha.svg)](https://pypi.org/project/private-captcha/) ![CI](https://github.com/PrivateCaptcha/private-captcha-py/actions/workflows/ci.yml/badge.svg)

Official Python client for Private Captcha API

<mark>Please check the [official documentation](https://docs.privatecaptcha.com/docs/integrations/python/) for the in-depth and up-to-date information.</mark>

## Quick Start

- Install `private-captcha` package
    ```bash
    pip install private-captcha
    ```
- Instantiate the `Client` class and call `verify()` method to verify the solution
    ```python
    from private_captcha import Client
    
    # Initialize the client with your API key
    client = Client(api_key="your-api-key-here")
    
    # Verify a captcha solution
    try:
        result = client.verify(solution="user-solution-from-frontend")
        if result.ok():
            print("Captcha verified successfully!")
        else:
            print(f"Verification failed: {result}")
    except Exception as e:
        print(f"Error: {e}")
    ```
- Integrate with Flask or Django using `client.verify_request()` helper

## Requirements

- Python 3.9+
- No external dependencies (uses only standard library)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues with this Python client, please open an issue on GitHub.
For Private Captcha service questions, visit [privatecaptcha.com](https://privatecaptcha.com).
