import { C as CodeLoader } from "./vue-content-loader.es-2c8e608f.js";
import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { C as ColumnSelector } from "./dropDown-614b998d.js";
import { s as selectDynamic } from "./selectDynamic-92e25ee3.js";
import { G as GenericNodeSettings } from "./genericNodeSettings-4fe5f36b.js";
import { d as defineComponent, r as ref, l as computed, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, p as createBaseVNode, h as createBlock, i as createCommentVNode, F as Fragment, q as renderList, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
import "./UnavailableFields-a03f512c.js";
import "./designer-9633482a.js";
const _hoisted_1 = {
  key: 0,
  class: "listbox-wrapper"
};
const _hoisted_2 = { class: "join-content" };
const _hoisted_3 = { class: "join-type-selector" };
const _hoisted_4 = { class: "join-mapping-section" };
const _hoisted_5 = { class: "table-wrapper" };
const _hoisted_6 = { class: "selectors-container" };
const _hoisted_7 = { class: "action-buttons" };
const _hoisted_8 = ["onClick"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "Join",
  setup(__props, { expose: __expose }) {
    const joinTypes = ["inner", "left", "right", "full", "semi", "anti", "cross"];
    const JOIN_TYPES_WITHOUT_COLUMN_SELECTION = ["anti", "semi"];
    const handleJoinTypeError = (error) => {
      console.error("Join type error:", error);
    };
    const result = ref(null);
    const nodeStore = useNodeStore();
    const dataLoaded = ref(false);
    const nodeJoin = ref(null);
    const updateSelectInputsHandler = (updatedInputs, isLeft) => {
      if (isLeft && nodeJoin.value) {
        nodeJoin.value.join_input.left_select.renames = updatedInputs;
      } else if (nodeJoin.value) {
        nodeJoin.value.join_input.right_select.renames = updatedInputs;
      }
    };
    const loadNodeData = async (nodeId) => {
      var _a;
      result.value = await nodeStore.getNodeData(nodeId, false);
      nodeJoin.value = (_a = result.value) == null ? void 0 : _a.setting_input;
      if (result.value) {
        dataLoaded.value = true;
      }
    };
    const addJoinCondition = () => {
      if (nodeJoin.value) {
        nodeJoin.value.join_input.join_mapping.push({
          left_col: "",
          right_col: ""
        });
      }
    };
    const showColumnSelection = computed(() => {
      var _a;
      const joinType = (_a = nodeJoin.value) == null ? void 0 : _a.join_input.how;
      return joinType && !JOIN_TYPES_WITHOUT_COLUMN_SELECTION.includes(joinType);
    });
    const removeJoinCondition = (index) => {
      if (nodeJoin.value && index >= 0) {
        nodeJoin.value.join_input.join_mapping.splice(index, 1);
      }
    };
    const handleChange = (newValue, index, side) => {
      if (side === "left") {
        if (nodeJoin.value) {
          nodeJoin.value.join_input.join_mapping[index].left_col = newValue;
        }
      } else {
        if (nodeJoin.value) {
          nodeJoin.value.join_input.join_mapping[index].right_col = newValue;
        }
      }
    };
    const pushNodeData = async () => {
      console.log("Pushing node data");
      nodeStore.updateSettings(nodeJoin);
    };
    __expose({
      loadNodeData,
      pushNodeData
    });
    return (_ctx, _cache) => {
      return dataLoaded.value && nodeJoin.value ? (openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(GenericNodeSettings, {
          modelValue: nodeJoin.value,
          "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => nodeJoin.value = $event)
        }, {
          default: withCtx(() => {
            var _a, _b, _c;
            return [
              _cache[6] || (_cache[6] = createBaseVNode("div", { class: "listbox-subtitle" }, "Join columns", -1)),
              createBaseVNode("div", _hoisted_2, [
                createBaseVNode("div", _hoisted_3, [
                  _cache[4] || (_cache[4] = createBaseVNode("label", { class: "join-type-label" }, "Join Type:", -1)),
                  nodeJoin.value ? (openBlock(), createBlock(ColumnSelector, {
                    key: 0,
                    modelValue: nodeJoin.value.join_input.how,
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => nodeJoin.value.join_input.how = $event),
                    "column-options": joinTypes,
                    placeholder: "Select join type",
                    "allow-other": false,
                    onError: handleJoinTypeError
                  }, null, 8, ["modelValue"])) : createCommentVNode("", true)
                ]),
                createBaseVNode("div", _hoisted_4, [
                  createBaseVNode("div", _hoisted_5, [
                    _cache[5] || (_cache[5] = createBaseVNode("div", { class: "selectors-header" }, [
                      createBaseVNode("div", { class: "selectors-title" }, "L"),
                      createBaseVNode("div", { class: "selectors-title" }, "R"),
                      createBaseVNode("div", { class: "selectors-title" })
                    ], -1)),
                    createBaseVNode("div", _hoisted_6, [
                      (openBlock(true), createElementBlock(Fragment, null, renderList((_a = nodeJoin.value) == null ? void 0 : _a.join_input.join_mapping, (selector, index) => {
                        var _a2, _b2, _c2, _d, _e, _f, _g;
                        return openBlock(), createElementBlock("div", {
                          key: index,
                          class: "selectors-row"
                        }, [
                          createVNode(ColumnSelector, {
                            modelValue: selector.left_col,
                            "onUpdate:modelValue": ($event) => selector.left_col = $event,
                            value: selector.left_col,
                            "column-options": (_b2 = (_a2 = result.value) == null ? void 0 : _a2.main_input) == null ? void 0 : _b2.columns,
                            "onUpdate:value": (value) => handleChange(value, index, "left")
                          }, null, 8, ["modelValue", "onUpdate:modelValue", "value", "column-options", "onUpdate:value"]),
                          createVNode(ColumnSelector, {
                            modelValue: selector.right_col,
                            "onUpdate:modelValue": ($event) => selector.right_col = $event,
                            value: selector.right_col,
                            "column-options": (_d = (_c2 = result.value) == null ? void 0 : _c2.right_input) == null ? void 0 : _d.columns,
                            "onUpdate:value": (value) => handleChange(value, index, "right")
                          }, null, 8, ["modelValue", "onUpdate:modelValue", "value", "column-options", "onUpdate:value"]),
                          createBaseVNode("div", _hoisted_7, [
                            index !== (((_e = nodeJoin.value) == null ? void 0 : _e.join_input.join_mapping.length) ?? 0) - 1 ? (openBlock(), createElementBlock("button", {
                              key: 0,
                              class: "action-button remove-button",
                              onClick: ($event) => removeJoinCondition(index)
                            }, " - ", 8, _hoisted_8)) : createCommentVNode("", true),
                            index === (((_g = (_f = nodeJoin.value) == null ? void 0 : _f.join_input.join_mapping) == null ? void 0 : _g.length) ?? 0) - 1 ? (openBlock(), createElementBlock("button", {
                              key: 1,
                              class: "action-button add-button",
                              onClick: addJoinCondition
                            }, " + ")) : createCommentVNode("", true)
                          ])
                        ]);
                      }), 128))
                    ])
                  ])
                ])
              ]),
              showColumnSelection.value ? (openBlock(), createBlock(selectDynamic, {
                key: 0,
                "select-inputs": (_b = nodeJoin.value) == null ? void 0 : _b.join_input.left_select.renames,
                "show-keep-option": true,
                "show-title": true,
                "show-headers": true,
                "show-data": true,
                title: "Left data",
                onUpdateSelectInputs: _cache[1] || (_cache[1] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, true))
              }, null, 8, ["select-inputs"])) : createCommentVNode("", true),
              showColumnSelection.value ? (openBlock(), createBlock(selectDynamic, {
                key: 1,
                "select-inputs": (_c = nodeJoin.value) == null ? void 0 : _c.join_input.right_select.renames,
                "show-keep-option": true,
                "show-headers": true,
                "show-title": true,
                "show-data": true,
                title: "Right data",
                onUpdateSelectInputs: _cache[2] || (_cache[2] = (updatedInputs) => updateSelectInputsHandler(updatedInputs, true))
              }, null, 8, ["select-inputs"])) : createCommentVNode("", true)
            ];
          }),
          _: 1,
          __: [6]
        }, 8, ["modelValue"])
      ])) : (openBlock(), createBlock(unref(CodeLoader), { key: 1 }));
    };
  }
});
const Join_vue_vue_type_style_index_0_scoped_7d5cefa4_lang = "";
const Join = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-7d5cefa4"]]);
export {
  Join as default
};
