import os
import tempfile
import importlib
import sys
sys.path.append('src')
import db
import dash

# Prevent register_page from executing when importing the module
dash.register_page = lambda *a, **k: None
from src.pages import event_detail


def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    os.environ['EVENTS_DB_FILE'] = tmp.name
    importlib.reload(db)
    db.init_db()
    importlib.reload(event_detail)
    return tmp.name


def test_get_event_by_tag():
    path = setup_temp_db()
    ev = db.get_event_by_tag('Science_Space_Moon_Landing_1969')
    assert ev['name'] == 'Moon Landing'
    os.unlink(path)


def test_layout_contains_links():
    path = setup_temp_db()
    comp = event_detail.layout(tag='Politics_War_World_War_I_1914')
    html_str = str(comp)
    assert 'World War I' in html_str
    assert '/event_detail?tag=Politics_War_World_War_II_1939' in html_str
    assert 'event-detail-select' in html_str
    os.unlink(path)
