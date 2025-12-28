import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { s as selectDynamic } from "./selectDynamic-92e25ee3.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { d as defineComponent, r as ref, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, h as createBlock, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import "./UnavailableFields-a03f512c.js";
import "./designer-9633482a.js";
const _hoisted_1 = { key: 0 };
const _hoisted_2 = { class: "listbox-wrapper" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "CrossJoin",
  setup(__props, { expose: __expose }) {
    const result = ref(null);
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeCrossJoin = ref(null);
    const updateSelectInputsHandler = (updatedInputs, isLeft) => {
      if (isLeft && nodeCrossJoin.value) {
        nodeCrossJoin.value.cross_join_input.left_select.renames = updatedInputs;
      } else if (nodeCrossJoin.value) {
        nodeCrossJoin.value.cross_join_input.right_select.renames = updatedInputs;
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      result.value = await nodeStore.getNodeData(nodeId, false);
      nodeCrossJoin.value = (_a = result.value) == null ? void 0 : _a.setting_input;
      console.log(result.value);
      if (result.value) {
        console.log("Data loaded");
        dataLoaded.value = true;
      }
    };
    const pushNodeData = async () => {
      console.log("Pushing node data");
      nodeStore.updateSettings(nodeCrossJoin);
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeCrossJoin.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeCrossJoin.value,
          "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => nodeCrossJoin.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b;
            return [
              createBaseVNode("div", _hoisted_2, [
                createVNode(selectDynamic, {
                  "select-inputs": (_a = nodeCrossJoin.value) == null ? void 0 : _a.cross_join_input.left_select.renames,
                  "show-keep-option": true,
                  "show-title": true,
                  "show-headers": true,
                  "show-data": true,
                  title: "Left data",
                  onUpdateSelectInputs: _cache[0] || (_cache[0] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, true))
                }, null, 8, ["select-inputs"]),
                createVNode(selectDynamic, {
                  "select-inputs": (_b = nodeCrossJoin.value) == null ? void 0 : _b.cross_join_input.right_select.renames,
                  "show-keep-option": true,
                  "show-headers": true,
                  "show-title": true,
                  "show-data": true,
                  title: "Right data",
                  onUpdateSelectInputs: _cache[1] || (_cache[1] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, true))
                }, null, 8, ["select-inputs"])
              ])
            ];
          }),
          _: 1
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const CrossJoin_vue_vue_type_style_index_0_scoped_e594e542_lang = "";
const CrossJoin = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-e594e542"]]);
export {
  CrossJoin as default
};
