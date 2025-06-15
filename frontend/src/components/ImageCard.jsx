import React, { useEffect } from 'react';
import '../App.css';

function ImageCard({ image, onAction }) {
  useEffect(() => {
    console.log("Image URL:", image.url);
  }, [image.url]);

  const cardClass = [
    'card',
    image.duplicate ? 'duplicate-border' : '',
    image.status === 'approved' ? 'approved-border' : ''
  ].join(' ');

  return (
    <div className={cardClass}>
      <img
        src={image.url || `/images/original/${image.filename}`}
        alt=""
        className="image"
      />
      <div className="card-actions">
        <button
          onClick={() => onAction(image.id || image.filename, 'approve')}
          className="approve-btn"
        >
          Approve
        </button>
        <button
          onClick={() => onAction(image.id || image.filename, 'delete')}
          className="delete-btn"
        >
          Delete
        </button>
      </div>
    </div>
  );
}

export default ImageCard;