import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Upload, AlertCircle, FileDown, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface ImportWizardProps {
  onClose: () => void;
  open: boolean;
}

export function ImportWizard({ onClose, open }: ImportWizardProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<'upload' | 'review' | 'result'>('upload');
  const [result, setResult] = useState<any>(null);
  const [errorCSV, setErrorCSV] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const importMutation = useMutation({
    mutationFn: async (vars: { file: File, createCategories: boolean }) => {
      const formData = new FormData();
      formData.append('file', vars.file);
      const res = await api.post(`/api/transactions/import?create_new_categories=${vars.createCategories}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return res.data;
    },
    onSuccess: (data) => {
      setResult(data);
      
      // Generate CSV blob if errors
      if (data.errors && data.errors.length > 0) {
          const headers = Object.keys(data.errors[0]).join(',');
          const rows = data.errors.map((row: any) => Object.values(row).map((v: any) => `"${v}"`).join(',')).join('\n');
          setErrorCSV(`${headers}\n${rows}`);
      } else {
          setErrorCSV(null);
      }

      // Check if we have unknown categories errors
      const catErrors = data.errors?.filter((e: any) => e.status && e.status.includes('Category') && e.status.includes('not found'));
      
      if (catErrors && catErrors.length > 0 && !isRetrying) {
        setStep('review');
      } else {
        setStep('result');
        queryClient.invalidateQueries({ queryKey: ['transactions'] });
        queryClient.invalidateQueries({ queryKey: ['stats'] });
      }
    },
    onError: (err: any) => {
        // Handle structural errors (400)
        setResult({ error: err.response?.data?.detail || "Import failed" });
        setStep('result');
    }
  });

  const handleUpload = () => {
    if (!file) return;
    setIsRetrying(false);
    importMutation.mutate({ file, createCategories: false });
  };

  const handleRetroactiveCreate = () => {
     if (!file) return;
     setIsRetrying(true);
     importMutation.mutate({ file, createCategories: true });
  }

  const downloadErrorCSV = () => {
      if (!errorCSV) return;
      const blob = new Blob([errorCSV], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'import_failures.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
  };

  const unknownCategories = result?.errors?.filter((e: any) => e.status && e.status.includes('not found')).map((e: any) => e.category) || [];
  const uniqueUnknown = [...new Set(unknownCategories)];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-white dark:bg-slate-900 border-gray-100 dark:border-slate-800 text-slate-900 dark:text-slate-100">
        <DialogHeader>
          <DialogTitle>Import Transactions</DialogTitle>
          <DialogDescription>Upload a CSV file to import transactions.</DialogDescription>
        </DialogHeader>

        {step === 'upload' && (
            <div className="space-y-4">
                <div 
                    className="border-2 border-dashed border-gray-200 dark:border-slate-700 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                >
                    <Upload className="h-10 w-10 text-gray-400 mb-2" />
                    <p className="text-sm text-gray-500">Click to select CSV file</p>
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        accept=".csv" 
                        className="hidden" 
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                </div>
                {file && (
                    <div className="text-sm text-center font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 py-2 rounded-lg">
                        {file.name}
                    </div>
                )}
                <DialogFooter>
                    <Button onClick={handleUpload} disabled={!file || importMutation.isPending}>
                       {importMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                       Upload & Import
                    </Button>
                </DialogFooter>
            </div>
        )}

        {step === 'review' && (
            <div className="space-y-4">
                 <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Unknown Categories Found</AlertTitle>
                    <AlertDescription>
                        {uniqueUnknown.length} categories in the file are not in your list:
                        <div className="mt-2 text-xs font-mono bg-white/50 p-2 rounded max-h-24 overflow-y-auto">
                            {uniqueUnknown.join(', ')}
                        </div>
                    </AlertDescription>
                </Alert>
                <p className="text-sm text-gray-500">
                    Would you like to automatically create these categories and retry importing the valid rows?
                </p>
                 <DialogFooter className="gap-2 sm:gap-0">
                    <Button variant="outline" onClick={() => setStep('result')}>
                        No, skip them 
                    </Button>
                    <Button onClick={handleRetroactiveCreate} disabled={importMutation.isPending}>
                        {importMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Yes, Create & Import
                    </Button>
                </DialogFooter>
            </div>
        )}

        {step === 'result' && (
             <div className="space-y-4">
                {result?.error ? (
                    <div className="text-center p-4">
                        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-2" />
                        <h3 className="font-semibold text-red-600">Import Failed</h3>
                        <p className="text-sm text-gray-500 mt-1">{result.error}</p>
                    </div>
                ) : (
                    <div className="text-center space-y-4">
                        <div className="flex justify-center gap-8">
                             <div className="text-center">
                                 <div className="text-2xl font-bold text-green-500">{result?.imported_count || 0}</div>
                                 <div className="text-xs text-gray-500 uppercase">Imported</div>
                             </div>
                             <div className="text-center">
                                 <div className="text-2xl font-bold text-red-500">{result?.failed_count || 0}</div>
                                 <div className="text-xs text-gray-500 uppercase">Failed</div>
                             </div>
                             {result?.new_categories_detected?.length > 0 && (
                                 <div className="text-center">
                                     <div className="text-2xl font-bold text-blue-500">{result.new_categories_detected.length}</div>
                                     <div className="text-xs text-gray-500 uppercase">New Cats</div>
                                 </div>
                             )}
                        </div>

                        {result?.failed_count > 0 && (
                            <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-xl border border-orange-100 dark:border-orange-900/50">
                                <p className="text-sm text-orange-700 dark:text-orange-400 mb-3">
                                    Some transactions failed validation. Download the error report to view reasons and rectify.
                                </p>
                                <Button variant="outline" size="sm" onClick={downloadErrorCSV} className="w-full">
                                    <FileDown className="mr-2 h-4 w-4" /> Download Error CSV
                                </Button>
                            </div>
                        )}
                    </div>
                )}
                <DialogFooter>
                    <Button onClick={onClose}>Close</Button>
                </DialogFooter>
             </div>
        )}

      </DialogContent>
    </Dialog>
  );
}
