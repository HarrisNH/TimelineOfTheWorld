# Timeline of the World

This is a small Dash application that displays a timeline of historical events stored in a SQLite database. You can add, edit and link events directly from the UI.

## Running the app

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Patch versions are pinned for reproducible test runs.
2. (Optional) specify a custom database path via the `EVENTS_DB_FILE` environment variable or the `--db` command line option.
3. Start the server:
   ```bash
   python src/app.py
   ```
   or
   ```bash
   python src/app.py --db /path/to/events.db
   ```

On first run a new database will be created and seeded with a few example events.

## Tests

Run the automated tests with:

```bash
pytest
```
