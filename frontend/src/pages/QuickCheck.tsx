import { useState, useRef } from "react";
import { api } from "../api";
import { Camera, AlertTriangle, Info } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { RiskBadge } from "../components/RiskBadge";
import { ReasonList } from "../components/ReasonList";
import { ReflexBanner } from "../components/ReflexBanner";

export function QuickCheck() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [values, setValues] = useState({
    age: "",
    sex: "",
    ast: "",
    alt: "",
    plt: "",
    anti_hcv_pos: false,
    hcv_rna_done: false
  });

  const [result, setResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const files = Array.from(e.target.files);
      const res = await api.quickExtract(files);
      if (res.status === "unreadable") {
        setError(res.hint || "Не удалось распознать значения. Пожалуйста, введите их вручную.");
      } else if (res.status === "error") {
        setError(res.hint || "Произошла ошибка при распознавании.");
      } else {
        setValues({
          age: res.age ? String(res.age) : "",
          sex: res.sex !== null ? String(res.sex) : "",
          ast: res.ast ? String(res.ast) : "",
          alt: res.alt ? String(res.alt) : "",
          plt: res.plt ? String(res.plt) : "",
          anti_hcv_pos: res.anti_hcv_pos || false,
          hcv_rna_done: res.hcv_rna_done || false,
        });
      }
    } catch (err: any) {
      setError(err.message || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    
    const payload = {
      age: values.age ? parseInt(values.age) : null,
      sex: values.sex !== "" ? parseInt(values.sex) : null,
      ast: values.ast ? parseFloat(values.ast.replace(',','.')) : null,
      alt: values.alt ? parseFloat(values.alt.replace(',','.')) : null,
      plt: values.plt ? parseFloat(values.plt.replace(',','.')) : null,
      anti_hcv_pos: values.anti_hcv_pos,
      hcv_rna_done: values.hcv_rna_done
    };

    try {
      const res = await api.quickCheck(payload);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Ошибка расчета");
    } finally {
      setLoading(false);
    }
  };

  const handleFillExample = () => {
    setValues({
      age: "62",
      sex: "1",
      ast: "55",
      alt: "32",
      plt: "110",
      anti_hcv_pos: true,
      hcv_rna_done: false
    });
  };

  return (
    <div className="max-w-xl mx-auto space-y-6 bg-slate-50 min-h-screen pb-16">
      <div className="bg-blue-600 p-4 text-white rounded-b-xl shadow-sm">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <ActivityIcon /> HepaRadar Quick Check
        </h1>
        <p className="text-sm text-blue-100 mt-1">Оценка риска фиброза по фото анализов</p>
      </div>

      <div className="px-4 space-y-6">
        {/* Upload Card */}
        <Card>
          <CardContent className="pt-6 space-y-4">
            <input 
              type="file" 
              accept="image/*" 
              multiple 
              className="hidden" 
              ref={fileInputRef} 
              onChange={handleUpload}
            />
            <Button 
              className="w-full h-16 text-lg gap-3 bg-slate-900 hover:bg-slate-800" 
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              <Camera className="w-6 h-6" />
              Сфотографировать анализ
            </Button>
            <div className="text-center text-sm text-slate-500">
              или <button onClick={handleFillExample} className="text-blue-600 underline">заполнить примером</button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg flex gap-3 text-sm border border-red-100">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {/* Form Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Значения показателей</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase">Возраст</label>
                <input 
                  type="number" 
                  value={values.age} 
                  onChange={e => setValues({...values, age: e.target.value})}
                  className="w-full p-2 border rounded-md"
                  placeholder="Лет"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase">Пол</label>
                <select 
                  value={values.sex} 
                  onChange={e => setValues({...values, sex: e.target.value})}
                  className="w-full p-2 border rounded-md bg-white"
                >
                  <option value="">—</option>
                  <option value="1">Мужской</option>
                  <option value="0">Женский</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase">АСТ</label>
                <input 
                  type="text" 
                  value={values.ast} 
                  onChange={e => setValues({...values, ast: e.target.value})}
                  className="w-full p-2 border rounded-md"
                  placeholder="Ед/л"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase">АЛТ</label>
                <input 
                  type="text" 
                  value={values.alt} 
                  onChange={e => setValues({...values, alt: e.target.value})}
                  className="w-full p-2 border rounded-md"
                  placeholder="Ед/л"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-500 uppercase">Тромбоц. (PLT)</label>
                <input 
                  type="text" 
                  value={values.plt} 
                  onChange={e => setValues({...values, plt: e.target.value})}
                  className="w-full p-2 border rounded-md"
                  placeholder="10^9/л"
                />
              </div>
            </div>

            <div className="pt-2 space-y-3">
              <label className="flex items-center gap-3 p-3 border rounded-lg bg-slate-50">
                <input 
                  type="checkbox" 
                  checked={values.anti_hcv_pos} 
                  onChange={e => setValues({...values, anti_hcv_pos: e.target.checked})}
                  className="w-5 h-5 text-blue-600 rounded border-gray-300"
                />
                <span className="text-sm font-medium">Антитела к гепатиту C (Anti-HCV) обнаружены</span>
              </label>
              
              {values.anti_hcv_pos && (
                <label className="flex items-center gap-3 p-3 border rounded-lg bg-slate-50 ml-4">
                  <input 
                    type="checkbox" 
                    checked={values.hcv_rna_done} 
                    onChange={e => setValues({...values, hcv_rna_done: e.target.checked})}
                    className="w-5 h-5 text-blue-600 rounded border-gray-300"
                  />
                  <span className="text-sm font-medium">Сдан ПЦР на РНК ВГС</span>
                </label>
              )}
            </div>

            <Button 
              className="w-full mt-4 bg-blue-600 hover:bg-blue-700" 
              onClick={handleCalculate}
              disabled={loading}
            >
              {loading ? "Расчет..." : "Рассчитать риск"}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <div className="space-y-4">
            {result.status === "incomplete" ? (
              <Card className="border-orange-200 bg-orange-50">
                <CardContent className="pt-6 text-center space-y-3">
                  <AlertTriangle className="w-10 h-10 text-orange-500 mx-auto" />
                  <h3 className="font-bold text-orange-900">Недостаточно данных</h3>
                  <p className="text-sm text-orange-800">{result.message}</p>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="pt-6 space-y-6">
                  {result.message && (
                    <div className="bg-slate-100 p-3 rounded-md text-sm text-slate-700 flex gap-2">
                      <Info className="w-5 h-5 text-blue-500 flex-shrink-0" />
                      {result.message}
                    </div>
                  )}

                  <div className="text-center space-y-2 border-b pb-6">
                    <p className="text-sm text-slate-500 uppercase font-bold tracking-wider">Зона риска фиброза</p>
                    <div className="flex justify-center scale-150 py-2">
                      <RiskBadge zone={result.zone} />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center divide-x">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">FIB-4</p>
                      <p className="text-lg font-mono">{result.fib4?.toFixed(2) || "—"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">APRI</p>
                      <p className="text-lg font-mono">{result.apri?.toFixed(2) || "—"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Де Ритис</p>
                      <p className="text-lg font-mono">{result.de_ritis?.toFixed(2) || "—"}</p>
                    </div>
                  </div>

                  {result.reflex_flag && (
                    <div className="pt-4">
                      <ReflexBanner flags={[{type: "hcv_rna_missing", msg: "Пациент с положительным Anti-HCV не сдавал подтверждающий ПЦР-тест на РНК ВГС. Необходим дозаказ исследования!"}]} />
                    </div>
                  )}

                  {result.factors && result.factors.length > 0 && (
                    <div className="pt-4">
                      <p className="text-xs font-bold text-slate-500 uppercase mb-2">Ключевые факторы</p>
                      <ReasonList reasons={result.factors.map((f: any) => `Показатель ${f.feature} (${f.value}) отклоняется от нормы, увеличивая риск.`)} />
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        <div className="text-center text-xs text-slate-400 px-4 mt-8 pb-4">
          <p className="font-semibold text-slate-500">Демонстрационный режим</p>
          <p>Фотографии и данные не сохраняются. Приложение не является медицинским изделием и не заменяет консультацию врача.</p>
        </div>
      </div>
    </div>
  );
}

function ActivityIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
  );
}
