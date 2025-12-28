import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import ExcelTableConfig from "./readExcel-67b4aee0.js";
import CsvTableConfig from "./readCsv-a8bb8b61.js";
import ParquetTableConfig from "./readParquet-92ce1dbc.js";
import { c as isInputExcelTable, d as isInputCsvTable, e as isInputParquetTable } from "./nodeInput-5d0d6b79.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { F as FileBrowser } from "./designer-9633482a.js";
import { d as defineComponent, r as ref, l as computed, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, u as unref, h as createBlock, i as createCommentVNode, f as createVNode, w as withCtx, _ as _export_sfc } from "./index-5429bbf8.js";
import "./dropDown-614b998d.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = { class: "file-upload-container" };
const _hoisted_4 = {
  for: "file-upload",
  class: "file-upload-label"
};
const _hoisted_5 = { class: "file-label-text" };
const _hoisted_6 = { key: 0 };
const _hoisted_7 = { class: "listbox-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Read",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const selectedFile = ref(null);
    const nodeRead = ref(null);
    const receivedTable = ref(null);
    const dataLoaded = ref(false);
    const modalVisibleForOpen = ref(false);
    const getDisplayFileName = computed(() => {
      var _a, _b;
      if ((_a = selectedFile.value) == null ? void 0 : _a.name) {
        return selectedFile.value.name;
      }
      if ((_b = receivedTable.value) == null ? void 0 : _b.name) {
        return receivedTable.value.name;
      }
      return "Choose a file...";
    });
    function createDefaultCsvSettings() {
      return {
        file_type: "csv",
        reference: "",
        starting_from_line: 0,
        delimiter: ",",
        has_headers: true,
        encoding: "utf-8",
        row_delimiter: "\n",
        quote_char: '"',
        infer_schema_length: 1e3,
        truncate_ragged_lines: false,
        ignore_errors: false
      };
    }
    function createDefaultExcelSettings() {
      return {
        file_type: "excel",
        sheet_name: "",
        start_row: 0,
        start_column: 0,
        end_row: 0,
        end_column: 0,
        has_headers: true,
        type_inference: false
      };
    }
    function createDefaultParquetSettings() {
      return {
        file_type: "parquet"
      };
    }
    const handleFileChange = (fileInfo) => {
      var _a;
      try {
        if (!fileInfo) {
          console.warn("No file info provided");
          return;
        }
        const ext = (_a = fileInfo.name.split(".").pop()) == null ? void 0 : _a.toLowerCase();
        if (!ext) {
          console.warn("No file type detected");
          return;
        }
        let fileType;
        let tableSettings;
        switch (ext) {
          case "xlsx":
            fileType = "excel";
            tableSettings = createDefaultExcelSettings();
            break;
          case "csv":
          case "txt":
            fileType = "csv";
            tableSettings = createDefaultCsvSettings();
            break;
          case "parquet":
            fileType = "parquet";
            tableSettings = createDefaultParquetSettings();
            break;
          default:
            console.warn("Unsupported file type:", ext);
            return;
        }
        receivedTable.value = {
          name: fileInfo.name,
          path: fileInfo.path,
          file_type: fileType,
          table_settings: tableSettings
        };
        selectedFile.value = fileInfo;
        modalVisibleForOpen.value = false;
      } catch (error) {
        console.error("Error handling file change:", error);
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      try {
        const nodeResult = await nodeStore.getNodeData(nodeId, false);
        if (!nodeResult) {
          console.warn("No node result received");
          dataLoaded.value = true;
          return;
        }
        nodeRead.value = nodeResult.setting_input;
        if (((_a = nodeResult.setting_input) == null ? void 0 : _a.is_setup) && nodeResult.setting_input.received_file) {
          receivedTable.value = nodeResult.setting_input.received_file;
        }
        dataLoaded.value = true;
      } catch (error) {
        console.error("Error loading node data:", error);
        dataLoaded.value = true;
      }
    };
    const pushNodeData = async () => {
      try {
        dataLoaded.value = false;
        if (!nodeRead.value || !receivedTable.value) {
          console.warn("No node read value available");
          dataLoaded.value = true;
          return;
        }
        nodeRead.value.is_setup = true;
        nodeRead.value.received_file = receivedTable.value;
        await nodeStore.updateSettings(nodeRead);
      } catch (error) {
        console.error("Error pushing node data:", error);
      } finally {
        dataLoaded.value = true;
      }
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      const _component_el_dialog = resolveComponent("el-dialog");
      return dataLoaded.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("div", {
              class: "file-upload-wrapper",
              onClick: _cache[0] || (_cache[0] = ($event) => modalVisibleForOpen.value = true)
            }, [
              createBaseVNode("label", _hoisted_4, [
                _cache[5] || (_cache[5] = createBaseVNode("i", { class: "fas fa-table file-icon" }, null, -1)),
                createBaseVNode("span", _hoisted_5, toDisplayString(getDisplayFileName.value), 1)
              ])
            ])
          ])
        ]),
        receivedTable.value ? (openBlock(), createElementBlock("div", _hoisted_6, [
          createBaseVNode("div", _hoisted_7, [
            _cache[6] || (_cache[6] = createBaseVNode("div", { class: "listbox-subtitle" }, "File Specs", -1)),
            unref(isInputExcelTable)(receivedTable.value.table_settings) ? (openBlock(), createBlock(ExcelTableConfig, {
              key: 0,
              modelValue: receivedTable.value.table_settings,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => receivedTable.value.table_settings = $event),
              path: receivedTable.value.path
            }, null, 8, ["modelValue", "path"])) : createCommentVNode("", true),
            unref(isInputCsvTable)(receivedTable.value.table_settings) ? (openBlock(), createBlock(CsvTableConfig, {
              key: 1,
              modelValue: receivedTable.value.table_settings,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => receivedTable.value.table_settings = $event)
            }, null, 8, ["modelValue"])) : createCommentVNode("", true),
            unref(isInputParquetTable)(receivedTable.value.table_settings) ? (openBlock(), createBlock(ParquetTableConfig, {
              key: 2,
              modelValue: receivedTable.value.table_settings,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => receivedTable.value.table_settings = $event)
            }, null, 8, ["modelValue"])) : createCommentVNode("", true)
          ])
        ])) : createCommentVNode("", true),
        createVNode(_component_el_dialog, {
          modelValue: modalVisibleForOpen.value,
          "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => modalVisibleForOpen.value = $event),
          title: "Select a file to Read",
          width: "70%"
        }, {
          default: withCtx(() => [
            createVNode(FileBrowser, {
              "allowed-file-types": ["csv", "txt", "parquet", "xlsx"],
              mode: "open",
              onFileSelected: handleFileChange
            })
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Read_vue_vue_type_style_index_0_scoped_f404e0dc_lang = "";
const Read = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-f404e0dc"]]);
export {
  Read as default
};
