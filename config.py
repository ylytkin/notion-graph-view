from pathlib import Path

from myutils.json import load_json_or_create

root_dir = Path(__file__).parent.resolve()

db_fpath = root_dir / 'db.sqlite'
db_url = 'sqlite:///' + db_fpath.as_posix()

config_fpath = root_dir / 'config.json'

graph_fpath = root_dir / 'graph.html'


def get_token() -> str:
    conf = load_json_or_create(config_fpath, factory=dict)
    
    try:
        return conf['token']

    except KeyError:
        raise RuntimeError(f'file "{config_fpath.as_posix()}" has invalid structure or does not exist')
