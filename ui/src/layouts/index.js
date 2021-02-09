import { Layout, Menu } from 'antd';
import { SecurityScanFilled } from '@ant-design/icons';
import { Outlet } from 'react-router';
import {Link} from "react-router-dom";
const { Header, Content, Footer } = Layout;

function AppLayout() {
    return (
        <Layout>
            <Header className='header'>

                <Menu theme='dark' mode='horizontal'>
                    <Menu.Item key='/' className='customclass'>
                        <Link to='/'>
                            <SecurityScanFilled style={{ color: '#ffffff', fontSize: '38px'}} />
                        </Link>

                    </Menu.Item>
                    <Menu.Item key='/fact-checker' className='customclass'>Fact Checker<Link to='/fact-checker'></Link></Menu.Item>
                    <Menu.Item className='customclass'>Knowledge Graph Updater</Menu.Item>
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
            <Footer style={{ textAlign: 'center', color: '#bfbfbf'}}>
                Albertus Andito - University of Sussex - 2021
            </Footer>
        </Layout>
    )
}

export default AppLayout;