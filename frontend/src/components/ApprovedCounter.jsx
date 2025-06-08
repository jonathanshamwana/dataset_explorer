import React, { useState, useEffect } from 'react';
import '../App.css';

function ApprovedCounter() {
  const [stats, setStats] = useState({ approved: 0, total: 0 });
  const GOAL = 3000;

  const fetchStats = () => {
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => setStats(data));
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const percentage = Math.min((stats.approved / GOAL) * 100, 100);

  return (
    <div className="approved-counter">
      <div className="counter-text">{stats.approved} / {GOAL} Approved</div>
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
}

export default ApprovedCounter;
