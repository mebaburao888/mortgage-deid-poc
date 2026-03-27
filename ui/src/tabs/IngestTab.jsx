import { useRef, useState } from 'react';
import { api } from '../api';

export default function IngestTab() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef();

  const pickFile = (e) => {
    const f = e.target.files[0];
    if (f) { setFile(f); setResult(null); setError(''); }
  };

  const upload = () => {
    if (!file) return;
    setLoading(true);
    setError('');
    api.ingest(file)
      .then((r) => setResult(r.data))
      .catch((e) => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <div className="card">
        <div
          className={`upload-area${file ? ' has-file' : ''}`}
          onClick={() => inputRef.current.click()}
          style={{ cursor: 'pointer' }}
        >
          {file ? (
            <>
              <div style={{ fontSize: 16, fontWeight: 600 }}>{file.name}</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>
                {(file.size / 1024).toFixed(1)} KB · click to change
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 24, marginBottom: 8 }}>↑</div>
              <div>Click to select a CSV file</div>
            </>
          )}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={pickFile}
        />
        <button className="btn" onClick={upload} disabled={loading || !file}>
          {loading ? 'Uploading & ingesting...' : 'Upload & Ingest'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <div className="card">
          <div className="success">Ingest complete</div>
          <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 12 }}>
            {[
              ['Tranche ID', result.tranche_id],
              ['Records', result.count],
              ['Timestamp', result.timestamp],
              ['Model', result.model],
              ['Collection', result.chroma_collection],
            ].map(([label, value]) => (
              <div key={label} className="stat-card">
                <div style={{ fontSize: 13, fontWeight: 600, wordBreak: 'break-all' }}>{value}</div>
                <div className="stat-label">{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
