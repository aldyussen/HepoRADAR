import { ShapFactor } from "../types";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { HelpCircle } from "lucide-react";

interface ShapExplanationProps {
  factors: ShapFactor[];
  loading?: boolean;
}

export function ShapExplanation({ factors, loading }: ShapExplanationProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-slate-500">
          Загрузка объяснений факторов риска...
        </CardContent>
      </Card>
    );
  }

  // Find max absolute impact to normalize bar widths
  const maxImpact = Math.max(
    ...factors.map(f => Math.abs(f.impact)),
    0.1 // avoid division by zero
  );

  return (
    <Card className="shadow-sm border border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-bold text-slate-800 flex items-center justify-between">
          <span>Вклад факторов в риск (SHAP)</span>
          <div className="group relative">
            <HelpCircle className="w-4 h-4 text-slate-400 cursor-help" />
            <div className="absolute right-0 top-6 hidden group-hover:block bg-slate-800 text-white text-xs rounded p-2 w-64 shadow-lg z-20 font-normal normal-case leading-relaxed">
              Модель машинного обучения определяет вклад каждого параметра. Красные полосы увеличивают вероятность риска, синие — снижают её.
            </div>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {factors.length === 0 ? (
          <p className="text-sm text-slate-500">Недостаточно клинических признаков для анализа факторов риска.</p>
        ) : (
          <div className="space-y-3">
            {factors.map((factor, index) => {
              const absPercent = Math.min((Math.abs(factor.impact) / maxImpact) * 100, 100);
              const isPositive = factor.impact >= 0;

              return (
                <div key={index} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-700">{factor.feature}</span>
                    <span className="text-slate-500 font-mono">{factor.value}</span>
                  </div>
                  
                  {/* Custom horizontal force bar */}
                  <div className="relative h-6 bg-slate-50 border border-slate-100 rounded-md overflow-hidden flex">
                    {/* Centered baseline indicator */}
                    <div className="absolute left-1/2 top-0 bottom-0 w-[2px] bg-slate-300 z-10" />

                    {isPositive ? (
                      // Red bar to the right
                      <div 
                        style={{ left: "50%", width: `${absPercent / 2}%` }}
                        className="absolute top-0 bottom-0 bg-red-500/80 hover:bg-red-500 rounded-r-sm transition-all duration-500 flex items-center pl-1 text-[10px] text-white font-mono font-bold"
                      >
                        +{factor.impact.toFixed(2)}
                      </div>
                    ) : (
                      // Blue bar to the left
                      <div 
                        style={{ right: "50%", width: `${absPercent / 2}%` }}
                        className="absolute top-0 bottom-0 bg-blue-500/80 hover:bg-blue-500 rounded-l-sm transition-all duration-500 flex items-center justify-end pr-1 text-[10px] text-white font-mono font-bold"
                      >
                        {factor.impact.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
