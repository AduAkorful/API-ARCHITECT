import { SAMPLE_PROMPTS } from '@/constants/samplePrompts';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { CheckCircle2, Download, Lightbulb, X } from 'lucide-react';
import toast from 'react-hot-toast';

interface OnboardingGuideProps {
  compact?: boolean;
  onDismiss?: () => void;
}

const steps = [
  {
    title: 'Describe your API',
    detail: 'Provide the endpoint path, method, and the data payload it should handle.',
  },
  {
    title: 'Review the generated spec',
    detail: 'API Architect turns your prompt into a Flask microservice with CI/CD ready to go.',
  },
  {
    title: 'Deploy & download artifacts',
    detail: 'Monitor build progress, open the Cloud Run URL, or download the generated source zip.',
  },
];

const OnboardingGuide: React.FC<OnboardingGuideProps> = ({ compact = false, onDismiss }) => {
  const handleCopyPrompt = (prompt: string) => {
    navigator.clipboard.writeText(prompt);
    toast.success('Prompt copied to clipboard');
  };

  return (
    <section
      className={cn(
        'relative rounded-xl border border-border/60 bg-secondary/30 p-6 shadow-lg shadow-black/5',
        compact ? 'space-y-4' : 'space-y-6'
      )}
    >
      {onDismiss && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-3 top-3 h-7 w-7 text-muted-foreground"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
      <div className="flex items-center gap-3">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Lightbulb className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">Getting started with API Architect</h3>
          <p className="text-sm text-muted-foreground">
            Follow these steps to turn natural language into a production-ready API in minutes.
          </p>
        </div>
      </div>

      <div className={cn('grid gap-4', compact ? 'md:grid-cols-3' : 'md:grid-cols-3')}>
        {steps.map((step, index) => (
          <div key={step.title} className="flex items-start gap-3 rounded-lg bg-background/60 p-4">
            <Badge variant="outline" className="mt-0.5">
              Step {index + 1}
            </Badge>
            <div>
              <p className="font-semibold text-sm text-foreground">{step.title}</p>
              <p className="text-xs text-muted-foreground mt-1 leading-snug">{step.detail}</p>
            </div>
          </div>
        ))}
      </div>

      {!compact && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <CheckCircle2 className="h-4 w-4" />
            Try a ready-made prompt
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {SAMPLE_PROMPTS.map(sample => (
              <div key={sample.label} className="rounded-lg border border-border/50 bg-background/60 p-4 space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-foreground">{sample.label}</p>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopyPrompt(sample.prompt)}
                  >
                    Copy
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground leading-snug">{sample.description}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Download className="h-4 w-4" />
            New: Each deployment now provides a downloadable source artifact directly from the dashboard.
          </div>
        </div>
      )}
    </section>
  );
};

export default OnboardingGuide;

