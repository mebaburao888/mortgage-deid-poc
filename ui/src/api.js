import axios from 'axios';

const BASE = 'http://localhost:8000';

export const api = {
  status: () => axios.get(`${BASE}/api/status`),
  query: (text, top_k) => axios.post(`${BASE}/api/query`, { text, top_k }),
  score: (payload) => axios.post(`${BASE}/api/score`, payload),
  export: (payload) => axios.post(`${BASE}/api/export`, payload),
  segments: (n) => axios.get(`${BASE}/api/segments`, { params: { n } }),
  segmentDetail: (id) => axios.get(`${BASE}/api/segment/${id}`),
  ingest: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return axios.post(`${BASE}/api/ingest`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  downloadUrl: (filename) => `${BASE}/api/download/${filename}`,
};
