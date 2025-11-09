export type ServiceStatus = 'PENDING' | 'BUILDING' | 'DEPLOYED' | 'FAILED';

export interface SchemaField {
  name: string;
  type: string;
  required?: boolean;
}

export interface EndpointSpec {
  path: string;
  method: string;
  schema_fields?: SchemaField[];
}

export interface ServiceSpec {
  endpoint?: EndpointSpec;
  // allow additional fields the AI may add
  [key: string]: any;
}

export interface ServiceMetadata {
  id: string;
  user_id: string;
  service_name: string;
  prompt: string;
  status: ServiceStatus;
  deployed_url?: string;
  build_log_url?: string;
  source_blob?: string;
  created_at: string; // ISO 8601 date string
  updated_at: string; // ISO 8601 date string
  spec?: ServiceSpec;
  error_message?: string;
}