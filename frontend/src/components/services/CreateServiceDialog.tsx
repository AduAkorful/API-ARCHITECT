import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateService } from '@/lib/api-client';
import toast from 'react-hot-toast';
import { Loader2, PlusCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { ServiceMetadata } from '@/types';

const CreateServiceDialog = () => {
  const [isOpen, setIsOpen] = useState(false); // <-- Control the dialog state manually
  const [prompt, setPrompt] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: generateService,
    onSuccess: (newService) => {
      toast.success('API generation started!');
      queryClient.setQueryData<ServiceMetadata[]>(['services'], (oldData = []) => {
        // Ensure oldData is an array before spreading
        return [newService, ...oldData];
      });
      setPrompt('');
      setIsOpen(false); // <-- Close the dialog on success
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to start generation.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      mutation.mutate(prompt);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <PlusCircle className="w-4 h-4 mr-2" />
          Create API
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[625px]">
        <DialogHeader>
          <DialogTitle>Create New API Service</DialogTitle>
          <DialogDescription>
            Describe the API you want to build. Be specific about endpoints, methods, and data schemas.
          </DialogDescription>
        </DialogHeader>
        <form id="create-service-form" onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <Label htmlFor="prompt" className="sr-only">Prompt</Label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Create a POST endpoint at /contact that accepts 'name' and 'email'..."
              className="w-full h-40 font-mono text-sm col-span-4"
              required
            />
          </div>
        </form>
         <DialogFooter>
            <Button
              type="submit"
              form="create-service-form"
              disabled={mutation.isLoading || !prompt.trim()}
            >
              {mutation.isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate API'}
            </Button>
          </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateServiceDialog;