from .kgupdater import KnowledgeGraphUpdater


def main():
    """
    A runner for the Knowledge Graph Updater to keep extracting triples from new scraped articles.
    """
    kgu = KnowledgeGraphUpdater()
    while True:
        kgu.update_missed_knowledge()


if __name__ == '__main__':
    main()
