import { signOut } from 'firebase/auth';
import { auth } from '@/lib/firebase';
import { useAuth } from '@/hooks/useAuth';
import { LogOut, User as UserIcon } from 'lucide-react';
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
  const { user } = useAuth();

  const handleSignOut = async () => {
    await signOut(auth);
  };

  const getInitials = (name?: string | null) => {
    if (!name) return '?';
    const nameParts = name.split(' ');
    if (nameParts.length > 1) {
      return (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <a href="/" className="mr-6 flex items-center space-x-3">
          <svg
            className="h-9 w-9"
            viewBox="0 0 64 64"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            role="img"
            aria-label="API Architect logo"
          >
            <defs>
              <linearGradient id="badge-bg" x1="12" y1="8" x2="54" y2="56" gradientUnits="userSpaceOnUse">
                <stop stopColor="#1B5FFF" />
                <stop offset="1" stopColor="#00B0FF" />
              </linearGradient>
              <linearGradient id="badge-glow" x1="12" y1="20" x2="44" y2="60" gradientUnits="userSpaceOnUse">
                <stop stopColor="#FFFFFF" stopOpacity="0.45" />
                <stop offset="1" stopColor="#FFFFFF" stopOpacity="0.05" />
              </linearGradient>
            </defs>
            <rect width="64" height="64" rx="18" fill="url(#badge-bg)" />
            <rect
              x="12"
              y="12"
              width="40"
              height="40"
              rx="12"
              fill="none"
              stroke="rgba(255,255,255,0.35)"
              strokeWidth="2"
            />
            <path
              d="M20 24H44M20 32H44M24 16V48M40 16V48"
              stroke="rgba(255,255,255,0.12)"
              strokeWidth="2"
            />
            <path
              d="M25 43L32 23L39 43"
              stroke="white"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M28.5 34.5H35.5"
              stroke="white"
              strokeWidth="3"
              strokeLinecap="round"
            />
            <rect
              x="18"
              y="18"
              width="28"
              height="28"
              rx="8"
              fill="url(#badge-glow)"
              opacity="0.45"
            />
          </svg>
          <span className="block font-semibold leading-tight tracking-tight">API Architect</span>
        </a>
        
        <div className="flex flex-1 items-center justify-end space-x-4">
          <CreateServiceDialog />
          
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user.photoURL || ''} alt={user.displayName || 'User'} />
                    <AvatarFallback>{getInitials(user.displayName)}</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {user.displayName}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut} className="cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;