import React, { useState } from 'react';
import { Input, Button, message } from 'antd';
import '../App.css';

function ScraperPanel({ refreshImages }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    if (!url) return message.error('Please enter a URL.');

    setLoading(true);

    try {
      const res = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const result = await res.json();

      if (res.ok && result.success && result.downloaded > 0) {
        message.success(`Scraped and uploaded ${result.downloaded} image${result.downloaded !== 1 ? 's' : ''}.`);
        refreshImages();
      } else if (res.ok && result.success && result.downloaded === 0) {
        message.error('Scraping succeeded, but no images were uploaded.');
      } else {
        message.error(result.error || 'Scrape failed.');
      }
    } catch (err) {
      message.error('Something went wrong.');
    } finally {
      setLoading(false);
      setUrl('');
    }
  };

  return (
    <div className="scraper-panel">
      <Input
        placeholder="Paste in your URL..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: '60%', marginRight: '1rem' }}
      />
      <Button
        className="scraper-btn"
        onClick={handleDownload}
        loading={loading}
      >
        Scrape
      </Button>
    </div>
  );
}

export default ScraperPanel;
