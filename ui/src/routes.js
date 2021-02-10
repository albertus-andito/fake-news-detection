import React from 'react';
import AppLayout from "./layouts";
import HomeView from "./views/HomeView";
import FactCheckerView from "./views/FactCheckerView";
import KnowledgeGraphUpdaterView from "./views/KnowledgeGraphUpdaterView";
// import { Navigate,  } from 'react-router-dom';

const routes = [
    {
        path: '/',
        element: <AppLayout />,
        children: [
            { path: 'fact-checker', element: <FactCheckerView />},
            { path: 'knowledge-graph-updater', element: <KnowledgeGraphUpdaterView />},
            { path: '/', element: <HomeView />},
        ]
    }
];

export default routes;