import { useState } from 'react';
import { api } from '../api';

function rateClass(r) {
  if (r > 0.5) return 'funded-rate-high';
  if (r >= 0.2) return 'funded-rate-medium';
  return 'funded-rate-low';
}

export default function SegmentsTab() {
  const [n, setN] = useState(4);
  const [segments, setSegments] = useState(null);
  const [selected, setSelected] = useState(null);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [descLoading, setDescLoading] = useState(false);
  const [error, setError] = useState('');

  const discover = () => {
    setLoading(true);
    setError('');
    setSelected(null);
    setDescription('');
    api.segments(n)
      .then((r) => setSegments(r.data.segments))
      .catch((e) => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  };

  const selectSegment = (seg) => {
    if (selected?.id === seg.id) {
      setSelected(null);
      setDescription('');
      return;
    }
    setSelected(seg);
    setDescLoading(true);
    api.segmentDetail(seg.id)
      .then((r) => setDescription(r.data.description))
      .catch(() => setDescription(''))
      .finally(() => setDescLoading(false));
  };

  return (
    <div>
      <div className="card">
        <div className="form-row">
          <label>Number of clusters</label>
          <input
            type="number"
            min={2}
            max={20}
            value={n}
            onChange={(e) => setN(Number(e.target.value))}
            style={{ width: 100 }}
          />
        </div>
        <button className="btn" onClick={discover} disabled={loading}>
          {loading ? 'Discovering...' : 'Discover Segments'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {segments && (
        <>
          <div className="section-title">{segments.length} segments — click a card for details</div>
          <div className="segment-grid">
            {segments.map((seg) => (
              <div
                key={seg.id}
                className={`segment-card${selected?.id === seg.id ? ' selected' : ''}`}
                onClick={() => selectSegment(seg)}
              >
                <div className="segment-label">{seg.label || `Segment ${seg.id}`}</div>
                <div className={`${rateClass(seg.funded_rate)}`} style={{ fontWeight: 600, marginBottom: 4 }}>
                  {(seg.funded_rate * 100).toFixed(1)}% funded
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{seg.size} records</div>
                <div className="feature-pills">
                  {Object.entries(seg.top_features || {})
                    .filter(([, v]) => v)
                    .slice(0, 4)
                    .map(([k, v]) => (
                      <span key={k} className="pill">{v}</span>
                    ))}
                </div>
              </div>
            ))}
          </div>

          {selected && (
            <div className="description-box">
              {descLoading ? (
                <span className="loading">Loading description...</span>
              ) : (
                description || 'No description available.'
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
