import { d as defineComponent, r as ref, n as onMounted, R as nextTick, o as onUnmounted, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, g as createTextVNode, a8 as withDirectives, a9 as vModelText, i as createCommentVNode } from "./index-5429bbf8.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "listbox-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Sample",
  setup(__props, { expose: __expose }) {
    const nodeStore = useNodeStore();
    const showContextMenu = ref(false);
    const showContextMenuRemove = ref(false);
    const dataLoaded = ref(false);
    const contextMenuColumn = ref(null);
    const contextMenuRef = ref(null);
    const nodeSample = ref(null);
    const nodeData = ref(null);
    const sampleSize = ref(1e3);
    const loadNodeData = async (nodeId) => {
      var _a, _b, _c;
      nodeData.value = await nodeStore.getNodeData(nodeId, false);
      nodeSample.value = (_a = nodeData.value) == null ? void 0 : _a.setting_input;
      if (!((_b = nodeData.value) == null ? void 0 : _b.setting_input.is_setup) && nodeSample.value) {
        nodeSample.value.sample_size = sampleSize.value;
      } else {
        if (nodeSample.value) {
          sampleSize.value = nodeSample.value.sample_size;
        }
      }
      dataLoaded.value = true;
      if ((_c = nodeSample.value) == null ? void 0 : _c.is_setup) {
        nodeSample.value.is_setup = true;
      }
    };
    const handleClickOutside = (event) => {
      var _a;
      if (!((_a = contextMenuRef.value) == null ? void 0 : _a.contains(event.target))) {
        showContextMenu.value = false;
        contextMenuColumn.value = null;
        showContextMenuRemove.value = false;
      }
    };
    const pushNodeData = async () => {
      if (nodeSample.value) {
        nodeSample.value.sample_size = sampleSize.value;
      }
      nodeStore.updateSettings(nodeSample);
      dataLoaded.value = false;
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
      const _component_el_col = resolveComponent("el-col");
      const _component_el_row = resolveComponent("el-row");
      return dataLoaded.value && nodeSample.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeSample.value,
          "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => nodeSample.value = $event)
        }, {
          default: withCtx(() => [
            createBaseVNode("div", _hoisted_2, [
              _cache[3] || (_cache[3] = createBaseVNode("div", { class: "listbox-subtitle" }, "Settings", -1)),
              createVNode(_component_el_row, null, {
                default: withCtx(() => [
                  createVNode(_component_el_col, {
                    span: 10,
                    class: "grid-content"
                  }, {
                    default: withCtx(() => _cache[2] || (_cache[2] = [
                      createTextVNode("Offset")
                    ])),
                    _: 1,
                    __: [2]
                  }),
                  createVNode(_component_el_col, {
                    span: 8,
                    class: "grid-content"
                  }, {
                    default: withCtx(() => [
                      withDirectives(createBaseVNode("input", {
                        "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => sampleSize.value = $event),
                        type: "number",
                        min: "0",
                        step: "1"
                      }, null, 512), [
                        [vModelText, sampleSize.value]
                      ])
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              })
            ])
          ]),
          _: 1
        }, 8, ["modelValue"])
      ])) : createCommentVNode("", true);
    };
  }
});
export {
  _sfc_main as default
};
