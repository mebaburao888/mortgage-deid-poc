import { useState } from 'react';
import StatusTab from './tabs/StatusTab';
import QueryTab from './tabs/QueryTab';
import ScoreTab from './tabs/ScoreTab';
import SegmentsTab from './tabs/SegmentsTab';
import ExportTab from './tabs/ExportTab';
import IngestTab from './tabs/IngestTab';

const TABS = [
  { id: 'status',   label: 'Status' },
  { id: 'query',    label: 'Query' },
  { id: 'score',    label: 'Score a Lead' },
  { id: 'segments', label: 'Segments' },
  { id: 'export',   label: 'Export' },
  { id: 'ingest',   label: 'Ingest' },
];

function TabContent({ tab }) {
  switch (tab) {
    case 'status':   return <StatusTab />;
    case 'query':    return <QueryTab />;
    case 'score':    return <ScoreTab />;
    case 'segments': return <SegmentsTab />;
    case 'export':   return <ExportTab />;
    case 'ingest':   return <IngestTab />;
    default:         return null;
  }
}

export default function App() {
  const [tab, setTab] = useState('status');

  return (
    <>
      <nav className="nav">
        <span className="nav-brand">Mortgage De-ID POC</span>
        <div className="nav-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`nav-tab${tab === t.id ? ' active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>
      <TabContent tab={tab} />
    </>
  );
}
