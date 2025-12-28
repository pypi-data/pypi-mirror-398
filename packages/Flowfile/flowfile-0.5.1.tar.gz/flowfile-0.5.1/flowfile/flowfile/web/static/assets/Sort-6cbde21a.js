import { d as defineComponent, r as ref, l as computed, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, F as Fragment, q as renderList, s as normalizeClass, t as toDisplayString, i as createCommentVNode, T as normalizeStyle, v as withModifiers, h as createBlock, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _hoisted_3 = {
  key: 0,
  class: "listbox"
};
const _hoisted_4 = ["onClick", "onContextmenu"];
const _hoisted_5 = { class: "listbox-wrapper" };
const _hoisted_6 = {
  key: 0,
  class: "table-wrapper"
};
const _hoisted_7 = { class: "styled-table" };
const _hoisted_8 = { key: 0 };
const _hoisted_9 = ["onContextmenu"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Sort",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const showContextMenuRemove = ref(false);
    const dataLoaded = ref(false);
    const contextMenuPosition = ref({ x: 0, y: 0 });
    const contextMenuColumn = ref(null);
    const contextMenuRef = ref(null);
    const selectedColumns = ref([]);
    const nodeSort = ref(null);
    const nodeData = ref(null);
    const sortOptions = ["Ascending", "Descending"];
    const firstSelectedIndex = ref(null);
    const openRowContextMenu = (event, index) => {
      event.preventDefault();
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
      contextMenuRowIndex.value = index;
      showContextMenuRemove.value = true;
    };
    const removeRow = () => {
      var _a;
      if (contextMenuRowIndex.value !== null) {
        (_a = nodeSort.value) == null ? void 0 : _a.sort_input.splice(contextMenuRowIndex.value, 1);
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
    const setSortSettings = (sortType, columns) => {
      if (columns) {
        columns.forEach((column) => {
          var _a;
          (_a = nodeSort.value) == null ? void 0 : _a.sort_input.push({ column, how: sortType });
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
    const getRange = (start, end) => {
      return start < end ? [...Array(end - start + 1).keys()].map((i) => i + start) : [...Array(start - end + 1).keys()].map((i) => i + end);
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeSort.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (!((_b = nodeData.value) == null ? void 0 : _b.setting_input.is_setup) && nodeSort.value) {
        nodeSort.value.sort_input = [];
      }
      dataLoaded.value = true;
      if ((_c = nodeSort.value) == null ? void 0 : _c.is_setup) {
        nodeSort.value.is_setup = true;
      }
    };
    const pushNodeData = async () => {
      nodeStore.updateSettings(nodeSort);
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      return dataLoaded.value && nodeSort.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeSort.value,
          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeSort.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b;
            return [
              createBaseVNode("div", _hoisted_2, [
                _cache[4] || (_cache[4] = createBaseVNode("div", { class: "listbox-subtitle" }, "Columns", -1)),
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
                !singleColumnSelected.value ? (openBlock(), createElementBlock("button", {
                  key: 0,
                  onClick: _cache[0] || (_cache[0] = ($event) => setSortSettings("Ascending", selectedColumns.value))
                }, " Ascending ")) : createCommentVNode("", true),
                singleColumnSelected.value ? (openBlock(), createElementBlock("button", {
                  key: 1,
                  onClick: _cache[1] || (_cache[1] = ($event) => setSortSettings("Ascending", selectedColumns.value))
                }, " Ascending ")) : createCommentVNode("", true),
                singleColumnSelected.value ? (openBlock(), createElementBlock("button", {
                  key: 2,
                  onClick: _cache[2] || (_cache[2] = ($event) => setSortSettings("Descending", selectedColumns.value))
                }, " Descending ")) : createCommentVNode("", true)
              ], 4)) : createCommentVNode("", true),
              createBaseVNode("div", _hoisted_5, [
                _cache[6] || (_cache[6] = createBaseVNode("div", { class: "listbox-subtitle" }, "Settings", -1)),
                dataLoaded.value ? (openBlock(), createElementBlock("div", _hoisted_6, [
                  createBaseVNode("table", _hoisted_7, [
                    _cache[5] || (_cache[5] = createBaseVNode("thead", null, [
                      createBaseVNode("tr", null, [
                        createBaseVNode("th", null, "Field"),
                        createBaseVNode("th", null, "Action")
                      ])
                    ], -1)),
                    createBaseVNode("tbody", null, [
                      nodeSort.value ? (openBlock(), createElementBlock("div", _hoisted_8, [
                        (openBlock(true), createElementBlock(Fragment, null, renderList(nodeSort.value.sort_input, (item, index) => {
                          return openBlock(), createElementBlock("tr", {
                            key: index,
                            onContextmenu: withModifiers(($event) => openRowContextMenu($event, index), ["prevent"])
                          }, [
                            createBaseVNode("td", null, toDisplayString(item.column), 1),
                            createBaseVNode("td", null, [
                              createVNode(_component_el_select, {
                                modelValue: item.how,
                                "onUpdate:modelValue": ($event) => item.how = $event,
                                size: "small"
                              }, {
                                default: withCtx(() => [
                                  (openBlock(), createElementBlock(Fragment, null, renderList(sortOptions, (aggOption) => {
                                    return createVNode(_component_el_option, {
                                      key: aggOption,
                                      label: aggOption,
                                      value: aggOption
                                    }, null, 8, ["label", "value"]);
                                  }), 64))
                                ]),
                                _: 2
                              }, 1032, ["modelValue", "onUpdate:modelValue"])
                            ])
                          ], 40, _hoisted_9);
                        }), 128))
                      ])) : createCommentVNode("", true)
                    ])
                  ])
                ])) : createCommentVNode("", true),
                showContextMenuRemove.value ? (openBlock(), createElementBlock("div", {
                  key: 1,
                  class: "context-menu",
                  style: normalizeStyle({
                    top: contextMenuPosition.value.y + "px",
                    left: contextMenuPosition.value.x + "px"
                  })
                }, [
                  createBaseVNode("button", { onClick: removeRow }, "Remove")
                ], 4)) : createCommentVNode("", true)
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Sort_vue_vue_type_style_index_0_scoped_0177dec6_lang = "";
const Sort = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-0177dec6"]]);
export {
  Sort as default
};
