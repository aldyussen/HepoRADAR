import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { WorklistItem, Zone, ScanSummary, sexLabel } from "../types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { RiskBadge } from "../components/RiskBadge";
import { Activity, Play, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "../components/ui/button";

export function Worklist() {
  const [items, setItems] = useState<WorklistItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  
  // Filters
  const [zone, setZone] = useState<Zone | "">("");
  const [ageMin, setAgeMin] = useState<number | "">("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  const [scanSummary, setScanSummary] = useState<ScanSummary | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState("");

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
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, pageSize, zone, ageMin]);

  // Fetch when page or filters change
  useEffect(() => {
    fetchWorklist();
  }, [fetchWorklist]);

  const handleScan = async () => {
    setScanning(true);
    setScanError("");
    try {
      const summary = await api.scanCohort();
      setScanSummary(summary);
      setPage(1);
      fetchWorklist();
    } catch (e: any) {
      setScanError(e.message || "Ошибка запуска сканирования");
    } finally {
      setScanning(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Список пациентов</h1>
        <Button 
          onClick={handleScan} 
          disabled={scanning}
          className="bg-blue-600 hover:bg-blue-700 text-white gap-2"
        >
          {scanning ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          {scanning ? "Сканирование..." : "Сканировать когорту"}
        </Button>
      </div>

      {scanError && (
        <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{scanError}</span>
        </div>
      )}

      {scanSummary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 bg-blue-50 border border-blue-100 p-4 rounded-xl">
          <div>
            <p className="text-xs text-slate-500 uppercase font-medium">Всего обработано</p>
            <p className="text-2xl font-bold text-slate-950">{scanSummary.total}</p>
          </div>
          <div>
            <p className="text-xs text-red-500 uppercase font-medium">Высокий риск</p>
            <p className="text-2xl font-bold text-red-600">{scanSummary.high}</p>
          </div>
          <div>
            <p className="text-xs text-amber-500 uppercase font-medium">Серая зона</p>
            <p className="text-2xl font-bold text-amber-600">{scanSummary.grey}</p>
          </div>
          <div>
            <p className="text-xs text-emerald-500 uppercase font-medium">Низкий риск</p>
            <p className="text-2xl font-bold text-emerald-600">{scanSummary.low}</p>
          </div>
          <div>
            <p className="text-xs text-indigo-500 uppercase font-medium">Утеряно связей</p>
            <p className="text-2xl font-bold text-indigo-600">{scanSummary.lost_count}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center bg-slate-50 p-4 rounded-lg border border-slate-100">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold text-slate-500">Зона риска</label>
          <select 
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
          <label className="text-xs font-semibold text-slate-500">Минимальный возраст</label>
          <input 
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
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 border border-dashed rounded-lg bg-white p-8 text-center">
          <AlertCircle className="w-12 h-12 mb-4 text-slate-300" />
          <p className="font-semibold text-slate-700 mb-1">Список пуст</p>
          <p className="text-sm max-w-sm">Запустите скан когорты или измените фильтры, чтобы найти потерянных пациентов.</p>
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
                    className="cursor-pointer hover:bg-slate-50 transition-colors"
                    onClick={() => navigate(`/patients/${patient.patient_id}`)}
                  >
                    <TableCell className="font-mono font-medium text-slate-900">{patient.mrn}</TableCell>
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
                      {patient.ml_risk !== null ? (patient.ml_risk * 100).toFixed(0) + "%" : "—"}
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
