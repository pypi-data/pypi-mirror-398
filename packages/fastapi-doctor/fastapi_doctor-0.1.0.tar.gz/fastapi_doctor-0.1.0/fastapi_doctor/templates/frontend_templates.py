"""
Frontend module templates: index.html, visual.py, root_route.py
"""


def get_templates_init_template() -> str:
    """Return the __init__.py template for the templates module."""
    return '''\
from .root_route import router as root_route

__all__ = ["root_route"]
'''


def get_root_route_template() -> str:
    """Return the root_route.py template for the home page route."""
    return '''\
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templates.visual import templates

router = APIRouter(prefix="")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )
'''


def get_visual_template() -> str:
    """Return the visual.py template for Jinja2 templates configuration."""
    return '''\
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/templates")
'''


def get_index_html_template() -> str:
    """Return the index.html template for the home page."""
    return '''\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FastAPI Server | Online</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
    href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap"
    rel="stylesheet"
    />
</head>
<body
    style="
    margin: 0;
    padding: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Syne', sans-serif;
    background: linear-gradient(
        135deg,
        #0a0a0f 0%,
        #1a1a2e 50%,
        #0f0f1a 100%
    );
    overflow: hidden;
    position: relative;
    "
>
    <!-- Animated background orbs -->
    <div
    style="
        position: absolute;
        width: 400px;
        height: 400px;
        background: radial-gradient(
        circle,
        rgba(0, 255, 136, 0.15) 0%,
        transparent 70%
        );
        border-radius: 50%;
        top: -100px;
        right: -100px;
        animation: float 8s ease-in-out infinite;
    "
    ></div>
    <div
    style="
        position: absolute;
        width: 300px;
        height: 300px;
        background: radial-gradient(
        circle,
        rgba(255, 107, 53, 0.1) 0%,
        transparent 70%
        );
        border-radius: 50%;
        bottom: -50px;
        left: -50px;
        animation: float 10s ease-in-out infinite reverse;
    "
    ></div>
    <div
    style="
        position: absolute;
        width: 200px;
        height: 200px;
        background: radial-gradient(
        circle,
        rgba(0, 210, 255, 0.08) 0%,
        transparent 70%
        );
        border-radius: 50%;
        top: 50%;
        left: 20%;
        animation: float 6s ease-in-out infinite;
    "
    ></div>

    <!-- Main content -->
    <div
    style="
        text-align: center;
        z-index: 10;
        padding: 60px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        backdrop-filter: blur(20px);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        animation: fadeIn 1s ease-out;
    "
    >
    <!-- Status indicator -->
    <div
        style="
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 20px;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 50px;
        margin-bottom: 40px;
        animation: pulse 2s ease-in-out infinite;
        "
    >
        <span
        style="
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            box-shadow: 0 0 20px #00ff88;
            animation: blink 1.5s ease-in-out infinite;
        "
        ></span>
        <span
        style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: #00ff88;
            text-transform: uppercase;
            letter-spacing: 2px;
        "
        >Server Online</span
        >
    </div>

    <!-- Logo/Icon -->
    <div
        style="
        width: 100px;
        height: 100px;
        margin: 0 auto 30px;
        background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
        border-radius: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 20px 40px rgba(0, 255, 136, 0.3);
        animation: rotateIn 0.8s ease-out;
        "
    >
        <svg
        width="50"
        height="50"
        viewBox="0 0 24 24"
        fill="none"
        style="filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))"
        >
        <path
            d="M13 3L4 14h7l-1 7 9-11h-7l1-7z"
            fill="#0a0a0f"
            stroke="#0a0a0f"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
        />
        </svg>
    </div>

    <!-- Title -->
    <h1
        style="
        font-size: 48px;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 15px 0;
        letter-spacing: -1px;
        text-shadow: 0 4px 30px rgba(0, 255, 136, 0.3);
        "
    >
        FastAPI
    </h1>

    <p
        style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        color: rgba(255, 255, 255, 0.5);
        margin: 0 0 40px 0;
        letter-spacing: 1px;
        "
    >
        High-performance API server ready to handle requests
    </p>

    <!-- Stats/Info boxes -->
    <div
        style="
        display: flex;
        gap: 20px;
        justify-content: center;
        flex-wrap: wrap;
        "
    >
        <div
        style="
            padding: 20px 30px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            transition: all 0.3s ease;
        "
        >
        <div
            style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.4);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            "
        >
            Status
        </div>
        <div style="font-size: 20px; font-weight: 700; color: #00ff88">
            Running
        </div>
        </div>
        <div
        style="
            padding: 20px 30px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
        "
        >
        <div
            style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.4);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            "
        >
            Framework
        </div>
        <div style="font-size: 20px; font-weight: 700; color: #ffffff">
            FastAPI
        </div>
        </div>
        <div
        style="
            padding: 20px 30px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
        "
        >
        <div
            style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.4);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
            "
        >
            API Docs
        </div>
        <a
            href="/docs"
            style="
            font-size: 20px;
            font-weight: 700;
            color: #00d4ff;
            text-decoration: none;
            "
            >/docs</a
        >
        </div>
    </div>

    <!-- Footer -->
    <p
        style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.25);
        margin: 50px 0 0 0;
        "
    >
        Powered by Python & Uvicorn
    </p>
    </div>

    <style>
    @keyframes float {
        0%,
        100% {
        transform: translateY(0px) scale(1);
        }
        50% {
        transform: translateY(-30px) scale(1.05);
        }
    }
    @keyframes fadeIn {
        from {
        opacity: 0;
        transform: translateY(30px);
        }
        to {
        opacity: 1;
        transform: translateY(0);
        }
    }
    @keyframes pulse {
        0%,
        100% {
        transform: scale(1);
        }
        50% {
        transform: scale(1.02);
        }
    }
    @keyframes blink {
        0%,
        100% {
        opacity: 1;
        }
        50% {
        opacity: 0.5;
        }
    }
    @keyframes rotateIn {
        from {
        opacity: 0;
        transform: rotate(-180deg) scale(0);
        }
        to {
        opacity: 1;
        transform: rotate(0deg) scale(1);
        }
    }
    </style>
</body>
</html>
'''

