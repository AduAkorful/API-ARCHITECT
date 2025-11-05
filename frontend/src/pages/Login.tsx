import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../lib/firebase';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';

// ... (rest of the file is identical)
const LoginPage = () => {
  const navigate = useNavigate();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) {
      navigate('/', { replace: true });
    }
  }, [user, loading, navigate]);

  const handleGoogleSignIn = async () => {
    const toastId = toast.loading('Signing in...');
    try {
      await signInWithPopup(auth, googleProvider);
      navigate('/');
      toast.success('Successfully signed in!', { id: toastId });
    } catch (error) {
      console.error('Error during sign in:', error);
      toast.error('Failed to sign in. Please try again.', { id: toastId });
    }
  };

  if (loading || (!loading && user)) {
     return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-16 h-16 border-4 border-primary border-dashed rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background p-4">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-foreground mb-2">API Architect</h1>
        <p className="text-muted-foreground mb-8">Generate and deploy microservices with a single prompt.</p>
      </div>
      <button
        onClick={handleGoogleSignIn}
        className="px-6 py-3 bg-card border border-border rounded-lg text-foreground font-semibold hover:bg-secondary transition-colors flex items-center gap-3"
      >
        <svg className="w-6 h-6" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
          <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z" />
          <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z" />
          <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.222,0-9.65-3.88-11.127-9.009l-6.571,4.819C9.656,39.663,16.318,44,24,44z" />
          <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.574l6.19,5.238C39.986,35.663,44,30.138,44,24C44,22.659,43.862,21.35,43.611,20.083z" />
        </svg>
        Sign in with Google
      </button>
    </div>
  );
};
export default LoginPage;