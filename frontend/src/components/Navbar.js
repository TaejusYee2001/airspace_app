import React from 'react';
import '../index.css';

function Navbar({ onScheduleClick }) {
  return (
    <div className="navbar">
      <h2>Flight Visualizer</h2>
      <div className="navbar-buttons">
        <button
          className="navbar-button"
          onClick={() => alert("Admin Page coming soon!")}
        >
          Admin Page
        </button>
        <button
          className="navbar-button"
          onClick={onScheduleClick}
        >
          Schedule Flight
        </button>
      </div>
    </div>
  );
}

export default Navbar;