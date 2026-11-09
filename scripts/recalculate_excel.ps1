# Configuration
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkbookPath = Join-Path $ProjectRoot 'excel/chapter11.xlsx'
$AuthorName = 'Yazad Madan'
$ExcelApplication = $null
$Workbook = $null

try {
    $ExcelApplication = New-Object -ComObject Excel.Application
    $ExcelApplication.Visible = $false
    $ExcelApplication.DisplayAlerts = $false
    $Workbook = $ExcelApplication.Workbooks.Open($WorkbookPath)
    $ExcelApplication.CalculateFullRebuild()
    $Workbook.BuiltinDocumentProperties.Item('Author').Value = $AuthorName
    $Workbook.Save()
    Write-Output 'Native Excel recalculation saved. Run the Python reconciliation tests.'
} finally {
    if ($null -ne $Workbook) {
        $Workbook.Close($false)
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($Workbook) | Out-Null
    }
    if ($null -ne $ExcelApplication) {
        $ExcelApplication.Quit()
        [Runtime.InteropServices.Marshal]::FinalReleaseComObject($ExcelApplication) | Out-Null
    }
}
