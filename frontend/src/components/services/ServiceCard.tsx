import React, { useState, useEffect, useRef } from 'react';
import { ServiceMetadata, ServiceStatus } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { Copy, Trash2, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';
import DeleteServiceDialog from './DeleteServiceDialog';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface ServiceCardProps {
  service: ServiceMetadata;
}

const statusConfig: Record<ServiceStatus, { color: string; text: string; pulse: boolean }> = {
  PENDING: { color: 'bg-slate-500', text: 'Pending', pulse: true },
  BUILDING: { color: 'bg-amber-500', text: 'Building', pulse: true },
  DEPLOYED: { color: 'bg-green-500', text: 'Deployed', pulse: false },
  FAILED: { color: 'bg-red-500', text: 'Failed', pulse: false },
  DELETING: { color: 'bg-gray-600', text: 'Deleting', pulse: true },
};

const ServiceCard: React.FC<ServiceCardProps> = ({ service }) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isJustDeployed, setIsJustDeployed] = useState(false);
  const prevStatusRef = useRef<ServiceStatus>();

  useEffect(() => {
    if ((prevStatusRef.current === 'BUILDING' || prevStatusRef.current === 'PENDING') && service.status === 'DEPLOYED') {
      setIsJustDeployed(true);
      const timer = setTimeout(() => setIsJustDeployed(false), 3000); // Animation duration
      return () => clearTimeout(timer);
    }
    prevStatusRef.current = service.status;
  }, [service.status]);

  const config = statusConfig[service.status];

  const handleCopyUrl = () => {
    if (service.deployed_url) {
      navigator.clipboard.writeText(service.deployed_url);
      toast.success('URL copied to clipboard!');
    }
  };

  return (
    <>
      <Card
        className={cn(
          'flex flex-col transition-all duration-300',
          isJustDeployed && 'animate-glow border-green-500'
        )}
      >
        <CardHeader>
          <div className="flex justify-between items-start gap-4">
            <CardTitle className="truncate">{service.service_name}</CardTitle>
            <Badge variant="outline" className="flex items-center gap-2 flex-shrink-0">
              <span className={cn('w-2 h-2 rounded-full', config.color, config.pulse && 'animate-pulse')} />
              <span>{config.text}</span>
            </Badge>
          </div>
          <CardDescription className="font-mono text-xs pt-2 truncate">
            {service.prompt}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-grow"></CardContent>
        <CardFooter className="flex justify-between items-center text-xs text-muted-foreground">
          <span>{formatDistanceToNow(new Date(service.created_at), { addSuffix: true })}</span>
          <div className="flex items-center gap-1">
            {service.status === 'DEPLOYED' && service.deployed_url && (
              <Button variant="ghost" size="icon" onClick={handleCopyUrl} title="Copy URL">
                <Copy className="w-4 h-4" />
              </Button>
            )}
            {service.build_log_url && (
              <a href={service.build_log_url} target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="icon" title="View Build Logs">
                  <ExternalLink className="w-4 h-4" />
                </Button>
              </a>
            )}
            <Button variant="ghost" size="icon" onClick={() => setShowDeleteDialog(true)} disabled={service.status === 'DELETING'} title="Delete Service">
              <Trash2 className="w-4 h-4 text-red-500" />
            </Button>
          </div>
        </CardFooter>
      </Card>
      <DeleteServiceDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        service={service}
      />
    </>
  );
};

export default ServiceCard;
