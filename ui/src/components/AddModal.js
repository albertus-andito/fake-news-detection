import {ExclamationCircleOutlined} from "@ant-design/icons";
import {Button, Modal, Table} from "antd";
import {useEffect, useState} from 'react';
import {showErrorNotification, tripleColumns} from "../utils";
import axios from "axios";

const { confirm } = Modal;

function AddModal({ triple, isArticle, source, sentence }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        setVisible(true);
    }, [triple])

    const showModal = () => confirm({
        title: 'Do you want to add this triple to the knowledge graph?',
        icon: <ExclamationCircleOutlined />,
        content: <Table dataSource={[triple]} columns={tripleColumns} pagination={{hideOnSinglePage: true}} scroll={{x: true}} />,
        width: 1000,
        okText: 'Yes',
        onOk() {
            if (isArticle !== true) {
                return axios.post('/kgu/triples/force/', [triple])
                        .then((res) => {
                            setVisible(false);
                        })
                        .catch((error) => {
                            showErrorNotification(error.response.data);
                        })
            } else {
                return axios.post('/kgu/article-triples/insert/', [{
                        source: source,
                        triples: [{
                            sentence: sentence,
                            triples: [{
                                added: false,
                                ...triple
                            }]
                        }]
                    }])
                    .then((res) => {
                        setVisible(false);
                    })
                    .catch((error) => {
                        showErrorNotification(error.response.data);
                    })
            }

        }
    });
    return(<>
        {visible && <Button type='primary' onClick={showModal} style={{'backgroundColor': 'green'}}>
            Add to Knowledge Graph
        </Button>}
        {!visible && 'Added to Knowledge Graph'}
    </>)
}

export default AddModal;