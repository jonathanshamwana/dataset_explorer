import React, { useState, useEffect, useCallback } from 'react';
import UploadPanel from './components/UploadPanel';
import ImageCard from './components/ImageCard';
import Toolbar from './components/Toolbar';
import Navbar from './components/Navbar';
import ApprovedCounter from './components/ApprovedCounter';
import ScraperPanel from './components/ScraperPanel';
import { Tabs, Pagination } from 'antd';
import './App.css';

function App() {
  const [images, setImages] = useState([]);
  const [status, setStatus] = useState('all');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const IMAGES_PER_PAGE = 50;

  const fetchImages = useCallback(() => {
    const offset = (page - 1) * IMAGES_PER_PAGE;
    fetch(`/api/images?status=${status}&limit=${IMAGES_PER_PAGE}&offset=${offset}`)
      .then(res => res.json())
      .then(data => {
        setImages(data.images);
        setTotal(data.total);
      });
  }, [page, status]);  

  useEffect(() => {
    fetchImages();
  }, [status, page]);

  const handleAction = (imageId, action) => {
    fetch('/api/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imageId, action })
    }).then(() => setImages(prev => prev.filter(img => img.id !== imageId)));
  };

  return (
    <>
      <Navbar />
      <div className="app-container">
      <h1 className="heading">Dataset Explorer</h1>
      <UploadPanel refreshImages={fetchImages} />
      <ScraperPanel refreshImages={fetchImages} />
      <Toolbar />
      <ApprovedCounter />
      <div className="tabs-wrapper">
        <Tabs
          activeKey={status}
          onChange={key => {
            setStatus(key);
            setPage(1);
          }}
          items={[
            { key: 'all', label: 'All' },
            { key: 'approved', label: 'Approved' },
            { key: 'deleted', label: 'Deleted' }
          ]}
        />
      </div>
      <div className="image-grid">
        {images?.map(image => (
          <ImageCard key={image.id || image.filename} image={image} onAction={handleAction} />
        ))}
      </div>

      <Pagination
        current={page}
        className={"page-tabs"}
        pageSize={IMAGES_PER_PAGE}
        total={total}
        onChange={setPage}
        showSizeChanger={false}
      />
      </div>
    </>
  );
}

export default App;