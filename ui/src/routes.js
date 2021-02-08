import React from 'react';
import AppLayout from "./layouts";
import HomeView from "./views/HomeView";
import FactCheckerView from "./views/FactCheckerView";
// import { Navigate,  } from 'react-router-dom';

const routes = [
    {
        path: '/',
        element: <AppLayout />,
        children: [
            { path: 'fact-checker', element: <FactCheckerView />},
            { path: '/', element: <HomeView />},
        ]
    }
];

export default routes;