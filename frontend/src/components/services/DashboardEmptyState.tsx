import CreateServiceDialog from "./CreateServiceDialog";

const DashboardEmptyState = () => {
  return (
    <div className="flex flex-col items-center justify-center text-center h-[calc(100vh-12rem)]">
      <h2 className="text-2xl font-bold text-foreground mb-2">Welcome to API Architect</h2>
      <p className="text-muted-foreground mb-6">You haven't created any services yet. Get started now!</p>
      {/* The Dialog component now contains its own trigger button */}
      <CreateServiceDialog /> 
    </div>
  );
};

export default DashboardEmptyState;