import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { WorklistItem, Zone, sexLabel } from "../types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { RiskBadge } from "../components/RiskBadge";
import { Activity, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";

export function Worklist() {
  const [items, setItems] = useState<WorklistItem[]>([]);
  const [total, setTotal] = useState(0);
  const [reflexCount, setReflexCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  
  // Filters
  const [zone, setZone] = useState<Zone | "">("");
  const [ageMin, setAgeMin] = useState<number | "">("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const fetchWorklist = useCallback(() => {
    setLoading(true);
    setError("");
    api.getWorklist({
      page,
      page_size: pageSize,
      zone: zone || undefined,
      age_min: ageMin === "" ? undefined : ageMin,
    })
      .then(res => {
        setItems(res.items);
        setTotal(res.total);
        setReflexCount(res.reflex_count || 0);
        if (res.total > 0 && !localStorage.getItem("heparadar_scan_summary")) {
          api.scanCohort()
            .then(sum => {
              localStorage.setItem("heparadar_scan_summary", JSON.stringify(sum));
            })
            .catch(() => {});
        }
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, pageSize, zone, ageMin]);

  // Fetch when page or filters change
  useEffect(() => {
    fetchWorklist();
  }, [fetchWorklist]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Список пациентов</h1>
          {reflexCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-0.5 text-sm font-medium text-amber-800 border border-amber-200" title="Пациенты, которым показан дозаказ ПЦР на HCV-RNA">
              ХВГ-рефлекс: {reflexCount}
            </span>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center bg-slate-50 p-4 rounded-lg border border-slate-100">
        <div className="flex flex-col gap-1">
          <label htmlFor="risk-zone-filter" className="text-xs font-semibold text-slate-500">Зона риска</label>
          <select 
            id="risk-zone-filter"
            aria-label="Фильтр по зоне риска"
            value={zone} 
            onChange={(e) => { setZone(e.target.value as Zone | ""); setPage(1); }}
            className="border border-slate-200 rounded-md p-1.5 text-sm bg-white min-w-[120px] focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Все зоны</option>
            <option value="high">Высокий</option>
            <option value="grey">Серая зона</option>
            <option value="low">Низкий</option>
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="min-age-filter" className="text-xs font-semibold text-slate-500">Минимальный возраст</label>
          <input 
            id="min-age-filter"
            aria-label="Фильтр по минимальному возрасту"
            type="number" 
            placeholder="Напр. 50"
            value={ageMin} 
            onChange={(e) => {
              const val = e.target.value;
              setAgeMin(val === "" ? "" : Number(val));
              setPage(1);
            }}
            className="border border-slate-200 rounded-md p-1.5 text-sm bg-white w-[140px] focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <Button 
          variant="outline" 
          onClick={() => { setZone(""); setAgeMin(""); setPage(1); }}
          className="self-end h-[34px] text-xs font-medium"
        >
          Сбросить фильтры
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Activity className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg">
          Ошибка загрузки списка: {error}
        </div>
      ) : total === 0 && !zone && !ageMin ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 border border-dashed rounded-lg bg-white p-8 text-center">
          <AlertCircle className="w-12 h-12 mb-4 text-slate-300 animate-pulse" />
          <p className="font-semibold text-slate-700 mb-1">База данных не отсканирована или пуста</p>
          <p className="text-sm max-w-sm mb-4">Для отображения списка потерянных пациентов необходимо запустить сканирование когорты.</p>
          <Button onClick={() => navigate("/scan")} className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl">
            Перейти к сканированию
          </Button>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 border border-dashed rounded-lg bg-white p-8 text-center">
          <AlertCircle className="w-12 h-12 mb-4 text-slate-300" />
          <p className="font-semibold text-slate-700 mb-1">Список пуст</p>
          <p className="text-sm max-w-sm">Измените фильтры, чтобы найти потерянных пациентов.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="border rounded-md bg-white overflow-hidden shadow-sm">
            <Table>
              <TableHeader className="bg-slate-50">
                <TableRow>
                  <TableHead className="font-semibold text-slate-700">Идентификатор (MRN)</TableHead>
                  <TableHead className="font-semibold text-slate-700">Возраст</TableHead>
                  <TableHead className="font-semibold text-slate-700">Пол</TableHead>
                  <TableHead className="font-semibold text-slate-700">Зона</TableHead>
                  <TableHead className="font-semibold text-slate-700">FIB-4</TableHead>
                  <TableHead className="font-semibold text-slate-700">APRI</TableHead>
                  <TableHead className="font-semibold text-slate-700">ML Риск</TableHead>
                  <TableHead className="font-semibold text-slate-700">Дата анализа</TableHead>
                  <TableHead className="font-semibold text-slate-700">Статус</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((patient) => (
                  <TableRow 
                    key={patient.patient_id} 
                    className="cursor-pointer hover:bg-slate-50 transition-colors focus:outline-none focus:bg-slate-100 focus:ring-2 focus:ring-blue-500 focus:ring-inset"
                    onClick={() => navigate(`/patients/${patient.patient_id}`)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        navigate(`/patients/${patient.patient_id}`);
                      }
                    }}
                    aria-label={`Профиль пациента с MRN ${patient.mrn}`}
                  >
                    <TableCell className="font-mono font-medium text-slate-900">
                      <div className="flex items-center gap-2">
                        {patient.mrn}
                        {patient.has_reflex && (
                          <span title="Показан дозаказ ПЦР">
                            <AlertCircle className="w-4 h-4 text-amber-500" />
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-700">{patient.age !== null ? patient.age : "—"}</TableCell>
                    <TableCell className="text-slate-700">{sexLabel(patient.sex)}</TableCell>
                    <TableCell><RiskBadge zone={patient.zone} /></TableCell>
                    <TableCell className="text-slate-700 font-medium">
                      {patient.fib4 !== null ? patient.fib4.toFixed(2) : "—"}
                    </TableCell>
                    <TableCell className="text-slate-700">
                      {patient.apri !== null ? patient.apri.toFixed(2) : "—"}
                    </TableCell>
                    <TableCell className="text-slate-700">
                      {patient.zone === "grey" ? (
                        patient.ml_risk !== null ? (patient.ml_risk * 100).toFixed(0) + "%" : "н/д"
                      ) : (
                        <span title="ML применяется в серой зоне для уточнения" className="cursor-help border-b border-dashed border-slate-300">
                          —
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-slate-500 font-mono text-xs">
                      {patient.last_lab_date || "—"}
                    </TableCell>
                    <TableCell>
                      {patient.is_lost ? (
                        <span className="inline-flex items-center rounded-full bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/10">
                          Потерян
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/10">
                          Активен
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center bg-white px-4 py-3 border rounded-md shadow-sm">
              <span className="text-sm text-slate-700">
                Страница <span className="font-semibold">{page}</span> из <span className="font-semibold">{totalPages}</span> (всего: <span className="font-semibold">{total}</span>)
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="text-xs"
                >
                  Назад
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="text-xs"
                >
                  Вперед
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
