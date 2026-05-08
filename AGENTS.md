# AGENTS.md

## Project Overview

This repository is for a Python-based Amazon suspicious error-deal alert bot.
The bot's first MVP must run only on mock data and send human-review alerts, not perform purchasing or account automation.

## Non-Negotiable Safety Boundaries

Do not implement or suggest any feature that performs or enables:

- Automatic purchasing or checkout.
- Amazon login automation.
- Cart testing or add-to-cart automation.
- Automatic coupon clipping/clicking.
- CAPTCHA bypass, proxy evasion, anti-bot bypass, or credential automation.
- High-volume scraping, crawling, or behavior that could violate Amazon or third-party service terms.

The bot is an alerting and triage tool only. It should help a human notice potentially interesting deals and manually verify them.

## MVP Scope

For the first implementation phase:

- Use mock deal data only.
- Keep the architecture ready for future data source adapters.
- Send notifications through Telegram Bot.
- Store alert history in SQLite to prevent duplicate alerts.
- Manage configuration through `.env` environment variables.
- Never hardcode real API tokens, bot tokens, chat IDs, or service credentials.

## Future Data Source Priority

When real data sources are added later, implement them in this order:

1. Keepa API.
2. Slickdeals RSS.
3. Reddit API.

Prefer adapter-style modules so each source can be tested independently and disabled safely.

## Target Categories

Focus deal scoring and filtering around:

- Appliances.
- Computer components.
- Computer peripherals.

## Target Keywords

The default keyword set should include:

- monitor
- gaming monitor
- OLED monitor
- SSD
- NVMe
- RAM
- DDR4
- DDR5
- keyboard
- mechanical keyboard
- mouse
- wireless mouse
- headset
- docking station
- USB hub
- robot vacuum
- air purifier
- coffee machine
- TV
- soundbar

## Engineering Guidelines

- Prefer simple, testable Python modules.
- Separate data collection, deal scoring/filtering, alert delivery, and persistence.
- Add unit tests for scoring, duplicate detection, and configuration parsing when implementation begins.
- Keep side effects isolated behind interfaces or small service modules.
- Treat Telegram delivery failures as recoverable errors and log them clearly.
- Use SQLite for local persistence unless a future requirement explicitly changes this.

## Configuration Guidelines

- Read runtime configuration from environment variables, optionally loaded from `.env` during local development.
- Keep `.env` ignored by git.
- Provide examples with placeholder values only if adding sample env files.
- Do not commit secrets.

## Documentation Guidelines

- Update `README.md` whenever setup steps, environment variables, architecture, or scope changes.
- Clearly label mock-only behavior versus future real-source behavior.
- Document safety constraints prominently so future contributors do not add automation that violates the project principles.
