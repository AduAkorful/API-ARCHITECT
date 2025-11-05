
const ServiceCardSkeleton = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg shadow-md p-4 animate-pulse">
      <div className="flex justify-between items-center mb-4">
        <div className="h-5 bg-slate-800 rounded w-3/5"></div>
        <div className="h-4 bg-slate-800 rounded w-1/4"></div>
      </div>
      <div className="space-y-2 mb-6">
        <div className="h-4 bg-slate-800 rounded"></div>
        <div className="h-4 bg-slate-800 rounded"></div>
        <div className="h-4 bg-slate-800 rounded w-4/5"></div>
      </div>
      <div className="flex justify-between items-center">
        <div className="h-4 bg-slate-800 rounded w-1/3"></div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-slate-800 rounded-md"></div>
          <div className="w-6 h-6 bg-slate-800 rounded-md"></div>
        </div>
      </div>
    </div>
  );
};

export default ServiceCardSkeleton;
