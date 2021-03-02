import {Button, Card, Form, Input, Radio, Space, Spin, Statistic, Table, Tag, Typography} from 'antd';
import React, { useState } from 'react';
import axios from 'axios';
import { CheckCircleOutlined } from '@ant-design/icons';
import TriplesFormInput from '../components/TriplesFormInput';

import {convertToDBpediaLink, convertObjectsToDBpediaLink, convertRelationToDBpediaLink} from '../utils';

const { TextArea } = Input;

function ArticleTextForm({loading, setLoading, setResult, algorithm}) {
    const onSubmit = (values) => {
        setLoading(true);
        console.log('Submitted', values);
        axios.post(`/fc/${algorithm}/fact-check/`, {
            text: values.text
        })
        .then(function (response) {
            console.log(response);
            setLoading(false);
            const result = []
            response.data.triples.forEach((sentence) => {
                sentence.triples.forEach((triple) => {
                    result.push({sentence: sentence.sentence, triple: triple.triple, exists: triple.exists})
                })
            })
            setResult({data: {triples: result, truthfulness: response.data.truthfulness}});
        })
    }

    return(
         <Form layout='vertical' onFinish={onSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
            <Form.Item
                label='Article Text'
                name='text'
                rules={[
                    {
                        required: true,
                        message: 'Please input the fake news text!',
                    }
                ]}
            >
                <TextArea rows={4} disabled={loading}/>
            </Form.Item>
            <Form.Item>
                <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}}>
                    Fact Check
                </Button>
            </Form.Item>
         </Form>
    );
}

function TriplesForm({loading, setLoading, setResult, algorithm}) {
    const onSubmit = (values) => {
        setLoading(true);
        console.log('Submitted', values);
        if (!values.triples || values.triples.length == 0) {
            setLoading(false);
        } else {
            values.triples.forEach(value => {
                value.objects = [value.objects]
            });
            axios.post(`/fc/${algorithm}/fact-check/triples/`, values.triples)
            .then(function (response) {
                console.log(response);
                setLoading(false);
                setResult(response);
            });
        }

    }

    return(
         <Form layout='vertical' onFinish={onSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
             <TriplesFormInput />
             <Form.Item>
                 <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}}>
                     Fact Check
                 </Button>
             </Form.Item>
         </Form>
    );
}

function FactCheckerView() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState();
    const [algorithm, setAlgorithm] =  useState('simple');
    const [inputType, setInputType] = useState('text');

    const onAlgorithmChange = (e) => {
        setAlgorithm(e.target.value);
    }

    const onInputTypeChange = (e) => {
        setInputType(e.target.value);
    }

    const inputTypes = [
        { label: 'Text', value: 'text' },
        { label: 'Triples', value: 'triples' },
    ];

    const algorithms = [
        { label: 'Simple', value: 'simple'},
        { label: 'Better', value: 'better'},
    ];

    const columns = [
        {
            title: 'Sentence',
            dataIndex: 'sentence',
            key: 'sentence',
        },
        {
            title: 'Subject',
            dataIndex: ['triple', 'subject'],
            key: 'subject',
            render: convertToDBpediaLink,
        },
        {
            title: 'Relation',
            dataIndex: ['triple', 'relation'],
            key: 'relation',
            render: convertRelationToDBpediaLink,
        },
        {
            title: 'Object',
            dataIndex: ['triple', 'objects'],
            key: 'object',
            render: convertObjectsToDBpediaLink,
        },
        {
            title: 'Exists',
            dataIndex: 'exists',
            key: 'exists',
            render: (value) => value
                ? <Tag color='green'>True</Tag>
                : <Tag color='red'>False</Tag> ,
        },
    ];

    return(
        <Card>
            <Typography.Title style={{ textAlign: 'center' }}>Fact Checker</Typography.Title>
            <Space>
                Fact Checker Algorithm:
                <Radio.Group
                    options={algorithms}
                    value={algorithm}
                    onChange={onAlgorithmChange}
                    optionType='button'
                    buttonStyle='solid'
                />

                Input Type:
                <Radio.Group
                    options={inputTypes}
                    value={inputType}
                    onChange={onInputTypeChange}
                    optionType='button'
                    buttonStyle='solid'
                />
            </Space>

            {inputType === 'text' && <ArticleTextForm loading={loading} setLoading={setLoading} setResult={setResult}
                                                      algorithm={algorithm} />}

            {inputType === 'triples' && <TriplesForm loading={loading} setLoading={setLoading} setResult={setResult}
                                                     algorithm={algorithm}/>}

            <Card>
                {result && <Typography.Title level={4} style={{ textAlign: 'center' }}>
                    Fact Check Result
                </Typography.Title>}
                <div style={{ textAlign: 'center'}}>
                    {loading && <Spin size='large'/>}
                </div>

                {result && <div>
                    <Statistic
                        title='Truthfulness'
                        value={result.data.truthfulness * 100}
                        precision={2}
                        prefix={<CheckCircleOutlined />}
                        suffix='%' />
                    <Table columns={columns} dataSource={result.data.triples} scroll={{x: true}}/>
                </div>}
            </Card>

        </Card>
    )
}

export default FactCheckerView;