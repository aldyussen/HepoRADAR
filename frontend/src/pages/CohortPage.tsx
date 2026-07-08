import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Title, Text, DonutChart, BarChart, Legend, Grid } from "@tremor/react";
import { ScanSummary } from "../types";
import { api } from "../api";
import { Button } from "../components/ui/button";
import { BarChart2, PieChart, Sparkles, ShieldAlert, ArrowRight, Activity } from "lucide-react";

export function CohortPage() {
  const [summary, setSummary] = useState<ScanSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const saved = localStorage.getItem("heparadar_scan_summary");
    if (saved) {
      try {
        setSummary(JSON.parse(saved));
        setLoading(false);
        return;
      } catch {}
    }

    api.getWorklist({ page: 1, page_size: 1 })
      .then(res => {
        if (res.total > 0) {
          api.scanCohort()
            .then(sum => {
              localStorage.setItem("heparadar_scan_summary", JSON.stringify(sum));
              setSummary(sum);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
        } else {
          setLoading(false);
        }
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Activity className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg max-w-md mx-auto mt-12">
        Ошибка загрузки аналитики: {error}
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="max-w-md mx-auto mt-16 text-center space-y-6 p-8 border border-dashed rounded-3xl bg-white shadow-sm">
        <div className="w-16 h-16 bg-slate-50 border border-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-400">
          <BarChart2 className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Аналитика когорты пуста</h2>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            Распределение когорты по группам риска строится на основе результатов сканирования.
            Пожалуйста, запустите сканирование базы данных.
          </p>
        </div>
        <Button
          onClick={() => navigate("/scan")}
          className="bg-blue-600 hover:bg-blue-700 text-white w-full rounded-2xl py-5 font-semibold"
        >
          Перейти к сканированию <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    );
  }

  // Risk data for donut chart
  const riskDistribution = [
    { name: "Высокий риск (FIB-4 > 2.67)", count: summary.high },
    { name: "Серая зона (1.30 - 2.67)", count: summary.grey },
    { name: "Низкий риск (FIB-4 < 1.30)", count: summary.low },
  ];

  const totalRisky = summary.high + summary.grey + summary.low;

  // Formatting percentages helper
  const getPercent = (value: number) => {
    if (totalRisky === 0) return "0%";
    return ((value / totalRisky) * 100).toFixed(1) + "%";
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-8 px-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Обзор когорты риска</h1>
          <p className="text-sm text-slate-500 mt-1">
            Аналитическое распределение пациентов на основе расчета биохимических индексов фиброза
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate("/scan")}
          className="rounded-xl border-slate-200 hover:bg-slate-50 text-slate-600 gap-2 self-start"
        >
          <Sparkles className="w-4 h-4 text-blue-500" /> Обновить результаты сканирования
        </Button>
      </div>

      {/* Main KPI Stats Row */}
      <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
        <Card className="decoration-sky-500 decoration-2 border-t-2">
          <Text className="text-slate-500 text-xs font-semibold uppercase">Размер когорты</Text>
          <Title className="text-3xl font-bold mt-1 text-slate-900">{summary.total}</Title>
          <Text className="text-slate-400 text-xs mt-1">Всего пациентов с анализами</Text>
        </Card>
        
        <Card className="decoration-red-500 decoration-2 border-t-2">
          <Text className="text-slate-500 text-xs font-semibold uppercase">Высокий риск</Text>
          <Title className="text-3xl font-bold mt-1 text-red-600">{summary.high}</Title>
          <Text className="text-slate-400 text-xs mt-1">Доля: {getPercent(summary.high)} от пациентов с FIB-4 ({totalRisky} из {summary.total})</Text>
        </Card>

        <Card className="decoration-amber-500 decoration-2 border-t-2">
          <Text className="text-slate-500 text-xs font-semibold uppercase">Серая зона</Text>
          <Title className="text-3xl font-bold mt-1 text-amber-600">{summary.grey}</Title>
          <Text className="text-slate-400 text-xs mt-1">Доля: {getPercent(summary.grey)} от пациентов с FIB-4 ({totalRisky} из {summary.total})</Text>
        </Card>

        <Card className="decoration-indigo-500 decoration-2 border-t-2">
          <Text className="text-slate-500 text-xs font-semibold uppercase">Потеряно контактов</Text>
          <Title className="text-3xl font-bold mt-1 text-indigo-600">{summary.lost_count}</Title>
          <Text className="text-slate-400 text-xs mt-1">Нуждаются в вызове к врачу</Text>
        </Card>
      </Grid>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Donut Chart: Risk Percentages */}
        <Card className="lg:col-span-1 flex flex-col justify-between">
          <div>
            <Title className="text-slate-800 text-lg font-bold flex items-center gap-2">
              <PieChart className="w-5 h-5 text-indigo-500" /> Процентное распределение
            </Title>
            <Text className="text-xs text-slate-400 mt-1">Распределение пациентов по зонам риска</Text>
          </div>
          
          <div className="my-6 flex justify-center">
            <DonutChart
              className="h-56 w-56"
              data={riskDistribution}
              category="count"
              index="name"
              colors={["red-500", "amber-500", "emerald-500"]}
              showLabel={true}
            />
          </div>

          <Legend
            categories={["Высокий риск", "Серая зона", "Низкий риск"]}
            colors={["red", "amber", "emerald"]}
            className="text-xs border-t pt-4"
          />
          {summary.total > totalRisky && (
            <div className="text-xs text-slate-400 mt-2 text-center">
              {summary.total - totalRisky} пациентов — FIB-4 не применим (возраст &lt;35)
            </div>
          )}
        </Card>

        {/* Bar Chart: Risk Exact Counts */}
        <Card className="lg:col-span-2 flex flex-col justify-between">
          <div>
            <Title className="text-slate-800 text-lg font-bold flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-indigo-500" /> Численное распределение рисков
            </Title>
            <Text className="text-xs text-slate-400 mt-1">Количество пациентов в каждой из зон риска</Text>
          </div>

          <div className="my-6">
            <BarChart
              className="h-64 mt-4"
              data={[
                { name: "Высокий", "Пациентов": summary.high },
                { name: "Серая зона", "Пациентов": summary.grey },
                { name: "Низкий", "Пациентов": summary.low }
              ]}
              index="name"
              categories={["Пациентов"]}
              colors={["indigo"]}
              yAxisWidth={30}
            />
          </div>

          <div className="border-t pt-4 flex justify-between items-center text-xs text-slate-400">
            <span>Общее число пациентов с расчетом FIB-4: {totalRisky}</span>
            <span className="font-semibold text-indigo-600 cursor-pointer hover:underline" onClick={() => navigate("/worklist")}>
              Перейти к списку пациентов &rarr;
            </span>
          </div>
        </Card>
      </div>

      {/* RAG Guideline Info banner */}
      <div className="bg-blue-50 border border-blue-100 rounded-3xl p-6 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
        <div className="flex gap-3">
          <ShieldAlert className="w-8 h-8 text-blue-500 flex-shrink-0" />
          <div>
            <h4 className="text-base font-bold text-slate-900">Интерпретация результатов серой зоны</h4>
            <p className="text-sm text-slate-500 mt-0.5">
              Согласно рекомендациям EASL/AASLD, пациенты в серой зоне риска (FIB-4 от 1.30 до 2.67) требуют проведения
              второго этапа неинвазивного скрининга (расчета APRI или ML-оценки риска) для исключения выраженного фиброза.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
