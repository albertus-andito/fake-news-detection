import {Button, Card, Divider, Modal, Popover, Radio, Space, Spin, Switch, Table, Tag, Typography} from "antd";
import React, { useState, useEffect } from 'react';
import axios from "axios";
import {convertToDBpediaLink, tripleColumns} from "../utils";
import TriplesTables from "../components/TriplesTables";
import {handleFactCheckResponse} from "./FactCheckerView";

function ArticleTable({selectedArticle, setSelectedArticle, isUpdating}) {
    const [articles, setArticles] = useState();

    const articleColumns = [
        {
            title: 'Article URL',
            dataIndex: 'source',
            key: 'source',
            sorter: {
                compare: (a, b) => (a.source || '').localeCompare(b.source || ''),
            },
            render: (text) => <a href={text}>{text}</a>,
        },
        {
            title: 'Headline',
            dataIndex: 'headlines',
            key: 'headlines',
            sorter: {
                compare: (a, b) => (a.headlines || '').localeCompare(b.headlines || ''),
            },
        },
        {
            title: 'Date',
            dataIndex: 'date',
            key: 'date',
            defaultSortOrder: 'descend',
            sorter: {
                compare: (a, b) => a.date - b.date
            },
            render: (text) => <p>{new Date(text * 1000).toUTCString()}</p>
        }
    ];

    const getArticles = () => {
        axios.get('/kgu/articles/extracted/')
            .then((res) => {
                setArticles(res.data.articles);
        })
    }

    const onSelectChange = (selectedRowKeys) => {
        setSelectedArticle(selectedRowKeys);
    }

    const rowSelection = {
        type: 'radio',
        selectedRowKeys: selectedArticle,
        onChange: onSelectChange,
    }

    useEffect(() => {
        getArticles();
    }, [isUpdating]);

    return(
        <Table
            dataSource={articles}
            columns={articleColumns}
            rowKey='source'
            rowSelection={rowSelection}
            pagination={{pageSize: 5}}
        />
    )
}

function UnresolvedCorefEntitiesTable({coreferingEntities}) {
    const columns = [
        {
            title: 'Source',
            dataIndex: 'source',
            key: 'source',
            render: (text) => <a href={text}>{text}</a>,
        },
        {
            title: 'Main Entity',
            dataIndex: 'main',
            key: 'main',
            render: convertToDBpediaLink,
        },
        {
            title: 'Corefering Entity',
            dataIndex: 'mention',
            key: 'mention',
            render: convertToDBpediaLink,
        }
    ];

    return(
      <Table
          dataSource={coreferingEntities}
          columns={columns}
          scroll={{x: true}}
      />

    );
}

function ArticleKnowledgeView() {
    const [isUpdating, setIsUpdating] = useState(false);
    const [autoAdd, setAutoAdd] = useState(false);
    const [extractionScope, setExtractionScope] = useState('noun_phrases')
    // const [coreferingEntities, setCoreferingEntities] = useState();

    const [selectedArticle, setSelectedArticle] = useState([]);
    const [loading, setLoading] = useState(false);

    const [exactMatch, setExactMatch] = useState([]);
    const [possibleMatch, setPossibleMatch] = useState([]);
    const [conflict, setConflict] = useState([]);
    const [unknown, setUnknown] = useState([]);

    const getPendingTriples = () => {
        if(selectedArticle.length === 0) {
            return;
        }
        setLoading(true);
        axios.get(`/kgu/article-triples/pending/${selectedArticle[0]}`)
            .then((res) => {
                axios.post('/fc/non-exact/fact-check/triples-sentences/', res.data.triples)
                    .then((res) => {
                        handleFactCheckResponse(res, setLoading, setExactMatch, setPossibleMatch, setConflict, setUnknown)
                    })
                    .catch((err) => {
                        console.log(err);
                    })
                })
    }

    // const getUnresolvedCorefEntities = () => {
    //     axios.get('/kgu/article-triples/corefering-entities/')
    //     .then(function(response) {
    //         console.log(response);
    //         let data = [];
    //         response.data.all_coref_entities.forEach((article) => {
    //             article.coref_entities.forEach((entity) => {
    //                 entity.mentions.forEach((mention) => {
    //                     data.push({source: article.source, main: entity.main, mention: mention.mention});
    //                 })
    //             })
    //         })
    //         setCoreferingEntities(data);
    //     })
    // }

    const onUpdateClick = () => {
        axios.get('/kgu/updates', {
            params: {
                auto_update: autoAdd,
                extraction_scope: extractionScope,
            }
        })
        .then(function() {
            setIsUpdating(true);
        });
        let status = setInterval(function() {
            axios.get('/kgu/updates/status')
            .then(function(response) {
                if (response.status == 200) {
                    setIsUpdating(false);
                    return clearInterval(status)
                }
            })
        }, 3000);
    };

    const onAutoAddChange = (checked) =>  {
        setAutoAdd(checked);
    }

    const autoAddPopoverContent = (
        <div>
            <p>If this is set to on, all non-conflicting triples will be automatically added to the knowledge graph.</p>
            <p>Otherwise, all triples will be put in the pending triples table below.</p>
        </div>
    )

    const extractionScopes = [
        { label: 'Noun phrases', value: 'noun_phrases'},
        { label: 'Named entities', value: 'named_entities'},
        { label: 'All', value: 'all'},
    ]

    const onExtractionScopeChange = (e) =>{
        setExtractionScope(e.target.value);
    }

    const extractionScopePopoverContent = (
        <div>
            <p>The scope of the extraction, deciding whether it should include only triples with relations between
                'named_entities', 'noun_phrases', or 'all'.</p>
        </div>
    )

    useEffect(() => {
        getPendingTriples();
    }, [selectedArticle])

    return(
        <Card style={{ textAlign: 'center'}}>
            <Typography.Title style={{ textAlign: 'center' }}>Knowledge Graph Updater</Typography.Title>
            <Typography.Title level={2} style={{ textAlign: 'center' }}>Article Knowledge</Typography.Title>

            <Divider>Update Triple Extraction from Articles</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Trigger an update so that triples are extracted from the scraped news articles.
            </Typography>
            <Space direction='vertical'>
                <Space>
                    <Popover content={autoAddPopoverContent} title='Automatically Add Knowledge'>
                        <Switch onChange={onAutoAddChange}/>
                    </Popover>
                    Automatically add non-conflicting triples to the knowledge graph
                </Space>
                <Popover content={extractionScopePopoverContent} title='Extraction Scope'>
                    <Space>
                        Extraction scope:
                        <Radio.Group
                            options={extractionScopes}
                            value={extractionScope}
                            onChange={onExtractionScopeChange}
                            defaultValue='noun_phrases'
                            optionType='button'
                            buttonStyle='solid'
                        />
                    </Space>
                </Popover>
                <Button
                    type='primary'
                    style={{ margin: '10px auto'}}
                    onClick={onUpdateClick}
                    loading={isUpdating}
                >
                    Update
                </Button>
            </Space>

            {/*<Divider>Unresolved Corefering Entities</Divider>*/}
            {/*<Typography style={{ textAlign: 'center' }}>*/}
            {/*    Corefering entities that are found in the articles. Resolve them if they are indeed the same entity.*/}
            {/*</Typography>*/}
            {/*<UnresolvedCorefEntitiesTable coreferingEntities={coreferingEntities}/>*/}

            <Divider>Pending Triples</Divider>
            <Typography style={{ textAlign: 'center' }}>
                Triples to be added to the knowledge graph.
            </Typography>

            <ArticleTable selectedArticle={selectedArticle} setSelectedArticle={setSelectedArticle} isUpdating={isUpdating}/>

            <div style={{ textAlign: 'center'}}>
                {loading && <Spin tip='Loading...' size='large'/>}
            </div>

            <TriplesTables
                algorithm='non-exact'
                exactMatch={exactMatch}
                possibleMatch={possibleMatch}
                conflict={conflict}
                unknown={unknown}
                setExactMatch={setExactMatch}
                setConflict={setConflict}
                setPossibleMatch={setPossibleMatch}
                setUnknown={setUnknown}
                isArticle={true}
                sourceUrl={selectedArticle[0]}
            />

        </Card>
    );
}

export default ArticleKnowledgeView;