import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { d as defineComponent, r as ref, n as onMounted, R as nextTick, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, i as createCommentVNode } from "./index-5429bbf8.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "RecordCount",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeData = ref(null);
    const nodeRecordCount = ref(null);
    const loadNodeData = async (nodeId) => {
      var _a;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeRecordCount.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      dataLoaded.value = true;
    };
    const pushNodeData = async () => {
      if (nodeRecordCount.value) {
        nodeStore.updateSettings(nodeRecordCount);
      }
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    onMounted(async () => {
      await nextTick();
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeRecordCount.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeRecordCount.value,
          "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeRecordCount.value = $event)
        }, {
          default: withCtx(() => _cache[1] || (_cache[1] = [
            createBaseVNode("p", null, " This node helps you quickly retrieve the total number of records from the selected table. It's a simple yet powerful tool to keep track of the data volume as you work through your tasks. ", -1),
            createBaseVNode("p", null, "This node does not need a setup", -1)
          ])),
          _: 1,
          __: [1]
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
export {
  _sfc_main as default
};
