import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteService } from '@/lib/api-client';
import toast from 'react-hot-toast';
import { Loader2, TriangleAlert } from 'lucide-react';
import { ServiceMetadata } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface DeleteServiceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  service: ServiceMetadata | null;
}

const DeleteServiceDialog: React.FC<DeleteServiceDialogProps> = ({ isOpen, onClose, service }) => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: deleteService,
    onMutate: async (deletedServiceId: string) => {
        await queryClient.cancelQueries({ queryKey: ['services'] });
        const previousServices = queryClient.getQueryData<ServiceMetadata[]>(['services']);
        queryClient.setQueryData<ServiceMetadata[]>(['services'], (old) =>
            old?.map(s => s.id === deletedServiceId ? { ...s, status: 'DELETING' } : s)
        );
        toast.loading('Deleting service...', { id: `delete-${deletedServiceId}` });
        onClose();
        return { previousServices };
    },
    onError: (err, variables, context) => {
      if (context?.previousServices) {
        queryClient.setQueryData(['services'], context.previousServices);
      }
      toast.error('Failed to delete service.', { id: `delete-${variables}` });
    },
    onSuccess: (data, variables) => {
      toast.success('Service deletion initiated.', { id: `delete-${variables}` });
    },
    onSettled: () => {
        queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  const handleDelete = () => {
    if (service) {
      mutation.mutate(service.id);
    }
  };
  
  if (!isOpen || !service) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/50">
            <TriangleAlert className="h-6 w-6 text-red-600 dark:text-red-400" aria-hidden="true" />
          </div>
          <DialogTitle className="text-center mt-4">Delete Service</DialogTitle>
          <DialogDescription className="text-center">
            Are you sure you want to delete the service "{service.service_name}"? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="sm:justify-center gap-2 pt-4">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={mutation.isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={mutation.isLoading}
          >
            {mutation.isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DeleteServiceDialog;
