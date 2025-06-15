import React from 'react';
import { Button } from "antd";
import '../App.css';

function Toolbar() {
  const runFilters = async () => {
    await fetch('/api/run-filters', { method: 'POST' });
    alert('Auto-filters applied');
  };

  return (
    <div className="mb-4">
      {/* <Button
       onClick={runFilters} 
       className="filters-button"
      >
        Run Auto Filters
      </Button> */}
    </div>
  );
}

export default Toolbar;
