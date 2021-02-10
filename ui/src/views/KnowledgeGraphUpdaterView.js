import {Button, Card, Divider, Modal, Table, Tag, Typography} from "antd";
import React, { useState, useEffect } from 'react';
import axios from "axios";
import {convertObjectsToDBpediaLink, convertToDBpediaLink} from "../utils";

function ConflictModal() {
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

    return(
        <>
            <Button type='primary' onClick={showModal} style={{ 'backgroundColor': 'red' }}>
                Yes. See Conflict.
            </Button>
            <Modal title='Conflict' visible={isModalVisible} onOk={handleOk} onCancel={handleCancel}>
                This is a conflict
            </Modal>
        </>
    )
}

function KnowledgeGraphUpdaterView() {
    const [pendingTriples, setPendingTriples] = useState();
    const [conflictedTriples, setConflictedTriples] = useState();
    const [isUpdating, setIsUpdating] = useState(false);

    const getPendingTriples = () => {
        axios.get('/kgu/article-triples/pending')
        .then(function (response) {
            console.log(response);
            let data = [];
            response.data.all_pending.forEach((row) => {
                row.triples.forEach((triple) => {
                    data.push({...triple, source: row.source})
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

    const columns = [
        {
            title: 'Source',
            dataIndex: 'source',
            key: 'source',
            render: (text) => <a href={text}>{text}</a>
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
                return conflict.length > 0 ? <ConflictModal /> : 'No';
            }
        }
    ];

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
            <Table dataSource={pendingTriples} columns={columns} scroll={{x: true}}>

            </Table>


        </Card>
    );
};

export default KnowledgeGraphUpdaterView;