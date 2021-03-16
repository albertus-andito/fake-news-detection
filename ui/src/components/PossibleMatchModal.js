import RemoveModal from "./RemoveModal";
import {Button, Modal, Table, Typography} from "antd";
import {useState} from 'react';
import {tripleColumns} from "../utils";

function PossibleMatchModal({ possibleMatches, algorithm }) {
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
            <Button type='primary' onClick={showModal} style={{'backgroundColor': 'green'}}>
                See Possible Matches
            </Button>
            <Modal title='Possible Matches' visible={isModalVisible} onOk={handleOk} onCancel={handleCancel} width={1000}>
                <Typography.Title level={5}>Triples in Knowledge Graph</Typography.Title>
                <Table dataSource={possibleMatches} columns={[...tripleColumns, ...action]}
                       pagination={{hideOnSinglePage: true}}/>
            </Modal>
        </>
    );
}

export default PossibleMatchModal;