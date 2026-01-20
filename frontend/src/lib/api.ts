import axios from 'axios';

const api = axios.create({
  baseURL: '/', // Proxy handles the rest
});

// Add auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
        // Redirect to login if unauthorized
        if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
            window.location.href = '/login';
        }
    }
    return Promise.reject(error);
  }
);

export default api;
