import { useState } from 'react';
import { ServiceMetadata } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Copy, Download, FileText, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getServiceArtifact, getServiceLogs } from '@/lib/api-client';

interface ServiceDetailsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  service: ServiceMetadata | null;
}

const ServiceDetailsDialog: React.FC<ServiceDetailsDialogProps> = ({ isOpen, onClose, service }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isFetchingLogs, setIsFetchingLogs] = useState(false);

  if (!service) return null;

  // Safely access nested values — spec or endpoint may be missing.
  const endpoint = service.spec?.endpoint;
  const deployed_url = service.deployed_url;

  const getCurlCommand = () => {
    if (!endpoint) return '';
    const fullUrl = deployed_url ? `${deployed_url}${endpoint.path}` : `https://...${endpoint.path}`;
    let curl = `curl -X ${endpoint.method.toUpperCase()} "${fullUrl}" \\\n+  -H "Content-Type: application/json"`;
    if (endpoint.method.toUpperCase() === 'POST' || endpoint.method.toUpperCase() === 'PUT') {
      const exampleBody = JSON.stringify(getExampleBody(), null, 2);
      curl += ` \\\n+  -d '${exampleBody}'`;
    }
    return curl;
  };

  const getExampleBody = () => {
    const body: { [key: string]: any } = {};
    if (!endpoint?.schema_fields) return body;
    endpoint.schema_fields.forEach(field => {
      if (field.type === 'str' || field.type === 'EmailStr') body[field.name] = `example_${field.name}`;
      if (field.type === 'int') body[field.name] = 123;
      if (field.type === 'bool') body[field.name] = true;
    });
    return body;
  };

  const handleCopy = (text: string, name: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${name} copied to clipboard!`);
  }

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadLogs = async () => {
    if (!service.build_id) {
      toast.error('Build logs are not available for this service yet.');
      return;
    }
    try {
      setIsFetchingLogs(true);
      const { blob, filename } = await getServiceLogs(service.id);
      downloadBlob(blob, filename);
      toast.success('Build logs downloaded');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to download build logs';
      toast.error(message);
    } finally {
      setIsFetchingLogs(false);
    }
  };

  // --- ADDED A CHECK FOR endpoint ---
  // Prevents crash if the spec is somehow malformed
  if (!endpoint) {
    return (
       <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
            <DialogDescription>Could not display details. The API specification is missing or malformed.</DialogDescription>
          </DialogHeader>
        </DialogContent>
       </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[650px]">
        <DialogHeader>
          <DialogTitle>{service.service_name}</DialogTitle>
          <DialogDescription>
            Details and examples for your generated API endpoint.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4 max-h-[70vh] overflow-y-auto">
          <div className="grid gap-3 rounded-md border border-border/60 bg-secondary/40 p-4">
            <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
              <div className="space-y-1">
                <h4 className="font-semibold text-sm uppercase text-muted-foreground tracking-wide">Deployment resources</h4>
                {service.build_log_url && (
                  <p className="text-xs text-muted-foreground">
                    Track the Cloud Build pipeline or download the generated source package.
                  </p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {service.build_id && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={isFetchingLogs}
                    onClick={handleDownloadLogs}
                  >
                    {isFetchingLogs ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <FileText className="mr-2 h-4 w-4" />
                    )}
                    Download build logs
                  </Button>
                )}
                {service.source_blob && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    disabled={isDownloading}
                    onClick={async () => {
                      try {
                        setIsDownloading(true);
                        const { download_url } = await getServiceArtifact(service.id);
                        window.open(download_url, '_blank', 'noopener,noreferrer');
                        toast.success('Download started');
                      } catch (err) {
                        const message = err instanceof Error ? err.message : 'Unable to download artifact';
                        toast.error(message);
                      } finally {
                        setIsDownloading(false);
                      }
                    }}
                  >
                    {isDownloading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="mr-2 h-4 w-4" />
                    )}
                    Download source code
                  </Button>
                )}
              </div>
            </div>
            {service.source_blob && (
              <p className="text-xs font-mono text-muted-foreground">
                {service.source_blob.split('/').pop()}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold">Endpoint</h4>
            <div className="flex items-center justify-between p-3 rounded-md bg-secondary">
              <code className="text-sm font-mono">{endpoint.method.toUpperCase()} {endpoint.path}</code>
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-semibold">Schema</h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Required</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {endpoint.schema_fields?.map(field => (
                  <TableRow key={field.name}>
                    <TableCell className="font-mono">{field.name}</TableCell>
                    <TableCell className="font-mono">{field.type}</TableCell>
                    <TableCell>{field.required ? 'Yes' : 'No'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {(endpoint.method.toUpperCase() === 'POST' || endpoint.method.toUpperCase() === 'PUT') && (
            <div className="space-y-2">
              <h4 className="font-semibold">Example Request Body</h4>
              <div className="relative p-3 rounded-md bg-secondary">
                <pre className="text-xs font-mono whitespace-pre-wrap">{JSON.stringify(getExampleBody(), null, 2)}</pre>
                <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-7 w-7" onClick={() => handleCopy(JSON.stringify(getExampleBody(), null, 2), 'Body')}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <h4 className="font-semibold">Example cURL Command</h4>
            <div className="relative p-3 rounded-md bg-secondary">
              <pre className="text-xs font-mono whitespace-pre-wrap">{getCurlCommand()}</pre>
              <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-7 w-7" onClick={() => handleCopy(getCurlCommand(), 'cURL')}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ServiceDetailsDialog;