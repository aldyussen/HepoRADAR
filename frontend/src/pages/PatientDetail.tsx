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

// Отложенные компоненты для будущего бэка (сохранены в репозитории):
// import { ReflexBanner } from "../components/ReflexBanner";
// import { ReferralModal } from "../components/ReferralModal";
// import { ReasonList } from "../components/ReasonList";

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

export function PatientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [patient, setPatient] = useState<PatientCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    const numericId = Number(id);
    if (isNaN(numericId)) {
      setError("Неверный ID пациента");
      setLoading(false);
      return;
    }
    
    api.getPatient(numericId)
      .then(setPatient)
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

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2 -ml-4 text-slate-500 hover:text-slate-900">
        <ArrowLeft className="w-4 h-4" /> Назад к списку
      </Button>

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

              {/* Будущие кнопки действий (закомментированы под будущий бэк):
              {latestScore && latestScore.is_lost && (
                <div className="border-t pt-3">
                  <ReferralModal patientId={patient.id} />
                </div>
              )}
              */}
            </CardContent>
          </Card>

          {/* Будущие баннеры (закомментированы под будущий бэк):
          {reflex && reflex.flags && reflex.flags.length > 0 && (
            <ReflexBanner flags={reflex.flags} />
          )}

          {latestScore && latestScore.reasons && (
            <ReasonList reasons={latestScore.reasons} />
          )}
          */}
        </div>
      </div>
    </div>
  );
}
