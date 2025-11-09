import CreateServiceDialog from "./CreateServiceDialog";
import OnboardingGuide from "./OnboardingGuide";

const DashboardEmptyState = () => {
  return (
    <div className="flex flex-col gap-8 items-center justify-center text-center py-12">
      <div className="max-w-2xl space-y-4">
        <h2 className="text-3xl font-bold text-foreground">Welcome to API Architect</h2>
        <p className="text-muted-foreground">
          Describe any microservice in plain English and watch it deploy to Google Cloud Run with CI/CD, security, and documentation built-in.
        </p>
        <div className="flex justify-center">
          {/* The Dialog component now contains its own trigger button */}
          <CreateServiceDialog />
        </div>
      </div>
      <div className="w-full max-w-5xl">
        <OnboardingGuide />
      </div>
    </div>
  );
};

export default DashboardEmptyState;