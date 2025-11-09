import { useMemo, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { generateService } from '@/lib/api-client';
import toast from 'react-hot-toast';
import { AlertCircle, CheckCircle2, Loader2, PlusCircle, Sparkles } from 'lucide-react';
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
import { SAMPLE_PROMPTS } from '@/constants/samplePrompts';

const CreateServiceDialog = () => {
  const [isOpen, setIsOpen] = useState(false); // <-- Control the dialog state manually
  const [prompt, setPrompt] = useState('');
  const queryClient = useQueryClient();

  const guidanceChecks = useMemo(() => {
    const normalized = prompt.toLowerCase();
    return [
      {
        id: 'method',
        label: 'Specify the HTTP method (GET, POST, PUT, DELETE)',
        satisfied: /\b(get|post|put|delete|patch)\b/i.test(prompt),
      },
      {
        id: 'path',
        label: 'Include a clear endpoint path like /resource or /resource/{id}',
        satisfied: /\/[a-z0-9\-{}_/]+/i.test(prompt),
      },
      {
        id: 'schema',
        label: 'Describe the request or response fields',
        satisfied: /\b(field|payload|body|returns?|include|with)\b/i.test(normalized),
      },
    ];
  }, [prompt]);

  const unmetChecks = guidanceChecks.filter(check => !check.satisfied).length;

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
          <div className="grid gap-6 py-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  Suggested prompts
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {SAMPLE_PROMPTS.map(sample => (
                  <div
                    key={sample.label}
                    className="rounded-md border border-border/60 bg-secondary/30 p-3 hover:border-primary transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold">{sample.label}</p>
                        <p className="text-xs text-muted-foreground mt-1 leading-snug">{sample.description}</p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setPrompt(sample.prompt)}
                        className="shrink-0"
                      >
                        Use
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <Label htmlFor="prompt" className="sr-only">Prompt</Label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Create a POST endpoint at /contact that accepts 'name' and 'email'..."
              className="w-full h-40 font-mono text-sm col-span-4"
              required
            />
            <div className="rounded-md border border-border/60 bg-secondary/40 p-3 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  Prompt guidance checklist
                </span>
                <span>{prompt.length} chars</span>
              </div>
              <div className="space-y-2">
                {guidanceChecks.map(check => (
                  <div key={check.id} className="flex items-start gap-2 text-xs">
                    {check.satisfied ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-500" />
                    ) : (
                      <AlertCircle className="mt-0.5 h-4 w-4 text-amber-500" />
                    )}
                    <span className={check.satisfied ? 'text-foreground' : 'text-muted-foreground'}>
                      {check.label}
                    </span>
                  </div>
                ))}
              </div>
              {prompt && unmetChecks === 0 && (
                <p className="text-xs text-emerald-500 font-medium">Looks great! Your prompt covers all the essentials.</p>
              )}
            </div>
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