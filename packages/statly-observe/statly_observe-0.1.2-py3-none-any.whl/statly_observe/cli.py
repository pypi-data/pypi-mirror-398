#!/usr/bin/env python3
"""Statly Observe CLI - Setup and configuration tool."""
import sys
import os
import re

COLORS = {
    'reset': '\033[0m',
    'bright': '\033[1m',
    'dim': '\033[2m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'cyan': '\033[36m',
}


def print_header():
    """Print the Statly ASCII header."""
    c = COLORS
    print()
    print(f"{c['cyan']}{c['bright']}  _____ _        _   _       ")
    print(f"{c['cyan']} / ____| |      | | | |      ")
    print(f"{c['cyan']}| (___ | |_ __ _| |_| |_   _ ")
    print(f"{c['cyan']} \\___ \\| __/ _` | __| | | | |")
    print(f"{c['cyan']} ____) | || (_| | |_| | |_| |")
    print(f"{c['cyan']}|_____/ \\__\\__,_|\\__|_|\\__, |")
    print(f"{c['cyan']}                        __/ |")
    print(f"{c['cyan']}                       |___/ {c['reset']}")
    print()
    print(f"{c['bright']}Statly Observe SDK Setup{c['reset']}")
    print(f"{c['dim']}Error tracking for Python applications{c['reset']}")
    print()


def print_step(num: int, msg: str):
    """Print a numbered step."""
    c = COLORS
    print(f"{c['green']}[{num}]{c['reset']} {msg}")


def detect_framework() -> str | None:
    """Detect Python web framework from installed packages."""
    try:
        import flask
        return 'flask'
    except ImportError:
        pass

    try:
        import django
        return 'django'
    except ImportError:
        pass

    try:
        import fastapi
        return 'fastapi'
    except ImportError:
        pass

    return None


def generate_code(dsn: str, framework: str | None) -> str:
    """Generate setup code based on detected framework."""
    if framework == 'flask':
        return f'''# Add to your Flask application
from flask import Flask
from statly_observe import Statly
from statly_observe.integrations.flask import init_flask

app = Flask(__name__)

# Initialize Statly
Statly.init(
    dsn="{dsn}",
    environment=os.getenv("FLASK_ENV", "development"),
)

# Attach to Flask app
init_flask(app)

@app.route("/")
def index():
    return "Hello World"

# Errors are automatically captured
'''

    if framework == 'django':
        return f'''# 1. Add to settings.py:
MIDDLEWARE = [
    'statly_observe.integrations.django.StatlyMiddleware',
    # ... other middleware (Statly should be first)
]

STATLY_DSN = "{dsn}"
STATLY_ENVIRONMENT = os.getenv("DJANGO_ENV", "development")

# 2. Add to wsgi.py or manage.py:
from statly_observe import Statly
from django.conf import settings

Statly.init(
    dsn=settings.STATLY_DSN,
    environment=settings.STATLY_ENVIRONMENT,
)
'''

    if framework == 'fastapi':
        return f'''# Add to your FastAPI application
from fastapi import FastAPI
from statly_observe import Statly
from statly_observe.integrations.fastapi import init_fastapi

app = FastAPI()

# Initialize Statly
Statly.init(
    dsn="{dsn}",
    environment=os.getenv("ENVIRONMENT", "development"),
)

# Attach to FastAPI app
init_fastapi(app)

@app.get("/")
async def root():
    return {{"message": "Hello World"}}

# Errors are automatically captured
'''

    # Generic setup
    return f'''# Add to your application entry point
from statly_observe import Statly

# Initialize the SDK
Statly.init(
    dsn="{dsn}",
    environment="production",  # or "development", "staging"
    release="1.0.0",  # Your app version
)

# Errors are captured automatically via sys.excepthook

# Manual capture example
try:
    risky_operation()
except Exception as e:
    Statly.capture_exception(e)

# Set user context (after login)
Statly.set_user(
    id="user-123",
    email="user@example.com",
)

# Always close before exit
Statly.close()
'''


def main():
    """Main CLI entry point."""
    c = COLORS
    args = sys.argv[1:]
    command = args[0] if args else None

    if command == 'init':
        print_header()

        print(f"{c['dim']}Get your DSN from: https://statly.live/dashboard/observe/setup{c['reset']}")
        print()

        try:
            dsn = input(f"{c['yellow']}?{c['reset']} Enter your DSN: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if not dsn:
            print(f"{c['yellow']}No DSN provided. Get one at https://statly.live{c['reset']}")
            sys.exit(1)

        # Validate DSN format
        if not re.match(r'^https://[^@]+@statly\.live/.+$', dsn):
            print(f"{c['yellow']}Warning: DSN format looks incorrect.{c['reset']}")
            print(f"{c['dim']}Expected format: https://<api-key>@statly.live/<org-slug>{c['reset']}")

        print()
        print_step(1, "Detecting your framework...")

        framework = detect_framework()
        if framework:
            print(f"   {c['green']}✓{c['reset']} Detected: {c['bright']}{framework}{c['reset']}")
        else:
            print(f"   {c['dim']}No framework detected, using generic setup{c['reset']}")

        print()
        print_step(2, "Generated setup code:")
        print()
        print(f"{c['dim']}{'─' * 50}{c['reset']}")
        print(generate_code(dsn, framework))
        print(f"{c['dim']}{'─' * 50}{c['reset']}")
        print()

        print_step(3, "Next steps:")
        print(f"   {c['dim']}1.{c['reset']} Copy the code above into your application")
        print(f"   {c['dim']}2.{c['reset']} Set your environment variables")
        print(f"   {c['dim']}3.{c['reset']} Trigger a test error to verify")
        print()
        print(f"{c['green']}✓{c['reset']} Setup complete! View errors at {c['cyan']}https://statly.live/dashboard/observe{c['reset']}")
        print()
        print(f"{c['dim']}Documentation: https://docs.statly.live/sdk/python/installation{c['reset']}")
        print()

    else:
        print(f"{c['bright']}Statly Observe CLI{c['reset']}")
        print()
        print("Usage:")
        print(f"  statly-observe init    {c['dim']}Setup Statly in your project{c['reset']}")
        print(f"  python -m statly_observe init")
        print()
        print("Get started at https://statly.live")


if __name__ == '__main__':
    main()
