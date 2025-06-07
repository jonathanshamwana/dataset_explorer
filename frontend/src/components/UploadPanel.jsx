import React from 'react';
import { InboxOutlined } from '@ant-design/icons';
import { message, Upload } from 'antd';
import '../App.css';

const { Dragger } = Upload;

function UploadPanel({ setImages }) {
  const props = {
    name: 'files',
    multiple: true,
    action: '/api/upload',
    onChange(info) {
      const { status } = info.file;
      if (status === 'done') {
        if (Array.isArray(info.file.response)) {
          setImages(prev => [...info.file.response, ...prev]);
          message.success(`${info.file.name} uploaded successfully.`);
        } else {
          message.error(`Unexpected server response for ${info.file.name}.`);
        }
      } else if (status === 'error') {
        message.error(`${info.file.name} upload failed.`);
      }
    },
    onError(err) {
      message.error(`Upload failed: ${err.message}`);
    }
  };

  return (
    <div className="upload-panel">
      <div className="upload-wrapper">
        <Dragger 
          {...props} 
          className="upload-dragger"
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">Click or drag to upload</p>
        </Dragger>
      </div>
    </div>
  );
}

export default UploadPanel;