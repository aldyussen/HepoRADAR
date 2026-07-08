import { useState } from "react";
import { api } from "../api";
import { IngestReport } from "../types";
import { Activity, UploadCloud, CheckCircle, AlertTriangle, AlertOctagon } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { useAuth } from "../lib/auth";

export function Ingest() {
  const { user } = useAuth();
  const role = user?.role || "viewer";

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<IngestReport | null>(null);

  if (role !== "admin") {
    return (
      <div className="max-w-md mx-auto mt-16 text-center space-y-6 p-8 border border-dashed rounded-3xl bg-white shadow-sm">
        <div className="w-16 h-16 bg-amber-50 border border-amber-100 rounded-full flex items-center justify-center mx-auto text-amber-500">
          <AlertOctagon className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-slate-900">Демо-режим ролей</h2>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            В демонстрационных целях импорт лабораторных данных (загрузка CSV) ограничен. Для выполнения этого действия требуются права роли <strong>Администратор</strong>.
          </p>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-left">
          <p className="text-xs text-slate-500 leading-relaxed">
            <strong>Примечание:</strong> Полноценная аутентификация и проверка JWT-токенов на сервере подключаются на Фазе 6 (L6). Сейчас вы можете переключить активную роль на <strong>Администратор (Admin)</strong> в верхнем меню, чтобы протестировать импорт.
          </p>
        </div>
      </div>
    );
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError("");
      setReport(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const data = await api.ingestCsv(file);
      setReport(data);
    } catch (e: any) {
      setError(e.message || "Ошибка при импорте файла");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-heading">Импорт данных</h1>
      <p className="text-slate-500 -mt-2">Загрузите CSV-файл с лабораторными данными для пополнения когорты.</p>

      <Card>
        <CardHeader>
          <CardTitle>Выбор файла CSV</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="flex items-center justify-center w-full">
              <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-slate-50 hover:bg-slate-100/70 transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <UploadCloud className="w-10 h-10 mb-3 text-slate-400" />
                  <p className="mb-2 text-sm text-slate-500 font-medium">
                    {file ? (
                      <span className="text-blue-600 font-semibold">{file.name}</span>
                    ) : (
                      <span>Кликните для выбора CSV файла</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-400">Максимальный размер: 10MB</p>
                </div>
                <input 
                  type="file" 
                  accept=".csv" 
                  className="hidden" 
                  onChange={handleFileChange}
                  disabled={loading}
                />
              </label>
            </div>

            {error && (
              <div className="p-4 bg-red-50 text-red-700 border border-red-100 rounded-lg flex items-center gap-2 text-sm">
                <AlertOctagon className="w-5 h-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex justify-end">
              <Button 
                type="submit" 
                disabled={!file || loading}
                className="bg-blue-600 hover:bg-blue-700 text-white gap-2"
              >
                {loading ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    Загрузка...
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    Загрузить данные
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {report && (
        <div className="space-y-6">
          {/* Main metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-slate-500 uppercase font-semibold">Строк обработано</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{report.rows_processed}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-emerald-600 uppercase font-semibold">Добавлено пациентов</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">{report.patients_ingested}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-blue-600 uppercase font-semibold">Добавлено анализов</p>
                <p className="text-2xl font-bold text-blue-600 mt-1">{report.labs_ingested}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-xs text-red-600 uppercase font-semibold">Отклонено строк</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{report.rows_rejected}</p>
              </CardContent>
            </Card>
          </div>

          {/* Quality flags summary */}
          {Object.keys(report.quality_flags).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" />
                  Флаги качества данных
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(report.quality_flags).map(([flag, count]) => (
                    <span 
                      key={flag}
                      className="inline-flex items-center gap-1.5 rounded-md bg-amber-50 px-2.5 py-1.5 text-xs font-semibold text-amber-800 ring-1 ring-inset ring-amber-600/20"
                    >
                      <span className="font-mono">{flag}</span>
                      <span className="bg-amber-200/50 px-1.5 py-0.5 rounded text-amber-950 font-bold">{count}</span>
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Rejected rows list */}
          {report.rejected_rows.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-red-700">Отклоненные строки</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-60 overflow-y-auto border rounded-md">
                  <Table>
                    <TableHeader className="bg-slate-50 sticky top-0">
                      <TableRow>
                        <TableHead className="w-24">Индекс строки</TableHead>
                        <TableHead>Причина отклонения</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {report.rejected_rows.map((row, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-mono text-slate-500 font-medium">#{row.row_index}</TableCell>
                          <TableCell className="text-red-600 font-medium">{row.reason}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {report.rows_rejected === 0 && report.rows_processed > 0 && (
            <div className="p-4 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded-lg flex items-center gap-2 text-sm font-medium">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              <span>Все данные успешно импортированы без ошибок!</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
