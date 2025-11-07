import { auth } from './firebase';
import { ServiceMetadata } from '../types';

// --- DEBUG LINE ---
// This will print the URL being used to the browser console on your live site.
console.log("API Base URL:", import.meta.env.VITE_API_BASE_URL);

const getApiClient = async () => {
  const user = auth.currentUser;
  // This check is critical for the race condition.
  if (!user) {
    // We wait for the auth state to be ready.
    // This is a simple promise-based way to wait.
    await new Promise<void>(resolve => {
        const unsubscribe = auth.onAuthStateChanged(user => {
            if (user) resolve();
            unsubscribe();
        });
    });
    // Re-check the user after waiting
    const freshUser = auth.currentUser;
    if (!freshUser) {
        throw new Error("User not authenticated after waiting.");
    }
    return freshUser;
  }
  return user;
};

const getHeaders = async () => {
    const user = await getApiClient();
    const token = await user.getIdToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
    };
};

const baseURL = import.meta.env.VITE_API_BASE_URL;

export const getServices = async (): Promise<ServiceMetadata[]> => {
  const headers = await getHeaders();
  const response = await fetch(`${baseURL}/services`, { headers });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
};

export const generateService = async (prompt: string): Promise<ServiceMetadata> => {
  const headers = await getHeaders();
  const response = await fetch(`${baseURL}/services/generate`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ prompt }),
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
};

export const deleteService = async (serviceId: string): Promise<{ message: string }> => {
  const headers = await getHeaders();
  const response = await fetch(`${baseURL}/services/${serviceId}`, {
    method: 'DELETE',
    headers,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
};