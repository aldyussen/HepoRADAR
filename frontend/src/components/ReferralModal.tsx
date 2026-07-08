import { useState } from "react";
import { api } from "../api";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Button } from "./ui/button";
import { FileText, Copy, Check } from "lucide-react";

export function ReferralModal({ patientId }: { patientId: string }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleOpen = async (isOpen: boolean) => {
    setOpen(isOpen);
    if (isOpen && !text) {
      setLoading(true);
      try {
        const res = await (api as any).createReferral(patientId);
        setText(res.text);
      } catch {
        setText("Ошибка генерации направления.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      {/* @ts-ignore */}
      <DialogTrigger asChild>
        <Button className="bg-blue-600 hover:bg-blue-700 gap-2">
          <FileText className="w-4 h-4" />
          Сформировать направление
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Черновик направления</DialogTitle>
          <DialogDescription>
            Вы можете скопировать этот текст и вставить его в МИС (медицинскую информационную систему).
          </DialogDescription>
        </DialogHeader>
        
        {loading ? (
          <div className="h-40 flex items-center justify-center text-slate-500">Генерация...</div>
        ) : (
          <div className="mt-4">
            <div className="bg-slate-50 p-4 rounded-md border text-sm whitespace-pre-wrap font-mono max-h-96 overflow-auto">
              {text}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="outline" onClick={handleCopy} className="gap-2">
                {copied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                {copied ? "Скопировано!" : "Копировать"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
