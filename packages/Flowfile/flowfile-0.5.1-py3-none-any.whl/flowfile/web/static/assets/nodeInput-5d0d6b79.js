import { r as ref } from "./index-5429bbf8.js";
function isInputCsvTable(settings) {
  return settings.file_type === "csv";
}
function isInputExcelTable(settings) {
  return settings.file_type === "excel";
}
function isInputParquetTable(settings) {
  return settings.file_type === "parquet";
}
const createSelectInputFromName = (columnName, keep = true) => {
  return {
    old_name: columnName,
    new_name: columnName,
    keep,
    is_altered: false,
    data_type_change: false,
    is_available: true,
    position: 0,
    original_position: 0
  };
};
function isOutputCsvTable(settings) {
  return settings.file_type === "csv";
}
function isOutputParquetTable(settings) {
  return settings.file_type === "parquet";
}
function isOutputExcelTable(settings) {
  return settings.file_type === "excel";
}
ref(null);
export {
  isOutputExcelTable as a,
  isOutputParquetTable as b,
  isInputExcelTable as c,
  isInputCsvTable as d,
  isInputParquetTable as e,
  createSelectInputFromName as f,
  isOutputCsvTable as i
};
