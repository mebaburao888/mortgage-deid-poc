import { useState } from 'react';
import { api } from '../api';

export default function ExportTab() {
  const [mode, setMode] = useState('query');
  const [queryText, setQueryText] = useState('');
  const [topK, setTopK] = useState(200);
  const [filters, setFilters] = useState([{ key: '', value: '' }]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addFilter = () => setFilters((f) => [...f, { key: '', value: '' }]);
  const removeFilter = (i) => setFilters((f) => f.filter((_, idx) => idx !== i));
  const setFilter = (i, field, val) =>
    setFilters((f) => f.map((row, idx) => (idx === i ? { ...row, [field]: val } : row)));

  const submit = () => {
    setLoading(true);
    setError('');
    setResult(null);

    let payload;
    if (mode === 'query') {
      if (!queryText.trim()) { setError('Enter a query'); setLoading(false); return; }
      payload = { query_text: queryText.trim(), top_k: topK };
    } else {
      const validFilters = filters.filter((f) => f.key.trim() && f.value.trim());
      if (validFilters.length === 0) { setError('Add at least one filter'); setLoading(false); return; }
      const filterObj = Object.fromEntries(validFilters.map((f) => [f.key.trim(), f.value.trim()]));
      payload = { filters: filterObj };
    }

    api.export(payload)
      .then((r) => setResult(r.data))
      .catch((e) => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <div className="card">
        <div className="section-title">Export mode</div>
        <div className="radio-group">
          <label className="radio-label">
            <input type="radio" checked={mode === 'query'} onChange={() => setMode('query')} />
            Similarity query
          </label>
          <label className="radio-label">
            <input type="radio" checked={mode === 'filter'} onChange={() => setMode('filter')} />
            Filter
          </label>
        </div>

        {mode === 'query' ? (
          <>
            <div className="form-row">
              <label>Query text</label>
              <input
                type="text"
                placeholder="e.g. high-income Millennial purchase loans..."
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
              />
            </div>
            <div className="form-row">
              <label>Top K: {topK}</label>
              <input
                type="range"
                min={10}
                max={500}
                step={10}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
              />
            </div>
          </>
        ) : (
          <>
            <div className="section-title">Filters</div>
            {filters.map((f, i) => (
              <div key={i} className="filter-row">
                <input
                  type="text"
                  placeholder="key (e.g. outcome)"
                  value={f.key}
                  onChange={(e) => setFilter(i, 'key', e.target.value)}
                />
                <input
                  type="text"
                  placeholder="value (e.g. funded)"
                  value={f.value}
                  onChange={(e) => setFilter(i, 'value', e.target.value)}
                />
                {filters.length > 1 && (
                  <button className="btn btn-secondary btn-sm" onClick={() => removeFilter(i)}>✕</button>
                )}
              </div>
            ))}
            <button className="btn btn-secondary btn-sm" onClick={addFilter} style={{ marginBottom: 14 }}>
              + Add filter
            </button>
          </>
        )}

        <button className="btn" onClick={submit} disabled={loading}>
          {loading ? 'Exporting...' : 'Export Audience'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <div className="card">
          <div className="success">{result.count} records exported</div>
          <div style={{ marginTop: 12 }}>
            <a
              className="download-link"
              href={`http://localhost:8000${result.file_url}`}
              download
            >
              ↓ Download CSV
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
