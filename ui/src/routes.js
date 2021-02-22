import React from 'react';
import AppLayout from "./layouts";
import HomeView from "./views/HomeView";
import FactCheckerView from "./views/FactCheckerView";
import ArticleKnowledgeView from "./views/ArticleKnowledgeView";
import EntityExplorerView from "./views/EntityExplorerView";
import AddOwnKnowledgeView from "./views/AddOwnKnowledgeView";
// import { Navigate,  } from 'react-router-dom';

const routes = [
    {
        path: '/',
        element: <AppLayout />,
        children: [
            { path: 'fact-checker', element: <FactCheckerView />},
            { path: 'article-knowledge', element: <ArticleKnowledgeView />},
            { path: 'own-knowledge', element: <AddOwnKnowledgeView />},
            { path: 'entity-explorer', element: <EntityExplorerView />},
            { path: '/', element: <HomeView />},
        ]
    }
];

export default routes;