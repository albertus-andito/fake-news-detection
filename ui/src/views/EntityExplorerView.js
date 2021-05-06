import {Button, Card, Form, Input, Table, Typography} from "antd";
import React, {useState} from "react";
import axios from "axios";
import {tripleColumns} from "../utils";
import RemoveModal from "../components/RemoveModal";

function EntityExplorerView() {
    const [triples, setTriples] = useState();

    let action = [
        {
            title: 'Action',
            key: 'action',
            shouldCellUpdate: () => {
                return true;
            },
            render: (value, row) => {
                return <RemoveModal
                    triple={{subject: row.subject, relation: row.relation, objects: row.objects}}
                    algorithm='non-exact'/>
            }
        }
    ];

    const onSubmit = (vals) => {
        console.log(vals.entity);
        const entityUrl = encodeURIComponent('http://dbpedia.org/resource/' + vals.entity.replace(' ', '_'))
        axios.get(`/kgu/entity/${entityUrl}`)
            .then((res) => {
                console.log(res.data.triples);
                setTriples(res.data.triples)
            })
    }

    return(
        <Card style={{ textAlign: 'center' }}>
            <Typography.Title style={{ textAlign: 'center' }}>Entity Explorer</Typography.Title>
            <Typography>Find all triples related to the entity. Please input the entity name in DBpedia format.</Typography>
            <br/>
            <Form layout='inline' onFinish={onSubmit}>
                <Form.Item name='entity'>
                    <Input addonBefore="http://dbpedia.org/resource/"/>
                </Form.Item>
                <Form.Item>
                    <Button type='primary' htmlType='submit'>View</Button>
                </Form.Item>
            </Form>

            <Table
                dataSource={triples}
                columns={[...tripleColumns, ...action]}
                pagination={{hideOnSinglePage: true, showSizeChanger: true}}
            />

        </Card>


    )
}

export default EntityExplorerView;