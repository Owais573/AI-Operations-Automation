"use client"

import * as React from "react"
import { useDropzone } from "react-dropzone"
import { Upload, File, X, Info, CheckCircle2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { toast } from "sonner"

interface FileUploadProps {
  onUpload: (file: File) => void
  isUploading?: boolean
}

export function FileUpload({ onUpload, isUploading = false }: FileUploadProps) {
  const [file, setFile] = React.useState<File | null>(null)
  const [showGuide, setShowGuide] = React.useState(false)

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    multiple: false,
  })

  const handleUpload = () => {
    if (file) {
      onUpload(file)
    }
  }

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation()
    setFile(null)
  }

  return (
    <div className="space-y-4 w-full max-w-2xl mx-auto">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Upload className="h-5 w-5 text-primary" />
          Ingest Operational Data
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowGuide(!showGuide)}
          className="text-xs flex items-center gap-1.5"
        >
          <Info className="h-3.5 w-3.5" />
          {showGuide ? "Hide Guide" : "View Data Guide"}
        </Button>
      </div>

      {showGuide && (
        <Card className="p-4 bg-primary/5 border-primary/20 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
          <h4 className="text-sm font-bold flex items-center gap-2 text-primary">
            <CheckCircle2 className="h-4 w-4" />
            CSV/Excel Structure Guide
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-muted-foreground">
            <div className="space-y-2">
              <p className="font-semibold text-foreground">Recommended Columns:</p>
              <ul className="list-disc list-inside space-y-1">
                <li><code className="text-primary font-mono">Date</code> (ISO or standard formats)</li>
                <li><code className="text-primary font-mono">Product / SKU</code></li>
                <li><code className="text-primary font-mono">Revenue / Cost / Amount</code></li>
                <li><code className="text-primary font-mono">Region / Department</code></li>
              </ul>
            </div>
            <div className="space-y-2">
              <p className="font-semibold text-foreground">Multi-Sheet & Schema:</p>
              <ul className="list-disc list-inside space-y-1">
                <li><span className="text-foreground">Smart Selection:</span> High-score sheet selected via keywords (sales, rev, stock).</li>
                <li><span className="text-foreground">System Fallback:</span> If no keywords match, the first sheet is safely selected.</li>
                <li><span className="text-foreground">AI Discovery:</span> Unexpected columns are autonomously indexed & analyzed.</li>
                <li><span className="text-foreground">Deduplication:</span> Exact duplicate records are automatically purged.</li>
              </ul>
            </div>
          </div>
        </Card>
      )}

      <div
        {...getRootProps()}
        className={`relative group cursor-pointer rounded-xl border-2 border-dashed transition-all duration-300 h-48 flex flex-col items-center justify-center p-6
          ${isDragActive ? "border-primary bg-primary/10" : "border-border hover:border-primary/50 hover:bg-muted/50"}
          ${file ? "border-emerald-500/50 bg-emerald-500/5" : ""}
          ${isUploading ? "pointer-events-none opacity-50" : ""}
        `}
      >
        <input {...getInputProps()} />
        
        {file ? (
          <div className="flex flex-col items-center gap-3 animate-in zoom-in-95 duration-200">
            <div className="h-12 w-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <File className="h-6 w-6 text-emerald-500" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 h-8 w-8 rounded-full hover:bg-destructive hover:text-destructive-foreground transition-colors"
              onClick={clearFile}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="text-center space-y-4">
            <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <Upload className="h-6 w-6 text-primary" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">
                {isDragActive ? "Drop the file here" : "Click or drag file to upload"}
              </p>
              <p className="text-xs text-muted-foreground">
                Supports CSV, XLSX, and XLS
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end pt-2">
        <Button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className="w-full sm:w-auto min-w-[120px]"
        >
          {isUploading ? (
            <span className="flex items-center gap-2">
              <div className="h-3.5 w-3.5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
              Processing...
            </span>
          ) : (
            "Start Workflow"
          )}
        </Button>
      </div>

      <div className="flex items-start gap-2 p-3 rounded-lg bg-orange-500/5 border border-orange-500/20">
        <AlertCircle className="h-4 w-4 text-orange-500 mt-0.5 shrink-0" />
        <p className="text-[10px] text-orange-500/80 leading-relaxed">
          <b>Note:</b> For best results, ensure your column headers are descriptive. 
          The AI Discovery Agent will autonomously include metrics from columns it recognizes as strategically relevant.
        </p>
      </div>
    </div>
  )
}
