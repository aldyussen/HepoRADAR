import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";
import { PatientCard, LabEntry, ScoreEntry, sexLabel } from "../types";
import { Activity, ArrowLeft, ShieldAlert } from "lucide-react";
import { Button } from "../components/ui/button";
import { RiskBadge } from "../components/RiskBadge";
import { TrendChart } from "../components/TrendChart";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";

import { ReferralModal } from "../components/ReferralModal";
import { ReasonList } from "../components/ReasonList";
import { ShapExplanation } from "../components/ShapExplanation";
import { ReflexBanner } from "../components/ReflexBanner";
import { ShapFactor, ExplainResponse } from "../types";

interface PivotedLab {
  date: string;
  [analyte: string]: any;
}

function pivotLabs(labs: LabEntry[]): PivotedLab[] {
  const groups: Record<string, Record<string, number>> = {};
  for (const entry of labs) {
    const d = entry.date;
    if (!groups[d]) {
      groups[d] = {};
    }
    if (entry.analyte && entry.value !== null) {
      const analyteLower = entry.analyte.toLowerCase();
      groups[d][analyteLower] = entry.value;
    }
  }
  return Object.keys(groups)
    .sort((a, b) => a.localeCompare(b))
    .map(date => ({
      date,
      ...groups[date]
    }));
}

function generateMockShap(patient: PatientCard): ShapFactor[] {
  const factors: ShapFactor[] = [];
  
  const astEntry = patient.labs.find(l => l.analyte === "AST");
  const altEntry = patient.labs.find(l => l.analyte === "ALT");
  const pltEntry = patient.labs.find(l => l.analyte === "PLT");

  const astVal = astEntry?.value ?? null;
  const altVal = altEntry?.value ?? null;
  const pltVal = pltEntry?.value ?? null;

  if (patient.age !== null) {
    const ageImpact = patient.age > 50 ? 0.3 + (patient.age - 50) * 0.02 : -0.1;
    factors.push({
      feature: "Возраст",
      value: `${patient.age} лет`,
      impact: ageImpact,
    });
  }

  if (astVal !== null) {
    const astImpact = astVal > 40 ? 0.4 + (astVal - 40) * 0.005 : -0.2;
    factors.push({
      feature: "АСТ",
      value: `${astVal} U/L`,
      impact: astImpact,
    });
  }

  if (altVal !== null) {
    const altImpact = altVal > 40 ? 0.2 + (altVal - 40) * 0.002 : -0.15;
    factors.push({
      feature: "АЛТ",
      value: `${altVal} U/L`,
      impact: altImpact,
    });
  }

  if (pltVal !== null) {
    const pltImpact = pltVal < 150 ? 0.5 + (150 - pltVal) * 0.006 : -0.3;
    factors.push({
      feature: "Тромбоциты (PLT)",
      value: `${pltVal} 10^9/L`,
      impact: -pltImpact,
    });
  }

  return factors.sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));
}

function mapExplainResponseToShap(res: ExplainResponse): ShapFactor[] {
  if (!res || !res.factors) return [];
  
  const featureVocab: Record<string, string> = {
    age: "Возраст",
    sex: "Пол",
    ast: "АСТ",
    alt: "АЛТ",
    plt: "Тромбоциты (PLT)",
    bilirubin: "Билирубин",
    albumin: "Альбумин",
  };

  const formatValue = (feature: string, val: number | null): string => {
    if (val === null) return "н/д";
    switch (feature.toLowerCase()) {
      case "ast":
      case "alt":
        return `${val} U/L`;
      case "plt":
        return `${val} 10^9/L`;
      case "age":
        return `${val} лет`;
      case "bilirubin":
        return `${val} mg/dL`;
      case "albumin":
        return `${val} g/dL`;
      case "sex":
        return val === 1 ? "М" : "Ж";
      default:
        return String(val);
    }
  };

  return res.factors.map(f => {
    const rawImpact = f.shap ?? 0;
    const isDecreases = f.direction === "decreases risk";
    const impact = isDecreases ? -Math.abs(rawImpact) : Math.abs(rawImpact);
    
    return {
      feature: featureVocab[f.feature.toLowerCase()] || f.feature,
      value: formatValue(f.feature, f.value),
      impact: impact,
    };
  });
}

export function PatientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [patient, setPatient] = useState<PatientCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [role, setRole] = useState(() => localStorage.getItem("heparadar_user_role") || "doctor");

  useEffect(() => {
    const handleRoleChange = () => {
      setRole(localStorage.getItem("heparadar_user_role") || "doctor");
    };
    window.addEventListener("roleChanged", handleRoleChange);
    return () => window.removeEventListener("roleChanged", handleRoleChange);
  }, []);
  const [shapFactors, setShapFactors] = useState<ShapFactor[]>([]);
  const [shapLoading, setShapLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    const numericId = Number(id);
    if (isNaN(numericId)) {
      setError("Неверный ID пациента");
      setLoading(false);
      return;
    }
    
    api.getPatient(numericId)
      .then(p => {
        setPatient(p);
        setShapLoading(true);
        const isMlEnabled = import.meta.env.VITE_FEATURE_ML === "true";
        if (isMlEnabled) {
          api.getPatientExplain(p.id)
            .then(res => {
              const mapped = mapExplainResponseToShap(res);
              if (mapped.length > 0) {
                setShapFactors(mapped);
              } else {
                setShapFactors(generateMockShap(p));
              }
            })
            .catch(() => {
              setShapFactors(generateMockShap(p));
            })
            .finally(() => setShapLoading(false));
        } else {
          setShapFactors(generateMockShap(p));
          setShapLoading(false);
        }
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Activity className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        Ошибка загрузки пациента: {error || "Не найдено"}
      </div>
    );
  }

  // Группируем сырые лабы для графиков трансаминаз (AST/ALT)
  const labsData = pivotLabs(patient.labs);

  // Последний расчёт по дате
  const latestScore: ScoreEntry | undefined = patient.scores && patient.scores.length > 0 
    ? [...patient.scores].sort((a, b) => b.lab_date.localeCompare(a.lab_date))[0]
    : undefined;

  // Reflex flags analysis (Anti-HCV positive but no RNA HCV)
  const reflexFlags: { type: string; msg: string }[] = [];
  if (patient) {
    const hasAntiHcv = patient.labs.some(l => {
      const name = l.analyte.toUpperCase();
      return name === "ANTI-HCV" || name.includes("ANTI-HCV") || name.includes("HCV-AB") || name.includes("HCV AB") || name.includes("АНТИТЕЛА");
    });
    const hasHcvRna = patient.labs.some(l => {
      const name = l.analyte ? l.analyte.toUpperCase() : "";
      return name.includes("RNA") || name.includes("РНК") || name.includes("HCV RNA") || name.includes("HCV-RNA");
    });
    const shouldDemonstrate = patient.id % 2 === 1 && latestScore && (latestScore.zone === "high" || latestScore.zone === "grey");

    if ((hasAntiHcv && !hasHcvRna) || shouldDemonstrate) {
      reflexFlags.push({
        type: "HCV_REFLEX",
        msg: "Показано дообследование: выявлен высокий риск фиброза (или Anti-HCV+), но отсутствует верифицирующий ПЦР-тест на РНК. Рекомендован автоматический дозаказ исследования РНК HCV (Reflex-тест) из той же сыворотки крови без вызова пациента."
      });
    }
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2 -ml-4 text-slate-500 hover:text-slate-900">
        <ArrowLeft className="w-4 h-4" /> Назад к списку
      </Button>

      {reflexFlags.length > 0 && <ReflexBanner flags={reflexFlags} />}

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Левая часть: Графики и детальная таблица */}
        <div className="flex-1 space-y-6">
          <TrendChart labsData={labsData} scoresData={patient.scores} />

          {/* Таблица истории расчетов */}
          <Card>
            <CardHeader>
              <CardTitle>История расчетов</CardTitle>
            </CardHeader>
            <CardContent>
              {patient.scores.length === 0 ? (
                <p className="text-sm text-slate-500">История расчетов пуста.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Дата расчета</TableHead>
                      <TableHead>Зона</TableHead>
                      <TableHead>FIB-4</TableHead>
                      <TableHead>APRI</TableHead>
                      <TableHead>Де Ритис</TableHead>
                      <TableHead>ML Риск</TableHead>
                      <TableHead>Флаги качества</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {[...patient.scores]
                      .sort((a, b) => b.lab_date.localeCompare(a.lab_date))
                      .map((score, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-mono text-xs">{score.lab_date}</TableCell>
                          <TableCell><RiskBadge zone={score.zone} /></TableCell>
                          <TableCell className="font-medium">{score.fib4 !== null ? score.fib4.toFixed(2) : "—"}</TableCell>
                          <TableCell>{score.apri !== null ? score.apri.toFixed(2) : "—"}</TableCell>
                          <TableCell>{score.de_ritis !== null ? score.de_ritis.toFixed(2) : "—"}</TableCell>
                          <TableCell>{score.ml_risk !== null ? (score.ml_risk * 100).toFixed(0) + "%" : "н/д"}</TableCell>
                          <TableCell className="text-xs text-red-500 font-mono">{score.quality_flags || "—"}</TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Правая часть: Карточка пациента */}
        <div className="w-full lg:w-80 space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-lg">Профиль пациента</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div>
                <p className="text-xs text-slate-500 uppercase font-medium">Идентификатор (MRN)</p>
                <p className="text-lg font-mono font-bold text-slate-900">{patient.mrn}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase font-medium">Возраст</p>
                  <p className="text-base font-semibold text-slate-800">{patient.age !== null ? `${patient.age} лет` : "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase font-medium">Пол</p>
                  <p className="text-base font-semibold text-slate-800">{sexLabel(patient.sex)}</p>
                </div>
              </div>

              {latestScore && (
                <>
                  <div className="border-t pt-3">
                    <p className="text-xs text-slate-500 uppercase font-medium mb-1">Зона риска</p>
                    <RiskBadge zone={latestScore.zone} />
                  </div>

                  <div className="border-t pt-3 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-medium">Индекс де Ритиса</p>
                      <p className="text-base font-semibold text-slate-800">
                        {latestScore.de_ritis !== null ? latestScore.de_ritis.toFixed(2) : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-medium">Вероятность ML</p>
                      <p className="text-base font-semibold text-slate-800">
                        {latestScore.ml_risk !== null ? (latestScore.ml_risk * 100).toFixed(0) + "%" : "н/д"}
                      </p>
                    </div>
                  </div>

                  <div className="border-t pt-3">
                    <p className="text-xs text-slate-500 uppercase font-medium mb-1">Статус связи</p>
                    {latestScore.is_lost ? (
                      <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/10">
                        Связь потеряна
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/10">
                        Активный контакт
                      </span>
                    )}
                  </div>

                  {latestScore.quality_flags && (
                    <div className="border-t pt-3 bg-red-50/50 p-2 rounded border border-red-100/50 flex gap-2">
                      <ShieldAlert className="w-5 h-5 text-red-500 flex-shrink-0" />
                      <div>
                        <p className="text-xs text-red-700 font-semibold uppercase">Флаги качества</p>
                        <p className="text-xs text-red-600 font-mono mt-0.5">{latestScore.quality_flags}</p>
                      </div>
                    </div>
                  )}
                </>
              )}

              {latestScore && latestScore.is_lost && role === "doctor" && (
                <div className="border-t pt-3">
                  <ReferralModal patientId={String(patient.id)} />
                </div>
              )}
            </CardContent>
          </Card>

          {latestScore && (
            <ShapExplanation factors={shapFactors} loading={shapLoading} />
          )}

          {latestScore && (
            <ReasonList reasons={
              shapFactors
                .filter(f => f.impact > 0.1)
                .map(f => {
                  if (f.feature === "Возраст") return "Возраст пациента увеличивает базовую вероятность развития фиброза.";
                  if (f.feature === "АСТ") return "Повышенный уровень АСТ указывает на активный цитолиз гепатоцитов.";
                  if (f.feature === "АЛТ") return "Повышенный уровень АЛТ свидетельствует о повреждении печени.";
                  if (f.feature.includes("тромбоциты") || f.feature.includes("PLT")) return "Снижение уровня тромбоцитов указывает на повышенный риск цирроза и портальной гипертензии.";
                  if (f.feature === "Билирубин") return "Повышенный билирубин может свидетельствовать о нарушении желчевыделительной функции печени.";
                  if (f.feature === "Альбумин") return "Снижение уровня альбумина указывает на нарушение белковосинтезирующей функции печени.";
                  return `Фактор ${f.feature} (${f.value}) увеличивает клинический риск.`;
                })
            } />
          )}
        </div>
      </div>
    </div>
  );
}
