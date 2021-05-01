import { Layout, Menu } from 'antd';
import { SecurityScanFilled } from '@ant-design/icons';
import { Outlet } from 'react-router';
import { Link } from 'react-router-dom';
const { Header, Content, Footer } = Layout;
const { SubMenu } =  Menu;

function AppLayout() {
    return (
        <Layout>
            <Header className='header'>

                <Menu theme='dark' mode='horizontal'>
                    <Menu.Item key='/'>
                        <Link to='/'>
                            <SecurityScanFilled style={{ color: '#ffffff', fontSize: '38px'}} />
                        </Link>

                    </Menu.Item>
                    <Menu.Item key='/fact-checker'>Fact Checker<Link to='/fact-checker'></Link></Menu.Item>
                    <SubMenu key='kgu-submenu' title="Knowledge Graph Updater">
                        <Menu.Item key='/article-knowledge'>
                            Pending Article Knowledge<Link to='/article-knowledge'></Link>
                        </Menu.Item>
                        <Menu.Item key='/new-article'>
                            Add New Article<Link to='/new-article'></Link>
                        </Menu.Item>
                        <Menu.Item key='/own-knowledge'>
                            Add Own Knowledge<Link to='/own-knowledge'></Link>
                        </Menu.Item>
                    </SubMenu>

                    <Menu.Item key='/entity-explorer'>Entity Explorer<Link to='/entity-explorer'></Link></Menu.Item>
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
                <a href="https://albertus-andito.com/" style={{color: '#ebd7fa'}}>
                    Albertus Andito
                </a> - <a href="https://sussex.ac.uk" style={{color: '#ebd7fa'}}>University of Sussex</a> - 2021
            </Footer>
        </Layout>
    )
}

export default AppLayout;