from kgupdater import KnowledgeGraphUpdater

if __name__ == '__main__':
    kgu = KnowledgeGraphUpdater()
    while True:
        kgu.update_missed_knowledge()