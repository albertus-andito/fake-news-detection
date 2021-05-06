import {Space, Table, Typography} from "antd";
import {convertObjectsToDBpediaLink, convertRelationToDBpediaLink, convertToDBpediaLink} from "../utils";
import RemoveModal from "./RemoveModal";
import ConflictModal from "./ConflictModal";
import PossibleMatchModal from "./PossibleMatchModal";
import AddModal from "./AddModal";
import DiscardModal from "./DiscardModal";
import {useRef, useState} from "react";
import {getColumnSearchProps} from "./ColumnSearchProps";
import {CheckSquareFilled, CloseSquareFilled, ExclamationCircleFilled, QuestionCircleFilled} from "@ant-design/icons";

function TriplesTables({exactMatch, possibleMatch, conflict, unknown,
                       setExactMatch, setPossibleMatch, setConflict, setUnknown,
                       algorithm, isArticle, sourceUrl}) {
    const [searchText, setSearchText] = useState('');
    const [searchedColumn, setSearchedColumn] = useState('');
    const searchInput = useRef(null);
    let columnSearchParams = [
        searchInput,
        searchText,
        setSearchText,
        searchedColumn,
        setSearchedColumn,
    ];

    let columns = [
        {
            title: 'Sentence',
            dataIndex: 'sentence',
            key: 'sentence',
            sorter: {
                compare: (a, b) =>
                    (a.sentence || '').localeCompare(b.sentence || ''),
            },
            ...getColumnSearchProps('sentence', ...columnSearchParams),
        },
        {
            title: 'Subject',
            dataIndex: ['triple', 'subject'],
            key: 'subject',
            sorter: {
                compare: (a, b) =>
                    (a.triple.subject || '').localeCompare(b.triple.subject || ''),
            },
            ...getColumnSearchProps(['triple', 'subject'], ...columnSearchParams),
            render: convertToDBpediaLink,
        },
        {
            title: 'Relation',
            dataIndex: ['triple', 'relation'],
            key: 'relation',
            sorter: {
                compare: (a, b) =>
                    (a.triple.relation || '').localeCompare(b.triple.relation || ''),
            },
            ...getColumnSearchProps(['triple', 'relation'], ...columnSearchParams),
            render: convertRelationToDBpediaLink,
        },
        {
            title: 'Object',
            dataIndex: ['triple', 'objects'],
            key: 'object',
            sorter: {
                compare: (a, b) =>
                    (a.triple.objects[0].replace('http://dbpedia.org/resource/', '') || '').localeCompare(
                        b.triple.objects[0].replace('http://dbpedia.org/resource/', '') || ''),
            },
            ...getColumnSearchProps(['triple', 'objects'], ...columnSearchParams),
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
                    return <RemoveModal triple={row.triple} algorithm={algorithm} />
                } else if (value === 'conflicts') {
                    return (
                        <Space>
                            <ConflictModal conflict={row.other_triples} algorithm={algorithm}/>
                            <AddModal triple={row.triple} isArticle={isArticle} source={sourceUrl} sentence={row.sentence}/>
                            {isArticle &&
                            <DiscardModal
                                triple={row.triple} source={sourceUrl} sentence={row.sentence}
                                tripleKey={row.key} data={conflict} setData={setConflict}
                            />}
                        </Space>)
                } else if (value === 'possible') {
                    return (
                        <Space>
                            <PossibleMatchModal possibleMatches={row.other_triples} algorithm={algorithm}/>
                            <AddModal triple={row.triple} isArticle={isArticle} source={sourceUrl} sentence={row.sentence}/>
                            {isArticle &&
                            <DiscardModal
                                triple={row.triple} source={sourceUrl} sentence={row.sentence}
                                tripleKey={row.key} data={possibleMatch} setData={setPossibleMatch}
                            />}
                        </Space>)
                } else if (value === 'none') {
                    return (
                        <Space>
                            <AddModal triple={row.triple} isArticle={isArticle} source={sourceUrl} sentence={row.sentence}/>
                            {isArticle &&
                            <DiscardModal
                                triple={row.triple} source={sourceUrl} sentence={row.sentence}
                                tripleKey={row.key} data={unknown} setData={setUnknown}
                            />}
                        </Space>)
                }

            }
        }
    ];

    return(<>
        {exactMatch.length > 0 && <div style={{marginTop: '20px'}}>
            <Space>
                <Typography.Title level={4}>Exact Matches</Typography.Title>
                <CheckSquareFilled style={{fontSize: '30px', color: '#52c41a'}}/>
            </Space>

            <Table columns={columns} dataSource={exactMatch} scroll={{x: true}}
                   pagination={{hideOnSinglePage: true}}/>
        </div>}

        {possibleMatch.length > 0 && <div style={{marginTop: '20px'}}>
            <Space>
                <Typography.Title level={4}>Possible Matches</Typography.Title>
                <ExclamationCircleFilled style={{fontSize: '30px', color: '#c4810c'}}/>
            </Space>
            <Table columns={columns} dataSource={possibleMatch} scroll={{x: true}}
                   pagination={{hideOnSinglePage: true}}/>
        </div>}

        {conflict.length > 0 && <div style={{marginTop: '20px'}}>
            <Space>
                <Typography.Title level={4}>Conflicting Triples</Typography.Title>
                <CloseSquareFilled style={{fontSize: '30px', color: '#c40c21'}}/>
            </Space>
            <Table columns={columns} dataSource={conflict} scroll={{x: true}}
                   pagination={{hideOnSinglePage: true}}/>
        </div>}

        {unknown.length > 0 && <div style={{marginTop: '20px'}}>
            <Space>
                <Typography.Title level={4}>Unknown Triples</Typography.Title>
                <QuestionCircleFilled style={{fontSize: '30px'}}/>
            </Space>

            <Table columns={columns} dataSource={unknown} scroll={{x: true}}
                   pagination={{hideOnSinglePage: true}}/>
        </div>}
    </>);
}

export default TriplesTables;