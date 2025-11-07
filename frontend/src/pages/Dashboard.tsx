import { useQuery } from '@tanstack/react-query';
import { getServices } from '@/lib/api-client';
import ServiceCard from '@/components/services/ServiceCard';
import ServiceCardSkeleton from '@/components/services/ServiceCardSkeleton';
import DashboardEmptyState from '@/components/services/DashboardEmptyState';
import { useAuth } from '@/hooks/useAuth'; // <-- Import useAuth

const Dashboard = () => {
  const { user } = useAuth(); // <-- Get the authenticated user

  const { data: services, isLoading, error } = useQuery({
    queryKey: ['services'],
    queryFn: getServices,
    // --- THE CRITICAL FIX ---
    // Only enable this query if the user object exists.
    enabled: !!user,
    refetchInterval: (data) => 
      data?.some(s => s.status === 'BUILDING' || s.status === 'PENDING' || s.status === 'DELETING') ? 5000 : false,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <ServiceCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return <div className="text-center text-red-500">An error occurred: {(error as Error).message}</div>;
  }

  if (!services || services.length === 0) {
    return <DashboardEmptyState />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {services.map((service) => (
        <ServiceCard key={service.id} service={service} />
      ))}
    </div>
  );
};

export default Dashboard;