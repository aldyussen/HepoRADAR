import { Badge } from "./ui/badge";
import { Zone } from "../types";

interface RiskBadgeProps {
  zone: Zone | null;
}

export function RiskBadge({ zone }: RiskBadgeProps) {
  switch (zone) {
    case 'high':
      return <Badge className="bg-red-500 hover:bg-red-600">Высокий</Badge>;
    case 'grey':
      return <Badge className="bg-amber-500 hover:bg-amber-600">Серая зона</Badge>;
    case 'low':
      return <Badge className="bg-emerald-500 hover:bg-emerald-600">Низкий</Badge>;
    case 'n/a':
      return <Badge className="bg-slate-300 text-slate-700 hover:bg-slate-400">Н/Д</Badge>;
    default:
      return <Badge className="bg-slate-500 hover:bg-slate-600">Неизвестно</Badge>;
  }
}
