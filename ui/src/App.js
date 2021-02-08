import {BrowserRouter, useRoutes} from 'react-router-dom';
import routes from './routes';
import './App.css';

function App() {
    return useRoutes(routes);
}

function AppWrapper() {
    return (
        <BrowserRouter><App/></BrowserRouter>
    )
}

export default AppWrapper;
