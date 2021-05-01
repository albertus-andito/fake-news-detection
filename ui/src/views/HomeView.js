import {Card, Typography} from 'antd';

function HomeView() {
    return(
        <Card>
            <Typography.Title style={{ textAlign: 'center' }}>SAFaC</Typography.Title>
            <Typography.Title level={2} style={{ textAlign: 'center' }}>
                Welcome to Semi Automated Fact Checker
            </Typography.Title>
            <Typography.Title level={5} style={{ textAlign: 'center' }}>
                This is a web app that helps trained human verifier to fact-check news and identify fake news.
                <br />
                Please navigate through the menu pages to start fact-checking and updating the knowledge graph.
                <br />
                <br />
            </Typography.Title>
        </Card>
    )
}

export default HomeView;