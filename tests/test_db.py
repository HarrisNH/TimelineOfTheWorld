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

def test_update_event_fields():
    path = setup_temp_db()
    db.insert_event('Cat','Topic','First','Country','2000-01-01',None,'','tag1','','')
    db.insert_event('Cat','Topic','Second','Country','2000-01-02',None,'','tag2','','')
    ev = db.get_event_by_tag('tag1')
    db.update_event(ev['id'], name='Updated', affects='tag2')
    updated = db.get_event_by_tag('tag1')
    assert updated['name'] == 'Updated'
    assert updated['affects'] == 'tag2'
    os.unlink(path)


def test_delete_event_removes_relationships():
    path = setup_temp_db()
    db.insert_event('Cat','Topic','First','Country','2000-01-01',None,'','tag1','','tag2')
    db.insert_event('Cat','Topic','Second','Country','2000-01-02',None,'','tag2','tag1','')
    e1 = db.get_event_by_tag('tag1')
    db.delete_event(e1['id'])
    assert db.get_event_by_tag('tag1') is None
    e2 = db.get_event_by_tag('tag2')
    assert 'tag1' not in (e2['affected_by'] or '')
    os.unlink(path)
