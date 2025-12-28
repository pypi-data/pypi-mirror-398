import { f as fetchSecretsApi } from "./secretApi-68435402.js";
import { d as defineComponent, r as ref, n as onMounted, c as openBlock, e as createElementBlock, p as createBaseVNode, t as toDisplayString, F as Fragment, q as renderList, i as createCommentVNode, _ as _export_sfc } from "./index-5429bbf8.js";
const _hoisted_1 = { class: "connection-settings-container" };
const _hoisted_2 = { class: "toggle-button" };
const _hoisted_3 = {
  key: 0,
  class: "connection-content"
};
const _hoisted_4 = { class: "form-group" };
const _hoisted_5 = ["value"];
const _hoisted_6 = { class: "form-group" };
const _hoisted_7 = ["value"];
const _hoisted_8 = { class: "form-group" };
const _hoisted_9 = ["value"];
const _hoisted_10 = ["value"];
const _hoisted_11 = { class: "form-group" };
const _hoisted_12 = ["value"];
const _hoisted_13 = { class: "form-row" };
const _hoisted_14 = { class: "form-group half" };
const _hoisted_15 = ["value"];
const _hoisted_16 = { class: "form-group half" };
const _hoisted_17 = ["value"];
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "DatabaseConnectionSettings",
  props: {
    modelValue: {}
  },
  emits: ["update:modelValue"],
  setup(__props, { emit: __emit }) {
    const props = __props;
    const emit = __emit;
    const isExpanded = ref(false);
    const availableSecrets = ref([]);
    const updateField = (field, value) => {
      emit("update:modelValue", {
        ...props.modelValue,
        [field]: value
      });
    };
    const fetchSecrets = async () => {
      try {
        const secrets = await fetchSecretsApi();
        availableSecrets.value = secrets;
      } catch (error) {
        console.error(
          "Error fetching secrets:",
          error instanceof Error ? error.message : String(error)
        );
        availableSecrets.value = [];
      }
    };
    const toggleExpanded = () => {
      isExpanded.value = !isExpanded.value;
    };
    onMounted(() => {
      fetchSecrets();
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        createBaseVNode("div", {
          class: "connection-header",
          onClick: toggleExpanded
        }, [
          _cache[6] || (_cache[6] = createBaseVNode("h4", { class: "connection-title" }, "In line connection settings", -1)),
          createBaseVNode("button", _hoisted_2, toDisplayString(isExpanded.value ? "▲" : "▼"), 1)
        ]),
        isExpanded.value ? (openBlock(), createElementBlock("div", _hoisted_3, [
          createBaseVNode("div", _hoisted_4, [
            _cache[8] || (_cache[8] = createBaseVNode("label", { for: "database-type" }, "Database Type", -1)),
            createBaseVNode("select", {
              id: "database-type",
              value: _ctx.modelValue.database_type,
              class: "form-control",
              onChange: _cache[0] || (_cache[0] = (e) => updateField("database_type", e.target.value))
            }, _cache[7] || (_cache[7] = [
              createBaseVNode("option", { value: "postgresql" }, "PostgreSQL", -1)
            ]), 40, _hoisted_5)
          ]),
          createBaseVNode("div", _hoisted_6, [
            _cache[9] || (_cache[9] = createBaseVNode("label", { for: "username" }, "Username", -1)),
            createBaseVNode("input", {
              id: "username",
              value: _ctx.modelValue.username,
              type: "text",
              class: "form-control",
              placeholder: "Enter username",
              onInput: _cache[1] || (_cache[1] = (e) => updateField("username", e.target.value))
            }, null, 40, _hoisted_7)
          ]),
          createBaseVNode("div", _hoisted_8, [
            _cache[11] || (_cache[11] = createBaseVNode("label", { for: "password-ref" }, "Password Reference", -1)),
            createBaseVNode("select", {
              id: "password-ref",
              value: _ctx.modelValue.password_ref,
              class: "form-control",
              onChange: _cache[2] || (_cache[2] = (e) => updateField("password_ref", e.target.value))
            }, [
              _cache[10] || (_cache[10] = createBaseVNode("option", { value: "" }, "Select a password from the secrets", -1)),
              (openBlock(true), createElementBlock(Fragment, null, renderList(availableSecrets.value, (secret) => {
                return openBlock(), createElementBlock("option", {
                  key: secret.name,
                  value: secret.name
                }, toDisplayString(secret.name), 9, _hoisted_10);
              }), 128))
            ], 40, _hoisted_9)
          ]),
          createBaseVNode("div", _hoisted_11, [
            _cache[12] || (_cache[12] = createBaseVNode("label", { for: "host" }, "Host", -1)),
            createBaseVNode("input", {
              id: "host",
              value: _ctx.modelValue.host,
              type: "text",
              class: "form-control",
              placeholder: "Enter host",
              onInput: _cache[3] || (_cache[3] = (e) => updateField("host", e.target.value))
            }, null, 40, _hoisted_12)
          ]),
          createBaseVNode("div", _hoisted_13, [
            createBaseVNode("div", _hoisted_14, [
              _cache[13] || (_cache[13] = createBaseVNode("label", { for: "port" }, "Port", -1)),
              createBaseVNode("input", {
                id: "port",
                value: _ctx.modelValue.port,
                type: "number",
                class: "form-control",
                placeholder: "Enter port",
                onInput: _cache[4] || (_cache[4] = (e) => updateField("port", Number(e.target.value)))
              }, null, 40, _hoisted_15)
            ]),
            createBaseVNode("div", _hoisted_16, [
              _cache[14] || (_cache[14] = createBaseVNode("label", { for: "database" }, "Database", -1)),
              createBaseVNode("input", {
                id: "database",
                value: _ctx.modelValue.database,
                type: "text",
                class: "form-control",
                placeholder: "Enter database name",
                onInput: _cache[5] || (_cache[5] = (e) => updateField("database", e.target.value))
              }, null, 40, _hoisted_17)
            ])
          ])
        ])) : createCommentVNode("", true)
      ]);
    };
  }
});
const DatabaseConnectionSettings_vue_vue_type_style_index_0_scoped_2fd11b08_lang = "";
const DatabaseConnectionSettings = /* @__PURE__ */ _export_sfc(_sfc_main, [["__scopeId", "data-v-2fd11b08"]]);
export {
  DatabaseConnectionSettings as default
};
