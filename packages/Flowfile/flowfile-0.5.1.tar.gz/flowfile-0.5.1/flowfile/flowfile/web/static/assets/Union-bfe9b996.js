import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { d as defineComponent, r as ref, n as onMounted, R as nextTick, o as onUnmounted, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, g as createTextVNode, i as createCommentVNode, _ as _export_sfc } from "./index-5429bbf8.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Union",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const dataLoaded = ref(false);
    const nodeData = ref(null);
    const unionInput = ref({ mode: "relaxed" });
    const nodeUnion = ref(null);
    const loadNodeData = async (nodeId) => {
      var _a;
      console.log("loadNodeData from union ");
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeUnion.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (nodeData.value) {
        if (nodeUnion.value) {
          if (nodeUnion.value.union_input) {
            unionInput.value = nodeUnion.value.union_input;
          } else {
            nodeUnion.value.union_input = unionInput.value;
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
    const pushNodeData = async () => {
      if (unionInput.value) {
        nodeStore.updateSettings(nodeUnion);
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
      return dataLoaded.value && nodeUnion.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeUnion.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeUnion.value = $event)
        }, {
          default: withCtx(() => _cache[1] || (_cache[1] = [
            createTextVNode(" 'Union multiple tables into one table, this node does not have settings' ")
          ])),
          _: 1,
          __: [1]
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
const Union_vue_vue_type_style_index_0_scoped_5786442f_lang = "";
const Union = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-5786442f"]]);
export {
  Union as default
};
