# Durax Schema

Shared database schema for [Durax](https://github.com/durax-io) - a multi-language durable execution framework.

- [edda](https://github.com/i2y/edda) (Python)
- [romancy](https://github.com/i2y/romancy) (Go)

## Quick Start

### 1. Install dbmate

```bash
# macOS
brew install dbmate

# Linux
curl -fsSL https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64 -o dbmate
chmod +x dbmate && sudo mv dbmate /usr/local/bin/
```

### 2. Run Migration

```bash
# PostgreSQL
DATABASE_URL="postgresql://user:pass@localhost:5432/dbname?sslmode=disable" \
  dbmate -d ./db/migrations/postgresql up

# MySQL
DATABASE_URL="mysql://user:pass@localhost:3306/dbname" \
  dbmate -d ./db/migrations/mysql up

# SQLite
DATABASE_URL="sqlite:./mydb.sqlite" \
  dbmate -d ./db/migrations/sqlite up
```

## Integration as Submodule

```bash
git submodule add https://github.com/durax-io/schema.git schema
git submodule update --init
```

## Other Commands

```bash
dbmate status   # Check migration status
dbmate down     # Rollback latest migration
```

## Documentation

- [Column Values Reference](docs/column-values.md) - Standard values for database columns across all implementations

## License

MIT
