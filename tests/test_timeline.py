import os
import tempfile
import importlib
import sys
sys.path.append('src')
import db
import types
import dash

# Prevent register_page from failing when importing timeline
dash.register_page = lambda *a, **k: None
from src.pages import timeline


def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    os.environ['EVENTS_DB_FILE'] = tmp.name
    importlib.reload(db)
    db.init_db()
    importlib.reload(timeline)
    return tmp.name


def test_filter_events_category():
    path = setup_temp_db()
    events = db.get_events()
    filtered = timeline.filter_events(events, categories=['Science'])
    assert all(e['category'] == 'Science' for e in filtered)
    os.unlink(path)
