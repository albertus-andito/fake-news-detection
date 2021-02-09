import {Button, Card, Form, Input, Typography} from 'antd';
import axios from 'axios';

const { TextArea } = Input;

const layout = {
    labelCol:  {
        span: 2,
    },
    wrapperCol: {
        span: 21,
    }
}

const tailLayout = {
    wrapperCol: {
        offset: 2,
        span: 16,
    },
};

function FactCheckerView() {

    const onSubmit = (values) => {
        console.log('Submitted', values);
        axios.post('/fc/simple/fact-check/', {
            text: values.text
        })
        .then(function (response) {
            console.log(response);
        })
    }

    return(
        <Card>
            <Typography.Title style={{ textAlign: 'center' }}>Fact Checker</Typography.Title>

            <Form {...layout} onFinish={onSubmit} >
                <Form.Item
                    label='Article Text'
                    name='text'
                >
                    <TextArea rows={4}/>
                </Form.Item>
                <Form.Item {...tailLayout}>
                    <Button type='primary' htmlType='submit'>
                        Fact Check
                    </Button>
                </Form.Item>
            </Form>
        </Card>
    )
}

export default FactCheckerView;