# homelab-telegram-bot

Telegram bot to control the homelab (Proxmox host, VMs/LXCs, Docker
containers) via inline-keyboard menus, restricted to a single allow-listed
chat ID.

## Architecture

- **Proxmox**: controlled via the official REST API (`bot/services/proxmox.py`)
  using a scoped API token for a dedicated `telegram-bot@pve` user — no root
  shell access, no need to run on the hypervisor itself.
- **Docker containers**: controlled via the Portainer API
  (`bot/services/portainer.py`).
- **Bot**: `python-telegram-bot`, long polling, single allow-listed chat ID
  checked on every update (`bot/auth.py`).
- Runs as an unprivileged container, deployed like the other services on
  this homelab (image on GHCR, Watchtower auto-updates it).

```
bot/
├── main.py              entry point: wiring + polling loop
├── config.py            env-var based settings (fails fast if incomplete)
├── logging_config.py    stdout logging setup
├── auth.py              single allow-listed chat ID check
├── services/
│   ├── proxmox.py       Proxmox REST API client
│   └── portainer.py     Portainer API client
└── handlers/
    ├── menu.py          builds the inline keyboards
    └── actions.py       routes button presses, runs the actual actions
```

## Proxmox setup (one-time)

1. **Datacenter → Permissions → Roles → Create**: `TelegramBotRole` with
   `VM.Audit`, `VM.PowerMgmt`, `Sys.Audit`, `Sys.PowerMgmt`.
2. **Datacenter → Permissions → Users → Add**: `telegram-bot@pve`.
3. **Datacenter → Permissions → Add → Permission**: path `/`, user
   `telegram-bot@pve`, role `TelegramBotRole`.
4. **Datacenter → Permissions → API Tokens → Add**: user `telegram-bot@pve`,
   token ID `bot`, **uncheck "Privilege Separation"**. Copy the secret
   immediately — it is shown once.

## Configuration

Copy `.env.example` to `.env` and fill in the real values:

- `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `ALLOWED_CHAT_ID` — your Telegram chat ID
- `PROXMOX_TOKEN_SECRET` — from the API token step above
- `PORTAINER_API_TOKEN` — Portainer → Account → Access Tokens

`.env` is git-ignored; never commit real secrets.

## Running locally

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill it in
venv/bin/python -m bot.main
```

## Deployment

CI (`.github/workflows/docker-publish.yml`) builds the image and pushes it
to `ghcr.io/eljakj/homelab-telegram-bot` on every push to `main`.

On the Docker host, only `docker-compose.yml` and `.env` are needed (not the
full source tree):

```bash
mkdir -p /opt/telegram-bot && cd /opt/telegram-bot
# copy docker-compose.yml and your filled-in .env here
docker compose pull
docker compose up -d
```

The `com.centurylinklabs.watchtower.enable=true` label lets the existing
Watchtower instance pick up new images automatically.
