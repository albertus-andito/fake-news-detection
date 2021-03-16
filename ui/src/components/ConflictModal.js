import RemoveModal from "./RemoveModal";
import {Button, Modal, Table, Typography} from "antd";
import {useState} from 'react';
import {tripleColumns} from "../utils";

function ConflictModal({ conflict, algorithm }) {
    const [isModalVisible, setIsModalVisible] = useState(false);

    const showModal = () => {
        setIsModalVisible(true);
    };

    const handleOk = () => {
        setIsModalVisible(false);
    };

    const handleCancel = () => {
        setIsModalVisible(false);
    };

    const action = [{
            title: 'Action',
            dataIndex: 'result',
            key: 'result',
            shouldCellUpdate: () => {
                return true;
            },
            render: (value, row) => {
                console.log(row)
                return <RemoveModal triple={{subject: row.subject, relation: row.relation, objects: row.objects}}
                        algorithm={algorithm}/>
            }
        }]

    return (
        <>
            <Button type='primary' onClick={showModal} style={{'backgroundColor': 'red'}}>
                See Conflict
            </Button>
            <Modal title='Conflict' visible={isModalVisible} onOk={handleOk} onCancel={handleCancel} width={1000}>
                <Typography.Title level={5}>Triples in Knowledge Graph</Typography.Title>
                <Table dataSource={conflict} columns={[...tripleColumns, ...action]}
                       pagination={{hideOnSinglePage: true}}/>
            </Modal>
        </>
    );
}

export default ConflictModal;