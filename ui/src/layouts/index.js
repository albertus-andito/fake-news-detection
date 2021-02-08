import { Layout, Menu } from 'antd';
import { SecurityScanFilled } from '@ant-design/icons';
import { Outlet } from 'react-router';
import {Link} from "react-router-dom";

const { Header, Content, Footer } = Layout;

function AppLayout() {
    return (
        <Layout>
            <Header className='header' >
                <Link to='/'>
                    <SecurityScanFilled style={{ color: '#ffffff', fontSize: '38px', margin: '10px 20px 0 0', float: 'left'}} />
                </Link>
                <Menu theme='dark' mode='horizontal' >
                    <Menu.Item key='/fact-checker'>Fact Checker<Link to='/fact-checker'></Link></Menu.Item>
                    <Menu.Item>Knowledge Graph Updater</Menu.Item>
                </Menu>
            </Header>
            <Content style={{
                        margin: '24px 16px',
                        padding: 24,
                        minHeight: '80vh',
                        overflow: 'initial',
                    }}>
                <div className='site-layout-content'>
                    <Outlet />
                </div>
            </Content>
            <Footer style={{ textAlign: 'center', backgroundColor: '#111d2c', color: '#bfbfbf'}}>
                Albertus Andito - University of Sussex - 2021
            </Footer>
        </Layout>
    )
}

export default AppLayout;