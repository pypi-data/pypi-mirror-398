import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { v as keymap, w as acceptCompletion, x as indentMore, q as EditorState, r as autocompletion, o as T, u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { p as python, o as oneDark } from "./designer-9633482a.js";
import { d as defineComponent, r as ref, X as shallowRef, m as watch, c as openBlock, e as createElementBlock, f as createVNode, u as unref, t as toDisplayString, i as createCommentVNode, w as withCtx, h as createBlock } from "./index-5429bbf8.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
const polarsCompletionVals = [
  // Polars basics
  { label: "pl", type: "variable", info: "Polars main module" },
  { label: "col", type: "function", info: "Column selector" },
  { label: "lit", type: "function", info: "Literal value" },
  { label: "expr", type: "function", info: "Expression builder" },
  // Common Polars operations
  { label: "select", type: "method", info: "Select columns" },
  { label: "filter", type: "method", info: "Filter rows" },
  { label: "group_by", type: "method", info: "Group by columns" },
  { label: "agg", type: "method", info: "Aggregate operations" },
  { label: "sort", type: "method", info: "Sort DataFrame" },
  { label: "with_columns", type: "method", info: "Add/modify columns" },
  { label: "join", type: "method", info: "Join operations" },
  // Aggregation functions
  { label: "sum", type: "method", info: "Sum values" },
  { label: "mean", type: "method", info: "Calculate mean" },
  { label: "min", type: "method", info: "Find minimum" },
  { label: "max", type: "method", info: "Find maximum" },
  { label: "count", type: "method", info: "Count records" },
  // Common variables
  { label: "input_df", type: "variable", info: "Input DataFrame" },
  { label: "output_df", type: "variable", info: "Output DataFrame" },
  // Basic Python
  { label: "print", type: "function" },
  { label: "len", type: "function" },
  { label: "range", type: "function" },
  { label: "list", type: "type" },
  { label: "dict", type: "type" },
  { label: "set", type: "type" },
  { label: "str", type: "type" },
  { label: "int", type: "type" },
  { label: "float", type: "type" },
  { label: "bool", type: "type" }
];
const _hoisted_1$1 = { class: "polars-editor-root" };
const _hoisted_2 = {
  key: 0,
  class: "validation-error"
};
const _sfc_main$1 = /* @__PURE__ */ defineComponent({
  __name: "pythonEditor",
  props: {
    editorString: { type: String, required: true }
  },
  emits: ["update-editor-string", "validation-error"],
  setup(__props, { expose: __expose, emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const validationError = ref(null);
    const polarsCompletions = (context) => {
      let word = context.matchBefore(/\w*/);
      if ((word == null ? void 0 : word.from) == (word == null ? void 0 : word.to) && !context.explicit) {
        return null;
      }
      return {
        from: word == null ? void 0 : word.from,
        options: polarsCompletionVals
      };
    };
    const tabKeymap = keymap.of([
      {
        key: "Tab",
        run: (view2) => {
          if (acceptCompletion(view2)) {
            return true;
          }
          return indentMore(view2);
        }
      }
    ]);
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
    const extensions = [
      python(),
      oneDark,
      EditorState.tabSize.of(4),
      autocompletion({
        override: [polarsCompletions],
        defaultKeymap: false,
        // Disable default keymap
        closeOnBlur: false
      }),
      tabKeymap
    ];
    const handleReady = (payload) => {
      view.value = payload.view;
    };
    const log = (type, event) => {
      console.log(type, event);
    };
    const handleBlur = async (_) => {
      try {
        validationError.value = null;
        emit("validation-error", null);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        validationError.value = errorMessage;
        emit("validation-error", errorMessage);
      }
    };
    watch(code, (newCode) => {
      emit("update-editor-string", newCode);
    });
    __expose({ insertTextAtCursor });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1$1, [
        createVNode(unref(T), {
          modelValue: code.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => code.value = $event),
          placeholder: "Enter Polars code here...",
          style: { height: "500px" },
          autofocus: true,
          "indent-with-tab": false,
          "tab-size": 4,
          extensions,
          onReady: handleReady,
          onFocus: _cache[1] || (_cache[1] = ($event) => log("focus", $event)),
          onBlur: handleBlur
        }, null, 8, ["modelValue"]),
        validationError.value ? (openBlock(), createElementBlock("div", _hoisted_2, toDisplayString(validationError.value), 1)) : createCommentVNode("", true)
      ]);
    };
  }
});
const pythonEditor_vue_vue_type_style_index_0_lang = "";
const createPolarsCodeNode = (flowId, nodeId) => {
  const polarsCodeInput = {
    polars_code: `# Example of usage (you can remove this)
# Single line transformations:
#   input_df.filter(pl.col('column_name') > 0)

# Multi-line transformations (must assign to output_df):
#   result = input_df.select(['a', 'b'])
#   filtered = result.filter(pl.col('a') > 0)
#   output_df = filtered.with_columns(pl.col('b').alias('new_b'))

# Multiple input dataframes are available as input_df_0, input_df_1, etc:
#   output_df = input_df_0.join(input_df_1, on='id')

# No inputs example (node will act as a starter node):
#   output_df = pl.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})

# Your code here:
input_df`
  };
  const nodePolarsCode = {
    flow_id: flowId,
    node_id: nodeId,
    pos_x: 0,
    pos_y: 0,
    polars_code_input: polarsCodeInput,
    cache_results: false
  };
  return nodePolarsCode;
};
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "PolarsCode",
  setup(__props, { expose: __expose }) {
    const showEditor = ref(false);
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const editorChild = ref(null);
    const nodePolarsCode = ref(null);
    const nodeData = ref(null);
    const handleEditorUpdate = (newCode) => {
      if (nodePolarsCode.value && nodePolarsCode.value.polars_code_input) {
        nodePolarsCode.value.polars_code_input.polars_code = newCode;
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c, _d;
      try {
        nodeData.value = await nodeStore.getNodeData(nodeId, false);
        if (nodeData.value) {
          const hasValidSetup = Boolean(
            ((_b = (_a = nodeData.value) == null ? void 0 : _a.setting_input) == null ? void 0 : _b.is_setup) && ((_d = (_c = nodeData.value) == null ? void 0 : _c.setting_input) == null ? void 0 : _d.polars_code_input)
          );
          nodePolarsCode.value = hasValidSetup ? nodeData.value.setting_input : createPolarsCodeNode(nodeStore.flow_id, nodeStore.node_id);
          showEditor.value = true;
          dataLoaded.value = true;
        }
      } catch (error) {
        console.error("Failed to load node data:", error);
        showEditor.value = false;
        dataLoaded.value = false;
      }
    };
    const pushNodeData = async () => {
      if (!nodePolarsCode.value || !nodePolarsCode.value.polars_code_input.polars_code) {
        return;
      }
      nodePolarsCode.value.is_setup = true;
      nodeStore.updateSettings(nodePolarsCode);
      showEditor.value = false;
      dataLoaded.value = false;
    };
    __expose({ loadNodeData, pushNodeData });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodePolarsCode.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, { "model-value": nodePolarsCode.value }, {
          default: withCtx(() => [
            showEditor.value && nodePolarsCode.value ? (openBlock(), createBlock(_sfc_main$1, {
              key: 0,
              ref_key: "editorChild",
              ref: editorChild,
              "editor-string": nodePolarsCode.value.polars_code_input.polars_code,
              onUpdateEditorString: handleEditorUpdate
            }, null, 8, ["editor-string"])) : createCommentVNode("", true)
          ]),
          _: 1
        }, 8, ["model-value"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
export {
  _sfc_main as default
};
