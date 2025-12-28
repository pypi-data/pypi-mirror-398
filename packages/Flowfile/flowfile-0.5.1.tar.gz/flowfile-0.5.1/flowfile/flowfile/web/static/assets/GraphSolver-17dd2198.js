import { d as defineComponent, r as ref, l as computed, n as onMounted, R as nextTick, o as onUnmounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, F as Fragment, q as renderList, s as normalizeClass, v as withModifiers, t as toDisplayString, h as createBlock, i as createCommentVNode, _ as _export_sfc } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import ContextMenu from "./ContextMenu-70ae0c79.js";
import SettingsSection from "./SettingsSection-7ded385d.js";
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
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "GraphSolver",
  props: { nodeId: { type: Number, required: true } },
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
    const graphSolverInput = ref({
      col_from: "",
      col_to: "",
      output_column_name: "group_column"
    });
    const nodeGraphSolver = ref(null);
    const singleColumnSelected = computed(() => selectedColumns.value.length === 1);
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
        if (section === "from" && graphSolverInput.value.col_from !== draggedColumnName.value) {
          graphSolverInput.value.col_from = draggedColumnName.value;
        } else if (section === "to") {
          graphSolverInput.value.col_to = draggedColumnName.value;
        }
        draggedColumnName.value = null;
      }
    };
    const openContextMenu = (columnName, event) => {
      selectedColumns.value = [columnName];
      contextMenuPosition.value = { x: event.clientX, y: event.clientY };
      contextMenuOptions.value = [
        {
          label: "Assign as From",
          action: "from",
          disabled: isColumnAssigned(columnName) || !singleColumnSelected.value
        },
        {
          label: "Assign as To",
          action: "to",
          disabled: isColumnAssigned(columnName) || !singleColumnSelected.value
        }
      ];
      showContextMenu.value = true;
    };
    const handleContextMenuSelect = (action) => {
      const column = selectedColumns.value[0];
      if (action === "from" && graphSolverInput.value.col_from !== column) {
        removeColumnIfExists(column);
        graphSolverInput.value.col_from = column;
      } else if (action === "to") {
        removeColumnIfExists(column);
        graphSolverInput.value.col_to = column;
      }
      closeContextMenu();
    };
    const isColumnAssigned = (columnName) => {
      return graphSolverInput.value.col_from === columnName || graphSolverInput.value.col_to === columnName;
    };
    const removeColumnIfExists = (columnName) => {
      if (graphSolverInput.value.col_from === columnName) {
        graphSolverInput.value.col_from = "";
      } else if (graphSolverInput.value.col_to === columnName) {
        graphSolverInput.value.col_to = "";
      }
    };
    const removeColumn = (type, _) => {
      if (type === "from") {
        graphSolverInput.value.col_from = "";
      } else if (type === "to") {
        graphSolverInput.value.col_to = "";
      }
    };
    const handleItemClick = (columnName) => {
      selectedColumns.value = [columnName];
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      console.log("loadNodeData from groupby");
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeGraphSolver.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeData.value) {
        if (nodeGraphSolver.value) {
          if (nodeGraphSolver.value.graph_solver_input) {
            graphSolverInput.value = nodeGraphSolver.value.graph_solver_input;
          } else {
            nodeGraphSolver.value.graph_solver_input = graphSolverInput.value;
          }
        }
      }
      dataLoaded.value = true;
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
      if (nodeGraphSolver.value) {
        nodeStore.updateSettings(nodeGraphSolver);
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
      const _component_el_input = resolveComponent("el-input");
      return dataLoaded.value && nodeGraphSolver.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeGraphSolver.value,
          "onUpdate:modelValue": _cache[8] || (_cache[8] = ($event) => nodeGraphSolver.value = $event)
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
                  title: "From Column",
                  item: graphSolverInput.value.col_from ?? "",
                  droppable: "true",
                  onRemoveItem: _cache[1] || (_cache[1] = ($event) => removeColumn("from", $event)),
                  onDragover: _cache[2] || (_cache[2] = withModifiers(() => {
                  }, ["prevent"])),
                  onDrop: _cache[3] || (_cache[3] = ($event) => onDropInSection("from"))
                }, null, 8, ["item"]),
                createVNode(SettingsSection, {
                  title: "To Column",
                  item: graphSolverInput.value.col_to ?? "",
                  droppable: "true",
                  onRemoveItem: _cache[4] || (_cache[4] = ($event) => removeColumn("to", $event)),
                  onDragover: _cache[5] || (_cache[5] = withModifiers(() => {
                  }, ["prevent"])),
                  onDrop: _cache[6] || (_cache[6] = ($event) => onDropInSection("to"))
                }, null, 8, ["item"]),
                createBaseVNode("div", _hoisted_6, [
                  _cache[9] || (_cache[9] = createBaseVNode("div", { class: "listbox-subtitle" }, "Select Output column name", -1)),
                  createVNode(_component_el_input, {
                    modelValue: graphSolverInput.value.output_column_name,
                    "onUpdate:modelValue": _cache[7] || (_cache[7] = ($event) => graphSolverInput.value.output_column_name = $event),
                    style: { "width": "240px" },
                    placeholder: "Please input"
                  }, null, 8, ["modelValue"])
                ])
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
const GraphSolver_vue_vue_type_style_index_0_scoped_b4673e65_lang = "";
const GraphSolver = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-b4673e65"]]);
export {
  GraphSolver as default
};
