import { useState } from 'react';
import { api } from '../api';

function OutcomeBadge({ outcome }) {
  const key = outcome || 'unknown';
  return <span className={`badge badge-${key}`}>{key}</span>;
}

export default function QueryTab() {
  const [text, setText] = useState('');
  const [topK, setTopK] = useState(10);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = () => {
    if (!text.trim()) return;
    setLoading(true);
    setError('');
    api.query(text.trim(), topK)
      .then((r) => setResults(r.data.results))
      .catch((e) => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <div className="card">
        <div className="form-row">
          <label>Search profiles</label>
          <input
            type="text"
            placeholder="e.g. Millennial first-time buyer, good credit, Purchase loan..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
        </div>
        <div className="form-row">
          <label>Top K: {topK}</label>
          <input
            type="range"
            min={1}
            max={50}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          />
        </div>
        <button className="btn" onClick={submit} disabled={loading || !text.trim()}>
          {loading ? 'Searching...' : 'Search'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {results && (
        <div className="card">
          <div className="section-title">{results.length} results</div>
          {results.length === 0 ? (
            <div className="loading">No results found</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Distance</th>
                    <th>Generation</th>
                    <th>Credit</th>
                    <th>Loan Purpose</th>
                    <th>Outcome</th>
                    <th>Email Token</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.rank}>
                      <td>{r.rank}</td>
                      <td>{r.distance}</td>
                      <td>{r.generation || '—'}</td>
                      <td>{r.credit_profile || '—'}</td>
                      <td>{r.loan_purpose || '—'}</td>
                      <td><OutcomeBadge outcome={r.outcome} /></td>
                      <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{r.email_token || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
