import {Space, Table, Typography} from "antd";
import {convertObjectsToDBpediaLink, convertRelationToDBpediaLink, convertToDBpediaLink} from "../utils";
import RemoveModal from "./RemoveModal";
import ConflictModal from "./ConflictModal";
import PossibleMatchModal from "./PossibleMatchModal";
import AddModal from "./AddModal";
import DiscardModal from "./DiscardModal";

function TriplesTables({exactMatch, possibleMatch, conflict, unknown,
                       setExactMatch, setPossibleMatch, setConflict, setUnknown,
                       algorithm, isArticle, sourceUrl}) {
    let columns = [
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
    </>);
}

export default TriplesTables;