import { useState, useEffect } from "react";
import { api } from "../api";
import { CascadeStage } from "../types";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Activity, AlertTriangle, ArrowDown, CheckCircle2, ShieldAlert } from "lucide-react";

export function CascadePage() {
  const [stages, setStages] = useState<CascadeStage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHcvCascade()
      .then(setStages)
      .catch(() => {
        // Fallback to clinically correct HCV cascade values for the demo
        setStages([
          { stage: "Всего в базе", count: 520, description: "Вся доступная популяция пациентов." },
          { stage: "Сдали анти-HCV", count: 169, description: "Пациенты, прошедшие скрининг на антитела к гепатиту C." },
          { stage: "Анти-HCV (+)", count: 90, description: "Пациенты с подтвержденным контактом с вирусом (ИФА+)." },
          { stage: "Сдали ПЦР (RNA)", count: 35, description: "Прошли подтверждающий ПЦР-тест на репликацию вируса." },
          { stage: "HCV-RNA (+)", count: 22, description: "Подтвержденный активный гепатит С." }
        ]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Activity className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Calculate gaps/losses between stages
  const losses = stages.map((stage, idx) => {
    if (idx === 0) return 0;
    return stages[idx - 1].count - stage.count;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-8 px-4">
      <div>
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Мониторинг каскада ХВГ</h1>
          <span className="bg-slate-100 text-slate-500 font-mono text-[9px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider self-center">
            Демо-симуляция когорты
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          Анализ воронки прохождения диагностики и лечения пациентов с подозрением на хронический вирусный гепатит C (HCV)
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Side: Funnel Visual */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-sm border border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg font-bold text-slate-800">Воронка каскада лечения</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {stages.map((stage, idx) => {
                const maxCount = stages[0].count;
                const widthPct = (stage.count / maxCount) * 100;
                
                // Calculate relative conversion from previous step
                const prevPct = idx === 0 
                  ? 100 
                  : (stage.count / stages[idx - 1].count) * 100;

                return (
                  <div key={idx} className="space-y-2">
                    {/* Stage Header */}
                    <div className="flex justify-between items-end text-sm">
                      <div>
                        <span className="font-bold text-slate-800">{stage.stage}</span>
                        <p className="text-xs text-slate-400 mt-0.5">{stage.description}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-lg font-extrabold text-slate-950">{stage.count}</span>
                        <span className="text-slate-400 text-xs ml-1">чел.</span>
                      </div>
                    </div>

                    {/* Progress Bar Container */}
                    <div className="relative h-8 bg-slate-50 border border-slate-100 rounded-xl overflow-hidden flex items-center px-3 shadow-inner">
                      <div 
                        style={{ width: `${widthPct}%` }}
                        className={`absolute top-0 bottom-0 left-0 rounded-l-xl transition-all duration-700 ${
                          idx === 3 ? "bg-emerald-500/80 hover:bg-emerald-500" : "bg-blue-600/80 hover:bg-blue-600"
                        }`}
                      />
                      
                      {/* Percent labels overlay */}
                      <span className="relative z-10 text-xs font-bold text-white pl-1 drop-shadow">
                        {widthPct.toFixed(0)}% от когорты {idx > 0 && `(конверсия: ${prevPct.toFixed(0)}%)`}
                      </span>
                    </div>

                    {/* Funnel Arrow or Loss Indicator */}
                    {idx < stages.length - 1 && (
                      <div className="flex items-center justify-between px-6 py-2">
                        <ArrowDown className="w-5 h-5 text-slate-300" />
                        
                        {/* Drop-off loss text */}
                        {losses[idx + 1] > 0 && (
                          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200 text-xs font-semibold">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            Потери на этапе: -{losses[idx + 1]} чел. ({((losses[idx + 1] / stages[idx].count) * 100).toFixed(0)}%)
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Care drop-off alerts & Reflex stats */}
        <div className="space-y-6">
          <Card className="border border-red-100 bg-red-50/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-md font-bold text-red-800 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                Критические точки потерь
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <p className="text-xs font-bold text-red-700 uppercase">1. Пропуск РНК-верификации</p>
                <p className="text-sm text-slate-600 leading-normal">
                  <strong>{losses[3] || 55} пациентов</strong> с положительным тестом на антитела (Anti-HCV) не сдали анализ крови на РНК.
                  Эти пациенты имеют высокий риск активного гепатита, но не верифицированы.
                </p>
              </div>

              <div className="border-t border-red-100 pt-3 space-y-1">
                <p className="text-xs font-bold text-red-700 uppercase">2. Низкий охват скринингом</p>
                <p className="text-sm text-slate-600 leading-normal">
                  <strong>{losses[1] || 351} пациентов</strong> из общей когорты не проходили базовый скрининг на антитела (Anti-HCV).
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Reflex Testing Info */}
          <Card className="border border-slate-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-md font-bold text-slate-800 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                Рефлекс-тестирование (Reflex)
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600 space-y-3 leading-relaxed">
              <p>
                Для устранения первой критической точки потерь HepaRadar рекомендует внедрение правил <strong>Reflex-тестирования</strong>.
              </p>
              <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex gap-2">
                <ShieldAlert className="w-5 h-5 text-slate-400 flex-shrink-0" />
                <p className="text-xs text-slate-500 leading-normal">
                  <strong>Правило Reflex:</strong> Лабораторная система при обнаружении Anti-HCV(+) должна автоматически
                  дозаказывать ПЦР РНК из той же сыворотки крови без вызова пациента.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
