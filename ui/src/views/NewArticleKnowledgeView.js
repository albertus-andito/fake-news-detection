import {Button, Card, Form, Input, Radio, Spin, Typography} from "antd";
import React, {useState} from 'react';
import TriplesTables from "../components/TriplesTables";
import axios from "axios";
import {handleFactCheckResponse} from "./FactCheckerView";

function NewArticleKnowledgeView() {
    const [loading, setLoading] = useState(false);
    const [currentUrl, setCurrentUrl] = useState();

    const [exactMatch, setExactMatch] = useState([]);
    const [possibleMatch, setPossibleMatch] = useState([]);
    const [conflict, setConflict] = useState([]);
    const [unknown, setUnknown] = useState([]);

    const extractionScopes = [
        { label: 'Noun phrases', value: 'noun_phrases'},
        { label: 'Named entities', value: 'named_entities'},
        { label: 'All', value: 'all'},
    ]
    const autoUpdateOptions = [
        { label: 'Yes', value: true},
        { label: 'No', value: false}
    ]

    const onSubmit = (values) => {
        setLoading(true);
        setCurrentUrl(values.url);
        console.log('Submitted', values);
        axios.post(`/kgu/articles/`, {
            url: values.url,
            extraction_scope: values.extractionScope,
            kg_auto_update: values.autoUpdate,
        })
            .then((res) => {
                axios.get(`/kgu/article-triples/pending/${values.url}`)
                .then((res) => {
                    axios.post('/fc/non-exact/fact-check/triples-sentences/', res.data.triples)
                        .then((res) => {
                            handleFactCheckResponse(res, setLoading, setExactMatch, setPossibleMatch, setConflict, setUnknown)
                        })
                        .catch((err) => {
                            console.log(err);
                        })
                    })
            })
    }

    return(
         <Card>
             <Typography.Title style={{ textAlign: 'center' }}>Knowledge Graph Updater</Typography.Title>
             <Typography.Title level={2} style={{ textAlign: 'center' }}>Add New Article</Typography.Title>

             <Form layout='horizontal' onFinish={onSubmit} requiredMark={false} style={{ margin: '24px 0 0 0'}}>
                 <Form.Item
                    label='Extraction Scope'
                    name='extractionScope'
                 >
                     <Radio.Group
                        options={extractionScopes}
                        defaultValue='noun_phrases'
                        optionType='button'
                        buttonStyle='solid'
                     />
                 </Form.Item>
                 <Form.Item
                    label='Knowledge Graph Auto Update'
                    name='autoUpdate'
                 >
                     <Radio.Group
                        options={autoUpdateOptions}
                        defaultValue={false}
                        optionType='button'
                        buttonStyle='solid'
                     />
                 </Form.Item>
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
                    <Input disabled={loading}/>
                 </Form.Item>
                 <Form.Item>
                    <Button type='primary' htmlType='submit' disabled={loading} style={{ width: '100%'}}>
                        Submit Article
                    </Button>
                 </Form.Item>
             </Form>

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
                sourceUrl={currentUrl}
            />
         </Card>


    )
}

export default NewArticleKnowledgeView;