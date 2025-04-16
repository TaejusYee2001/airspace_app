import React, { useState } from 'react';
import GlobeComponent from './components/Globe';

function App() {
  const [scheduling, setScheduling] = useState(false);

  return (
    <div className="App" style={{ height: "100vh", width: "100vw" }}>
      <GlobeComponent schedulingExternal={scheduling} setSchedulingExternal={setScheduling} />
    </div>
  );
}

export default App;