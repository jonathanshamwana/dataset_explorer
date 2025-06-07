import React, { useState } from 'react';
import { Input, Button, message } from 'antd';

function ScraperPanel() {
  const [url, setUrl] = useState('');

  const handleDownload = async () => {
    if (!url) return message.error('Please enter a URL.');

    try {
      const res = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const result = await res.json();

      if (res.ok && result.success) {
        message.success(`Downloaded ${result.downloaded} images.`);
      } else {
        message.error(result.error || 'Download failed.');
      }
    } catch (err) {
      message.error('Something went wrong. Check your URL or try again.');
    }

    setUrl('');
  };

  return (
    <div className="scraper-panel">
      <Input
        placeholder="Paste in a URL..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: '60%', marginRight: '1rem' }}
      />
      <Button className="scraper-btn" onClick={handleDownload} >
        Scrape
      </Button>
    </div>
  );
}

export default ScraperPanel;
