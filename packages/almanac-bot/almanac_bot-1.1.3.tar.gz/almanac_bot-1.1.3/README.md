# Almanac Bot

[![PyPi package](https://img.shields.io/pypi/v/almanac-bot.svg)](https://pypi.python.org/pypi/almanac-bot)
[![Docker Hub](https://img.shields.io/docker/v/logoff/almanac-bot?label=Docker%20Hub)](https://hub.docker.com/r/logoff/almanac-bot)

A Twitter bot that tweets historical events (ephemeris) on their anniversary dates. Each day, it finds events that happened on that calendar date (any year) and tweets them with localized text.

## Features

- Tweets historical events on their anniversary (month+day matching)
- Supports multiple events per day
- Template variables: `${date}` (localized) and `${years_ago}` (calculated)
- Idempotency: won't tweet the same event twice on the same day
- Dry-run mode for testing without sending tweets
- Stateless execution triggered by external scheduler (Ofelia)

## Dependencies

- [Docker](https://www.docker.com/)
- [Python 3.13](https://www.python.org/)
- [PostgreSQL 17.3+](https://www.postgresql.org/)
- [just](https://just.systems/) (optional, for convenience commands)

## Quick Start

### 1. Create configuration

```sh
cp config.ini.default config.ini
```

Fill in the Twitter API credentials and other settings:

```ini
[language]
locale=ca_ES  # or en_US, es_ES, etc.

[twitter]
bearer_token=...
consumer_key=...
consumer_secret=...
access_token_key=...
access_token_secret=...

[postgresql]
user=almanac
password=almanac
hostname=postgres
database=almanac
```

### 2. Launch with Docker Compose

```sh
just docker-up
# or: docker compose up -d
```

This starts:

- **postgres**: PostgreSQL database
- **almanac-bot**: The bot container (kept alive for scheduled execution)
- **ofelia**: Scheduler that triggers the bot daily at 8:00 AM

### 3. Load ephemeris data

```sh
just docker-load-data
# or: docker exec -it almanac-bot uv run python -m typer almanacbot.data_loader run
```

CSV format (`init_db.csv`):

```csv
date;text;location
1899-11-29 12:00 Europe/Madrid;El ${date}, avui fa ${years_ago} anys...;(41.38,2.17)
```

## Usage

### Manual execution

```sh
# Run once (will tweet if there are events for today)
just docker-run

# Dry-run mode (shows what would be tweeted without sending)
just docker-dry-run
```

### Scheduled execution

The bot is automatically triggered by Ofelia at 8:00 AM daily. Check the schedule in `compose.yaml`:

```yaml
labels:
  ofelia.job-exec.almanac.schedule: "0 0 8 * * *"  # Daily at 8 AM
```

### View logs

```sh
just docker-logs            # Bot logs
just docker-logs-scheduler  # Scheduler logs (follow mode)
```

## Development

### Run tests

```sh
just test            # Unit tests
just test-cov        # With coverage report
just test-integration  # Integration tests (starts postgres automatically)
```

### Linting

```sh
just lint      # Check for issues
just lint-fix  # Auto-fix issues
```

### Build Docker image

```sh
just docker-build
```

## Database

### Schema

The ephemeris table stores historical events:

```sql
CREATE TABLE almanac.ephemeris (
    id serial primary key,
    date timestamp with time zone not null,
    text text not null,
    location point default null,
    last_tweeted_at timestamp with time zone default null
);
```

### Clean database

```sh
just docker-clean-db
```

## Just Commands Reference

```sh
just help  # Show all available commands
```

| Command                      | Description                |
| ---------------------------- | -------------------------- |
| `just docker-up`             | Start all services         |
| `just docker-down`           | Stop all services          |
| `just docker-serve`          | Start and follow logs      |
| `just docker-load-data`      | Load ephemeris from CSV    |
| `just docker-run`            | Run bot manually           |
| `just docker-dry-run`        | Run without tweeting       |
| `just docker-logs`           | View bot logs              |
| `just docker-logs-scheduler` | View scheduler logs        |
| `just docker-build`          | Build Docker image         |
| `just docker-clean-db`       | Remove database volume     |
| `just test`                  | Run unit tests             |
| `just test-cov`              | Run tests with coverage    |
| `just test-integration`      | Run integration tests      |
| `just lint`                  | Check code style           |
| `just lint-fix`              | Fix code style             |

## Architecture

```text
                    Ofelia (scheduler)
                           │
                           │ triggers daily at 8 AM
                           ▼
┌─────────────────────────────────────────────────────┐
│                   almanac-bot                       │
│                                                     │
│  1. Query ephemeris for today (month+day match)     │
│  2. Filter out already-tweeted (idempotency)        │
│  3. Tweet each event                                │
│  4. Mark as tweeted (last_tweeted_at)               │
│  5. Exit                                            │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
                      PostgreSQL
```

## Production Deployment (Docker Swarm)

For production deployment on Docker Swarm:

### 1. Create Docker secrets

```sh
# Create secret from your config.ini file
docker secret create almanac_config /path/to/config.ini
```

### 2. Prepare the stack directory

```sh
mkdir -p /path/to/almanac-bot/{init_db,postgres}

# Copy the database init script (creates schema on first run)
cp postgres/init-ephemeris-db.sh /path/to/almanac-bot/postgres/

# Copy your ephemeris CSV data
cp your_data.csv /path/to/almanac-bot/init_db/init_db.csv
```

### 3. Configure the stack

```sh
# Copy the example and adjust paths
cp docker-compose.swarm.example.yaml /path/to/almanac-bot/docker-compose.swarm.yaml

# Edit the file and update volume paths to match your directory
```

### 4. Deploy

```sh
docker stack deploy -c /path/to/almanac-bot/docker-compose.swarm.yaml almanac
```

### 5. Load ephemeris data into database

After the stack is running, load the CSV data into PostgreSQL:

```sh
# Find the bot container
docker ps | grep almanac-bot

# Load the CSV into the database
docker exec <container_id> uv run python -m typer almanacbot.data_loader run
```

## License

MIT
