import { useState } from 'react';
import { api } from '../api';

const DEFAULTS = {
  fico: 700,
  income: 80000,
  loan_purpose: 'Purchase',
  loan_type: 'Conventional',
  generation: 'Millennial',
  credit_profile: 'Good',
  channel: 'Online',
};

function scoreClass(s) {
  if (s >= 70) return 'score-high';
  if (s >= 40) return 'score-medium';
  return 'score-low';
}

function scoreLabel(s) {
  if (s >= 70) return 'High propensity';
  if (s >= 40) return 'Medium propensity';
  return 'Low propensity';
}

export default function ScoreTab() {
  const [form, setForm] = useState(DEFAULTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = () => {
    setLoading(true);
    setError('');
    api.score({ ...form, fico: Number(form.fico), income: Number(form.income) })
      .then((r) => setResult(r.data))
      .catch((e) => setError(e.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <div className="card">
        <div className="form-grid">
          <div>
            <label>FICO Score</label>
            <input
              type="number"
              min={300}
              max={850}
              value={form.fico}
              onChange={(e) => set('fico', e.target.value)}
            />
          </div>
          <div>
            <label>Annual Income ($)</label>
            <input
              type="number"
              min={0}
              step={1000}
              value={form.income}
              onChange={(e) => set('income', e.target.value)}
            />
          </div>
          <div>
            <label>Loan Purpose</label>
            <select value={form.loan_purpose} onChange={(e) => set('loan_purpose', e.target.value)}>
              {['Purchase', 'Refinance', 'Cash-Out', 'HELOC'].map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </div>
          <div>
            <label>Loan Type</label>
            <select value={form.loan_type} onChange={(e) => set('loan_type', e.target.value)}>
              {['Conventional', 'FHA', 'VA', 'Jumbo'].map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </div>
          <div>
            <label>Generation</label>
            <select value={form.generation} onChange={(e) => set('generation', e.target.value)}>
              {['GenZ', 'Millennial', 'GenX', 'Boomer', 'Silent'].map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </div>
          <div>
            <label>Credit Profile</label>
            <select value={form.credit_profile} onChange={(e) => set('credit_profile', e.target.value)}>
              {['Exceptional', 'Excellent', 'Very Good', 'Good', 'Fair', 'Poor'].map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </div>
          <div>
            <label>Channel</label>
            <select value={form.channel} onChange={(e) => set('channel', e.target.value)}>
              {['Social', 'Direct', 'Referral', 'Broker', 'Online'].map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
          </div>
        </div>
        <button className="btn" onClick={submit} disabled={loading}>
          {loading ? 'Scoring...' : 'Score Lead'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <div className="card">
          <div className="score-display">
            <div className={`score-number ${scoreClass(result.score)}`}>{result.score}</div>
            <div className={`score-label ${scoreClass(result.score)}`}>{scoreLabel(result.score)}</div>
            <div className="score-meta">
              Funded rate: {(result.funded_rate * 100).toFixed(1)}% &nbsp;·&nbsp;
              Based on {result.neighbor_count} nearest neighbors
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
