import React from "react";

export const convertToDBpediaLink = (text) => {
    if (text.startsWith('http://dbpedia.org/')){
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