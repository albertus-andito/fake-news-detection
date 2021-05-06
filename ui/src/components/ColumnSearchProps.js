import React from 'react';
import { Button, Input, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

const getColumnSearchProps = (
    dataIndex,
    searchInput,
    searchText,
    setSearchText,
    searchedColumn,
    setSearchedColumn
) => ({
    filterDropdown: ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
    }) => (
        <div style={{ padding: 8 }}>
            <Input
                ref={searchInput}
                placeholder={`Search ${dataIndex}`}
                value={selectedKeys[0]}
                onChange={(e) =>
                    setSelectedKeys(e.target.value ? [e.target.value] : [])
                }
                onPressEnter={() =>
                    handleSearch(
                        selectedKeys,
                        confirm,
                        dataIndex,
                        setSearchText,
                        setSearchedColumn
                    )
                }
                style={{ width: 188, marginBottom: 8, display: 'block' }}
            />
            <Space>
                <Button
                    type="primary"
                    onClick={() =>
                        handleSearch(
                            selectedKeys,
                            confirm,
                            dataIndex,
                            setSearchText,
                            setSearchedColumn
                        )
                    }
                    icon={<SearchOutlined />}
                    size="small"
                    style={{ width: 90 }}
                >
                    Search
                </Button>
                <Button
                    onClick={() => handleReset(clearFilters, setSearchText)}
                    size="small"
                    style={{ width: 90 }}
                >
                    Reset
                </Button>
            </Space>
        </div>
    ),
    filterIcon: (filtered) => (
        <SearchOutlined style={{ color: filtered ? '#51258f' : undefined }} />
    ),
    onFilter: (value, record) =>{
        if (typeof dataIndex === 'string') {
            return record[dataIndex]
                    ? record[dataIndex]
                          .toString()
                          .toLowerCase()
                          .includes(value.toLowerCase())
                    : ''
        }
        return record[dataIndex[0]][dataIndex[1]]
                ? record[dataIndex[0]][dataIndex[1]]
                      .toString()
                      .toLowerCase()
                      .replace('http://dbpedia.org/resource/', '')
                      .replace('http://dbpedia.org/ontology/', '')
                      .includes(value.toLowerCase())
                : ''

    },
    onFilterDropdownVisibleChange: (visible) => {
        if (visible) {
            setTimeout(() => searchInput.current.select(), 100);
        }
    },
});

const handleSearch = (
    selectedKeys,
    confirm,
    dataIndex,
    setSearchText,
    setSearchedColumn
) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
};

const handleReset = (clearFilters, setSearchText) => {
    clearFilters();
    setSearchText('');
};

export { getColumnSearchProps };