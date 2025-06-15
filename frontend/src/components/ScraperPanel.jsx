import React, { useState } from 'react';
import { Input, Button, message } from 'antd';
import '../App.css';

function ScraperPanel({ refreshImages }) {
  const [galleryUrl, setGalleryUrl] = useState('');
  const [freeformUrl, setFreeformUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGalleryDownload = async () => {
    if (!galleryUrl) return message.error('Please enter a GalleryDL URL.');
    setLoading(true);
    try {
      const res = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: galleryUrl })
      });

      const result = await res.json();
      console.log("RESULT", result);

      if (res.ok && result.success && result.downloaded > 0) {
        message.success(`Scraped and uploaded ${result.downloaded} image${result.downloaded !== 1 ? 's' : ''}.`);
        refreshImages();
      } else if (res.ok && result.success && result.downloaded === 0) {
        message.error('Scraping succeeded, but no images were uploaded.');
      } else {
        message.error(result.error || 'GalleryDL scrape failed.');
      }
    } catch (err) {
      message.error('Something went wrong during GalleryDL scraping.');
    } finally {
      setLoading(false);
      setGalleryUrl('');
    }
  };

  const handleFreeScrape = async () => {
    if (!freeformUrl) return message.error('Please enter a URL for freeform scraping.');

    setLoading(true);
    try {
      const res = await fetch('/api/freescrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: freeformUrl })
      });

      const result = await res.json();

      if (res.ok && result.success && result.downloaded > 0) {
        message.success(`Freeform scrape uploaded ${result.downloaded} image${result.downloaded !== 1 ? 's' : ''}.`);
        refreshImages();
      } else if (res.ok && result.success && result.downloaded === 0) {
        message.error('Freeform scraping succeeded, but no images were uploaded.');
      } else {
        message.error(result.error || 'Freeform scrape failed.');
      }
    } catch (err) {
      message.error('Something went wrong during freeform scraping.');
    } finally {
      setLoading(false);
      setFreeformUrl('');
    }
  };

  return (
    <div className="scraper-panel">
      <Input
        placeholder="GalleryDL scraping — paste your URL..."
        value={galleryUrl}
        onChange={(e) => setGalleryUrl(e.target.value)}
        style={{ width: '60%', marginRight: '1rem' }}
      />
      <Button
        className="scraper-btn"
        onClick={handleGalleryDownload}
        loading={loading}
      >
        Scrape
      </Button>

      <div>
        <Input
          placeholder="Freeform scraping — paste your URL..."
          value={freeformUrl}
          onChange={(e) => setFreeformUrl(e.target.value)}
          style={{ width: '60%', marginRight: '1rem' }}
        />
        <Button
          className="scraper-btn free-form-btn"
          onClick={handleFreeScrape}
          loading={loading}
        >
          Scrape
        </Button>
      </div>
    </div>
  );
}

export default ScraperPanel;
