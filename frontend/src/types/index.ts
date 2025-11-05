export type ServiceStatus = 'PENDING' | 'BUILDING' | 'DEPLOYED' | 'FAILED' | 'DELETING';

export interface ServiceMetadata {
  id: string;
  user_id: string;
  service_name: string;
  prompt: string;
  status: ServiceStatus;
  deployed_url?: string;
  build_log_url?: string;
  created_at: string; // ISO 8601 date string
  updated_at: string; // ISO 8601 date string
  spec: object;
}