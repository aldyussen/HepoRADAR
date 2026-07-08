import { AreaChart, Card, Title } from '@tremor/react';
import { ScoreEntry } from '../types';

interface TrendChartProps {
  labsData: any[];
  scoresData: ScoreEntry[];
}

export function TrendChart({ labsData, scoresData }: TrendChartProps) {
  return (
    <div className="space-y-6">
      <Card>
        <Title>Динамика трансаминаз (АСТ, АЛТ)</Title>
        {labsData.length === 0 ? (
          <p className="text-sm text-slate-500 mt-4">Нет данных для графиков трансаминаз (АСТ, АЛТ).</p>
        ) : (
          <AreaChart
            className="h-64 mt-4"
            data={labsData}
            index="date"
            categories={["ast", "alt"]}
            colors={["blue", "cyan"]}
            yAxisWidth={40}
          />
        )}
      </Card>
      
      <Card>
        <Title>Динамика расчетных индексов (FIB-4, APRI)</Title>
        {scoresData.length === 0 ? (
          <p className="text-sm text-slate-500 mt-4">Нет данных для расчетных индексов (FIB-4, APRI).</p>
        ) : (
          <AreaChart
            className="h-64 mt-4"
            data={scoresData.map(s => ({
              date: s.lab_date,
              fib4: s.fib4 ?? 0,
              apri: s.apri ?? 0
            }))}
            index="date"
            categories={["fib4", "apri"]}
            colors={["red", "amber"]}
            yAxisWidth={40}
          />
        )}
      </Card>
    </div>
  );
}
