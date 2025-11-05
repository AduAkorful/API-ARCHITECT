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

const CreateServiceDialog = () => {
  const [prompt, setPrompt] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: generateService,
    onSuccess: () => {
      toast.success('API generation started!');
      queryClient.invalidateQueries({ queryKey: ['services'] });
      setPrompt('');
      // The shadcn dialog will close itself via its own state management
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
    <Dialog onOpenChange={(isOpen) => !isOpen && mutation.reset()}>
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
        <form onSubmit={handleSubmit}>
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
          <DialogFooter>
            <Button
              type="submit"
              disabled={mutation.isLoading || !prompt.trim()}
            >
              {mutation.isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate API'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateServiceDialog;