import {Button, Card, Divider, Modal, Table, Tag, Typography} from "antd";
import React, { useState, useEffect } from 'react';
import axios from "axios";
import {convertObjectsToDBpediaLink, convertToDBpediaLink} from "../utils";
import {ExclamationCircleOutlined} from "@ant-design/icons";

const { confirm } = Modal;

const tripleColumns = [
    {
        title: 'Subject',
        dataIndex: 'subject',
        key: 'subject',
        render: convertToDBpediaLink,
    },
    {
        title: 'Relation',
        dataIndex: 'relation',
        key: 'relation',
        render: convertToDBpediaLink,
    },
    {
        title: 'Object',
        dataIndex: 'objects',
        key: 'object',
        render: convertObjectsToDBpediaLink,
    },
];

function ConflictModal({ conflict }) {
    const [isModalVisible, setIsModalVisible] = useState(false);

    const inKnowledgeGraphConflicts = conflict.map((c) => {
        return c.inKnowledgeGraph;
    })

    const showModal = () => {
        setIsModalVisible(true);
    };

    const handleOk = () => {
        setIsModalVisible(false);
    };

    const handleCancel = () => {
        setIsModalVisible(false);
    };

    return (
        <>
            <Button type='primary' onClick={showModal} style={{'backgroundColor': 'red'}}>
                Yes. See Conflict.
            </Button>
            <Modal title='Conflict' visible={isModalVisible} onOk={handleOk} onCancel={handleCancel}>
                <Typography.Title level={5}>Triples in Knowledge Graph</Typography.Title>
                <Table dataSource={inKnowledgeGraphConflicts} columns={tripleColumns}
                       pagination={{hideOnSinglePage: true}}/>
            </Modal>
        </>
    );
}

function PendingTriplesTable({ pendingTriples, conflictedTriples, getPendingTriples }) {
    const [selectedRowKeys, setSelectedRowKeys] = useState([]);
    const hasSelected = selectedRowKeys.length > 0;

    const onSelectChange = (selectedRowKeys) => {
        // console.log("selectedRowKeys changed: ", selectedRowKeys);
        setSelectedRowKeys(selectedRowKeys);
    }

    const rowSelection = {
        selectedRowKeys: selectedRowKeys,
        onChange: onSelectChange,
    }

    // TODO: move this to util components
    const showErrorModal = (message) => {
        Modal.error({
            title: 'Error!',
            content: (
                <div>
                    {message}
                </div>
            ),
            onOk() {
                Modal.destroyAll();
            }
        });
    }

    const showAddModal = () => {
        const selectedTriples = pendingTriples.filter((triple) => selectedRowKeys.includes(triple.key));
        const triplesToAdd = selectedTriples.map((triple) => {
            const tripleToAdd = {
                source: triple.source,
                triples: [{
                    sentence: triple.sentence,
                    triples: [{subject: triple.subject, relation: triple.relation, objects: triple.objects, added: triple.added}]
                }]
            }
            return tripleToAdd
        })
        confirm({
            title: 'Do you want to add these triples to the knowledge graph?',
            icon: <ExclamationCircleOutlined />,
            content: <Table dataSource={selectedTriples} columns={tripleColumns} pagination={{hideOnSinglePage: true}} scroll={{x: true}} />,
            onOk() {
                console.log(triplesToAdd)
                return axios.post('/kgu/article-triples/insert/', triplesToAdd)
                            .then(function (response) {
                                getPendingTriples();
                            })
                            .catch(function (error) {
                                showErrorModal(error.response); //FIXME
                            });
            }
        });
    }

    const showDiscardModal = () => {
        const selectedTriples = pendingTriples.filter((triple) => selectedRowKeys.includes(triple.key));
        const triplesToDelete = selectedTriples.map((triple) => {
            const tripleToAdd = {
                source: triple.source,
                triples: [{
                    sentence: triple.sentence,
                    triples: [{subject: triple.subject, relation: triple.relation, objects: triple.objects, added: triple.added}]
                }]
            }
            return tripleToAdd
        })
        confirm({
            title: 'Are you sure you want to delete these triples?',
            icon: <ExclamationCircleOutlined />,
            content: <Table dataSource={selectedTriples} columns={tripleColumns} pagination={{hideOnSinglePage: true}} scroll={{x: true}} />,
            okText: 'Yes',
            okType: 'danger',
            cancelText: 'No',
            onOk() {
                return axios.delete('/kgu/article-triples/pending/', { data: triplesToDelete})
                            .then(function (response) {
                                getPendingTriples();
                            })
                            .catch(function (error) {
                                showErrorModal(error.response); //FIXME
                            });
            }
        });
    }


    const columns = [
        {
            title: 'Source',
            dataIndex: 'source',
            key: 'source',
            render: (text) => <a href={text}>{text}</a>
        },
        {
            title: 'Sentence',
            dataIndex: 'sentence',
            key: 'sentence',
        },
        {
            title: 'Subject',
            dataIndex: 'subject',
            key: 'subject',
            render: convertToDBpediaLink,
        },
        {
            title: 'Relation',
            dataIndex: 'relation',
            key: 'relation',
            render: convertToDBpediaLink,
        },
        {
            title: 'Object',
            dataIndex: 'objects',
            key: 'object',
            render: convertObjectsToDBpediaLink,
        },
        {
            title: 'Has Conflict',
            dataIndex: 'hasConflict',
            key: 'hasConflict',
            render: (value, row) => {
                let article = conflictedTriples.filter(function(el) {
                    return el.source === row.source;
                })
                if (article.length == 0) return 'No';
                let conflict = article[0].conflicts.filter(function(el) {
                    return el.toBeInserted.subject === row.subject
                        && el.toBeInserted.relation === row.relation
                        // && el.toBeInserted.objects === row.objects;
                });
                return conflict.length > 0 ? <ConflictModal conflict={conflict}/> : 'No';
            }
        }
    ];

    return (
        <>
            <Button
                type='primary'
                disabled={!hasSelected}
                onClick={showAddModal}
                style={{ float: 'left', margin: '10px 0 10px 10px' }}
            >
                Add to Knowledge Graph
            </Button>
            <Button
                type='primary'
                disabled={!hasSelected}
                onClick={showDiscardModal}
                style={{ float: 'left', margin: '10px 0 10px 10px' }}
            >
                Discard triples
            </Button>
            <Table
                dataSource={pendingTriples}
                columns={columns}
                rowSelection={rowSelection}
                scroll={{x: true}}
            />
        </>
    );
;}

function KnowledgeGraphUpdaterView() {
    const [pendingTriples, setPendingTriples] = useState();
    const [conflictedTriples, setConflictedTriples] = useState();
    const [isUpdating, setIsUpdating] = useState(false);



    const getPendingTriples = () => {
        axios.get('/kgu/article-triples/pending')
        .then(function (response) {
            console.log(response);
            let data = [];
            response.data.all_pending.forEach((article) => {
                article.triples.forEach((sentence) => {
                    sentence.triples.forEach((triple) => {
                        data.push({...triple, source: article.source, sentence: sentence.sentence,
                            key: sentence.sentence+triple['subject']+triple['relation']+triple['objects']})
                    })
                })
            })
            setPendingTriples(data);
        });
    };

    const getConflictedTriples = () => {
        axios.get('/kgu/article-triples/conflicts/')
        .then(function (response) {
            console.log(response);
            setConflictedTriples(response.data.all_conflicts);
        });
    };

    const onUpdateClick = () => {
        axios.get('/kgu/updates')
        .then(function() {
            setIsUpdating(true);
        });
        let status = setInterval(function() {
            axios.get('/kgu/updates/status')
            .then(function(response) {
                if (response.status == 200) {
                    setIsUpdating(false);
                    getPendingTriples();
                    getConflictedTriples();
                    return clearInterval(status)
                }
            })
        }, 3000);
    };

    useEffect(() => {
        getPendingTriples();
        getConflictedTriples();
    }, []);

    return(
        <Card style={{ textAlign: 'center'}}>
            <Typography.Title style={{ textAlign: 'center' }}>Knowledge Graph Updater</Typography.Title>
            <Divider>Update Triple Extraction from Articles</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Trigger an update so that triples are extracted from the scraped news articles.
            </Typography>
            <Button
                type='primary'
                style={{ margin: '10px auto'}}
                onClick={onUpdateClick}
                loading={isUpdating}
            >
                Update
            </Button>

            <Divider>Pending Triples</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Triples to be added to the knowledge graph.
            </Typography>

            <PendingTriplesTable
                pendingTriples={pendingTriples}
                conflictedTriples={conflictedTriples}
                getPendingTriples={getPendingTriples}
            />


        </Card>
    );
};

export default KnowledgeGraphUpdaterView;