import { useState, useEffect, useRef } from 'react';
import { ServiceMetadata, ServiceStatus } from '@/types';
// ... rest of imports
import { formatDistanceToNow } from 'date-fns';
import { Copy, Trash2, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';
import DeleteServiceDialog from './DeleteServiceDialog';

// ... (rest of the component code is perfect as-is)
interface ServiceCardProps {
  service: ServiceMetadata;
}
