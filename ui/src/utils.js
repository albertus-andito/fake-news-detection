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

export const convertObjectsToDBpediaLink = (objects) => {
    const elements = [];
    objects.forEach(o => elements.push(convertToDBpediaLink(o)));
    return elements;
};