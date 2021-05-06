import React from "react";
import {notification} from "antd";

export const convertToDBpediaLink = (text) => {
    if (text.startsWith('http://dbpedia.org/')) {
        return (
            <a href={text.replace('http://dbpedia.org/', 'http://localhost:8890/')}>
                {text.substring(text.lastIndexOf('/') + 1)}
            </a>
        );
    }
    return text;
}

export const convertRelationToDBpediaLink = (text) => {
    const tokens = text.split(' ');
    if (tokens.length === 1) {
        return convertToDBpediaLink(text);
    }
    if (tokens.length === 3) {
        return (<>
            {tokens[0]} {convertToDBpediaLink(tokens[1])} {tokens[2]}
        </>)
    }
    let element = '';
    tokens.forEach(token => element += convertToDBpediaLink(token) + ' ')
    return (<p>{element}</p>);
}

export const convertObjectsToDBpediaLink = (objects) => {
    const elements = [];
    objects.forEach(o => elements.push(convertToDBpediaLink(o)));
    return elements;
};

export const tripleColumns = [
    {
        title: 'Subject',
        dataIndex: 'subject',
        key: 'subject',
        render: convertToDBpediaLink,
    },
    {
        title: 'Relation',
        dataIndex: 'relation',
        key: 'relation',
        render: convertToDBpediaLink,
    },
    {
        title: 'Object',
        dataIndex: 'objects',
        key: 'object',
        render: convertObjectsToDBpediaLink,
    },
];

export const showErrorNotification = (message) => {
    notification['error']({
        message: 'Error!',
        description: message,
    });
}