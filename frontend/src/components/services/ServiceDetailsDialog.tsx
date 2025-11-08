import { ServiceMetadata } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Copy } from 'lucide-react';
import toast from 'react-hot-toast';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface ServiceDetailsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  service: ServiceMetadata | null;
}

const ServiceDetailsDialog: React.FC<ServiceDetailsDialogProps> = ({ isOpen, onClose, service }) => {
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
                {endpoint.schema_fields.map(field => (
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