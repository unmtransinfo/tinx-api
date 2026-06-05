# TIN-X API

This is the backend API for TIN-X.

TIN-X (Target Importance and Novelty eXplorer) is an interactive visualization tool for
illuminating associations between diseases and potential drug targets and is publicly available
via <https://datascience.unm.edu/tin-x/>. TIN-X uses natural language processing to identify disease
and protein mentions within PubMed content using previously published tools for named entity
recognition (NER) of gene/protein and disease names.

See also the repo [TIN-X UI](https://github.com/unmtransinfo/tinx-ui).

## References

- "TIN-X version 3: update with expanded dataset and modernized architecture for enhanced illumination of understudied targets", Vincent T. Metzger, Daniel C. Cannon, Jeremy J. Yang, Stephen L. Mathias, Cristian G. Bologa, Anna Waller, Stephan C. Schürer, Dušica Vidović, Keith J. Kelleher, Timothy K. Sheils, Lars Juhl Jensen, Christophe G. Lambert, Tudor I. Oprea, Jeremy S. Edwards, [PeerJ 12:e17470, https://doi.org/10.7717/peerj.17470](https://peerj.com/articles/17470/) (2024).
- "TIN-X: target importance and novelty explorer", Daniel C Cannon, Jeremy J Yang, Stephen L Mathias, Oleg Ursu, Subramani Mani, Anna Waller, Stephan C Schürer, Lars Juhl Jensen, Larry A Sklar, Cristian G Bologa, Tudor I. Oprea, [Bioinformatics, Volume 33, Issue 16, 2601–2603, (2017) https://doi.org/10.1093/bioinformatics/btx200](https://academic.oup.com/bioinformatics/article/33/16/2601/3111842)

## Documentation

In-progress with 2026 maintenance updates, [docs/old](docs/old) has some (outdated) documentation.

## Development

### Launching the Dev Environment

**Prerequisites:**

1. Clone the [tinx-ui](https://github.com/unmtransinfo/tinx-ui) repo alongside this one (i.e. `../tinx-ui/`).
2. Copy `.env.example` to `.env` and fill in credentials:
   ```bash
   cp .env.example .env
   # edit .env — at minimum change MYSQL_ROOT_PASSWORD and DB_PASSWORD
   ```
3. Generate the MySQL tuning config:
   ```bash
   ./tune.sh
   ```
   This reads `DB_CPUS` and `DB_MEMORY` from `.env` and writes `mysql-tuning.cnf`.

**Start all services:**

```bash
docker compose -f docker-compose-dev.yml up --build
```

This brings up four services:

| Service    | Description                                                                                                                                     | Default port  |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| `tinx_ui`  | Dev server for the [TIN-X UI](https://github.com/unmtransinfo/tinx-ui) (hot-reload)                                                             | 8080          |
| `tinx_api` | Django REST API                                                                                                                                 | 8000          |
| `db`       | MySQL 8.0 via [`unmtransinfo/tinx_db`](https://hub.docker.com/r/unmtransinfo/tinx_db) — downloads and restores the TIN-X database on first boot | internal only |
| `solr`     | Solr 6.6.6 search index                                                                                                                         | internal only |

**First-time startup** will take a while as the `db` service downloads and restores the database dump (likely several hours).

**After the database is ready**, rebuild the Solr search index:

```bash
docker compose -f docker-compose-dev.yml exec tinx_api python manage.py rebuild_index
```

> **Note:** The production `docker-compose.yml` is being updated and is not yet ready for use. Use `docker-compose-dev.yml` for now.

### Code Formatting with Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) hooks to automatically format Python code with [isort](https://github.com/PyCQA/isort) and [Black](https://black.readthedocs.io/), and formats Docker Compose files with [DCLint](https://github.com/zavoloklom/docker-compose-linter/tree/main) before each commit.

**Setup (one-time):**

```bash
pre-commit install
```

**Running hooks manually:**

You can run all pre-commit hooks manually without committing:

```bash
pre-commit run --all-files
```

## TODO:

- Get rid of search/list endpoint shown by views
- Fix `/targets/{target_id}/disease/{doid}/` endpoint: Exception Type: KeyError at /targets/2911/diseases/DOID:0060241/
- Cleanup views: make sure all `target_id` params shown as such, `doid` params shown as such. Rename `id` params
