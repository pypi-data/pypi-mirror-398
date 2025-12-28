import { d as defineComponent, r as ref, a3 as watchEffect, l as computed, n as onMounted, o as onUnmounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, p as createBaseVNode, i as createCommentVNode, t as toDisplayString, T as normalizeStyle, g as createTextVNode, F as Fragment, q as renderList, s as normalizeClass, v as withModifiers, w as withCtx, u as unref, h as createBlock, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { u as unavailableField } from "./UnavailableFields-a03f512c.js";
const _hoisted_1 = { key: 0 };
const _hoisted_2 = {
  key: 1,
  class: "listbox-subtitle"
};
const _hoisted_3 = { class: "listbox-wrapper" };
const _hoisted_4 = { class: "table-wrapper" };
const _hoisted_5 = { class: "styled-table" };
const _hoisted_6 = { key: 0 };
const _hoisted_7 = { key: 0 };
const _hoisted_8 = { key: 1 };
const _hoisted_9 = { id: "selectable-container" };
const _hoisted_10 = ["onDragstart", "onDragover", "onDrop"];
const _hoisted_11 = ["onClick", "onContextmenu"];
const _hoisted_12 = {
  key: 0,
  class: "unavailable-field"
};
const _hoisted_13 = { style: { "margin-left": "20px" } };
const _hoisted_14 = { key: 1 };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "selectDynamic",
  props: {
    selectInputs: {
      type: Array,
      default: () => []
    },
    showOldColumns: { type: Boolean, default: true },
    showNewColumns: { type: Boolean, default: true },
    showKeepOption: { type: Boolean, default: false },
    showDataType: { type: Boolean, default: false },
    title: { type: String, default: "Select columns" },
    showOptionKeepUnseen: { type: Boolean, default: false },
    showHeaders: { type: Boolean, default: true },
    showData: { type: Boolean, default: true },
    showTitle: { type: Boolean, default: true },
    draggable: { type: Boolean, default: false },
    showMissing: { type: Boolean, default: true },
    originalColumnHeader: { type: String, default: "Original column name" },
    sortedBy: { type: String, default: "none" }
  },
  emits: ["updateSelectInputs", "update:sortedBy"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const sortState = ref("none");
    const initializeOrder = () => {
      const sortedInputs = [...props.selectInputs].sort(
        (a, b) => a.is_available === b.is_available ? 0 : a.is_available ? -1 : 1
      );
      if (sortState.value === "none") {
        localSelectInputs.value = [...sortedInputs];
      }
    };
    const toggleSort = () => {
      if (props.sortedBy === "none") {
        emit("update:sortedBy", "asc");
        localSelectInputs.value.sort((a, b) => a.old_name.localeCompare(b.old_name));
      } else if (props.sortedBy === "asc") {
        emit("update:sortedBy", "desc");
        localSelectInputs.value.sort((a, b) => b.old_name.localeCompare(a.old_name));
      } else {
        emit("update:sortedBy", "none");
        localSelectInputs.value.sort((a, b) => a.original_position - b.original_position);
      }
      localSelectInputs.value.forEach((input, i) => input.position = i);
    };
    const props = __props;
    const dataLoaded = ref(true);
    const selectedColumns = ref([]);
    const firstSelectedIndex = ref(null);
    const contextMenuPosition = ref({ x: 0, y: 0 });
    const showContextMenu = ref(false);
    const draggingIndex = ref(-1);
    const dragOverIndex = ref(-1);
    const nodeStore = useNodeStore();
    const dataTypes = nodeStore.getDataTypes();
    const localSelectInputs = ref(
      [...props.selectInputs].sort(
        (a, b) => a.is_available === b.is_available ? 0 : a.is_available ? -1 : 1
      )
    );
    watchEffect(() => {
      localSelectInputs.value = [...props.selectInputs].sort(
        (a, b) => a.is_available === b.is_available ? 0 : a.is_available ? -1 : 1
      );
    });
    const standardColumnCount = computed(
      () => [props.showOldColumns, props.showNewColumns, props.showDataType].filter(Boolean).length
    );
    const standardColumnWidth = computed(() => {
      const totalColumns = standardColumnCount.value + 0.5;
      return totalColumns > 0 ? 100 / totalColumns + "%" : "0%";
    });
    const selectColumnWidth = computed(
      () => standardColumnCount.value > 0 ? 50 / (standardColumnCount.value + 0.5) + "%" : "0%"
    );
    const isSelected = (columnName) => selectedColumns.value.includes(columnName);
    const getRange = (start, end) => start < end ? Array.from({ length: end - start + 1 }, (_, i) => i + start) : Array.from({ length: start - end + 1 }, (_, i) => i + end);
    const handleDragStart = (index, event) => {
      var _a;
      draggingIndex.value = index;
      (_a = event.dataTransfer) == null ? void 0 : _a.setData("text", "");
      if (event.dataTransfer)
        event.dataTransfer.effectAllowed = "move";
    };
    const handleDragOver = (index) => {
      dragOverIndex.value = index;
    };
    const handleDrop = (index) => {
      const itemToMove = localSelectInputs.value.splice(draggingIndex.value, 1)[0];
      localSelectInputs.value.splice(index, 0, itemToMove);
      draggingIndex.value = -1;
      dragOverIndex.value = -1;
      localSelectInputs.value.forEach((input, i) => input.position = i);
    };
    const handleItemClick = (clickedIndex, columnName, event) => {
      if (event.shiftKey && firstSelectedIndex.value !== null) {
        const range = getRange(firstSelectedIndex.value, clickedIndex);
        selectedColumns.value = range.map((index) => localSelectInputs.value[index].old_name).filter(Boolean);
      } else {
        firstSelectedIndex.value = clickedIndex;
        selectedColumns.value = [localSelectInputs.value[clickedIndex].old_name];
      }
    };
    const openContextMenu = (clickedIndex, columnName, event) => {
      showContextMenu.value = true;
      event.stopPropagation();
      if (!selectedColumns.value.includes(columnName)) {
        handleItemClick(clickedIndex, columnName, event);
      }
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
    };
    const selectAllSelected = () => {
      localSelectInputs.value.forEach((column) => {
        if (selectedColumns.value.includes(column.old_name)) {
          column.keep = true;
        }
      });
    };
    const deselectAllSelected = () => {
      localSelectInputs.value.forEach((column) => {
        if (selectedColumns.value.includes(column.old_name)) {
          column.keep = false;
        }
      });
    };
    const hasMissingFields = computed(
      () => localSelectInputs.value.some((column) => !column.is_available)
    );
    const handleClickOutside = (event) => {
      const container = document.getElementById("selectable-container");
      if (container && !container.contains(event.target)) {
        selectedColumns.value = [];
        showContextMenu.value = false;
      }
    };
    onMounted(() => {
      window.addEventListener("click", handleClickOutside);
      initializeOrder();
    });
    onUnmounted(() => {
      window.removeEventListener("click", handleClickOutside);
    });
    const emit = __emit;
    const removeMissingFields = () => {
      const availableColumns = localSelectInputs.value.filter((column) => column.is_available);
      localSelectInputs.value = availableColumns;
      emit("updateSelectInputs", availableColumns);
    };
    __expose({ localSelectInputs });
    return (_ctx, _cache) => {
      const _component_el_input = resolveComponent("el-input");
      const _component_el_option = resolveComponent("el-option");
      const _component_el_select = resolveComponent("el-select");
      const _component_el_checkbox = resolveComponent("el-checkbox");
      return openBlock(), createElementBlock("div", null, [
        dataLoaded.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
          hasMissingFields.value ? (openBlock(), createElementBlock("div", {
            key: 0,
            class: "remove-missing-fields",
            onClick: removeMissingFields
          }, [
            createVNode(unavailableField, { "tooltip-text": "Field not available click for removing them for memory" }),
            _cache[0] || (_cache[0] = createBaseVNode("span", null, "Remove Missing Fields", -1))
          ])) : createCommentVNode("", true),
          props.showTitle ? (openBlock(), createElementBlock("div", _hoisted_2, toDisplayString(props.title), 1)) : createCommentVNode("", true),
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("div", _hoisted_4, [
              createBaseVNode("table", _hoisted_5, [
                createBaseVNode("thead", null, [
                  props.showHeaders ? (openBlock(), createElementBlock("tr", _hoisted_6, [
                    props.showOldColumns ? (openBlock(), createElementBlock("th", {
                      key: 0,
                      style: normalizeStyle({ width: standardColumnWidth.value }),
                      onClick: toggleSort
                    }, [
                      createTextVNode(toDisplayString(__props.originalColumnHeader) + " ", 1),
                      props.sortedBy === "asc" ? (openBlock(), createElementBlock("span", _hoisted_7, "▲")) : props.sortedBy === "desc" ? (openBlock(), createElementBlock("span", _hoisted_8, "▼")) : createCommentVNode("", true)
                    ], 4)) : createCommentVNode("", true),
                    props.showNewColumns ? (openBlock(), createElementBlock("th", {
                      key: 1,
                      style: normalizeStyle({ width: standardColumnWidth.value })
                    }, " New column name ", 4)) : createCommentVNode("", true),
                    props.showDataType ? (openBlock(), createElementBlock("th", {
                      key: 2,
                      style: normalizeStyle({ width: standardColumnWidth.value })
                    }, "Data type", 4)) : createCommentVNode("", true),
                    props.showKeepOption ? (openBlock(), createElementBlock("th", {
                      key: 3,
                      style: normalizeStyle({ width: selectColumnWidth.value })
                    }, "Select", 4)) : createCommentVNode("", true)
                  ])) : createCommentVNode("", true)
                ]),
                createBaseVNode("tbody", _hoisted_9, [
                  (openBlock(true), createElementBlock(Fragment, null, renderList(localSelectInputs.value, (column, index) => {
                    return openBlock(), createElementBlock("tr", {
                      key: column.old_name,
                      class: normalizeClass({ "drag-over": dragOverIndex.value === index }),
                      style: normalizeStyle({ opacity: column.is_available ? 1 : 0.6 }),
                      draggable: "true",
                      onDragstart: ($event) => handleDragStart(index, $event),
                      onDragover: withModifiers(($event) => handleDragOver(index), ["prevent"]),
                      onDrop: ($event) => handleDrop(index)
                    }, [
                      props.showOldColumns ? (openBlock(), createElementBlock("td", {
                        key: 0,
                        class: normalizeClass({ "highlight-row": isSelected(column.old_name) }),
                        onClick: ($event) => handleItemClick(index, column.old_name, $event),
                        onContextmenu: withModifiers(($event) => openContextMenu(index, column.old_name, $event), ["prevent"])
                      }, [
                        !column.is_available ? (openBlock(), createElementBlock("div", _hoisted_12, [
                          createVNode(unavailableField),
                          createBaseVNode("span", _hoisted_13, toDisplayString(column.old_name), 1)
                        ])) : (openBlock(), createElementBlock("div", _hoisted_14, toDisplayString(column.old_name), 1))
                      ], 42, _hoisted_11)) : createCommentVNode("", true),
                      props.showNewColumns ? (openBlock(), createElementBlock("td", {
                        key: 1,
                        class: normalizeClass({ "highlight-row": isSelected(column.old_name) })
                      }, [
                        createVNode(_component_el_input, {
                          modelValue: column.new_name,
                          "onUpdate:modelValue": ($event) => column.new_name = $event,
                          size: "small",
                          class: "smaller-el-input"
                        }, null, 8, ["modelValue", "onUpdate:modelValue"])
                      ], 2)) : createCommentVNode("", true),
                      props.showDataType ? (openBlock(), createElementBlock("td", {
                        key: 2,
                        class: normalizeClass({ "highlight-row": isSelected(column.old_name) })
                      }, [
                        createVNode(_component_el_select, {
                          modelValue: column.data_type,
                          "onUpdate:modelValue": ($event) => column.data_type = $event,
                          size: "small"
                        }, {
                          default: withCtx(() => [
                            (openBlock(true), createElementBlock(Fragment, null, renderList(unref(dataTypes), (dataType) => {
                              return openBlock(), createBlock(_component_el_option, {
                                key: dataType,
                                label: dataType,
                                value: dataType
                              }, null, 8, ["label", "value"]);
                            }), 128))
                          ]),
                          _: 2
                        }, 1032, ["modelValue", "onUpdate:modelValue"])
                      ], 2)) : createCommentVNode("", true),
                      props.showKeepOption ? (openBlock(), createElementBlock("td", {
                        key: 3,
                        class: normalizeClass({ "highlight-row": isSelected(column.old_name) })
                      }, [
                        createVNode(_component_el_checkbox, {
                          modelValue: column.keep,
                          "onUpdate:modelValue": ($event) => column.keep = $event
                        }, null, 8, ["modelValue", "onUpdate:modelValue"])
                      ], 2)) : createCommentVNode("", true)
                    ], 46, _hoisted_10);
                  }), 128))
                ])
              ])
            ])
          ])
        ])) : createCommentVNode("", true),
        showContextMenu.value ? (openBlock(), createElementBlock("div", {
          key: 1,
          class: "context-menu",
          style: normalizeStyle({ top: contextMenuPosition.value.y + "px", left: contextMenuPosition.value.x + "px" })
        }, [
          createBaseVNode("button", { onClick: selectAllSelected }, "Select"),
          createBaseVNode("button", { onClick: deselectAllSelected }, "Deselect")
        ], 4)) : createCommentVNode("", true)
      ]);
    };
  }
});
const selectDynamic_vue_vue_type_style_index_0_scoped_c49d6287_lang = "";
const selectDynamic = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-c49d6287"]]);
export {
  selectDynamic as s
};
