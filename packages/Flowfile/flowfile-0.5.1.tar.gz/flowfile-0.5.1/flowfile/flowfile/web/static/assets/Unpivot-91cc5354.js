import { d as defineComponent, r as ref, n as onMounted, R as nextTick, o as onUnmounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, F as Fragment, q as renderList, s as normalizeClass, v as withModifiers, t as toDisplayString, h as createBlock, i as createCommentVNode, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import ContextMenu from "./ContextMenu-23e909da.js";
import SettingsSection from "./SettingsSection-f0f75a42.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = { class: "listbox" };
const _hoisted_4 = ["onClick", "onContextmenu", "onDragstart", "onDrop"];
const _hoisted_5 = { class: "listbox-wrapper" };
const _hoisted_6 = { class: "listbox-wrapper" };
const _hoisted_7 = { class: "switch-container" };
const _hoisted_8 = {
  key: 1,
  class: "listbox-wrapper"
};
const _hoisted_9 = { class: "listbox-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Unpivot",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const dataLoaded = ref(false);
    const contextMenuPosition = ref({ x: 0, y: 0 });
    const selectedColumns = ref([]);
    const contextMenuOptions = ref([]);
    const contextMenuRef = ref(null);
    const nodeData = ref(null);
    const draggedColumnName = ref(null);
    const dataTypeSelectorOptions = ["all", "numeric", "string", "date", "all"];
    const unpivotInput = ref({
      index_columns: [],
      value_columns: [],
      data_type_selector: null,
      data_type_selector_mode: "column"
    });
    const nodeUnpivot = ref(null);
    const getColumnClass = (columnName) => {
      return selectedColumns.value.includes(columnName) ? "is-selected" : "";
    };
    const onDragStart = (columnName, event) => {
      var _a;
      draggedColumnName.value = columnName;
      (_a = event.dataTransfer) == null ? void 0 : _a.setData("text/plain", columnName);
    };
    const onDrop = (index) => {
      var _a, _b;
      if (draggedColumnName.value) {
        const colSchema = (_b = (_a = nodeData.value) == null ? void 0 : _a.main_input) == null ? void 0 : _b.table_schema;
        if (colSchema) {
          const fromIndex = colSchema.findIndex((col) => col.name === draggedColumnName.value);
          if (fromIndex !== -1 && fromIndex !== index) {
            const [movedColumn] = colSchema.splice(fromIndex, 1);
            colSchema.splice(index, 0, movedColumn);
          }
        }
        draggedColumnName.value = null;
      }
    };
    const onDropInSection = (section) => {
      if (draggedColumnName.value) {
        removeColumnIfExists(draggedColumnName.value);
        console.log("section", unpivotInput.value.index_columns);
        if (section === "index" && !unpivotInput.value.index_columns.includes(draggedColumnName.value)) {
          unpivotInput.value.index_columns.push(draggedColumnName.value);
        } else if (section === "value" && !unpivotInput.value.value_columns.includes(draggedColumnName.value)) {
          unpivotInput.value.value_columns.push(draggedColumnName.value);
        }
        draggedColumnName.value = null;
      }
    };
    const openContextMenu = (columnName, event) => {
      selectedColumns.value = [columnName];
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
      contextMenuOptions.value = [
        {
          label: "Add to Index",
          action: "index",
          disabled: isColumnAssigned(columnName)
        },
        {
          label: "Add to Value",
          action: "value",
          disabled: isColumnAssigned(columnName) || !(unpivotInput.value.data_type_selector_mode === "column")
        }
      ];
      showContextMenu.value = true;
    };
    const handleContextMenuSelect = (action) => {
      const column = selectedColumns.value[0];
      if (action === "index" && !unpivotInput.value.index_columns.includes(column)) {
        removeColumnIfExists(column);
        unpivotInput.value.index_columns.push(column);
      } else if (action === "value" && !unpivotInput.value.index_columns.includes(column)) {
        removeColumnIfExists(column);
        unpivotInput.value.value_columns.push(column);
      }
      closeContextMenu();
    };
    const isColumnAssigned = (columnName) => {
      return unpivotInput.value.index_columns.includes(columnName) || unpivotInput.value.value_columns.includes(columnName);
    };
    const removeColumnIfExists = (column) => {
      unpivotInput.value.index_columns = unpivotInput.value.index_columns.filter(
        (col) => col !== column
      );
      unpivotInput.value.value_columns = unpivotInput.value.value_columns.filter(
        (col) => col !== column
      );
    };
    const removeColumn = (type, column) => {
      if (type === "index") {
        unpivotInput.value.index_columns = unpivotInput.value.index_columns.filter(
          (col) => col !== column
        );
      } else if (type === "value") {
        unpivotInput.value.value_columns = unpivotInput.value.value_columns.filter(
          (col) => col !== column
        );
      }
    };
    const handleItemClick = (columnName) => {
      selectedColumns.value = [columnName];
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      console.log("loadNodeData from unpivot ");
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeUnpivot.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeData.value) {
        if (nodeUnpivot.value) {
          if (nodeUnpivot.value.unpivot_input) {
            unpivotInput.value = nodeUnpivot.value.unpivot_input;
          } else {
            nodeUnpivot.value.unpivot_input = unpivotInput.value;
          }
        }
      }
      dataLoaded.value = true;
      console.log("loadNodeData from groupby");
    };
    const handleClickOutside = (event) => {
      const targetEvent = event.target;
      if (targetEvent.id === "pivot-context-menu")
        return;
      showContextMenu.value = false;
    };
    const closeContextMenu = () => {
      showContextMenu.value = false;
    };
    const pushNodeData = async () => {
      if (unpivotInput.value) {
        if (unpivotInput.value.data_type_selector_mode === "data_type") {
          unpivotInput.value.value_columns = [];
        } else {
          unpivotInput.value.data_type_selector = null;
        }
        nodeUnpivot.value.unpivot_input = unpivotInput.value;
        nodeStore.updateSettings(nodeUnpivot);
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
      const _component_el_switch = resolveComponent("el-switch");
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      return dataLoaded.value && nodeUnpivot.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeUnpivot.value,
          "onUpdate:modelValue": _cache[9] || (_cache[9] = ($event) => nodeUnpivot.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b;
            return [
              createBaseVNode("div", _hoisted_2, [
                createBaseVNode("ul", _hoisted_3, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList((_b = (_a = nodeData.value) == null ? void 0 : _a.main_input) == null ? void 0 : _b.table_schema, (col_schema, index) => {
                    return openBlock(), createElementBlock("li", {
                      key: col_schema.name,
                      class: normalizeClass(getColumnClass(col_schema.name)),
                      draggable: "true",
                      onClick: ($event) => handleItemClick(col_schema.name),
                      onContextmenu: withModifiers(($event) => openContextMenu(col_schema.name, $event), ["prevent"]),
                      onDragstart: ($event) => onDragStart(col_schema.name, $event),
                      onDragover: _cache[0] || (_cache[0] = withModifiers(() => {
                      }, ["prevent"])),
                      onDrop: ($event) => onDrop(index)
                    }, toDisplayString(col_schema.name) + " (" + toDisplayString(col_schema.data_type) + ") ", 43, _hoisted_4);
                  }), 128))
                ])
              ]),
              showContextMenu.value ? (openBlock(), createBlock(ContextMenu, {
                key: 0,
                id: "pivot-context-menu",
                ref_key: "contextMenuRef",
                ref: contextMenuRef,
                position: contextMenuPosition.value,
                options: contextMenuOptions.value,
                onSelect: handleContextMenuSelect,
                onClose: closeContextMenu
              }, null, 8, ["position", "options"])) : createCommentVNode("", true),
              createBaseVNode("div", _hoisted_5, [
                createVNode(SettingsSection, {
                  title: "Index Keys",
                  items: unpivotInput.value.index_columns,
                  droppable: "true",
                  onRemoveItem: _cache[1] || (_cache[1] = ($event) => removeColumn("index", $event)),
                  onDragover: _cache[2] || (_cache[2] = withModifiers(() => {
                  }, ["prevent"])),
                  onDrop: _cache[3] || (_cache[3] = ($event) => onDropInSection("index"))
                }, null, 8, ["items"])
              ]),
              createBaseVNode("div", _hoisted_6, [
                createBaseVNode("div", _hoisted_7, [
                  _cache[10] || (_cache[10] = createBaseVNode("span", null, "Value selector", -1)),
                  createVNode(_component_el_switch, {
                    modelValue: unpivotInput.value.data_type_selector_mode,
                    "onUpdate:modelValue": _cache[4] || (_cache[4] = ($event) => unpivotInput.value.data_type_selector_mode = $event),
                    "active-value": "column",
                    "inactive-value": "data_type",
                    "active-text": "Column",
                    "inactive-text": "Data Type",
                    "inline-prompt": ""
                  }, null, 8, ["modelValue"])
                ]),
                unpivotInput.value.data_type_selector_mode === "column" ? (openBlock(), createBlock(SettingsSection, {
                  key: 0,
                  title: "Columns to unpivot",
                  "title-font-size": "14px",
                  items: unpivotInput.value.value_columns,
                  droppable: "true",
                  onRemoveItem: _cache[5] || (_cache[5] = ($event) => removeColumn("value", $event)),
                  onDragover: _cache[6] || (_cache[6] = withModifiers(() => {
                  }, ["prevent"])),
                  onDrop: _cache[7] || (_cache[7] = ($event) => onDropInSection("value"))
                }, null, 8, ["items"])) : (openBlock(), createElementBlock("div", _hoisted_8, [
                  _cache[11] || (_cache[11] = createBaseVNode("div", { class: "listbox-subtitle" }, "Dynamic data type selector", -1)),
                  createBaseVNode("div", _hoisted_9, [
                    createVNode(_component_el_select, {
                      modelValue: unpivotInput.value.data_type_selector,
                      "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => unpivotInput.value.data_type_selector = $event),
                      placeholder: "Select",
                      size: "small",
                      style: { "width": "100%" }
                    }, {
                      default: withCtx(() => [
                        (openBlock(), createElementBlock(Fragment, null, renderList(dataTypeSelectorOptions, (item) => {
                          return createVNode(_component_el_option, {
                            key: item,
                            label: item,
                            value: item,
                            style: { "width": "400px" }
                          }, null, 8, ["label", "value"]);
                        }), 64))
                      ]),
                      _: 1
                    }, 8, ["modelValue"])
                  ])
                ]))
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
const Unpivot_vue_vue_type_style_index_0_scoped_e713e710_lang = "";
const Unpivot = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-e713e710"]]);
export {
  Unpivot as default
};
