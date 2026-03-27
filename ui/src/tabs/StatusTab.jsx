import { useEffect, useState } from 'react';
import { api } from '../api';

const OUTCOME_ORDER = ['funded', 'rejected', 'ghost', 'unknown'];

function badgeFill(outcome) {
  const map = { funded: 'funded', rejected: 'rejected', ghost: 'ghost' };
  return map[outcome] || 'unknown';
}

export default function StatusTab() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const load = () => {
    api.status()
      .then((r) => setData(r.data))
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, []);

  if (error) return <div className="error">Error: {error}</div>;
  if (!data) return <div className="loading">Loading...</div>;

  const outcomes = data.outcome_breakdown || {};
  const total = Object.values(outcomes).reduce((a, b) => a + b, 0);
  const allOutcomes = [
    ...OUTCOME_ORDER.filter((k) => k in outcomes),
    ...Object.keys(outcomes).filter((k) => !OUTCOME_ORDER.includes(k)),
  ];

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{data.record_count.toLocaleString()}</div>
          <div className="stat-label">Records</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data.total_docs.toLocaleString()}</div>
          <div className="stat-label">Vectors</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data.tranches.length}</div>
          <div className="stat-label">Tranches</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{total.toLocaleString()}</div>
          <div className="stat-label">Labelled</div>
        </div>
      </div>

      {data.tranches.length > 0 && (
        <div className="card">
          <div className="section-title">Tranches</div>
          <div className="feature-pills">
            {data.tranches.map((t) => (
              <span key={t} className="pill">{t}</span>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="section-title">Outcome Breakdown</div>
        {total === 0 ? (
          <div className="loading">No labelled records</div>
        ) : (
          <div className="bar-chart">
            {allOutcomes.map((outcome) => {
              const count = outcomes[outcome] || 0;
              const pct = total > 0 ? (count / total) * 100 : 0;
              const fill = badgeFill(outcome);
              return (
                <div key={outcome} className="bar-row">
                  <div className="bar-label">{outcome}</div>
                  <div className="bar-track">
                    <div
                      className={`bar-fill bar-fill-${fill}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="bar-count">{count}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
