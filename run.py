from src.crawling import update
from src.graph_view import build_graph, display_graph
from config import graph_fpath


def main():
    print('Updating database. This might take some time if running for the first time.')
    update(progress_bar=True)

    print('Building the graph.')
    g = build_graph()
    display_graph(g)

    print(f'Finished. The graph can be viewed via:\n    {graph_fpath.as_posix()}')


if __name__ == '__main__':
    main()
