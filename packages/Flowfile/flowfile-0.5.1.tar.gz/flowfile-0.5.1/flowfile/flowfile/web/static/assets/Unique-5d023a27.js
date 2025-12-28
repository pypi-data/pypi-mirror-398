import { f as createSelectInputFromName } from "./nodeInput-5d0d6b79.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { s as selectDynamic } from "./selectDynamic-92e25ee3.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { d as defineComponent, r as ref, l as computed, n as onMounted, R as nextTick, o as onUnmounted, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, h as createBlock, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import "./UnavailableFields-a03f512c.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Unique",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const showContextMenuRemove = ref(false);
    const dataLoaded = ref(false);
    const contextMenuColumn = ref(null);
    const contextMenuRef = ref(null);
    const nodeUnique = ref(null);
    const nodeData = ref(null);
    const selection = ref([]);
    const uniqueInput = ref({
      columns: [],
      strategy: "any"
    });
    const loadSelection = (nodeData2, columnsToKeep) => {
      var _a;
      if ((_a = nodeData2.main_input) == null ? void 0 : _a.columns) {
        selection.value = nodeData2.main_input.columns.map((column) => {
          const keep = columnsToKeep.includes(column);
          return createSelectInputFromName(column, keep);
        });
      }
    };
    const loadData = async (nodeId) => {
      var _a;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeUnique.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      dataLoaded.value = true;
      if (nodeData.value) {
        if (nodeUnique.value) {
          if (nodeUnique.value.unique_input) {
            uniqueInput.value = nodeUnique.value.unique_input;
          } else {
            nodeUnique.value.unique_input = uniqueInput.value;
          }
          loadSelection(nodeData.value, uniqueInput.value.columns);
        }
      }
    };
    const calculateSelects = (updatedInputs) => {
      console.log(updatedInputs);
      selection.value = updatedInputs;
      uniqueInput.value.columns = updatedInputs.filter((input) => input.keep).map((input) => input.old_name);
    };
    const setUniqueColumns = () => {
      uniqueInput.value.columns = selection.value.filter((input) => input.keep).map((input) => input.old_name);
    };
    const loadNodeData = async (nodeId) => {
      loadData(nodeId);
      dataLoaded.value = true;
    };
    const handleClickOutside = (event) => {
      var _a;
      if (!((_a = contextMenuRef.value) == null ? void 0 : _a.contains(event.target))) {
        showContextMenu.value = false;
        contextMenuColumn.value = null;
        showContextMenuRemove.value = false;
      }
    };
    const getMissingColumns = (availableColumns, usedColumns) => {
      const availableSet = new Set(availableColumns);
      return Array.from(new Set(usedColumns.filter((usedColumn) => !availableSet.has(usedColumn))));
    };
    const missingColumns = computed(() => {
      var _a, _b;
      if (nodeData.value && ((_a = nodeData.value.main_input) == null ? void 0 : _a.columns)) {
        return getMissingColumns((_b = nodeData.value.main_input) == null ? void 0 : _b.columns, uniqueInput.value.columns);
      }
      return [];
    });
    const calculateMissingColumns = () => {
      var _a, _b;
      if (nodeData.value && ((_a = nodeData.value.main_input) == null ? void 0 : _a.columns)) {
        return getMissingColumns((_b = nodeData.value.main_input) == null ? void 0 : _b.columns, uniqueInput.value.columns);
      }
      return [];
    };
    const validateNode = async () => {
      var _a, _b;
      if ((_a = nodeUnique.value) == null ? void 0 : _a.unique_input) {
        await loadData(Number(nodeUnique.value.node_id));
      }
      const missingColumnsLocal = calculateMissingColumns();
      if (missingColumnsLocal.length > 0 && nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: `The fields ${missingColumns.value.join(", ")} are missing in the available columns.`
        });
      } else if (((_b = nodeUnique.value) == null ? void 0 : _b.unique_input.columns.length) == 0) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: "Please select at least one field."
        });
      } else if (nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    const instantValidate = async () => {
      var _a;
      if (missingColumns.value.length > 0 && nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: `The fields ${missingColumns.value.join(", ")} are missing in the available columns.`
        });
      } else if (((_a = nodeUnique.value) == null ? void 0 : _a.unique_input.columns.length) == 0) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: false,
          error: "Please select at least one field."
        });
      } else if (nodeUnique.value) {
        nodeStore.setNodeValidation(nodeUnique.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    const pushNodeData = async () => {
      var _a, _b, _c, _d;
      dataLoaded.value = false;
      setUniqueColumns();
      console.log("doing this");
      console.log((_a = nodeUnique.value) == null ? void 0 : _a.is_setup);
      console.log(nodeUnique.value);
      if ((_b = nodeUnique.value) == null ? void 0 : _b.is_setup) {
        nodeUnique.value.is_setup = true;
      }
      nodeStore.updateSettings(nodeUnique);
      await instantValidate();
      if ((_c = nodeUnique.value) == null ? void 0 : _c.unique_input) {
        nodeStore.setNodeValidateFunc((_d = nodeUnique.value) == null ? void 0 : _d.node_id, validateNode);
      }
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    onMounted(async () => {
      await nextTick();
      window.addEventListener("click", handleClickOutside);
    });
    onUnmounted(() => {
      window.removeEventListener("click", handleClickOutside);
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeUnique.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeUnique.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeUnique.value = $event)
        }, {
          default: withCtx(() => [
            createVNode(selectDynamic, {
              "select-inputs": selection.value,
              "show-keep-option": true,
              "show-data-type": false,
              "show-new-columns": false,
              "show-old-columns": true,
              "show-headers": true,
              "show-title": false,
              "show-data": true,
              title: "Select data",
              "original-column-header": "Column",
              onUpdateSelectInputs: calculateSelects
            }, null, 8, ["select-inputs"])
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Unique_vue_vue_type_style_index_0_scoped_c7455058_lang = "";
const Unique = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-c7455058"]]);
export {
  Unique as default
};
