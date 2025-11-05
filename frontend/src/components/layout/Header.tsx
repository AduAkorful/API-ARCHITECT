import { signOut } from 'firebase/auth';
import { auth } from '@/lib/firebase';
import { useAuth } from '@/hooks/useAuth';
import { LogOut } from 'lucide-react';
import CreateServiceDialog from '@/components/services/CreateServiceDialog';
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const Header = () => {
  // ... (rest of the component logic is the same)
  const { user } = useAuth();
  const handleSignOut = async () => { /* ... */ };
  const getInitials = (name?: string | null) => { /* ... */ };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <a href="/" className="mr-6 flex items-center space-x-2">
          <span className="font-bold">API Architect</span>
        </a>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <CreateServiceDialog />
          {user && (
            <DropdownMenu>
              {/* ... The rest of the DropdownMenu JSX is identical ... */}
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;