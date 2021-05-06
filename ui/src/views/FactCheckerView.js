import {
    Alert,
    Button,
    Card,
    Form,
    Input,
    Modal,
    notification,
    Radio,
    Space,
    Spin,
    Statistic,
    Table,
    Tag,
    Typography
} from 'antd';
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TriplesFormInput from '../components/TriplesFormInput';

import TriplesTables from "../components/TriplesTables";

const crypto = require('crypto');

const { TextArea } = Input;

export const handleFactCheckResponse = (response, setLoading, setExactMatch, setPossibleMatch, setConflict, setUnknown) => {
    setLoading(false);
    const [exactMatch, possibleMatch, conflict, unknown] = [[],[],[],[]];
    response.data.triples.forEach((sentence) => {
        sentence.triples.forEach((triple) => {
            const pushed = {key: crypto.randomBytes(16).toString('hex'), sentence: sentence.sentence,
                            triple: triple.triple, result: triple.result};
            if (triple.result === 'exists') {
                exactMatch.push({...pushed});
            } else if (triple.result === 'conflicts') {
                conflict.push({...pushed, other_triples: triple.other_triples});
            } else if (triple.result === 'possible') {
                possibleMatch.push({...pushed, other_triples: triple.other_triples});
            } else if (triple.result === 'none') {
                unknown.push({...pushed});
            }
        })
    })
    setExactMatch(exactMatch);
    setConflict(conflict);
    setPossibleMatch(possibleMatch);
    setUnknown(unknown);
}

function ArticleTextForm({loading, setLoading, algorithm, extractionScope, currentInputText, setCurrentInputText,
                             setExactMatch, setPossibleMatch, setConflict, setUnknown}) {
    const onSubmit = (values) => {
        setLoading(true);
        console.log('Submitted', values);
        axios.post(`/fc/${algorithm}/fact-check/`, {
            text: values.text,
            extraction_scope: extractionScope,
        })
        .then(function (response) {
            handleFactCheckResponse(response, setLoading, setExactMatch, setPossibleMatch, setConflict, setUnknown);
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
                        message: 'Please input the text!',
                    }
                ]}
            >
                <TextArea
                    rows={4}
                    disabled={loading}
                    defaultValue={currentInputText}
                    onChange={e => setCurrentInputText(e.target.value)}
                />
            </Form.Item>
            <Form.Item>
                <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}} size='large'>
                    Fact Check
                </Button>
            </Form.Item>
         </Form>
    );
}

function TriplesForm({loading, setLoading, algorithm, setExactMatch, setPossibleMatch, setConflict, setUnknown}) {
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
                const [exactMatch, possibleMatch, conflict, unknown] = [[],[],[],[]];
                response.data.triples.forEach((triple) => {
                    const pushed = {triple: triple.triple, result: triple.result};
                    if (triple.result === 'exists') {
                        exactMatch.push({...pushed});
                    } else if (triple.result === 'conflicts') {
                        conflict.push({...pushed, other_triples: triple.other_triples});
                    } else if (triple.result === 'possible') {
                        possibleMatch.push({...pushed, other_triples: triple.other_triples});
                    } else if (triple.result === 'none') {
                        unknown.push({...pushed});
                    }
                })

                setExactMatch(exactMatch);
                setConflict(conflict);
                setPossibleMatch(possibleMatch);
                setUnknown(unknown);
            });
        }

    }

    return(
         <Form layout='vertical' onFinish={onSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
             <TriplesFormInput />
             <Form.Item>
                 <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}} size='large'>
                     Fact Check
                 </Button>
             </Form.Item>
         </Form>
    );
}

function URLForm({ loading, setLoading, algorithm, extractionScope, currentInputText, setCurrentInputText,
                     setExactMatch, setConflict, setPossibleMatch, setUnknown }) {
    const onSubmit = (values) => {
        setLoading(true);
        console.log('Submitted', values);
        axios.post(`/fc/${algorithm}/fact-check/url/`, {
            url: values.url,
            extraction_scope: extractionScope,
        })
        .then(function (response) {
            handleFactCheckResponse(response, setLoading, setExactMatch, setPossibleMatch, setConflict, setUnknown);
        })
    }

    return(
         <Form layout='vertical' onFinish={onSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
            <Form.Item
                label='Article URL'
                name='url'
                rules={[
                    {
                        required: true,
                        message: 'Please input the article url!',
                    }
                ]}
            >
                <Input
                    disabled={loading}
                    defaultValue={currentInputText}
                    onChange={e => setCurrentInputText(e.target.value)}
                />
            </Form.Item>
            <Form.Item>
                <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}} size='large'>
                    Fact Check
                </Button>
            </Form.Item>
         </Form>
    );
}

function FactCheckerView() {
    const [loading, setLoading] = useState(false);
    const [algorithm, setAlgorithm] =  useState('exact');
    const [inputType, setInputType] = useState('text');
    const [currentInputText, setCurrentInputText] = useState('');
    const [extractionScope, setExtractionScope] = useState('noun_phrases')
    const [exactMatch, setExactMatch] = useState([]);
    const [possibleMatch, setPossibleMatch] = useState([]);
    const [conflict, setConflict] = useState([]);
    const [unknown, setUnknown] = useState([]);

    const onAlgorithmChange = (e) => {
        setAlgorithm(e.target.value);
    }

    const onInputTypeChange = (e) => {
        setInputType(e.target.value);
    }

    const onExtractionScopeChange = (e) =>{
        setExtractionScope(e.target.value);
    }

    const inputTypes = [
        { label: 'Text', value: 'text' },
        { label: 'Triples', value: 'triples' },
        { label: 'URL', value: 'url'},
    ];

    const algorithms = [
        { label: 'Exact Match Only', value: 'exact'},
        { label: 'With Non Exact Match', value: 'non-exact'},
    ];

    const extractionScopes = [
        { label: 'Noun phrases', value: 'noun_phrases'},
        { label: 'Named entities', value: 'named_entities'},
        { label: 'All', value: 'all'},
    ]

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

                Extraction scope:
                <Radio.Group
                    options={extractionScopes}
                    value={extractionScope}
                    onChange={onExtractionScopeChange}
                    optionType='button'
                    buttonStyle='solid'
                />
            </Space>

            {inputType === 'text' && <ArticleTextForm loading={loading} setLoading={setLoading} algorithm={algorithm}
                                                      extractionScope={extractionScope}
                                                      currentInputText={currentInputText} setCurrentInputText={setCurrentInputText}
                                                      setExactMatch={setExactMatch} setPossibleMatch={setPossibleMatch}
                                                      setConflict={setConflict} setUnknown={setUnknown}/>}

            {inputType === 'triples' && <TriplesForm loading={loading} setLoading={setLoading} algorithm={algorithm}
                                                     setExactMatch={setExactMatch} setPossibleMatch={setPossibleMatch}
                                                     setConflict={setConflict} setUnknown={setUnknown}/>}

            {inputType === 'url' && <URLForm loading={loading} setLoading={setLoading} algorithm={algorithm}
                                             extractionScope={extractionScope}
                                             currentInputText={currentInputText} setCurrentInputText={setCurrentInputText}
                                             setExactMatch={setExactMatch} setPossibleMatch={setPossibleMatch}
                                             setConflict={setConflict} setUnknown={setUnknown}/>}

            <Card>
                {(exactMatch.length > 0 || possibleMatch.length > 0 || conflict.length > 0 || unknown.length > 0) &&
                <Typography.Title level={3} style={{ textAlign: 'center' }}>
                    Fact Check Result
                </Typography.Title>}
                <div style={{ textAlign: 'center'}}>
                    {loading && <Spin size='large'/>}
                </div>

                {/*{result && <div>*/}
                {/*    <Statistic*/}
                {/*        title='Truthfulness'*/}
                {/*        value={result.data.truthfulness * 100}*/}
                {/*        precision={2}*/}
                {/*        prefix={<CheckCircleOutlined />}*/}
                {/*        suffix='%' />*/}
                {/*    <Table columns={columns} dataSource={result.data.triples} scroll={{x: true}}/>*/}
                {/*</div>}*/}

                <TriplesTables algorithm={algorithm} exactMatch={exactMatch} possibleMatch={possibleMatch}
                               conflict={conflict} unknown={unknown}/>

            </Card>

        </Card>
    )
}

export default FactCheckerView;