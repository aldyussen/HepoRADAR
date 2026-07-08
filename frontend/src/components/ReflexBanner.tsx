import { ReflexFlag } from "../types";
import { AlertTriangle } from "lucide-react";

export function ReflexBanner({ flags }: { flags: ReflexFlag[] }) {
  if (!flags || flags.length === 0) return null;

  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-md mb-6">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-amber-900">Внимание: Показано дообследование</h3>
          <ul className="mt-2 space-y-1 text-sm text-amber-800">
            {flags.map((flag, idx) => (
              <li key={idx}>• {flag.msg}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
