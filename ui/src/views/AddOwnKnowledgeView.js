import {Alert, Button, Card, Divider, Form, Input, Typography} from "antd";
import axios from "axios";
import React, { useState } from 'react';
import showErrorModal from "../components/ShowErrorModal";

function EqualizeTripleForm() {
    const [isSuccess, setSuccess] = useState(false);

    const onEqualizeEntitiesSubmit = (values) =>{
        setSuccess(false);
        axios.post('/kgu/entity/equals/', values)
        .then(response => {
            setSuccess(true);
        }).catch(error => {
            console.log('error')
            showErrorModal(error)
            setSuccess(false)
        })
    }

    return(
        <Form onFinish={onEqualizeEntitiesSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
            <Form.Item
                label='Entity 1'
                name='entity_a'
                required={true}
            >
                <Input placeholder='http://dbpedia.org/resource/...'/>
            </Form.Item>
            <Form.Item
                label='Entity 2'
                name='entity_b'
                required={true}
            >
                <Input placeholder='http://dbpedia.org/resource/...'/>
            </Form.Item>
            <Form.Item>
                <Button type="primary" htmlType="submit">
                    Submit
                </Button>
            </Form.Item>
            {isSuccess && <Alert message="Entities have been set as equals" type="success" />}
        </Form>
    );
}

function AddOwnKnowledge() {
    return(
        <Card style={{ textAlign: 'center'}}>
            <Typography.Title style={{ textAlign: 'center' }}>Knowledge Graph Updater</Typography.Title>
            <Typography.Title level={2} style={{ textAlign: 'center' }}>Own Knowledge</Typography.Title>

            <Divider>Equalize Entities</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Make two entities equal
            </Typography>
            <EqualizeTripleForm />
        </Card>
    )
}

export default AddOwnKnowledge;