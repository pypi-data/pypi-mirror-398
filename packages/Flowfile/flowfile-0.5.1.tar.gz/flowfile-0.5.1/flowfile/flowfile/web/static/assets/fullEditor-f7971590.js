var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => {
  __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
  return value;
};
import { u as useNodeStore, P as PopOver, V as ViewPlugin, p as Decoration, q as EditorState, r as autocompletion, R as RangeSetBuilder, o as T } from "./vue-codemirror.esm-41b0e0d7.js";
import { d as defineComponent, r as ref, m as watch, n as onMounted, c as openBlock, e as createElementBlock, q as renderList, p as createBaseVNode, t as toDisplayString, F as Fragment, _ as _export_sfc, s as normalizeClass, f as createVNode, w as withCtx, X as shallowRef, u as unref, a as axios, R as nextTick, i as createCommentVNode, l as computed, aq as debounce, T as normalizeStyle, h as createBlock } from "./index-5429bbf8.js";
const _hoisted_1$5 = { class: "cool-button-container" };
const _hoisted_2$4 = ["onClick"];
const _sfc_main$5 = /* @__PURE__ */ defineComponent({
  __name: "columnsSelector",
  emits: ["value-selected"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const emit = __emit;
    const ranVal = ref(0);
    const showOptions = ref(false);
    const nodeStore = useNodeStore();
    const menuContents = ref({
      title: "Existing fields",
      icon: "room",
      children: []
    });
    watch(
      () => {
        var _a, _b;
        return (_b = (_a = nodeStore.nodeData) == null ? void 0 : _a.main_input) == null ? void 0 : _b.table_schema;
      },
      (newColumns) => {
        if (newColumns) {
          updateColumnData(newColumns);
        }
      },
      { deep: true }
    );
    const handleButtonClick = (columnSelector) => {
      const val = columnSelector.node_type === "c" ? `[${columnSelector.label}]` : columnSelector.label;
      ranVal.value++;
      emit("value-selected", val);
    };
    const updateColumnData = (columns) => {
      const childrenNodes = columns.map((col) => ({
        label: col.name,
        hasAction: true,
        node_type: "c",
        name: col.name + "(" + col.data_type + ")"
      }));
      if (menuContents.value) {
        menuContents.value.children = childrenNodes;
      }
    };
    onMounted(async () => {
      var _a, _b;
      if ((_b = (_a = nodeStore.nodeData) == null ? void 0 : _a.main_input) == null ? void 0 : _b.columns) {
        updateColumnData(nodeStore.nodeData.main_input.table_schema);
      }
    });
    __expose({ showOptions });
    return (_ctx, _cache) => {
      return openBlock(true), createElementBlock(Fragment, null, renderList(menuContents.value.children, (child, index) => {
        return openBlock(), createElementBlock("div", { key: index }, [
          createBaseVNode("div", _hoisted_1$5, [
            createBaseVNode("button", {
              class: "cool-button",
              onClick: ($event) => handleButtonClick(child)
            }, toDisplayString(child.name), 9, _hoisted_2$4)
          ])
        ]);
      }), 128);
    };
  }
});
const columnsSelector_vue_vue_type_style_index_0_scoped_93995232_lang = "";
const ColumnSelector = /* @__PURE__ */ _export_sfc(_sfc_main$5, [["__scopeId", "data-v-93995232"]]);
const _hoisted_1$4 = { class: "radio-menu" };
const _hoisted_2$3 = ["onClick"];
const _sfc_main$4 = /* @__PURE__ */ defineComponent({
  __name: "Sidebar",
  props: {
    options: {
      type: Array,
      required: true
    },
    modelValue: {
      type: String,
      default: ""
    },
    defaultIcon: {
      type: String,
      default: "fas fa-circle"
      // Default Font Awesome icon
    }
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emits = __emit;
    const selectedOption = ref(props.modelValue);
    const onToggle = (value) => {
      emits("update:modelValue", value);
    };
    watch(
      () => props.modelValue,
      (newValue) => {
        selectedOption.value = newValue;
      }
    );
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$4, [
        (openBlock(true), createElementBlock(Fragment, null, renderList(__props.options, (option, index) => {
          return openBlock(), createElementBlock("label", {
            key: index,
            class: normalizeClass(["radio-option", { selected: selectedOption.value === option.value }]),
            onClick: ($event) => onToggle(option.value)
          }, [
            createVNode(PopOver, {
              content: option.text
            }, {
              default: withCtx(() => [
                createBaseVNode("i", {
                  class: normalizeClass([option.icon || __props.defaultIcon, "icon"])
                }, null, 2)
              ]),
              _: 2
            }, 1032, ["content"])
          ], 10, _hoisted_2$3);
        }), 128))
      ]);
    };
  }
});
const Sidebar_vue_vue_type_style_index_0_scoped_a8e433fb_lang = "";
const Sidebar = /* @__PURE__ */ _export_sfc(_sfc_main$4, [["__scopeId", "data-v-a8e433fb"]]);
const _hoisted_1$3 = { class: "function-editor-root" };
const _sfc_main$3 = /* @__PURE__ */ defineComponent({
  __name: "FunctionEditor",
  props: {
    editorString: {},
    columns: { default: () => [] }
  },
  emits: ["update-editor-string"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const expressionsList = ref([]);
    const expressionDocs = ref({});
    const fetchExpressions = async () => {
      try {
        const response = await axios.get("editor/expressions");
        expressionsList.value = response.data;
      } catch (error) {
        console.error("Failed to fetch expressions:", error);
      }
    };
    const fetchExpressionDocs = async () => {
      try {
        const response = await axios.get("editor/expression_doc");
        const docsMap = {};
        response.data.forEach((category) => {
          category.expressions.forEach((expr) => {
            docsMap[expr.name] = expr.doc;
          });
        });
        expressionDocs.value = docsMap;
      } catch (error) {
        console.error("Failed to fetch expression docs:", error);
      }
    };
    onMounted(() => {
      fetchExpressions();
      fetchExpressionDocs();
    });
    const polarsCompletions = (context) => {
      let functionWord = context.matchBefore(/\w+/);
      let columnWord = context.matchBefore(/\[\w*/);
      if ((!functionWord || functionWord.from === functionWord.to) && (!columnWord || columnWord.from === columnWord.to) && !context.explicit) {
        return null;
      }
      const options = [];
      if (functionWord && context.state.sliceDoc(functionWord.from - 1, functionWord.from) !== "[") {
        const currentText = functionWord.text.toLowerCase();
        expressionsList.value.filter((funcName) => funcName.toLowerCase().startsWith(currentText)).forEach((funcName) => {
          options.push({
            label: funcName,
            type: "function",
            info: expressionDocs.value[funcName] || `Function: ${funcName}`,
            apply: (editorView) => {
              const insert = funcName + "(";
              editorView.dispatch({
                changes: { from: functionWord.from, to: functionWord.to, insert },
                selection: { anchor: functionWord.from + insert.length }
              });
            }
          });
        });
      }
      if (columnWord) {
        const bracketContent = columnWord.text.slice(1).toLowerCase();
        props.columns.filter((column) => column.toLowerCase().startsWith(bracketContent)).forEach((column) => {
          options.push({
            label: column,
            type: "variable",
            info: `Column: ${column}`,
            apply: (editorView) => {
              editorView.dispatch({
                changes: {
                  from: columnWord.from + 1,
                  to: columnWord.to,
                  insert: column
                },
                selection: { anchor: columnWord.from + 1 + column.length }
              });
            }
          });
        });
      }
      return {
        from: (functionWord == null ? void 0 : functionWord.from) || (columnWord ? columnWord.from + 1 : context.pos),
        options
      };
    };
    const insertTextAtCursor = (text) => {
      if (view.value) {
        view.value.dispatch({
          changes: {
            from: view.value.state.selection.main.head,
            to: view.value.state.selection.main.head,
            insert: text
          }
        });
      }
    };
    const code = ref(props.editorString);
    const view = shallowRef(null);
    const highlightPlugin = ViewPlugin.fromClass(
      class {
        constructor(view2) {
          __publicField(this, "decorations");
          this.decorations = this.buildDecorations(view2);
        }
        update(update) {
          if (update.docChanged || update.viewportChanged) {
            this.decorations = this.buildDecorations(update.view);
          }
        }
        buildDecorations(view2) {
          const builder = new RangeSetBuilder();
          const { doc } = view2.state;
          const regexFunction = /\b([a-zA-Z_]\w*)\(/g;
          const regexColumn = /\[[^\]]+\]/g;
          const regexString = /(["'])(?:(?=(\\?))\2.)*?\1/g;
          const matches = [];
          for (let { from, to } of view2.visibleRanges) {
            const text = doc.sliceString(from, to);
            let match;
            regexFunction.lastIndex = 0;
            while ((match = regexFunction.exec(text)) !== null) {
              const start = from + match.index;
              const end = start + match[1].length;
              matches.push({ start, end, type: "function" });
            }
            regexColumn.lastIndex = 0;
            while ((match = regexColumn.exec(text)) !== null) {
              const start = from + match.index;
              const end = start + match[0].length;
              matches.push({ start, end, type: "column" });
            }
            regexString.lastIndex = 0;
            while ((match = regexString.exec(text)) !== null) {
              const start = from + match.index;
              const end = start + match[0].length;
              matches.push({ start, end, type: "string" });
            }
          }
          matches.sort((a, b) => a.start - b.start);
          for (const match of matches) {
            if (match.type === "function") {
              builder.add(match.start, match.end, Decoration.mark({ class: "cm-function" }));
            } else if (match.type === "column") {
              builder.add(match.start, match.end, Decoration.mark({ class: "cm-column" }));
            } else if (match.type === "string") {
              builder.add(match.start, match.end, Decoration.mark({ class: "cm-string" }));
            }
          }
          return builder.finish();
        }
      },
      {
        decorations: (v) => v.decorations
      }
    );
    const extensions = [
      EditorState.tabSize.of(2),
      autocompletion({
        override: [polarsCompletions],
        defaultKeymap: true,
        activateOnTyping: true,
        icons: false
      }),
      highlightPlugin
    ];
    const handleReady = (payload) => {
      view.value = payload.view;
    };
    watch(code, (newCode) => {
      emit("update-editor-string", newCode);
    });
    __expose({ insertTextAtCursor });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$3, [
        createVNode(unref(T), {
          modelValue: code.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => code.value = $event),
          placeholder: "Code goes here...",
          style: { height: "250px" },
          autofocus: true,
          "indent-with-tab": true,
          "tab-size": 2,
          extensions,
          onReady: handleReady
        }, null, 8, ["modelValue"])
      ]);
    };
  }
});
const FunctionEditor_vue_vue_type_style_index_0_lang = "";
const _hoisted_1$2 = { class: "container" };
const _hoisted_2$2 = {
  key: 0,
  class: "result-content loading"
};
const _hoisted_3$2 = {
  key: 1,
  class: "result-content loading"
};
const _hoisted_4$1 = {
  key: 2,
  class: "result-content success"
};
const _hoisted_5$1 = { class: "content" };
const _hoisted_6 = {
  key: 3,
  class: "result-content error"
};
const _hoisted_7 = { class: "content" };
const _sfc_main$2 = /* @__PURE__ */ defineComponent({
  __name: "instantFuncResults",
  props: {
    nodeId: { type: Number, required: true }
  },
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const hasInput = ref(false);
    const props = __props;
    const instantFuncResult = ref({
      result: "",
      success: false
    });
    const getInstantFuncResults = async (funcString, flowId) => {
      if (funcString !== "") {
        hasInput.value = true;
        const response = await axios.get("/custom_functions/instant_result", {
          params: {
            node_id: props.nodeId,
            flow_id: flowId,
            func_string: funcString
          }
        });
        instantFuncResult.value = response.data;
        console.log(instantFuncResult.value.result);
      } else {
        hasInput.value = false;
      }
    };
    onMounted(() => {
      if (nodeStore.inputCode !== "") {
        hasInput.value = true;
        getInstantFuncResults(nodeStore.inputCode, nodeStore.flow_id);
      }
    });
    __expose({ getInstantFuncResults });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$2, [
        !hasInput.value ? (openBlock(), createElementBlock("div", _hoisted_2$2, _cache[0] || (_cache[0] = [
          createBaseVNode("div", { class: "label" }, "Waiting for input", -1),
          createBaseVNode("div", { class: "content" }, null, -1)
        ]))) : instantFuncResult.value.success === null ? (openBlock(), createElementBlock("div", _hoisted_3$2, _cache[1] || (_cache[1] = [
          createBaseVNode("div", { class: "label" }, "Processing", -1),
          createBaseVNode("div", { class: "content" }, "Function valid, run process to see results", -1)
        ]))) : instantFuncResult.value.success ? (openBlock(), createElementBlock("div", _hoisted_4$1, [
          _cache[2] || (_cache[2] = createBaseVNode("div", { class: "label" }, "Example result", -1)),
          createBaseVNode("div", _hoisted_5$1, toDisplayString(instantFuncResult.value.result), 1)
        ])) : (openBlock(), createElementBlock("div", _hoisted_6, [
          _cache[3] || (_cache[3] = createBaseVNode("div", { class: "label" }, "Validation error", -1)),
          createBaseVNode("div", _hoisted_7, toDisplayString(instantFuncResult.value.result), 1)
        ]))
      ]);
    };
  }
});
const instantFuncResults_vue_vue_type_style_index_0_scoped_66ed8b64_lang = "";
const InstantFuncResults = /* @__PURE__ */ _export_sfc(_sfc_main$2, [["__scopeId", "data-v-66ed8b64"]]);
const _hoisted_1$1 = ["onClick"];
const _hoisted_2$1 = {
  key: 0,
  class: "toggle-icon"
};
const _hoisted_3$1 = {
  key: 0,
  class: "tree-subview"
};
const _hoisted_4 = { class: "cool-button-container" };
const _hoisted_5 = ["onClick"];
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "FuncSelector",
  emits: ["value-selected"],
  setup(__props, { emit: __emit }) {
    const nodeStore = useNodeStore();
    const formatDoc = (doc) => {
      if (!doc)
        return "";
      return doc.replace(/\n/g, "<br>");
    };
    const emit = __emit;
    const handleButtonClick = (funcName) => {
      emit("value-selected", funcName);
    };
    const openNodes = ref(/* @__PURE__ */ new Set());
    const toggle = (expressionGroup) => {
      const key = expressionGroup.expression_type;
      if (openNodes.value.has(key)) {
        openNodes.value.delete(key);
      } else {
        openNodes.value.add(key);
      }
    };
    const isOpen = (expressionGroup) => {
      const key = expressionGroup.expression_type;
      return openNodes.value.has(key);
    };
    onMounted(async () => {
      await nextTick();
      apiData.value = await nodeStore.getExpressionsOverview();
    });
    const apiData = ref([
      {
        expression_type: "date_functions",
        expressions: [
          {
            name: "add_days",
            doc: "\n    Add a specified number of days to a date or timestamp.\n\n    Parameters:\n    - s (Any): The date or timestamp to add days to. Can be a Flowfile expression or any other value.\n    - days (int): The number of days to add.\n\n    Returns:\n    - pl.Expr: A Flowfile expression representing the result of adding `days` to `s`.\n\n    Note: If `s` is not a Flowfile expression, it will be converted into one.\n    "
          },
          {
            name: "add_hours",
            doc: "\n    Add a specified number of hours to a timestamp.\n\n    Parameters:\n    - s (Any): The timestamp to add hours to. Can be a Flowfile expression or any other value.\n    - hours (int): The number of hours to add.\n\n    Returns:\n    - pl.Expr: A Flowfile expression representing the result of adding `hours` to `s`.\n\n    Note: If `s` is not a Flowfile expression, it will be converted into one.\n    "
          }
          // Add more expressions as needed
        ]
      }
      // Add more expression groups as needed
    ]);
    return (_ctx, _cache) => {
      return openBlock(true), createElementBlock(Fragment, null, renderList(apiData.value, (expressionGroup) => {
        return openBlock(), createElementBlock("div", {
          key: expressionGroup.expression_type,
          class: "tree-node"
        }, [
          createBaseVNode("div", {
            onClick: ($event) => toggle(expressionGroup)
          }, [
            createBaseVNode("span", null, toDisplayString(expressionGroup.expression_type), 1),
            expressionGroup.expressions ? (openBlock(), createElementBlock("span", _hoisted_2$1, toDisplayString(isOpen(expressionGroup) ? "▼" : "▶"), 1)) : createCommentVNode("", true)
          ], 8, _hoisted_1$1),
          expressionGroup.expressions && isOpen(expressionGroup) ? (openBlock(), createElementBlock("ul", _hoisted_3$1, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(expressionGroup.expressions, (expression) => {
              return openBlock(), createElementBlock("li", {
                key: expression.name,
                class: "tree-leaf"
              }, [
                createBaseVNode("div", null, [
                  createVNode(PopOver, {
                    content: formatDoc(expression.doc),
                    title: expression.name
                  }, {
                    default: withCtx(() => [
                      createBaseVNode("div", _hoisted_4, [
                        createBaseVNode("button", {
                          class: "cool-button",
                          onClick: ($event) => handleButtonClick(expression.name)
                        }, toDisplayString(expression.name), 9, _hoisted_5)
                      ])
                    ]),
                    _: 2
                  }, 1032, ["content", "title"])
                ])
              ]);
            }), 128))
          ])) : createCommentVNode("", true)
        ]);
      }), 128);
    };
  }
});
const FuncSelector_vue_vue_type_style_index_0_scoped_967e57c5_lang = "";
const FuncSelector = /* @__PURE__ */ _export_sfc(_sfc_main$1, [["__scopeId", "data-v-967e57c5"]]);
const _hoisted_1 = { class: "container" };
const _hoisted_2 = { class: "selector" };
const _hoisted_3 = {
  ref: "editorWrapper",
  class: "editor-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "fullEditor",
  props: {
    editorString: { type: String, required: true }
  },
  setup(__props, { expose: __expose }) {
    const optionSelection = ref("");
    const nodeStore = useNodeStore();
    const radioOptions = [
      { value: "fields", text: "Fields", icon: "fa fa-columns" },
      { value: "functions", text: "Functions", icon: "fas fa-atom" }
    ];
    const props = __props;
    const startX = ref(0);
    const startWidth = ref(0);
    const treeNodeWidth = ref("200px");
    const instantFuncResultsRef = ref(null);
    const code = ref(props.editorString);
    nodeStore.setInputCode(props.editorString);
    const functionEditor = ref(null);
    const showTools = ref(true);
    const showHideOptions = () => {
      showTools.value = !showTools.value;
    };
    const showSideBar = computed(() => parseInt(treeNodeWidth.value.replace("px", "")) > 50);
    const handleCodeChange = (newCode) => {
      code.value = newCode;
      nodeStore.setInputCode(newCode);
    };
    const resizeWidth = (event) => {
      const deltaX = event.clientX - startX.value;
      const newWidth = startWidth.value + deltaX;
      treeNodeWidth.value = Math.min(newWidth, 300) + "px";
    };
    watch(
      code,
      debounce((newCode) => {
        if (instantFuncResultsRef.value) {
          instantFuncResultsRef.value.getInstantFuncResults(newCode, nodeStore.flow_id);
        }
      }, 1500)
    );
    __expose({ showHideOptions, functionEditor, showTools });
    const handleNodeSelected = (nodeLabel) => {
      var _a;
      (_a = functionEditor.value) == null ? void 0 : _a.insertTextAtCursor(nodeLabel);
    };
    onMounted(async () => {
      await nextTick();
      if (instantFuncResultsRef.value) {
        instantFuncResultsRef.value.getInstantFuncResults(props.editorString, nodeStore.flow_id);
      }
    });
    const initResize = (event) => {
      startX.value = event.clientX;
      startWidth.value = parseInt(treeNodeWidth.value.replace("px", ""));
      document.addEventListener("mousemove", resizeWidth);
      document.addEventListener("mouseup", stopResize);
    };
    const stopResize = () => {
      document.removeEventListener("mousemove", resizeWidth);
      document.removeEventListener("mouseup", stopResize);
    };
    return (_ctx, _cache) => {
      var _a, _b;
      return openBlock(), createElementBlock(Fragment, null, [
        createBaseVNode("div", _hoisted_1, [
          showSideBar.value ? (openBlock(), createElementBlock("div", {
            key: 0,
            class: "options-container",
            style: normalizeStyle({ width: treeNodeWidth.value })
          }, [
            createVNode(Sidebar, {
              modelValue: optionSelection.value,
              "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => optionSelection.value = $event),
              options: radioOptions
            }, null, 8, ["modelValue"]),
            _cache[1] || (_cache[1] = createBaseVNode("div", { class: "divider" }, null, -1)),
            createBaseVNode("div", _hoisted_2, [
              optionSelection.value === "fields" ? (openBlock(), createBlock(ColumnSelector, {
                key: 0,
                onValueSelected: handleNodeSelected
              })) : (openBlock(), createBlock(FuncSelector, {
                key: 1,
                ref: "func-selector",
                onValueSelected: handleNodeSelected
              }, null, 512))
            ])
          ], 4)) : createCommentVNode("", true),
          createBaseVNode("div", {
            class: "resizer",
            onMousedown: initResize
          }, null, 32),
          createBaseVNode("div", _hoisted_3, [
            createVNode(_sfc_main$3, {
              ref_key: "functionEditor",
              ref: functionEditor,
              class: "prism-editor-ref",
              "editor-string": code.value,
              columns: (_b = (_a = unref(nodeStore).nodeData) == null ? void 0 : _a.main_input) == null ? void 0 : _b.columns,
              onUpdateEditorString: handleCodeChange
            }, null, 8, ["editor-string", "columns"])
          ], 512)
        ]),
        createVNode(InstantFuncResults, {
          ref_key: "instantFuncResultsRef",
          ref: instantFuncResultsRef,
          "node-id": unref(nodeStore).node_id
        }, null, 8, ["node-id"])
      ], 64);
    };
  }
});
const fullEditor_vue_vue_type_style_index_0_scoped_9df088eb_lang = "";
const mainEditorRef = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-9df088eb"]]);
export {
  mainEditorRef as default
};
