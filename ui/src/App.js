import {BrowserRouter, useRoutes} from 'react-router-dom';
import routes from './routes';
import './App.css';
import axios from 'axios';

function App() {
    axios.defaults.baseURL = 'http://localhost:5000';
    return useRoutes(routes);
}

function AppWrapper() {
    return (
        <BrowserRouter><App/></BrowserRouter>
    )
}

export default AppWrapper;
