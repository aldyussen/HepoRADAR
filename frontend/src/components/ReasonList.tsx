import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { AlertCircle } from "lucide-react";

export function ReasonList({ reasons }: { reasons: string[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <AlertCircle className="w-5 h-5 text-slate-500" />
          Факторы риска
        </CardTitle>
      </CardHeader>
      <CardContent>
        {reasons && reasons.length > 0 ? (
          <ul className="space-y-3">
            {reasons.map((r, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Нет явных факторов</p>
        )}
      </CardContent>
    </Card>
  );
}
