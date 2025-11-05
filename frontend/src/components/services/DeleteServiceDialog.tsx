import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteService } from '@/lib/api-client';
// ... rest of imports
import toast from 'react-hot-toast';
import { Loader2, TriangleAlert } from 'lucide-react';
import { ServiceMetadata } from '@/types';

// ... (rest of the component code is perfect as-is)
interface DeleteServiceDialogProps {
  //...
}
