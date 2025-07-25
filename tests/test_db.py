import os
import tempfile
import importlib
import sys
sys.path.append('src')
import db


def setup_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    os.environ['EVENTS_DB_FILE'] = tmp.name
    importlib.reload(db)
    db.init_db()
    return tmp.name


def test_insert_event_unique():
    path = setup_temp_db()
    db.insert_event('Cat', 'Topic', 'Name', 'Country', '2000-01-01', None, '', 'tag1', '', '')
    try:
        db.insert_event('Cat', 'Topic', 'Name2', 'Country', '2000-01-01', None, '', 'tag1', '', '')
    except ValueError:
        pass
    else:
        assert False, 'duplicate tag did not raise'
    os.unlink(path)
