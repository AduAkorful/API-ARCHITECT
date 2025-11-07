import { useState, useEffect, useRef } from 'react';
import { ServiceMetadata, ServiceStatus } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { Trash2, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import DeleteServiceDialog from './DeleteServiceDialog';
import ServiceDetailsDialog from './ServiceDetailsDialog'; // Import new dialog
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ServiceCardProps {
  service: ServiceMetadata;
}
// ... (statusConfig is the same)

const ServiceCard: React.FC<ServiceCardProps> = ({ service }) => {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false); // State for new dialog
  const [isJustDeployed, setIsJustDeployed] = useState(false);
  const prevStatusRef = useRef<ServiceStatus>();

  useEffect(() => {
    if ((prevStatusRef.current === 'BUILDING' || prevStatusRef.current === 'PENDING') && service.status === 'DEPLOYED') {
      setIsJustDeployed(true);
      const timer = setTimeout(() => setIsJustDeployed(false), 3000);
      return () => clearTimeout(timer);
    }
    prevStatusRef.current = service.status;
  }, [service.status]);

  const config = statusConfig[service.status];

  return (
    <>
      <Card
        className={cn(
          'flex flex-col transition-all duration-300 hover:border-primary cursor-pointer',
          isJustDeployed && 'animate-glow border-green-500'
        )}
        onClick={() => setShowDetailsDialog(true)}
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
            <TooltipProvider>
              {service.status === 'DEPLOYED' && service.deployed_url && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <a href={service.deployed_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
                      <Button variant="ghost" size="icon">
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    </a>
                  </TooltipTrigger>
                  <TooltipContent><p>Open Live URL</p></TooltipContent>
                </Tooltip>
              )}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={e => { e.stopPropagation(); setShowDeleteDialog(true); }} disabled={service.status === 'DELETING'}>
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent><p>Delete Service</p></TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </CardFooter>
      </Card>
      
      <DeleteServiceDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        service={service}
      />
      <ServiceDetailsDialog
        isOpen={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        service={service}
      />
    </>
  );
};

export default ServiceCard;