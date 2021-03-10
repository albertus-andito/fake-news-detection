import {Alert, Button, Card, Divider, Form, Input, Typography} from "antd";
import axios from "axios";
import React, { useState } from 'react';
import showErrorModal from "../components/ShowErrorModal";
import TriplesFormInput from "../components/TriplesFormInput";

function AddTriplesForm() {
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const onSubmit = (values) => {
        if (!values.triples || values.triples.length == 0) {
            setIsLoading(false);
        } else {
            values.triples.forEach(value => {
                value.objects = [value.objects]
            });
            axios.post(`/kgu/triples/`, values.triples)
                .then(response => {
                    setIsSuccess(true);
                    setIsLoading(false);
                })
                .catch(error => {
                    setIsLoading(false);
                    if (error.response.status == 409) {
                        console.log(error.response.data)
                    }
                });
        }
    }

    return(
        <Form layout='vertical' onFinish={onSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
             <TriplesFormInput />
             <Form.Item>
                 <Button type='primary' htmlType='submit' disabled={isLoading}>
                     Add Triples to Knowledge Graph
                 </Button>
             </Form.Item>
            {isSuccess && <Alert message="Triples have been added to the knowledge graph" type="success" />}
         </Form>
    )
}

function EqualizeTripleForm() {
    const [isLoading, setIsLoading] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const onEqualizeEntitiesSubmit = (values) =>{
        setIsLoading(true);
        setIsSuccess(false);
        axios.post('/kgu/entity/equals/', values)
        .then(response => {
            setIsSuccess(true);
            setIsLoading(false);
        }).catch(error => {
            showErrorModal(error);
            setIsSuccess(false);
            setIsLoading(false);

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
                <Button type="primary" htmlType="submit" disabled={isLoading}>
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

            <Divider>Add Triples</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Manually add triples. At least Subject and Relation must be in DBpedia format.
            </Typography>
            <AddTriplesForm />

            <Divider>Equalize Entities</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Make two entities equal
            </Typography>
            <EqualizeTripleForm />
        </Card>
    )
}

export default AddOwnKnowledge;