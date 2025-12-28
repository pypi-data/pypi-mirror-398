import { d as defineComponent, r as ref, l as computed, n as onMounted, R as nextTick, o as onUnmounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, F as Fragment, q as renderList, s as normalizeClass, t as toDisplayString, i as createCommentVNode, T as normalizeStyle, v as withModifiers, h as createBlock, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = {
  key: 0,
  class: "listbox"
};
const _hoisted_4 = ["onClick", "onContextmenu"];
const _hoisted_5 = ["onClick"];
const _hoisted_6 = {
  key: 1,
  class: "table-wrapper"
};
const _hoisted_7 = { class: "styled-table" };
const _hoisted_8 = ["onContextmenu"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "GroupBy",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const showContextMenuRemove = ref(false);
    const dataLoaded = ref(false);
    const contextMenuPosition = ref({ x: 0, y: 0 });
    const contextMenuColumn = ref(null);
    const contextMenuRef = ref(null);
    const selectedColumns = ref([]);
    const nodeGroupBy = ref(null);
    const nodeData = ref(null);
    const aggOptions = [
      "groupby",
      "sum",
      "max",
      "median",
      "min",
      "count",
      "n_unique",
      "first",
      "last",
      "concat"
    ];
    const firstSelectedIndex = ref(null);
    const groupByInput = ref({
      agg_cols: []
    });
    const openRowContextMenu = (event, index) => {
      event.preventDefault();
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
      contextMenuRowIndex.value = index;
      showContextMenuRemove.value = true;
    };
    const removeRow = () => {
      if (contextMenuRowIndex.value !== null) {
        groupByInput.value.agg_cols.splice(contextMenuRowIndex.value, 1);
      }
      showContextMenuRemove.value = false;
      contextMenuRowIndex.value = null;
    };
    const contextMenuRowIndex = ref(null);
    const singleColumnSelected = computed(() => selectedColumns.value.length == 1);
    const openContextMenu = (clickedIndex, columnName, event) => {
      event.preventDefault();
      event.stopPropagation();
      if (!selectedColumns.value.includes(columnName)) {
        selectedColumns.value = [columnName];
      }
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
      showContextMenu.value = true;
    };
    const setAggregations = (aggType, columns) => {
      if (columns) {
        columns.forEach((column) => {
          const new_column_name = aggType !== "groupby" ? column + "_" + aggType : column;
          groupByInput.value.agg_cols.push({
            old_name: column,
            agg: aggType,
            new_name: new_column_name
          });
        });
      }
      showContextMenu.value = false;
      contextMenuColumn.value = null;
    };
    const handleItemClick = (clickedIndex, columnName, event) => {
      if (event.shiftKey && firstSelectedIndex.value !== null) {
        const range = getRange(firstSelectedIndex.value, clickedIndex);
        selectedColumns.value = range.map((index) => {
          var _a, _b;
          return (_b = (_a = nodeData.value) == null ? void 0 : _a.main_input) == null ? void 0 : _b.columns[index];
        }).filter((col) => col !== void 0);
      } else {
        if (firstSelectedIndex.value === clickedIndex) {
          selectedColumns.value = [];
        } else {
          firstSelectedIndex.value = clickedIndex;
          selectedColumns.value = [columnName];
        }
      }
    };
    const singleColumnAggOptions = [
      { value: "count", label: "Count" },
      { value: "max", label: "Max" },
      { value: "median", label: "Median" },
      { value: "min", label: "Min" },
      { value: "sum", label: "Sum" },
      { value: "n_unique", label: "N_unique" },
      { value: "first", label: "First" },
      { value: "last", label: "Last" },
      { value: "concat", label: "Concat" }
    ];
    const getRange = (start, end) => {
      return start < end ? [...Array(end - start + 1).keys()].map((i) => i + start) : [...Array(start - end + 1).keys()].map((i) => i + end);
    };
    const loadData = async (nodeId) => {
      var _a;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeGroupBy.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeData.value) {
        if (nodeGroupBy.value) {
          if (nodeGroupBy.value.groupby_input) {
            groupByInput.value = nodeGroupBy.value.groupby_input;
          } else {
            nodeGroupBy.value.groupby_input = groupByInput.value;
          }
        }
      }
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
        return getMissingColumns(
          (_b = nodeData.value.main_input) == null ? void 0 : _b.columns,
          groupByInput.value.agg_cols.map((col) => col.old_name)
        );
      }
      return [];
    });
    const calculateMissingColumns = () => {
      var _a, _b;
      if (nodeData.value && ((_a = nodeData.value.main_input) == null ? void 0 : _a.columns)) {
        return getMissingColumns(
          (_b = nodeData.value.main_input) == null ? void 0 : _b.columns,
          groupByInput.value.agg_cols.map((col) => col.old_name)
        );
      }
      return [];
    };
    const validateNode = async () => {
      var _a, _b;
      if ((_a = nodeGroupBy.value) == null ? void 0 : _a.groupby_input) {
        await loadData(Number(nodeGroupBy.value.node_id));
      }
      const missingColumnsLocal = calculateMissingColumns();
      if (missingColumnsLocal.length > 0 && nodeGroupBy.value) {
        nodeStore.setNodeValidation(nodeGroupBy.value.node_id, {
          isValid: false,
          error: `The fields ${missingColumns.value.join(", ")} are missing in the available columns.`
        });
      } else if (((_b = nodeGroupBy.value) == null ? void 0 : _b.groupby_input.agg_cols.length) == 0) {
        nodeStore.setNodeValidation(nodeGroupBy.value.node_id, {
          isValid: false,
          error: "Please select at least one field."
        });
      } else if (nodeGroupBy.value) {
        nodeStore.setNodeValidation(nodeGroupBy.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    const instantValidate = async () => {
      var _a;
      if (missingColumns.value.length > 0 && nodeGroupBy.value) {
        nodeStore.setNodeValidation(nodeGroupBy.value.node_id, {
          isValid: false,
          error: `The fields ${missingColumns.value.join(", ")} are missing in the available columns.`
        });
      } else if (((_a = nodeGroupBy.value) == null ? void 0 : _a.groupby_input.agg_cols.length) == 0) {
        nodeStore.setNodeValidation(nodeGroupBy.value.node_id, {
          isValid: false,
          error: "Please select at least one field."
        });
      } else if (nodeGroupBy.value) {
        nodeStore.setNodeValidation(nodeGroupBy.value.node_id, {
          isValid: true,
          error: ""
        });
      }
    };
    const pushNodeData = async () => {
      var _a, _b, _c;
      dataLoaded.value = false;
      if ((_a = nodeGroupBy.value) == null ? void 0 : _a.is_setup) {
        nodeGroupBy.value.is_setup = true;
      }
      nodeStore.updateSettings(nodeGroupBy);
      await instantValidate();
      if ((_b = nodeGroupBy.value) == null ? void 0 : _b.groupby_input) {
        nodeStore.setNodeValidateFunc((_c = nodeGroupBy.value) == null ? void 0 : _c.node_id, validateNode);
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
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_input = resolveComponent("el-input");
      return dataLoaded.value && nodeGroupBy.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeGroupBy.value,
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeGroupBy.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b;
            return [
              createBaseVNode("div", _hoisted_2, [
                dataLoaded.value ? (openBlock(), createElementBlock("ul", _hoisted_3, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList((_b = (_a = nodeData.value) == null ? void 0 : _a.main_input) == null ? void 0 : _b.table_schema, (col_schema, index) => {
                    return openBlock(), createElementBlock("li", {
                      key: col_schema.name,
                      class: normalizeClass({ "is-selected": selectedColumns.value.includes(col_schema.name) }),
                      onClick: ($event) => handleItemClick(index, col_schema.name, $event),
                      onContextmenu: ($event) => openContextMenu(index, col_schema.name, $event)
                    }, toDisplayString(col_schema.name) + " (" + toDisplayString(col_schema.data_type) + ") ", 43, _hoisted_4);
                  }), 128))
                ])) : createCommentVNode("", true)
              ]),
              showContextMenu.value ? (openBlock(), createElementBlock("div", {
                key: 0,
                ref_key: "contextMenuRef",
                ref: contextMenuRef,
                class: "context-menu",
                style: normalizeStyle({
                  top: contextMenuPosition.value.y + "px",
                  left: contextMenuPosition.value.x + "px"
                })
              }, [
                createBaseVNode("button", {
                  onClick: _cache[0] || (_cache[0] = ($event) => setAggregations("groupby", selectedColumns.value))
                }, "Group by"),
                (openBlock(), createElementBlock(Fragment, null, renderList(singleColumnAggOptions, (option) => {
                  return openBlock(), createElementBlock(Fragment, {
                    key: option.value
                  }, [
                    singleColumnSelected.value ? (openBlock(), createElementBlock("button", {
                      key: 0,
                      onClick: ($event) => setAggregations(option.value, selectedColumns.value)
                    }, toDisplayString(option.label), 9, _hoisted_5)) : createCommentVNode("", true)
                  ], 64);
                }), 64))
              ], 4)) : createCommentVNode("", true),
              _cache[3] || (_cache[3] = createBaseVNode("div", { class: "listbox-subtitle" }, "Settings", -1)),
              dataLoaded.value ? (openBlock(), createElementBlock("div", _hoisted_6, [
                createBaseVNode("table", _hoisted_7, [
                  _cache[2] || (_cache[2] = createBaseVNode("thead", null, [
                    createBaseVNode("tr", null, [
                      createBaseVNode("th", null, "Field"),
                      createBaseVNode("th", null, "Action"),
                      createBaseVNode("th", null, "Output Field Name")
                    ])
                  ], -1)),
                  createBaseVNode("tbody", null, [
                    (openBlock(true), createElementBlock(Fragment, null, renderList(groupByInput.value.agg_cols, (item, index) => {
                      return openBlock(), createElementBlock("tr", {
                        key: index,
                        onContextmenu: withModifiers(($event) => openRowContextMenu($event, index), ["prevent"])
                      }, [
                        createBaseVNode("td", null, toDisplayString(item.old_name), 1),
                        createBaseVNode("td", null, [
                          createVNode(_component_el_select, {
                            modelValue: item.agg,
                            "onUpdate:modelValue": ($event) => item.agg = $event,
                            size: "small"
                          }, {
                            default: withCtx(() => [
                              (openBlock(), createElementBlock(Fragment, null, renderList(aggOptions, (aggOption) => {
                                return createVNode(_component_el_option, {
                                  key: aggOption,
                                  label: aggOption,
                                  value: aggOption
                                }, null, 8, ["label", "value"]);
                              }), 64))
                            ]),
                            _: 2
                          }, 1032, ["modelValue", "onUpdate:modelValue"])
                        ]),
                        createBaseVNode("td", null, [
                          createVNode(_component_el_input, {
                            modelValue: item.new_name,
                            "onUpdate:modelValue": ($event) => item.new_name = $event,
                            class: "w-50 m-2",
                            size: "small"
                          }, null, 8, ["modelValue", "onUpdate:modelValue"])
                        ])
                      ], 40, _hoisted_8);
                    }), 128))
                  ])
                ])
              ])) : createCommentVNode("", true),
              showContextMenuRemove.value ? (openBlock(), createElementBlock("div", {
                key: 2,
                class: "context-menu",
                style: normalizeStyle({
                  top: contextMenuPosition.value.y + "px",
                  left: contextMenuPosition.value.x + "px"
                })
              }, [
                createBaseVNode("button", { onClick: removeRow }, "Remove")
              ], 4)) : createCommentVNode("", true)
            ];
          }),
          _: 1,
          __: [3]
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const GroupBy_vue_vue_type_style_index_0_scoped_734437d8_lang = "";
const GroupBy = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-734437d8"]]);
export {
  GroupBy as default
};
