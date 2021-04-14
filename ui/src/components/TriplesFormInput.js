import {Button, Form, Input, Row, Space} from 'antd';
import {MinusCircleOutlined, PlusOutlined} from '@ant-design/icons';

function TriplesFormInput() {
    return(
        <Form.List name='triples'>
            {(fields, { add, remove }) => (
                <>
                    {fields.map(field => (
                        <Space key={field.key} style={{ display: 'flex', marginBottom: 0, justifyContent: 'center', width: '100%' }} align='baseline'>
                            <Form.Item
                                {...field}
                                name={[field.name, 'subject']}
                                fieldKey={[field.fieldKey, 'subject']}
                                rules={[{ required: true, message: 'Missing subject' }]}
                                style={{ width: '100%', marginRight: 100 }}
                            >
                                <Input placeholder='Subject' />
                            </Form.Item>
                            <Form.Item
                                {...field}
                                name={[field.name, 'relation']}
                                fieldKey={[field.fieldKey, 'relation']}
                                rules={[{ required: true, message: 'Missing relation' }]}
                                style={{ width: '100%', marginRight: 100 }}
                            >
                                <Input placeholder='Relation' />
                            </Form.Item>
                            <Form.Item
                                {...field}
                                name={[field.name, 'objects']}
                                fieldKey={[field.fieldKey, 'objects']}
                                rules={[{ required: true, message: 'Missing object' }]}
                                style={{ width: '100%', marginRight: 100 }}
                            >
                                <Input placeholder='Object' />
                            </Form.Item>
                            <MinusCircleOutlined onClick={() => remove(field.name)} />
                        </Space>
                    ))}
                    <Form.Item>
                        <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                            More triple
                        </Button>
                    </Form.Item>
                </>
            )}
        </Form.List>
    );
}

export default TriplesFormInput;