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
import {CheckCircleOutlined, ExclamationCircleOutlined} from '@ant-design/icons';
import TriplesFormInput from '../components/TriplesFormInput';

import {convertToDBpediaLink, convertObjectsToDBpediaLink, convertRelationToDBpediaLink, tripleColumns} from '../utils';
import showErrorModal from "../components/ShowErrorModal";

const { TextArea } = Input;
const { confirm } = Modal;

function ArticleTextForm({loading, setLoading, algorithm, setExactMatch, setPossibleMatch, setConflict, setUnknown}) {
    const onSubmit = (values) => {
        setLoading(true);
        console.log('Submitted', values);
        axios.post(`/fc/${algorithm}/fact-check/`, {
            text: values.text
        })
        .then(function (response) {
            console.log(response);
            setLoading(false);
            const [exactMatch, possibleMatch, conflict, unknown] = [[],[],[],[]];
            response.data.triples.forEach((sentence) => {
                sentence.triples.forEach((triple) => {
                    const pushed = {sentence: sentence.sentence, triple: triple.triple, result: triple.result};
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
                 <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}}>
                     Fact Check
                 </Button>
             </Form.Item>
         </Form>
    );
}

function AddModal({ triple }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        setVisible(true);
    }, [triple])

    const showModal = () => confirm({
        title: 'Do you want to add this triple to the knowledge graph?',
        icon: <ExclamationCircleOutlined />,
        content: <Table dataSource={[triple]} columns={tripleColumns} pagination={{hideOnSinglePage: true}} scroll={{x: true}} />,
        width: 1000,
        okText: 'Yes',
        onOk() {
            return axios.post('/kgu/triples/force/', [triple])
                        .then((res) => {
                            setVisible(false);
                        })
                        .catch((error) => {
                            showErrorNotification(error.response.data);
                        })
        }
    });
    return(<>
        {visible && <Button type='primary' onClick={showModal} style={{'backgroundColor': 'green'}}>
            Add to Knowledge Graph
        </Button>}
        {!visible && 'Added to Knowledge Graph'}
    </>)
}

function showErrorNotification(message) {
    notification['error']({
        message: 'Error!',
        description: message,
    });
}

function RemoveModal({ triple }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        axios.post('/fc/exact/fact-check/triples/', [triple])
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

function ConflictModal({ conflict }) {
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
                return <RemoveModal triple={{subject: row.subject, relation: row.relation, objects: row.objects}} />
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

function FactCheckerView() {
    const [loading, setLoading] = useState(false);
    const [algorithm, setAlgorithm] =  useState('exact');
    const [inputType, setInputType] = useState('text');
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

    const inputTypes = [
        { label: 'Text', value: 'text' },
        { label: 'Triples', value: 'triples' },
    ];

    const algorithms = [
        { label: 'Exact Match Only', value: 'exact'},
        { label: 'With Non Exact Match', value: 'non-exact'},
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
            title: 'Action',
            dataIndex: 'result',
            key: 'result',
            shouldCellUpdate: () => {
                return true;
            },
            render: (value, row) => {
                if (value === 'exists') {
                    return <RemoveModal triple={row.triple} />
                } else if (value === 'conflicts') {
                    return (<Space>
                            <ConflictModal conflict={row.other_triples}/>
                            <AddModal triple={row.triple} />
                    </Space>)
                } else if (value === 'none') {
                    return <AddModal triple={row.triple} />
                }

            }
        }
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

            {inputType === 'text' && <ArticleTextForm loading={loading} setLoading={setLoading} algorithm={algorithm}
                                                      setExactMatch={setExactMatch} setPossibleMatch={setPossibleMatch}
                                                      setConflict={setConflict} setUnknown={setUnknown}/>}

            {inputType === 'triples' && <TriplesForm loading={loading} setLoading={setLoading} algorithm={algorithm}
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

                {exactMatch.length > 0 && <div style={{marginTop: '20px'}}>
                    <Typography.Title level={4}>Exact Matches</Typography.Title>
                    <Table columns={columns} dataSource={exactMatch} scroll={{x: true}}
                           pagination={{hideOnSinglePage: true}}/>
                </div>}

                {possibleMatch.length > 0 && <div style={{marginTop: '20px'}}>
                    <Typography.Title level={4}>Possible Matches</Typography.Title>
                    <Table columns={columns} dataSource={possibleMatch} scroll={{x: true}}
                           pagination={{hideOnSinglePage: true}}/>
                </div>}

                {conflict.length > 0 && <div style={{marginTop: '20px'}}>
                    <Typography.Title level={4}>Conflicting Triples</Typography.Title>
                    <Table columns={columns} dataSource={conflict} scroll={{x: true}}
                           pagination={{hideOnSinglePage: true}}/>
                </div>}

                {unknown.length > 0 && <div style={{marginTop: '20px'}}>
                    <Typography.Title level={4}>Unknown Triples</Typography.Title>
                    <Table columns={columns} dataSource={unknown} scroll={{x: true}}
                           pagination={{hideOnSinglePage: true}}/>
                </div>}
            </Card>

        </Card>
    )
}

export default FactCheckerView;