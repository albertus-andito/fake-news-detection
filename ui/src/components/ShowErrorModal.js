import {Modal} from "antd";

function showErrorModal(message) {
    Modal.error({
        title: 'Error!',
        content:
                {message}
        ,
        onOk() {
            Modal.destroyAll();
        }
    });
}

export default showErrorModal;