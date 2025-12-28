import { i as isOutputCsvTable, a as isOutputExcelTable, b as isOutputParquetTable } from "./nodeInput-5d0d6b79.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { d as defineComponent, r as ref, l as computed, b as resolveComponent, c as openBlock, e as createElementBlock, p as createBaseVNode, h as createBlock, i as createCommentVNode, f as createVNode, w as withCtx, u as unref, g as createTextVNode, F as Fragment, q as renderList, a as axios, _ as _export_sfc } from "./index-5429bbf8.js";
import CsvTableConfig from "./outputCsv-076b85ab.js";
import ExcelTableConfig from "./outputExcel-0fd17dbe.js";
import ParquetTableConfig from "./outputParquet-b61e0847.js";
import { w as warning_filled_default, F as FileBrowser } from "./designer-9633482a.js";
function createDefaultOutputSettings() {
  return {
    name: "output.csv",
    directory: ".",
    file_type: "csv",
    write_mode: "overwrite",
    table_settings: {
      file_type: "csv",
      delimiter: ",",
      encoding: "utf-8"
    }
  };
}
function createCsvTableSettings() {
  return {
    file_type: "csv",
    delimiter: ",",
    encoding: "utf-8"
  };
}
function createParquetTableSettings() {
  return {
    file_type: "parquet"
  };
}
function createExcelTableSettings() {
  return {
    file_type: "excel",
    sheet_name: "Sheet1"
  };
}
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "main-part" };
const _hoisted_3 = { class: "file-upload-row" };
const _hoisted_4 = {
  key: 1,
  class: "warning-message"
};
const _hoisted_5 = { class: "main-part" };
const _hoisted_6 = { class: "file-type-row" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Output",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const nodeOutput = ref(null);
    const dataLoaded = ref(false);
    const showFileSelectionModal = ref(false);
    const selectedDirectoryExists = ref(null);
    const localFileInfos = ref([]);
    const hasFileExtension = computed(() => {
      var _a, _b;
      return ((_b = (_a = nodeOutput.value) == null ? void 0 : _a.output_settings.name) == null ? void 0 : _b.includes(".")) ?? false;
    });
    function getWriteOptions(fileType) {
      return fileType === "csv" ? ["overwrite", "new file", "append"] : ["overwrite", "new file"];
    }
    async function fetchFiles() {
      var _a, _b;
      try {
        const response = await axios.get("/files/files_in_local_directory/", {
          params: { directory: (_a = nodeOutput.value) == null ? void 0 : _a.output_settings.directory },
          headers: { accept: "application/json" }
        });
        localFileInfos.value = response.data;
        selectedDirectoryExists.value = true;
      } catch (err) {
        const axiosError = err;
        if (((_b = axiosError.response) == null ? void 0 : _b.status) === 404) {
          localFileInfos.value = [];
          selectedDirectoryExists.value = false;
        }
      }
    }
    function detectFileType(fileName) {
      var _a;
      if (!fileName)
        return;
      const extension = (_a = fileName.split(".").pop()) == null ? void 0 : _a.toLowerCase();
      if (!extension || !["csv", "xlsx", "xls", "parquet"].includes(extension)) {
        return;
      }
      const verifiedExtension = extension;
      const fileTypeMap = {
        csv: "csv",
        xlsx: "excel",
        xls: "excel",
        parquet: "parquet"
      };
      if (nodeOutput.value && fileTypeMap[verifiedExtension]) {
        nodeOutput.value.output_settings.file_type = fileTypeMap[verifiedExtension];
        nodeOutput.value.output_settings.write_mode = "overwrite";
        updateTableSettings(fileTypeMap[verifiedExtension]);
      }
    }
    function updateTableSettings(fileType) {
      if (!nodeOutput.value)
        return;
      switch (fileType) {
        case "csv":
          nodeOutput.value.output_settings.table_settings = createCsvTableSettings();
          break;
        case "parquet":
          nodeOutput.value.output_settings.table_settings = createParquetTableSettings();
          break;
        case "excel":
          nodeOutput.value.output_settings.table_settings = createExcelTableSettings();
          break;
      }
    }
    function handleFileNameChange() {
      var _a;
      if ((_a = nodeOutput.value) == null ? void 0 : _a.output_settings.name) {
        detectFileType(nodeOutput.value.output_settings.name);
      }
    }
    function handleFileTypeChange() {
      if (!nodeOutput.value)
        return;
      const fileExtMap = {
        csv: ".csv",
        excel: ".xlsx",
        parquet: ".parquet"
      };
      const baseName = nodeOutput.value.output_settings.name.split(".")[0];
      nodeOutput.value.output_settings.name = baseName + (fileExtMap[nodeOutput.value.output_settings.file_type] || "");
      if (!nodeOutput.value.output_settings.write_mode) {
        nodeOutput.value.output_settings.write_mode = "overwrite";
      }
      updateTableSettings(nodeOutput.value.output_settings.file_type);
    }
    function handleDirectorySelected(directoryPath) {
      if (!nodeOutput.value)
        return;
      nodeOutput.value.output_settings.directory = directoryPath;
      showFileSelectionModal.value = false;
      fetchFiles();
    }
    function handleFileSelected(filePath, currentPath, fileName) {
      if (!nodeOutput.value)
        return;
      nodeOutput.value.output_settings.name = fileName;
      nodeOutput.value.output_settings.directory = currentPath;
      showFileSelectionModal.value = false;
      detectFileType(fileName);
    }
    function handleFolderChange() {
      fetchFiles();
    }
    const querySearch = (queryString, cb) => {
      const results = queryString ? localFileInfos.value.filter(
        (item) => item.file_name.toLowerCase().startsWith(queryString.toLowerCase())
      ) : localFileInfos.value;
      cb(results);
    };
    async function loadNodeData(nodeId) {
      const nodeResult = await nodeStore.getNodeData(nodeId, false);
      if ((nodeResult == null ? void 0 : nodeResult.setting_input) && nodeResult.setting_input.is_setup) {
        nodeOutput.value = nodeResult.setting_input;
      } else {
        nodeOutput.value = {
          output_settings: createDefaultOutputSettings(),
          flow_id: nodeStore.flow_id,
          node_id: nodeId,
          cache_results: false,
          pos_x: 0,
          pos_y: 0,
          is_setup: false,
          description: ""
        };
      }
      dataLoaded.value = true;
    }
    async function pushNodeData() {
      var _a;
      if ((_a = nodeOutput.value) == null ? void 0 : _a.output_settings) {
        await nodeStore.updateSettings(nodeOutput);
        dataLoaded.value = false;
      }
    }
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      const _component_el_input = resolveComponent("el-input");
      const _component_el_icon = resolveComponent("el-icon");
      const _component_el_autocomplete = resolveComponent("el-autocomplete");
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_dialog = resolveComponent("el-dialog");
      return dataLoaded.value && nodeOutput.value && nodeOutput.value.output_settings ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", _hoisted_2, [
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("label", {
              class: "file-upload-label",
              onClick: _cache[0] || (_cache[0] = ($event) => showFileSelectionModal.value = true)
            }, _cache[9] || (_cache[9] = [
              createBaseVNode("i", { class: "file-icon fas fa-upload" }, null, -1),
              createBaseVNode("span", { class: "file-label-text" }, "Folder", -1)
            ])),
            nodeOutput.value.output_settings ? (openBlock(), createBlock(_component_el_input, {
              key: 0,
              modelValue: nodeOutput.value.output_settings.directory,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeOutput.value.output_settings.directory = $event),
              size: "small",
              onChange: handleFolderChange
            }, null, 8, ["modelValue"])) : createCommentVNode("", true),
            selectedDirectoryExists.value === false ? (openBlock(), createElementBlock("span", _hoisted_4, [
              createVNode(_component_el_icon, null, {
                default: withCtx(() => [
                  createVNode(unref(warning_filled_default))
                ]),
                _: 1
              })
            ])) : createCommentVNode("", true)
          ]),
          createVNode(_component_el_autocomplete, {
            modelValue: nodeOutput.value.output_settings.name,
            "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeOutput.value.output_settings.name = $event),
            "fetch-suggestions": querySearch,
            clearable: "",
            class: "inline-input w-50",
            placeholder: "Select file or create file",
            "trigger-on-focus": false,
            onChange: handleFileNameChange,
            onSelect: handleFileNameChange
          }, null, 8, ["modelValue"])
        ]),
        createBaseVNode("div", _hoisted_5, [
          createBaseVNode("div", _hoisted_6, [
            _cache[10] || (_cache[10] = createTextVNode(" File type: ")),
            createVNode(_component_el_select, {
              modelValue: nodeOutput.value.output_settings.file_type,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeOutput.value.output_settings.file_type = $event),
              class: "m-2",
              placeholder: "Select",
              size: "small",
              disabled: hasFileExtension.value,
              onChange: handleFileTypeChange
            }, {
              default: withCtx(() => [
                (openBlock(), createElementBlock(Fragment, null, renderList(["csv", "excel", "parquet"], (type) => {
                  return createVNode(_component_el_option, {
                    key: type,
                    label: type,
                    value: type
                  }, null, 8, ["label", "value"]);
                }), 64))
              ]),
              _: 1
            }, 8, ["modelValue", "disabled"])
          ]),
          _cache[11] || (_cache[11] = createTextVNode(" Writing option: ")),
          createVNode(_component_el_select, {
            modelValue: nodeOutput.value.output_settings.write_mode,
            "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => nodeOutput.value.output_settings.write_mode = $event),
            class: "m-2",
            placeholder: "Select output option",
            size: "small",
            disabled: !nodeOutput.value.output_settings.file_type
          }, {
            default: withCtx(() => [
              (openBlock(true), createElementBlock(Fragment, null, renderList(getWriteOptions(nodeOutput.value.output_settings.file_type), (option) => {
                return openBlock(), createBlock(_component_el_option, {
                  key: option,
                  label: option,
                  value: option
                }, null, 8, ["label", "value"]);
              }), 128))
            ]),
            _: 1
          }, 8, ["modelValue", "disabled"]),
          unref(isOutputCsvTable)(nodeOutput.value.output_settings.table_settings) ? (openBlock(), createBlock(CsvTableConfig, {
            key: 0,
            modelValue: nodeOutput.value.output_settings.table_settings,
            "onUpdate:modelValue": _cache[5] || (_cache[5] = ($event) => nodeOutput.value.output_settings.table_settings = $event)
          }, null, 8, ["modelValue"])) : createCommentVNode("", true),
          unref(isOutputExcelTable)(nodeOutput.value.output_settings.table_settings) ? (openBlock(), createBlock(ExcelTableConfig, {
            key: 1,
            modelValue: nodeOutput.value.output_settings.table_settings,
            "onUpdate:modelValue": _cache[6] || (_cache[6] = ($event) => nodeOutput.value.output_settings.table_settings = $event)
          }, null, 8, ["modelValue"])) : createCommentVNode("", true),
          unref(isOutputParquetTable)(nodeOutput.value.output_settings.table_settings) ? (openBlock(), createBlock(ParquetTableConfig, {
            key: 2,
            modelValue: nodeOutput.value.output_settings.table_settings,
            "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => nodeOutput.value.output_settings.table_settings = $event)
          }, null, 8, ["modelValue"])) : createCommentVNode("", true)
        ]),
        createVNode(_component_el_dialog, {
          modelValue: showFileSelectionModal.value,
          "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => showFileSelectionModal.value = $event),
          title: "Select directory or file to write to",
          width: "70%"
        }, {
          default: withCtx(() => [
            createVNode(FileBrowser, {
              "allowed-file-types": ["csv", "xlsx", "parquet"],
              "allow-directory-selection": true,
              mode: "create",
              onDirectorySelected: handleDirectorySelected,
              onOverwriteFile: handleFileSelected,
              onCreateFile: handleFileSelected
            })
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
const Output_vue_vue_type_style_index_0_scoped_4c6e3071_lang = "";
const Output = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-4c6e3071"]]);
export {
  Output as default
};
