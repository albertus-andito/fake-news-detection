import axios from "axios";
import React, {useState, useEffect} from "react";
import {ExclamationCircleOutlined} from "@ant-design/icons";
import {Button, Modal, Table} from "antd";
import {showErrorNotification, tripleColumns} from "../utils";

const { confirm } = Modal;

function RemoveModal({ triple, algorithm }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        let url = '/fc/exact/fact-check/triples/';
        if (algorithm === 'non-exact') {
            url += 'transitive/';
        }
        axios.post(url, [triple])
             .then((res) => {
                 console.log(res);
                 if(res.data.triples[0].result === 'exists') {
                     setVisible(true)
                 } else if (res.data.triples[0].result === 'none') {
                     setVisible(false)
                 }
             })
    }, [triple])

    const showModal = () => confirm({
        title: 'Do you want to remove this triple from the knowledge graph?',
        icon: <ExclamationCircleOutlined />,
        content: <Table dataSource={[triple]} columns={tripleColumns} pagination={{hideOnSinglePage: true}} scroll={{x: true}} />,
        width: 1000,
        okType: 'danger',
        okText: 'Yes',
        onOk() {
            return axios.delete('/kgu/triples/', {data: triple})
                        .then((res) => {
                            setVisible(false);
                        }).catch((error) => {
                            showErrorNotification(error.response.data);
                        })
        }
    });
    return(<>
        {visible && <Button type='primary' onClick={showModal} style={{'backgroundColor': 'red'}}>
            Remove from Knowledge Graph
        </Button>}
        {!visible && 'Removed from Knowledge Graph'}
    </>);
}

export default RemoveModal;