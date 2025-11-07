import { auth } from './firebase';
import { ServiceMetadata } from '../types';

console.log("API Base URL:", import.meta.env.VITE_API_BASE_URL);

const getApiClient = async () => {
  // ... (rest of the file is the same)
};

const getApiClient = async () => {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated.");
  }
  const token = await user.getIdToken();
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  const baseURL = import.meta.env.VITE_API_BASE_URL;

  return {
    get: async <T>(path: string): Promise<T> => {
      const response = await fetch(`${baseURL}${path}`, { headers });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },
    post: async <T>(path: string, body: object): Promise<T> => {
      const response = await fetch(`${baseURL}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },
    delete: async <T>(path: string): Promise<T> => {
       const response = await fetch(`${baseURL}${path}`, {
        method: 'DELETE',
        headers,
      });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }
  };
};

export const getServices = async (): Promise<ServiceMetadata[]> => {
  const client = await getApiClient();
  return client.get('/services');
};

export const generateService = async (prompt: string): Promise<ServiceMetadata> => {
  const client = await getApiClient();
  return client.post('/services/generate', { prompt });
};

export const deleteService = async (serviceId: string): Promise<{ message: string }> => {
  const client = await getApiClient();
  return client.delete(`/services/${serviceId}`);
};