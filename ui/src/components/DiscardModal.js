import {ExclamationCircleOutlined} from "@ant-design/icons";
import {Button, Modal, Table} from "antd";
import {useEffect, useState} from 'react';
import {showErrorNotification, tripleColumns} from "../utils";
import axios from "axios";

const { confirm } = Modal;

function DiscardModal({ triple, source, sentence, tripleKey, data, setData }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        setVisible(true);
    }, [triple])

    const showModal = () => confirm({
        title: 'Are you sure you want to discard this triple?',
        icon: <ExclamationCircleOutlined />,
        content: <Table dataSource={[triple]} columns={tripleColumns} pagination={{hideOnSinglePage: true}} scroll={{x: true}} />,
        width: 1000,
        okText: 'Yes',
        okType: 'danger',
        onOk() {
            return axios.delete('/kgu/article-triples/pending/', {data: [{
                    source: source,
                    triples: [{
                        sentence: sentence,
                        triples: [{
                            added: false,
                            ...triple
                        }]
                    }]
                }]})
                .then((res) => {
                    setVisible(false);
                    console.log(tripleKey);
                    const remainingData = data.filter(item => item.key !== tripleKey);
                    setData(remainingData);
                })
                .catch((error) => {
                    showErrorNotification(error.response.data);
                })
            }
    });
    return(<>
        {visible && <Button type='primary' onClick={showModal} style={{'backgroundColor': 'red'}}>
            Discard Triple
        </Button>}
        {!visible && 'Triple discarded'}
    </>)
}

export default DiscardModal;