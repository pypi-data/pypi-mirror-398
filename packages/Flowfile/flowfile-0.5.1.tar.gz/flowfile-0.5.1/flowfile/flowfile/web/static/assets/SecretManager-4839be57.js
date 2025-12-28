import { r as ref, l as computed, d as defineComponent, n as onMounted, e as createElementBlock, p as createBaseVNode, v as withModifiers, a8 as withDirectives, a9 as vModelText, al as vModelDynamic, s as normalizeClass, g as createTextVNode, t as toDisplayString, u as unref, O as isRef, i as createCommentVNode, F as Fragment, q as renderList, c as openBlock } from "./index-5429bbf8.js";
import { f as fetchSecretsApi, a as addSecretApi, g as getSecretValueApi, d as deleteSecretApi } from "./secretApi-68435402.js";
function useSecretManager() {
  const secrets = ref([]);
  const isLoading = ref(true);
  const searchTerm = ref("");
  const visibleSecrets = ref([]);
  const copyMessage = ref("");
  const filteredSecrets = computed(() => {
    const sortedSecrets = [...secrets.value].sort((a, b) => a.name.localeCompare(b.name));
    if (!searchTerm.value) {
      return sortedSecrets;
    }
    const term = searchTerm.value.toLowerCase();
    return sortedSecrets.filter((secret) => secret.name.toLowerCase().includes(term));
  });
  const loadSecrets = async () => {
    isLoading.value = true;
    visibleSecrets.value = [];
    try {
      secrets.value = await fetchSecretsApi();
    } catch (error) {
      console.error("Failed to load secrets:", error);
      secrets.value = [];
      throw error;
    } finally {
      isLoading.value = false;
    }
  };
  const addSecret = async (secretInput) => {
    if (secrets.value.some((s) => s.name === secretInput.name)) {
      throw new Error(`Secret with name "${secretInput.name}" already exists.`);
    }
    try {
      await addSecretApi({ ...secretInput });
      await loadSecrets();
      return secretInput.name;
    } catch (error) {
      console.error("Failed to add secret:", error);
      throw error;
    }
  };
  const toggleSecretVisibility = (secretName) => {
    const index = visibleSecrets.value.indexOf(secretName);
    if (index === -1) {
      visibleSecrets.value.push(secretName);
    } else {
      visibleSecrets.value.splice(index, 1);
    }
  };
  const copySecretToClipboard = async (secretName) => {
    copyMessage.value = "";
    try {
      const secretValue = await getSecretValueApi(secretName);
      await navigator.clipboard.writeText(secretValue);
      copyMessage.value = `Value for '${secretName}' copied!`;
      setTimeout(() => {
        copyMessage.value = "";
      }, 2500);
      return true;
    } catch (error) {
      console.error("Failed to copy secret:", error);
      copyMessage.value = `Failed to copy ${secretName}.`;
      setTimeout(() => {
        copyMessage.value = "";
      }, 3e3);
      throw error;
    }
  };
  const deleteSecret = async (secretName) => {
    try {
      await deleteSecretApi(secretName);
      await loadSecrets();
      return secretName;
    } catch (error) {
      console.error("Failed to delete secret:", error);
      throw error;
    }
  };
  return {
    secrets,
    filteredSecrets,
    isLoading,
    searchTerm,
    visibleSecrets,
    copyMessage,
    loadSecrets,
    addSecret,
    toggleSecretVisibility,
    copySecretToClipboard,
    deleteSecret
  };
}
const _hoisted_1 = { class: "secret-manager-container" };
const _hoisted_2 = { class: "card mb-3" };
const _hoisted_3 = { class: "card-content" };
const _hoisted_4 = { class: "form-grid" };
const _hoisted_5 = { class: "form-field" };
const _hoisted_6 = { class: "form-field" };
const _hoisted_7 = { class: "password-field" };
const _hoisted_8 = ["type"];
const _hoisted_9 = { class: "form-actions" };
const _hoisted_10 = ["disabled"];
const _hoisted_11 = { class: "card mb-3" };
const _hoisted_12 = { class: "card-header" };
const _hoisted_13 = { class: "card-title" };
const _hoisted_14 = {
  key: 0,
  class: "search-container"
};
const _hoisted_15 = { class: "card-content" };
const _hoisted_16 = {
  key: 0,
  class: "loading-state"
};
const _hoisted_17 = {
  key: 1,
  class: "empty-state"
};
const _hoisted_18 = {
  key: 2,
  class: "flex-col gap-2"
};
const _hoisted_19 = { class: "secret-info" };
const _hoisted_20 = { class: "secret-name" };
const _hoisted_21 = { class: "secret-actions" };
const _hoisted_22 = ["aria-label", "onClick"];
const _hoisted_23 = {
  key: 3,
  class: "empty-state"
};
const _hoisted_24 = { class: "modal-content" };
const _hoisted_25 = { class: "modal-actions" };
const _hoisted_26 = ["disabled"];
const _hoisted_27 = {
  key: 0,
  class: "fas fa-spinner fa-spin"
};
const _sfc_main = /* @__PURE__ */ defineComponent({
  __name: "SecretManager",
  setup(__props) {
    const { secrets, filteredSecrets, isLoading, searchTerm, loadSecrets, addSecret, deleteSecret } = useSecretManager();
    const newSecret = ref({ name: "", value: "" });
    const showNewSecret = ref(false);
    const isSubmitting = ref(false);
    const isDeleting = ref(false);
    const showDeleteModal = ref(false);
    const secretToDelete = ref("");
    const handleAddSecret = async () => {
      if (!newSecret.value.name || !newSecret.value.value)
        return;
      isSubmitting.value = true;
      try {
        const secretName = await addSecret(newSecret.value);
        newSecret.value = { name: "", value: "" };
        showNewSecret.value = false;
        alert(`Secret "${secretName}" added successfully.`);
      } catch (error) {
        const errorMsg = error.message || "An unknown error occurred while adding the secret.";
        alert(`Error adding secret: ${errorMsg}`);
      } finally {
        isSubmitting.value = false;
      }
    };
    const handleConfirmDelete = (secretName) => {
      secretToDelete.value = secretName;
      showDeleteModal.value = true;
    };
    const cancelDelete = () => {
      showDeleteModal.value = false;
      secretToDelete.value = "";
    };
    const handleDeleteSecret = async () => {
      if (!secretToDelete.value)
        return;
      isDeleting.value = true;
      try {
        const nameToDelete = secretToDelete.value;
        await deleteSecret(nameToDelete);
        cancelDelete();
        alert(`Secret "${nameToDelete}" deleted successfully.`);
      } catch (error) {
        alert("Failed to delete secret. Please try again.");
        cancelDelete();
      } finally {
        isDeleting.value = false;
      }
    };
    onMounted(() => {
      loadSecrets().catch((error) => {
        alert("Failed to load secrets. Please try again.");
      });
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", _hoisted_1, [
        _cache[21] || (_cache[21] = createBaseVNode("div", { class: "mb-3" }, [
          createBaseVNode("h2", { class: "page-title" }, "Secret Manager"),
          createBaseVNode("p", { class: "page-description" }, "Securely store and manage credentials for your integrations")
        ], -1)),
        createBaseVNode("div", _hoisted_2, [
          _cache[8] || (_cache[8] = createBaseVNode("div", { class: "card-header" }, [
            createBaseVNode("h3", { class: "card-title" }, "Add New Secret")
          ], -1)),
          createBaseVNode("div", _hoisted_3, [
            createBaseVNode("form", {
              class: "form",
              onSubmit: withModifiers(handleAddSecret, ["prevent"])
            }, [
              createBaseVNode("div", _hoisted_4, [
                createBaseVNode("div", _hoisted_5, [
                  _cache[5] || (_cache[5] = createBaseVNode("label", {
                    for: "secret-name",
                    class: "form-label"
                  }, "Secret Name", -1)),
                  withDirectives(createBaseVNode("input", {
                    id: "secret-name",
                    "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => newSecret.value.name = $event),
                    type: "text",
                    class: "form-input",
                    placeholder: "api_key, database_password, etc.",
                    required: ""
                  }, null, 512), [
                    [vModelText, newSecret.value.name]
                  ])
                ]),
                createBaseVNode("div", _hoisted_6, [
                  _cache[6] || (_cache[6] = createBaseVNode("label", {
                    for: "secret-value",
                    class: "form-label"
                  }, "Secret Value", -1)),
                  createBaseVNode("div", _hoisted_7, [
                    withDirectives(createBaseVNode("input", {
                      id: "secret-value",
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => newSecret.value.value = $event),
                      type: showNewSecret.value ? "text" : "password",
                      class: "form-input",
                      placeholder: "Enter secret value",
                      required: ""
                    }, null, 8, _hoisted_8), [
                      [vModelDynamic, newSecret.value.value]
                    ]),
                    createBaseVNode("button", {
                      type: "button",
                      class: "toggle-visibility",
                      "aria-label": "Toggle new secret visibility",
                      onClick: _cache[2] || (_cache[2] = ($event) => showNewSecret.value = !showNewSecret.value)
                    }, [
                      createBaseVNode("i", {
                        class: normalizeClass(showNewSecret.value ? "fa-solid fa-eye-slash" : "fa-solid fa-eye")
                      }, null, 2)
                    ])
                  ])
                ])
              ]),
              createBaseVNode("div", _hoisted_9, [
                createBaseVNode("button", {
                  type: "submit",
                  class: "btn btn-primary",
                  disabled: !newSecret.value.name || !newSecret.value.value || isSubmitting.value
                }, [
                  _cache[7] || (_cache[7] = createBaseVNode("i", { class: "fa-solid fa-plus" }, null, -1)),
                  createTextVNode(" " + toDisplayString(isSubmitting.value ? "Adding..." : "Add Secret"), 1)
                ], 8, _hoisted_10)
              ])
            ], 32)
          ])
        ]),
        createBaseVNode("div", _hoisted_11, [
          createBaseVNode("div", _hoisted_12, [
            createBaseVNode("h3", _hoisted_13, "Your Secrets (" + toDisplayString(unref(filteredSecrets).length) + ")", 1),
            unref(secrets).length > 0 ? (openBlock(), createElementBlock("div", _hoisted_14, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[3] || (_cache[3] = ($event) => isRef(searchTerm) ? searchTerm.value = $event : null),
                type: "text",
                placeholder: "Search secrets...",
                class: "search-input",
                "aria-label": "Search secrets"
              }, null, 512), [
                [vModelText, unref(searchTerm)]
              ]),
              _cache[9] || (_cache[9] = createBaseVNode("i", { class: "fa-solid fa-search search-icon" }, null, -1))
            ])) : createCommentVNode("", true)
          ]),
          createBaseVNode("div", _hoisted_15, [
            unref(isLoading) ? (openBlock(), createElementBlock("div", _hoisted_16, _cache[10] || (_cache[10] = [
              createBaseVNode("div", { class: "loading-spinner" }, null, -1),
              createBaseVNode("p", null, "Loading secrets...", -1)
            ]))) : !unref(isLoading) && unref(secrets).length === 0 ? (openBlock(), createElementBlock("div", _hoisted_17, _cache[11] || (_cache[11] = [
              createBaseVNode("i", { class: "fa-solid fa-lock" }, null, -1),
              createBaseVNode("p", null, "You haven't added any secrets yet", -1),
              createBaseVNode("p", null, "Secrets are securely stored and can be used in your flows", -1)
            ]))) : unref(filteredSecrets).length > 0 ? (openBlock(), createElementBlock("div", _hoisted_18, [
              (openBlock(true), createElementBlock(Fragment, null, renderList(unref(filteredSecrets), (secret) => {
                return openBlock(), createElementBlock("div", {
                  key: secret.name,
                  class: "secret-item"
                }, [
                  createBaseVNode("div", _hoisted_19, [
                    createBaseVNode("div", _hoisted_20, [
                      _cache[12] || (_cache[12] = createBaseVNode("i", { class: "fa-solid fa-key" }, null, -1)),
                      createBaseVNode("span", null, toDisplayString(secret.name), 1)
                    ]),
                    _cache[13] || (_cache[13] = createBaseVNode("div", { class: "secret-value" }, [
                      createBaseVNode("input", {
                        type: "password",
                        value: "••••••••••••••••",
                        readonly: "",
                        class: "form-input",
                        "aria-label": "Masked secret value"
                      })
                    ], -1))
                  ]),
                  createBaseVNode("div", _hoisted_21, [
                    createBaseVNode("button", {
                      type: "button",
                      class: "btn btn-danger",
                      "aria-label": `Delete secret ${secret.name}`,
                      onClick: ($event) => handleConfirmDelete(secret.name)
                    }, _cache[14] || (_cache[14] = [
                      createBaseVNode("i", { class: "fa-solid fa-trash-alt" }, null, -1),
                      createBaseVNode("span", null, "Delete", -1)
                    ]), 8, _hoisted_22)
                  ])
                ]);
              }), 128))
            ])) : (openBlock(), createElementBlock("div", _hoisted_23, [
              _cache[15] || (_cache[15] = createBaseVNode("i", { class: "fa-solid fa-search" }, null, -1)),
              createBaseVNode("p", null, 'No secrets found matching "' + toDisplayString(unref(searchTerm)) + '"', 1)
            ]))
          ])
        ]),
        showDeleteModal.value ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: "modal-overlay",
          onClick: cancelDelete
        }, [
          createBaseVNode("div", {
            class: "modal-container",
            onClick: _cache[4] || (_cache[4] = withModifiers(() => {
            }, ["stop"]))
          }, [
            createBaseVNode("div", { class: "modal-header" }, [
              _cache[17] || (_cache[17] = createBaseVNode("h3", { class: "modal-title" }, "Delete Secret", -1)),
              createBaseVNode("button", {
                class: "modal-close",
                "aria-label": "Close delete confirmation",
                onClick: cancelDelete
              }, _cache[16] || (_cache[16] = [
                createBaseVNode("i", { class: "fa-solid fa-times" }, null, -1)
              ]))
            ]),
            createBaseVNode("div", _hoisted_24, [
              createBaseVNode("p", null, [
                _cache[18] || (_cache[18] = createTextVNode(" Are you sure you want to delete the secret ")),
                createBaseVNode("strong", null, toDisplayString(secretToDelete.value), 1),
                _cache[19] || (_cache[19] = createTextVNode("? "))
              ]),
              _cache[20] || (_cache[20] = createBaseVNode("p", { class: "warning-text" }, " This action cannot be undone and may break any flows that use this secret. ", -1))
            ]),
            createBaseVNode("div", _hoisted_25, [
              createBaseVNode("button", {
                class: "btn btn-secondary",
                onClick: cancelDelete
              }, "Cancel"),
              createBaseVNode("button", {
                class: "btn btn-danger-filled",
                disabled: isDeleting.value,
                onClick: handleDeleteSecret
              }, [
                isDeleting.value ? (openBlock(), createElementBlock("i", _hoisted_27)) : createCommentVNode("", true),
                createTextVNode(" " + toDisplayString(isDeleting.value ? "Deleting..." : "Delete Secret"), 1)
              ], 8, _hoisted_26)
            ])
          ])
        ])) : createCommentVNode("", true)
      ]);
    };
  }
});
export {
  _sfc_main as default
};
