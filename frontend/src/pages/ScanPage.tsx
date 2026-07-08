import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { ScanSummary } from "../types";
import { Button } from "../components/ui/button";
import { Activity, Play, RefreshCw, AlertCircle, CheckCircle2, ShieldAlert } from "lucide-react";

export function ScanPage() {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<ScanSummary | null>(() => {
    const saved = localStorage.getItem("heparadar_scan_summary");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

  const [animatedLost, setAnimatedLost] = useState(0);
  const [animatedTotal, setAnimatedTotal] = useState(0);
  const navigate = useNavigate();

  // Animation effect for counters
  useEffect(() => {
    if (!summary) return;

    // Animate lost_count
    let lostStart = 0;
    const lostEnd = summary.lost_count;
    const duration = 1200; // 1.2s total animation

    setAnimatedLost(0);
    if (lostEnd > 0) {
      const lostStep = Math.max(Math.floor(duration / lostEnd), 15);
      const lostTimer = setInterval(() => {
        lostStart += 1;
        setAnimatedLost(lostStart);
        if (lostStart >= lostEnd) {
          clearInterval(lostTimer);
        }
      }, lostStep);
      return () => clearInterval(lostTimer);
    } else {
      setAnimatedLost(0);
    }

    // Animate total
    let totalStart = 0;
    const totalEnd = summary.total;
    setAnimatedTotal(0);
    if (totalEnd > 0) {
      const totalStep = Math.max(Math.floor(duration / totalEnd), 15);
      const totalTimer = setInterval(() => {
        totalStart += Math.ceil(totalEnd / 50); // Increment faster for larger numbers
        if (totalStart >= totalEnd) {
          totalStart = totalEnd;
          clearInterval(totalTimer);
        }
        setAnimatedTotal(totalStart);
      }, totalStep);
      return () => clearInterval(totalTimer);
    } else {
      setAnimatedTotal(0);
    }
  }, [summary]);

  const handleScan = async () => {
    setScanning(true);
    setError("");
    setSummary(null);
    try {
      const result = await api.scanCohort();
      setSummary(result);
      localStorage.setItem("heparadar_scan_summary", JSON.stringify(result));
    } catch (e: any) {
      setError(e.message || "Ошибка при сканировании когорты");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8 px-4">
      <div className="text-center space-y-4">
        <div className="inline-flex p-3 bg-blue-50 rounded-2xl text-blue-600 border border-blue-100 shadow-sm animate-pulse">
          <Activity className="w-8 h-8" />
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          Сканирование когорты HepaRadar
        </h1>
        <p className="text-lg text-slate-500 max-w-2xl mx-auto">
          Запустите интеллектуальный поиск в лабораторной базе МИС. Система автоматически рассчитает
          индексы FIB-4, APRI, De Ritis и выявит пациентов с высоким риском заболеваний печени, потерявших контакт с врачом.
        </p>
      </div>

      {/* Main Scanner Card */}
      <div className="bg-white border rounded-3xl p-8 shadow-md relative overflow-hidden flex flex-col items-center justify-center min-h-[350px]">
        {/* Pulsing background glow during scanning */}
        {scanning && (
          <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/10 via-indigo-500/5 to-cyan-500/10 animate-pulse pointer-events-none" />
        )}

        {error && (
          <div className="mb-6 w-full p-4 bg-red-50 text-red-700 border border-red-200 rounded-2xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        {!scanning && !summary ? (
          // Initial Idle State
          <div className="text-center space-y-6">
            <div className="w-24 h-24 bg-slate-50 rounded-full flex items-center justify-center border border-slate-100 mx-auto shadow-inner">
              <Play className="w-10 h-10 text-slate-400 translate-x-0.5" />
            </div>
            <Button
              onClick={handleScan}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-lg px-8 py-6 rounded-2xl shadow-lg transition-all transform hover:scale-105 active:scale-95"
            >
              Запустить сканирование когорты
            </Button>
            <p className="text-xs text-slate-400">
              Расчет индексов займет несколько секунд в зависимости от размера базы данных
            </p>
          </div>
        ) : scanning ? (
          // Scanning State (WOW Loader)
          <div className="text-center space-y-6">
            <div className="relative w-28 h-28 mx-auto flex items-center justify-center">
              <div className="absolute inset-0 border-4 border-blue-100 rounded-full" />
              <div className="absolute inset-0 border-4 border-t-blue-600 rounded-full animate-spin" />
              <Activity className="w-10 h-10 text-blue-600 animate-pulse" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold text-slate-900">Прочёсывание лабораторной базы...</h3>
              <p className="text-sm text-slate-400 max-w-sm mx-auto">
                Извлечение биохимических маркеров (АСТ, АЛТ, Тромбоциты), LOINC-сопоставление и вычисление скоров FIB-4
              </p>
            </div>
          </div>
        ) : (
          // Scan Completed (WOW Counter & Stats)
          <div className="w-full text-center space-y-8 animate-fade-in">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-sm font-semibold border border-emerald-200 mb-2">
                <CheckCircle2 className="w-4 h-4" /> Анализ завершен
              </div>
              
              <div className="flex flex-col items-center justify-center">
                <span className="text-7xl font-extrabold text-indigo-600 tracking-tight transition-all">
                  {animatedLost}
                </span>
                <span className="text-base font-semibold text-slate-500 uppercase tracking-wider mt-1">
                  Утерянных контактов выявлено
                </span>
              </div>
            </div>

            {/* Results Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full border-t border-b border-slate-100 py-6">
              <div className="p-3">
                <p className="text-xs text-slate-400 uppercase font-semibold">Обработано всего</p>
                <p className="text-2xl font-bold text-slate-800 mt-1">{animatedTotal}</p>
              </div>
              <div className="p-3">
                <p className="text-xs text-red-500 uppercase font-semibold">Высокий риск</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{summary!.high}</p>
              </div>
              <div className="p-3">
                <p className="text-xs text-amber-500 uppercase font-semibold">Серая зона</p>
                <p className="text-2xl font-bold text-amber-600 mt-1">{summary!.grey}</p>
              </div>
              <div className="p-3">
                <p className="text-xs text-emerald-500 uppercase font-semibold">Низкий риск</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">{summary!.low}</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button
                variant="outline"
                onClick={handleScan}
                className="rounded-xl px-6 py-5 border-slate-200 hover:bg-slate-50 text-slate-600 font-medium"
              >
                <RefreshCw className="w-4 h-4 mr-2" /> Пересканировать базу
              </Button>
              <Button
                onClick={() => navigate("/worklist")}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl px-8 py-5 shadow-md"
              >
                Перейти к списку пациентов
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Helpful clinical warning banner */}
      <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100 flex gap-3 text-slate-500 text-sm">
        <ShieldAlert className="w-5 h-5 text-slate-400 flex-shrink-0" />
        <p className="leading-relaxed">
          <strong>Внимание:</strong> Результаты расчетов FIB-4 основаны на лабораторных показателях АСТ, АЛТ и тромбоцитов.
          Показатель FIB-4 имеет сниженную диагностическую точность для пациентов моложе 35 и старше 65 лет. Рекомендуется дополнительный ML-анализ для пациентов в серой зоне.
        </p>
      </div>
    </div>
  );
}
