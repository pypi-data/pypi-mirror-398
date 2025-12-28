import { u as useNodeStore } from "./vue-codemirror.esm-41b0e0d7.js";
import { i as info_filled_default } from "./designer-9633482a.js";
import { d as defineComponent, r as ref, m as watch, b as resolveComponent, c as openBlock, e as createElementBlock, f as createVNode, w as withCtx, L as renderSlot, p as createBaseVNode, g as createTextVNode, u as unref, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "settings-wrapper" };
const _hoisted_2 = { class: "settings-section" };
const _hoisted_3 = { class: "setting-group" };
const _hoisted_4 = { class: "setting-header" };
const _hoisted_5 = { class: "setting-description-wrapper" };
const _hoisted_6 = { class: "setting-description" };
const _hoisted_7 = { class: "setting-group" };
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "genericNodeSettings",
  props: {
    modelValue: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    var _a, _b;
    const nodeStore = useNodeStore();
    const props = __props;
    const emit = __emit;
    const activeTab = ref("main");
    const localSettings = ref({
      cache_results: ((_a = props.modelValue) == null ? void 0 : _a.cache_results) ?? false,
      description: ((_b = props.modelValue) == null ? void 0 : _b.description) ?? ""
    });
    watch(
      () => props.modelValue,
      (newValue) => {
        if (newValue) {
          localSettings.value = {
            cache_results: newValue.cache_results,
            description: newValue.description ?? ""
          };
        }
      },
      { deep: true }
    );
    const handleSettingChange = () => {
      emit("update:modelValue", {
        ...props.modelValue,
        cache_results: localSettings.value.cache_results,
        description: localSettings.value.description
      });
    };
    const handleDescriptionChange = (value) => {
      nodeStore.updateNodeDescription(props.modelValue.node_id, value);
      handleSettingChange();
    };
    return (_ctx, _cache) => {
      const _component_el_tab_pane = resolveComponent("el-tab-pane");
      const _component_el_icon = resolveComponent("el-icon");
      const _component_el_tooltip = resolveComponent("el-tooltip");
      const _component_el_switch = resolveComponent("el-switch");
      const _component_el_input = resolveComponent("el-input");
      const _component_el_tabs = resolveComponent("el-tabs");
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createVNode(_component_el_tabs, {
          modelValue: activeTab.value,
          "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => activeTab.value = $event)
        }, {
          default: withCtx(() => [
            createVNode(_component_el_tab_pane, {
              label: "Main Settings",
              name: "main"
            }, {
              default: withCtx(() => [
                renderSlot(_ctx.$slots, "default", {}, void 0, true)
              ]),
              _: 3
            }),
            createVNode(_component_el_tab_pane, {
              label: "General Settings",
              name: "general"
            }, {
              default: withCtx(() => [
                createBaseVNode("div", _hoisted_2, [
                  createBaseVNode("div", _hoisted_3, [
                    createBaseVNode("div", _hoisted_4, [
                      _cache[4] || (_cache[4] = createBaseVNode("span", { class: "setting-title" }, "Cache Results", -1)),
                      createBaseVNode("div", _hoisted_5, [
                        createBaseVNode("span", _hoisted_6, [
                          _cache[3] || (_cache[3] = createTextVNode(" Store results on disk to speed up subsequent executions and verify results. ")),
                          createVNode(_component_el_tooltip, {
                            effect: "dark",
                            content: "Caching is only active when the flow is executed in performance mode",
                            placement: "top"
                          }, {
                            default: withCtx(() => [
                              createVNode(_component_el_icon, { class: "info-icon" }, {
                                default: withCtx(() => [
                                  createVNode(unref(info_filled_default))
                                ]),
                                _: 1
                              })
                            ]),
                            _: 1
                          })
                        ])
                      ])
                    ]),
                    createVNode(_component_el_switch, {
                      modelValue: localSettings.value.cache_results,
                      "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => localSettings.value.cache_results = $event),
                      onChange: handleSettingChange
                    }, null, 8, ["modelValue"])
                  ]),
                  createBaseVNode("div", _hoisted_7, [
                    _cache[5] || (_cache[5] = createBaseVNode("div", { class: "setting-header" }, [
                      createBaseVNode("span", { class: "setting-title" }, "Node Description"),
                      createBaseVNode("span", { class: "setting-description" }, " Add a description to document this node's purpose ")
                    ], -1)),
                    createVNode(_component_el_input, {
                      modelValue: localSettings.value.description,
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => localSettings.value.description = $event),
                      type: "textarea",
                      rows: 4,
                      placeholder: "Add a description for this node...",
                      onChange: handleDescriptionChange
                    }, null, 8, ["modelValue"])
                  ])
                ])
              ]),
              _: 1
            })
          ]),
          _: 3
        }, 8, ["modelValue"])
      ]);
    };
  }
});
const genericNodeSettings_vue_vue_type_style_index_0_scoped_61b43f35_lang = "";
const GenericNodeSettings = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-61b43f35"]]);
export {
  GenericNodeSettings as G
};
