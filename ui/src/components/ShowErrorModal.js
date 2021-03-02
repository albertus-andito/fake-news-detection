import {Modal} from "antd";

const showErrorModal = (message) => {
    Modal.error({
        title: 'Error!',
        content: (
            <div>
                {message}
            </div>
        ),
        onOk() {
            Modal.destroyAll();
        }
    });
}

export default showErrorModal;